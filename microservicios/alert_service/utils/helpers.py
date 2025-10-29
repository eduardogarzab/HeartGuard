import logging
import os
from typing import Any, Dict

import requests
from flask import current_app, g

logger = logging.getLogger(__name__)


def _get_service_url(config_key: str, env_key: str) -> str:
    if current_app:
        url = current_app.config.get(config_key)
    else:
        url = None
    return url or os.getenv(env_key, "")


def _post_with_timeout(url: str, payload: Dict[str, Any], timeout: float = 2.0) -> None:
    if not url:
        logger.warning("Target URL not configured for payload: %s", payload)
        return

    try:
        requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        logger.error("Failed to send payload to %s: %s", url, exc)


def send_audit_event(action: str, details: Dict[str, Any]) -> None:
    payload = {
        "service": "alert_service",
        "action": action,
        "user_id": getattr(g, "user_id", None),
        "org_id": getattr(g, "org_id", None),
        "details": details,
    }
    url = _get_service_url("AUDIT_SERVICE_URL", "AUDIT_SERVICE_URL")
    _post_with_timeout(url, payload)


def send_analytics_event(event_type: str, payload: Dict[str, Any]) -> None:
    body = {
        "service": "alert_service",
        "event_type": event_type,
        "user_id": getattr(g, "user_id", None),
        "org_id": getattr(g, "org_id", None),
        "payload": payload,
    }
    url = _get_service_url("ANALYTICS_SERVICE_URL", "ANALYTICS_SERVICE_URL")
    _post_with_timeout(url, body)


__all__ = ["send_audit_event", "send_analytics_event"]
