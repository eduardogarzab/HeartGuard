"""Client for interacting with the auth service."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

DEFAULT_VALIDATE_ENDPOINT = "/api/auth/v1/validate"


class AuthClient:
    """HTTP client for token validation."""

    def __init__(self, base_url: str | None) -> None:
        if not base_url:
            raise ValueError("AUTH_SERVICE_URL is not configured")
        self.base_url = base_url.rstrip("/")

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a token with the auth service."""
        url = f"{self.base_url}{DEFAULT_VALIDATE_ENDPOINT}"
        try:
            response = requests.post(url, json={"token": token}, timeout=5)
            if response.status_code != 200:
                return None
            return response.json()
        except requests.RequestException:
            return None


__all__ = ["AuthClient"]
