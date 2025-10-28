from flask import Flask
from flask_jwt_extended import JWTManager
from config import settings
from responses import ok, err
from token_store import is_token_revoked

# Rutas
from routes.auth import bp as auth_bp
from routes.users import bp as users_bp

def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET
    app.config["JSON_SORT_KEYS"] = False
    # Store full identity dict without tripping PyJWT subject validation
    app.config["JWT_IDENTITY_CLAIM"] = "identity"
    app.config["JWT_DECODE_SUBJECT"] = False

    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return is_token_revoked(jwt_payload)

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return err("Token revocado", code="token_revoked", status=401)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return err("Token expirado", code="token_expired", status=401)

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return err("Token inválido", code="token_invalid", status=422, details={"reason": reason})

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return err("Cabecera de autorización inválida", code="auth_header_missing", status=401, details={"reason": reason})

    @app.get("/health")
    def health():
        return ok({"service": "auth_service", "status": "healthy"})

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=settings.SERVICE_PORT, debug=(settings.FLASK_ENV=="development"))
