# Compromisos Slack - Microservicio de integración Slack-Asana

Este microservicio detecta compromisos de trabajo en mensajes de Slack y permite crear tareas automáticamente en Asana.

## Características

- Detecta automáticamente compromisos de trabajo en mensajes de Slack usando IA (OpenAI o Claude)
- Ofrece crear tareas en Asana con un botón interactivo
- Mapea canales de Slack a proyectos de Asana
- Asigna tareas basándose en las menciones en el mensaje

## Requisitos previos

- Python 3.8 o superior
- Cuenta de Slack con permisos para crear aplicaciones
- Cuenta de Asana con acceso a la API
- API key de OpenAI o Claude

## Instalación

1. Clonar el repositorio:
```bash
git clone <repo-url>
cd compromisos_slack
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:
- `SLACK_BOT_TOKEN`: Token del bot de Slack (empieza con xoxb-)
- `SLACK_SIGNING_SECRET`: Secret para verificar requests de Slack
- `OPENAI_API_KEY` o `CLAUDE_API_KEY`: API key del LLM a usar
- `ASANA_PAT`: Personal Access Token de Asana

## Configuración de Slack

1. Crear una nueva app en https://api.slack.com/apps
2. En "OAuth & Permissions", agregar los siguientes scopes:
   - `chat:write`
   - `users:read`
   - `users:read.email`
3. Instalar la app en tu workspace y copiar el Bot User OAuth Token
4. En "Event Subscriptions":
   - Habilitar eventos
   - URL: `https://tu-dominio.com/slack/events`
   - Suscribirse a: `message.channels`, `message.groups`
5. En "Interactive Components":
   - Habilitar interactividad
   - Request URL: `https://tu-dominio.com/slack/interactions`

## Configuración de canales

Editar `channel_map.json` para mapear IDs de canales de Slack a IDs de proyectos de Asana:

```json
{
  "C1234567890": "1234567890123456",
  "C0987654321": "6543210987654321"
}
```

Para obtener el ID de un canal de Slack:
- Click derecho en el canal → "Ver detalles del canal" → ID al final de la URL

Para obtener el ID de un proyecto de Asana:
- Abrir el proyecto en Asana → copiar el número de la URL

## Ejecución

### Desarrollo local:
```bash
python main.py
```

El servidor correrá en http://localhost:5000

### Producción:
Se recomienda usar Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Con ngrok (para pruebas):
```bash
ngrok http 5000
```

Luego actualizar las URLs en la configuración de Slack con la URL de ngrok.

## Uso

1. El bot monitoreará automáticamente los mensajes en los canales donde esté instalado
2. Cuando detecte un posible compromiso (mensaje con @mención), mostrará un botón
3. Al hacer click en "Crear tarea en Asana", se creará la tarea y se confirmará en el hilo

## Estructura del proyecto

- `main.py`: Servidor Flask con endpoints para Slack
- `llm_evaluator.py`: Evaluación de compromisos usando IA
- `slack_helpers.py`: Funciones auxiliares para interactuar con Slack
- `asana_client.py`: Cliente para crear tareas en Asana
- `channel_map.py`: Mapeo de canales a proyectos
- `channel_map.json`: Configuración de mapeo de canales

## Troubleshooting

- **Error 403 en Slack**: Verificar el signing secret y que los eventos estén habilitados
- **No se detectan compromisos**: Verificar que el mensaje contenga una @mención
- **Error al crear tarea en Asana**: Verificar que el canal esté mapeado en channel_map.json
- **No encuentra el usuario en Asana**: El email del usuario de Slack debe coincidir con el de Asana

## Seguridad

- El microservicio valida todas las requests usando el signing secret de Slack
- Las credenciales se almacenan en variables de entorno
- No se almacena información sensible en archivos o logs#   t r a c k e r - c o m p r o m i s o s  
 #   t r a c k e r - c o m p r o m i s o s  
 #   t r a c k e r - c o m p r o m i s o s  
 #   t r a c k e r - c o m p r o m i s o s  
 #   t r a c k e r - c o m p r o m i s o s  
 #   t r a c k e r - c o m p r o m i s o s  
 #   t r a c k e r - c o m p r o m i s o s  
 