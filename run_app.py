import os
import sys
from main import app
import logging

if __name__ == '__main__':
    # Configuración para Windows
    if sys.platform == 'win32':
        # Evitar problemas con el buffer en Windows
        os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Deshabilitar el log de werkzeug para reducir ruido
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    print("\n" + "="*50)
    print("Starting Slack-Asana Integration Server")
    print(f"URL: http://localhost:5000")
    print("="*50 + "\n")
    
    # Ejecutar la aplicación con configuración más robusta
    try:
        app.run(
            host='0.0.0.0',  # Escuchar en todas las interfaces
            port=5000,
            debug=True,
            threaded=True,  # Importante para manejar múltiples requests
            use_reloader=False,  # Evitar problemas con el reloader en Windows
            processes=1  # Usar un solo proceso
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()