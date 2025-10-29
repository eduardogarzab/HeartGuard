from flask import Flask

from config import settings
from responses import ok
from routes.media import bp as media_bp


def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    @app.get("/health")
    def health():
        return ok({"service": "media_service", "status": "healthy"})

    app.register_blueprint(media_bp)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        debug=(settings.FLASK_ENV == "development"),
    )
