"""Aplicación Flask para el Media Service."""
from __future__ import annotations

from flask import Flask

from .blueprints.media import media_bp
from .config import get_config
from .utils.responses import success_response


def create_app() -> Flask:
    """Crea y configura la instancia principal de Flask."""
    app = Flask(__name__)

    config = get_config()
    app.config.from_object(config)

    # Límite de carga máximo basado en configuración (en bytes)
    app.config["MAX_CONTENT_LENGTH"] = config.MEDIA_MAX_FILE_BYTES

    app.register_blueprint(media_bp)

    @app.route("/health", methods=["GET"])
    def health_check():  # pragma: no cover - endpoint trivial
        payload = {
            "service": "media-service",
            "status": "healthy",
            "cdn_base_url": app.config.get("MEDIA_CDN_BASE_URL"),
        }
        return success_response(data=payload, message="OK")

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - entrada manual
    cfg = get_config()
    app.run(host=cfg.HOST, port=cfg.PORT, debug=cfg.DEBUG)
