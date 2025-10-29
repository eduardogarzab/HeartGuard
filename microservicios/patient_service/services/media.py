"""Helper to interact with the media_service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

import requests

from config import settings


@dataclass
class SignedPhoto:
    url: str
    expires_in: Optional[int]


class MediaServiceError(Exception):
    """Raised when the media service cannot return a signed URL."""


def _extract_object_name(path: str, org_id: str) -> Optional[str]:
    if not path:
        return None
    normalized = path.strip().lstrip("/")
    parts = normalized.split("/")
    if len(parts) < 3:
        return None
    prefix_org, entity, object_name = parts[0], parts[1], parts[-1]
    if prefix_org != str(org_id) or entity != "patients" or not object_name:
        return None
    return object_name


def request_signed_photo(path: str, auth_header: Optional[str], org_id: str) -> Optional[SignedPhoto]:
    if not path or not auth_header or not settings.MEDIA_SERVICE_URL:
        return None

    object_name = _extract_object_name(path, org_id)
    if not object_name:
        return None

    url = f"{settings.MEDIA_SERVICE_URL.rstrip('/')}/v1/media/patients/{quote(object_name)}"
    headers = {
        "Authorization": auth_header,
        "Accept": "application/json",
        "X-Org-ID": str(org_id),
    }
    try:
        resp = requests.get(url, headers=headers, timeout=settings.MEDIA_TIMEOUT_SECONDS)
    except requests.RequestException as exc:  # pragma: no cover - network failure
        raise MediaServiceError(str(exc)) from exc

    if resp.status_code != 200:
        raise MediaServiceError(f"media_service returned {resp.status_code}")

    try:
        payload = resp.json()
    except ValueError as exc:
        raise MediaServiceError("invalid JSON response") from exc

    signed_url = payload.get("data", {}).get("signed_url")
    expires_in = payload.get("data", {}).get("expires_in")
    if not signed_url:
        raise MediaServiceError("signed_url missing in response")

    return SignedPhoto(url=signed_url, expires_in=expires_in)
