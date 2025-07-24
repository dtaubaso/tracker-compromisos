import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

def evaluate_commitment(message_text):
    prompt = f"""
    Este mensaje de Slack podría implicar un compromiso de trabajo. Si lo es, devolvé un JSON con este formato:
    {{
      "es_compromiso": true|false,
      "asignado_a": "nombre o ID de usuario",
      "descripcion": "tarea",
      "fecha_limite": "fecha o null"
    }}
    
    Mensaje: {message_text}
    """
    
    if OPENAI_API_KEY:
        return evaluate_with_openai(prompt)
    elif CLAUDE_API_KEY:
        return evaluate_with_claude(prompt)
    else:
        raise Exception("No LLM API key configured")

def evaluate_with_openai(prompt):
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system',
                'content': 'Eres un asistente que evalúa si los mensajes contienen compromisos de trabajo. Responde solo con JSON válido.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'temperature': 0.1
    }
    
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Intentar extraer JSON del contenido
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                return json.loads(content[json_start:json_end])
            return None
    else:
        print(f"Error calling OpenAI API: {response.status_code} - {response.text}")
        return None

def evaluate_with_claude(prompt):
    headers = {
        'x-api-key': CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'claude-3-opus-20240229',
        'max_tokens': 1000,
        'messages': [
            {
                'role': 'user',
                'content': prompt + "\n\nIMPORTANTE: Responde SOLO con el JSON solicitado, sin texto adicional."
            }
        ],
        'temperature': 0.1
    }
    
    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result['content'][0]['text']
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                return json.loads(content[json_start:json_end])
            return None
    else:
        print(f"Error calling Claude API: {response.status_code} - {response.text}")
        return None