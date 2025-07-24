import os
import json
import hashlib
import hmac
import time
import threading
from flask import Flask, request, jsonify
#from dotenv import load_dotenv
from llm_evaluator import evaluate_commitment
from slack_helpers import post_message_with_button, post_thread_message, get_user_info, open_task_dialog
from asana_client import create_asana_task
from channel_map import get_asana_project_id

#load_dotenv()

app = Flask(__name__)

SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

print(f"=== STARTING SLACK-ASANA INTEGRATION ===")
print(f"SLACK_BOT_TOKEN configured: {'Yes' if SLACK_BOT_TOKEN else 'No'}")
print(f"SLACK_SIGNING_SECRET configured: {'Yes' if SLACK_SIGNING_SECRET else 'No'}")
print(f"Bot token starts with: {SLACK_BOT_TOKEN[:10]}..." if SLACK_BOT_TOKEN else "No bot token")
print(f"="*40)

# Cache para evitar procesar eventos duplicados
processed_events = set()

@app.route('/')
def home():
    return 'Slack-Asana Integration Service is running!'

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'service': 'slack-asana-integration',
        'bot_token_configured': bool(SLACK_BOT_TOKEN),
        'signing_secret_configured': bool(SLACK_SIGNING_SECRET)
    })

@app.route('/test', methods=['GET', 'POST'])
def test():
    print(f"TEST endpoint hit - Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    if request.method == 'POST':
        print(f"Body: {request.get_data(as_text=True)}")
    return jsonify({'message': 'Test successful', 'method': request.method})

def verify_slack_signature(request_body, timestamp, signature):
    req = str.encode(f"v0:{timestamp}:{request_body}")
    request_hash = 'v0=' + hmac.new(
        str.encode(SLACK_SIGNING_SECRET),
        req,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(request_hash, signature)

def process_asana_task_creation(task_data):
    """Procesa la creación de tarea en Asana en un thread separado"""
    try:
        # Usar el proyecto seleccionado por el usuario, o el del canal como fallback
        asana_project_id = task_data.get('project_id')
        if not asana_project_id:
            asana_project_id = get_asana_project_id(task_data['channel'])
        
        # Obtener email del usuario seleccionado
        user_info = get_user_info(task_data['selected_user_id'])
        user_email = user_info.get('profile', {}).get('email')
        user_name = user_info.get('real_name', user_info.get('name', 'Usuario'))
        
        print(f"Usuario seleccionado: {user_name} - Email: {user_email}")
        print(f"Proyecto seleccionado: {asana_project_id}")
        
        # Crear tarea con título y descripción
        task_result = create_asana_task(
            name=task_data['title'],
            assignee_email=user_email,
            project_id=asana_project_id,
            due_on=task_data['due_date'],
            description=task_data['description'],
            subtasks=task_data['subtasks']
        )
        
        # Construir mensaje de confirmación
        confirmation_text = f"✅ Tarea creada: '{task_data['title']}' → [ver en Asana]({task_result['url']})"
        
        if task_result['assignee_found']:
            confirmation_text += f"\nAsignada a: <@{task_data['selected_user_id']}>"
        else:
            confirmation_text += f"\n⚠️ No se pudo asignar a <@{task_data['selected_user_id']}> (email no encontrado en Asana: {user_email})"
        
        if task_data['due_date']:
            confirmation_text += f"\nFecha límite: {task_data['due_date']}"
        
        post_thread_message(
            channel=task_data['channel'],
            thread_ts=task_data['thread_ts'],
            text=confirmation_text
        )
        
    except Exception as e:
        print(f"Error creando tarea: {str(e)}")
        post_thread_message(
            channel=task_data['channel'],
            thread_ts=task_data['thread_ts'],
            text=f"❌ Error al crear la tarea: {str(e)}"
        )

@app.route('/slack/events', methods=['POST'])
def slack_events():
    print("=== SLACK EVENTS ENDPOINT HIT ===")
    print(f"Headers: {dict(request.headers)}")
    print(f"Content-Type: {request.content_type}")
    
    if request.content_type != 'application/json':
        print(f"ERROR: Invalid content type: {request.content_type}")
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')
    
    if abs(time.time() - float(timestamp)) > 60 * 5:
        print("ERROR: Request timestamp too old")
        return jsonify({'error': 'Request timestamp too old'}), 400
    
    # Obtener el body raw para verificación
    request_body = request.get_data(as_text=True)
    
    if not verify_slack_signature(request_body, timestamp, signature):
        print("ERROR: Invalid signature")
        return jsonify({'error': 'Invalid signature'}), 403
    
    # Parsear el JSON después de verificar la firma
    try:
        data = json.loads(request_body)
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON")
        return jsonify({'error': 'Invalid JSON'}), 400
    
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data['challenge']})
    
    if 'event' in data:
        event = data['event']
        event_id = data.get('event_id')
        
        # Evitar procesar eventos duplicados
        if event_id in processed_events:
            return jsonify({'status': 'ok'})
        
        processed_events.add(event_id)
        
        # Limpiar cache después de 1000 eventos
        if len(processed_events) > 1000:
            processed_events.clear()
        
        if (event.get('type') == 'message' and 
            not event.get('bot_id') and 
            event.get('text')):
            
            text = event['text']
            
            if '@' in text:
                commitment_data = evaluate_commitment(text)
                
                if commitment_data and commitment_data.get('es_compromiso'):
                    channel = event['channel']
                    thread_ts = event.get('thread_ts', event['ts'])
                    
                    post_message_with_button(
                        channel=channel,
                        thread_ts=thread_ts,
                        original_message=text,
                        commitment_data=commitment_data,
                        message_ts=event['ts']
                    )
    
    return jsonify({'status': 'ok'})

@app.route('/slack/interactions', methods=['POST'])
def slack_interactions():
    print("=== INTERACTION ENDPOINT HIT ===")
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')
    
    if abs(time.time() - float(timestamp)) > 60 * 5:
        print("ERROR: Request timestamp too old")
        return jsonify({'error': 'Request timestamp too old'}), 400
    
    if not verify_slack_signature(request.get_data(as_text=True), timestamp, signature):
        print("ERROR: Invalid signature")
        return jsonify({'error': 'Invalid signature'}), 403
    
    payload = json.loads(request.form.get('payload'))
    print(f"Received interaction type: {payload.get('type')}")
    print(f"Full payload: {json.dumps(payload, indent=2)}")
    
    if payload['type'] == 'interactive_message':
        action = payload['actions'][0]
        
        if action['name'] == 'create_asana_task':
            print("=== BUTTON CLICKED: create_asana_task ===")
            action_value = json.loads(action['value'])
            commitment_data = action_value['commitment_data']
            channel = payload['channel']['id']
            thread_ts = action_value.get('thread_ts')
            trigger_id = payload['trigger_id']
            
            print(f"Channel: {channel}")
            print(f"Thread TS: {thread_ts}")
            print(f"Trigger ID: {trigger_id}")
            print(f"Commitment data: {commitment_data}")
            
            # Abrir el diálogo modal
            try:
                print("Attempting to open dialog...")
                result = open_task_dialog(
                    trigger_id=trigger_id,
                    commitment_data=commitment_data,
                    original_message=action_value['original_message'],
                    channel=channel,
                    thread_ts=thread_ts
                )
                print(f"Dialog open result: {result}")
                if not result.get('ok'):
                    print(f"Error opening dialog: {result}")
                    print(f"Error details: {result.get('error', 'No error details')}")
                else:
                    print("Dialog opened successfully!")
                
            except Exception as e:
                print(f"Exception opening dialog: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
            
            return '', 200
    
    elif payload['type'] == 'view_closed':
        # Usuario cerró el modal sin enviar
        print("Usuario canceló la creación de tarea")
        return jsonify({'status': 'ok'})
    
    elif payload['type'] == 'view_submission':
        # Manejar el envío del modal
        view = payload['view']
        
        if view['callback_id'] == 'create_asana_task_modal':
            metadata = json.loads(view['private_metadata'])
            
            # Obtener TODOS los valores del formulario
            values = view['state']['values']
            
            # Crear un diccionario con todos los datos necesarios
            task_data = {
                'channel': metadata['channel'],
                'thread_ts': metadata['thread_ts'],
                'selected_user_id': values['assignee_block']['assignee_select']['selected_user'],
                'due_date': values['due_date_block']['due_date_picker'].get('selected_date'),
                'title': values['title_block']['title_input']['value'],
                'description': values['description_block']['description_input']['value'],
                'subtasks': values['subtasks_block']['subtasks_input']['value'] if values['subtasks_block']['subtasks_input'].get('value') else None,
                'project_id': values['project_block']['project_select']['selected_option']['value']
            }
            
            # Iniciar thread para procesar la tarea
            thread = threading.Thread(target=process_asana_task_creation, args=(task_data,))
            thread.daemon = True
            thread.start()
            
            # Responder inmediatamente a Slack para cerrar el modal
            return '', 200
    
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)