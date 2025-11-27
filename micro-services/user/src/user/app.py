"""
Aplicación Flask principal del User Service
"""
from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from .blueprints.user import user_bp
from .config import get_config
from .utils.response_builder import error_response, fail_response, success_response


def create_app() -> Flask:
    """Factory para crear la aplicación Flask del servicio."""
    app = Flask(__name__)

    config = get_config()
    app.config.from_object(config)

    CORS(app, resources={
        r"/users/*": {
            "origins": config.CORS_ORIGINS,
            "methods": ["GET", "PATCH", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Trace-ID"],
        },
        r"/orgs/*": {
            "origins": config.CORS_ORIGINS,
            "methods": ["GET", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Trace-ID"],
        },
    })

    app.register_blueprint(user_bp)

    @app.route('/health', methods=['GET'])
    def global_health():  # pragma: no cover - endpoint simple
        return success_response(data={'service': 'user-service', 'status': 'healthy'}, message='OK')

    @app.errorhandler(404)
    def not_found(_error):  # pragma: no cover - uso genérico
        return fail_response(message='El recurso solicitado no existe', error_code='not_found', status_code=404)

    @app.errorhandler(500)
    def internal_error(_error):  # pragma: no cover - uso genérico
        return error_response(message='Error interno del servidor', error_code='internal_error', status_code=500)

    return app


app = create_app()


if __name__ == '__main__':  # pragma: no cover - entrada manual
    config = get_config()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
