"""Notification service to manage push devices and alert deliveries."""
from __future__ import annotations

import datetime as dt
import os
from typing import Dict, List

import requests
from flask import Blueprint, current_app, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("notifications", __name__)

PUSH_DEVICES: Dict[str, Dict] = {
    "pd-1": {
        "id": "pd-1",
        "user_id": "usr-2",
        "platform": "ios",
        "token": "ios-token-123",
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
}

ALERT_DELIVERIES: List[Dict] = []
INVITATION_NOTIFICATIONS: Dict[str, Dict] = {}


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "notification", "status": "healthy", "devices": len(PUSH_DEVICES)})


@bp.route("/push-devices", methods=["GET"])
@require_auth(optional=True)
def list_devices() -> "Response":
    return render_response({"push_devices": list(PUSH_DEVICES.values())}, meta={"total": len(PUSH_DEVICES)})


@bp.route("/push-devices", methods=["POST"])
@require_auth(optional=True)
def register_device() -> "Response":
    payload, _ = parse_request_data(request)
    user_id = payload.get("user_id")
    token = payload.get("token")
    if not user_id or not token:
        raise APIError("user_id and token are required", status_code=400, error_id="HG-NOTIFY-VALIDATION")
    device_id = f"pd-{len(PUSH_DEVICES) + 1}"
    device = {
        "id": device_id,
        "user_id": user_id,
        "platform": payload.get("platform", "ios"),
        "token": token,
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    PUSH_DEVICES[device_id] = device
    return render_response({"push_device": device}, status_code=201)


@bp.route("/deliveries", methods=["POST"])
@require_auth(optional=True)
def create_delivery() -> "Response":
    payload, _ = parse_request_data(request)
    alert_id = payload.get("alert_id")
    device_id = payload.get("device_id")
    if not alert_id or not device_id:
        raise APIError("alert_id and device_id are required", status_code=400, error_id="HG-NOTIFY-DELIVERY")
    delivery = {
        "id": f"delivery-{len(ALERT_DELIVERIES) + 1}",
        "alert_id": alert_id,
        "device_id": device_id,
        "status": "sent",
        "sent_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    ALERT_DELIVERIES.append(delivery)
    return render_response({"delivery": delivery}, status_code=201)


def _organization_service_base_url() -> str:
    base_url = current_app.config.get("ORGANIZATION_SERVICE_URL")
    if base_url:
        return base_url.rstrip("/")
    env_url = os.getenv("ORGANIZATION_SERVICE_URL", "http://organization-service:5002/organization")
    current_app.config["ORGANIZATION_SERVICE_URL"] = env_url
    return env_url.rstrip("/")


def _call_organization_service(method: str, path: str, **kwargs) -> requests.Response:
    url = f"{_organization_service_base_url()}{path}"
    timeout = current_app.config.get("ORGANIZATION_HTTP_TIMEOUT", 5)
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as exc:  # pragma: no cover - network failure
        raise APIError(
            "Failed to contact organization service",
            status_code=502,
            error_id="HG-NOTIFY-ORG-SERVICE",
        ) from exc

    if response.status_code >= 400:
        message = "Organization service error"
        try:
            payload = response.json()
            message = (
                payload.get("error", {}).get("message")
                or payload.get("message")
                or message
            )
        except ValueError:
            if response.text:
                message = response.text
        raise APIError(message, status_code=response.status_code, error_id="HG-NOTIFY-ORG-SERVICE")

    return response


def _consume_invitation_token(signed_token: str) -> None:
    _call_organization_service(
        "POST",
        f"/invitations/{signed_token}/consume",
        headers={"Accept": "application/json"},
        json={"action": "revoke"},
    )


def _parse_iso_datetime(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise APIError("Invalid ISO datetime", status_code=400, error_id="HG-NOTIFY-ISO") from exc


@bp.route("/invitations/send", methods=["POST"])
@require_auth(optional=True)
def send_invitation_notification() -> "Response":
    payload, _ = parse_request_data(request)

    signed_token = payload.get("invite_token") or payload.get("token")
    email = payload.get("email")
    link = payload.get("signed_url") or payload.get("link")
    expires_at = payload.get("expires_at")
    invitation_id = payload.get("invitation_id")

    if not signed_token:
        raise APIError("invite_token is required", status_code=400, error_id="HG-NOTIFY-INVITE-TOKEN")
    if not email:
        raise APIError("email is required", status_code=400, error_id="HG-NOTIFY-EMAIL")
    if not link:
        raise APIError("signed_url is required", status_code=400, error_id="HG-NOTIFY-LINK")

    created_at = dt.datetime.utcnow().isoformat() + "Z"
    record = {
        "invite_token": signed_token,
        "email": email,
        "signed_url": link,
        "expires_at": expires_at,
        "invitation_id": invitation_id,
        "status": "sent",
        "created_at": created_at,
        "sent_at": created_at,
    }
    INVITATION_NOTIFICATIONS[signed_token] = record
    return render_response({"notification": record}, status_code=202)


@bp.route("/invitations/sweep", methods=["POST"])
@require_auth(optional=True)
def sweep_invitation_expirations() -> "Response":
    now = dt.datetime.now(dt.timezone.utc)
    expired_tokens: List[str] = []

    for token, record in list(INVITATION_NOTIFICATIONS.items()):
        if record.get("revoked_at"):
            continue
        expires_at = record.get("expires_at")
        try:
            expires = _parse_iso_datetime(expires_at)
        except APIError as exc:
            record["error"] = exc.message
            continue
        if not expires:
            continue
        if expires <= now:
            try:
                _consume_invitation_token(token)
                record["revoked_at"] = dt.datetime.utcnow().isoformat() + "Z"
                expired_tokens.append(token)
            except APIError as exc:
                record["error"] = exc.message

    meta = {"total": len(expired_tokens)}
    return render_response({"expired_tokens": expired_tokens}, meta=meta)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/notifications")
