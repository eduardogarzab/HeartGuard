# signal_service/app/__init__.py
import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    """
    Application factory function.
    Initializes the Flask app, registers blueprints, and sets up teardown contexts.
    """
    app = Flask(__name__)

    # Cargar variables de entorno
    load_dotenv()

    # Configuración de la aplicación
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key')

    # Importar y registrar blueprints
    from .routes.ingest import ingest_bp
    from .routes.streams import streams_bp

    app.register_blueprint(ingest_bp, url_prefix='/api')
    app.register_blueprint(streams_bp, url_prefix='/api')

    # Registrar el teardown de la base de datos
    # Esto asegura que la sesión de SQLAlchemy se cierre correctamente después de cada request.
    from .database import SessionLocal
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        SessionLocal.remove()

    return app
