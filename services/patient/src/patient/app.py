"""
Aplicación Flask principal del Patient Service
"""
from flask import Flask, jsonify
from flask_cors import CORS
from .config import get_config
from .blueprints.patient import patient_bp


def create_app():
    """
    Factory para crear la aplicación Flask
    
    Returns:
        Flask app configurada
    """
    app = Flask(__name__)
    
    # Cargar configuración
    config = get_config()
    app.config.from_object(config)
    
    # Configurar CORS
    CORS(app, resources={
        r"/patient/*": {
            "origins": config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Registrar blueprints
    app.register_blueprint(patient_bp)
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'service': 'HeartGuard Patient Service',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'dashboard': '/patient/dashboard',
                'profile': '/patient/profile',
                'alerts': '/patient/alerts',
                'devices': '/patient/devices',
                'readings': '/patient/readings',
                'care_team': '/patient/care-team',
                'location': '/patient/location/latest',
                'health': '/patient/health'
            }
        }), 200
    
    # Health check global
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'patient-service'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'El recurso solicitado no existe'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Error interno del servidor'
        }), 500
    
    return app


# Crear instancia de la app
app = create_app()


if __name__ == '__main__':
    config = get_config()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
