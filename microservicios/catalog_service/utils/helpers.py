"""Helper utilities for integrations."""
from __future__ import annotations

import threading
from typing import Any, Dict, Optional

import requests
from flask import current_app, g


def _post_async(url: str, payload: Dict[str, Any]) -> None:
    def _worker():
        try:
            requests.post(url, json=payload, timeout=5)
        except requests.RequestException:
            # Fire-and-forget: intentionally swallow exceptions to avoid
            # blocking the main request flow.
            pass

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()


def log_audit_event(action: str, catalog_name: str, data: Dict[str, Any]) -> None:
    """Send audit events to the external audit service."""

    url: Optional[str] = current_app.config.get("AUDIT_SERVICE_URL")
    if not url:
        return

    payload = {
        "action": action,
        "catalog": catalog_name,
        "data": data,
        "user_id": getattr(g, "user_id", None),
        "org_id": getattr(g, "org_id", None),
    }
    _post_async(url, payload)


def log_analytics_event(event_name: str, payload: Dict[str, Any]) -> None:
    """Stub for analytics logging to the analytics service."""

    url: Optional[str] = current_app.config.get("ANALYTICS_SERVICE_URL")
    if not url:
        return

    body = {
        "event": event_name,
        "payload": payload,
        "user_id": getattr(g, "user_id", None),
        "org_id": getattr(g, "org_id", None),
    }
    _post_async(url, body)
