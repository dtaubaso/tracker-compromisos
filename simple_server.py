from flask import Flask, request, jsonify
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Deshabilitar la verificación de firma temporalmente para debugging
SKIP_VERIFICATION = True

@app.route('/')
def home():
    return 'Server is running!'

@app.route('/slack/events', methods=['POST'])
def slack_events():
    try:
        print("\n=== SLACK EVENTS REQUEST ===")
        print(f"Method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Headers: {dict(request.headers)}")
        
        # Obtener el body
        data = request.get_data(as_text=True)
        print(f"Raw body: {data[:200]}...")  # Primeros 200 caracteres
        
        # Intentar parsear JSON
        try:
            json_data = json.loads(data)
            print(f"Parsed JSON type: {json_data.get('type')}")
            
            # Manejar url_verification
            if json_data.get('type') == 'url_verification':
                print("URL verification challenge received")
                return jsonify({'challenge': json_data['challenge']})
                
        except Exception as e:
            print(f"Error parsing JSON: {e}")
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f"ERROR in slack_events: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/slack/interactions', methods=['POST'])
def slack_interactions():
    try:
        print("\n=== SLACK INTERACTIONS REQUEST ===")
        print(f"Method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        
        # Obtener el payload
        payload_str = request.form.get('payload', '')
        print(f"Payload exists: {bool(payload_str)}")
        
        if payload_str:
            payload = json.loads(payload_str)
            print(f"Interaction type: {payload.get('type')}")
            print(f"User: {payload.get('user', {}).get('name')}")
            
            if payload['type'] == 'interactive_message':
                print("Button clicked!")
                
        return '', 200
        
    except Exception as e:
        print(f"ERROR in slack_interactions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Starting SIMPLE Debug Server")
    print("URL: http://localhost:5000")
    print("="*50 + "\n")
    
    # Usar servidor de desarrollo simple
    app.run(host='127.0.0.1', port=5000, debug=False)