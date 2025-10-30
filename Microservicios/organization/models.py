"""In-memory organization profile storage.
TODO: replace with persistent storage (Postgres/Mongo).
"""
import html
from typing import Dict

ORGANIZATION_PROFILE: Dict[str, Dict] = {
    "default": {
        "name": "Heartguard Health",
        "logo_url": "https://example.com/logo.png",
        "policies": "Default policies",
        "settings": {
            "alert_threshold_bpm": 120,
            "timezone": "UTC",
        },
    }
}


def get_org(org_id: str = "default") -> Dict:
    return ORGANIZATION_PROFILE.setdefault(org_id, ORGANIZATION_PROFILE["default"].copy())


def update_org(payload: Dict, org_id: str = "default") -> Dict:
    profile = get_org(org_id)
    if "name" in payload:
        profile["name"] = str(payload["name"]).strip()
    if "logo_url" in payload:
        profile["logo_url"] = str(payload["logo_url"]).strip()
    if "policies" in payload:
        sanitized = html.escape(str(payload["policies"]))[:5000]
        profile["policies"] = sanitized
    if "settings" in payload:
        settings = profile.setdefault("settings", {})
        incoming = payload["settings"]
        if "alert_threshold_bpm" in incoming:
            try:
                bpm = int(incoming["alert_threshold_bpm"])
                settings["alert_threshold_bpm"] = max(30, min(250, bpm))
            except (ValueError, TypeError):
                pass
        if "timezone" in incoming:
            settings["timezone"] = str(incoming["timezone"]).strip()
    ORGANIZATION_PROFILE[org_id] = profile
    return profile
