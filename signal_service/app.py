# signal_service/app.py
from app import create_app

# Crear la instancia de la aplicación usando la factory
app = create_app()

if __name__ == '__main__':
    # Ejecutar la aplicación en modo de desarrollo.
    # Para producción, se debe usar un servidor WSGI como Gunicorn.
    # Ejemplo de Gunicorn: gunicorn --bind 0.0.0.0:8000 app:app
    app.run(debug=True, port=8000)
