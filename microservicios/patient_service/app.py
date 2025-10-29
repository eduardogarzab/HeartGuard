"""Application factory for the patient service."""

from flask import Flask
from flask_jwt_extended import JWTManager

from config import settings
from responses import err, ok
from routes.patients import bp as patients_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET
    app.config["JWT_ALGORITHM"] = settings.JWT_ALGORITHM
    app.config["JSON_SORT_KEYS"] = False
    app.config["JWT_IDENTITY_CLAIM"] = "identity"
    app.config["JWT_DECODE_SUBJECT"] = False

    jwt = JWTManager(app)

    @jwt.invalid_token_loader
    def invalid_token(reason: str):
        return err("Token inválido", code="token_invalid", status=422, details={"reason": reason})

    @jwt.unauthorized_loader
    def missing_token(reason: str):
        return err(
            "Cabecera de autorización inválida",
            code="auth_header_missing",
            status=401,
            details={"reason": reason},
        )

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):  # pragma: no cover - handled by library
        return err("Token expirado", code="token_expired", status=401)

    @app.get("/health")
    def health():
        return ok({"service": "patient_service", "status": "healthy"})

    app.register_blueprint(patients_bp)
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        debug=(settings.FLASK_ENV == "development"),
    )
