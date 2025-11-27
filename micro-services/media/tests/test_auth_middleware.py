from __future__ import annotations

import uuid

import jwt
from flask import Blueprint

from media.middleware import require_token
from media.utils.responses import success_response


def _setup_route(app, rule: str, allowed: set[str]):
    bp = Blueprint(f"test_{uuid.uuid4().hex}", __name__)

    @bp.route(rule, methods=["GET"])
    @require_token(allow=allowed)
    def protected(auth_subject):  # type: ignore[no-redef]
        return success_response(data={"subject": auth_subject.subject_id})

    app.register_blueprint(bp)
    return app.test_client()


def test_require_token_block_without_header(flask_app):
    client = _setup_route(flask_app, "/secure", {"user"})
    resp = client.get("/secure")
    assert resp.status_code == 401


def test_require_token_accepts_user(flask_app):
    client = _setup_route(flask_app, "/secure-user", {"user"})
    payload = {
        "account_type": "user",
        "user_id": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, flask_app.config["JWT_SECRET"], algorithm=flask_app.config["JWT_ALGORITHM"])
    resp = client.get("/secure-user", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["data"]["subject"] == payload["user_id"]


def test_require_token_blocks_forbidden_type(flask_app):
    client = _setup_route(flask_app, "/secure-patient", {"patient"})
    payload = {
        "account_type": "user",
        "user_id": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, flask_app.config["JWT_SECRET"], algorithm=flask_app.config["JWT_ALGORITHM"])
    resp = client.get("/secure-patient", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    body = resp.get_json()
    assert body["error"] == {"code": "forbidden"}
