# signal_service/app.py
import os
from dotenv import load_dotenv
from app import create_app

# Cargar variables de entorno
load_dotenv()

# Crear la instancia de la aplicación usando la factory
app = create_app()

if __name__ == '__main__':
    # Obtener el puerto de las variables de entorno, con un valor por defecto
    port = int(os.getenv('SIGNAL_SERVICE_PORT', 8000))
    # Ejecutar la aplicación en modo de desarrollo.
    # Para producción, se debe usar un servidor WSGI como Gunicorn.
    # Ejemplo de Gunicorn: gunicorn --bind 0.0.0.0:5007 app:app
    app.run(debug=True, port=port)
