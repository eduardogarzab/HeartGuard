"""Encrypted token persistence utilities."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from .config import APP_CONFIG

LOGGER = logging.getLogger(__name__)


@dataclass
class SessionTokens:
    access_token: str
    refresh_token: str
    account_type: str
    metadata: dict[str, Any]


class TokenStorage:
    """Persist JWT tokens using Fernet symmetric encryption."""

    def __init__(self, storage_path: Path | None = None, key_path: Path | None = None) -> None:
        self.storage_path = storage_path or APP_CONFIG.session_file
        self.key_path = key_path or APP_CONFIG.session_key_file
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.key_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_key(self) -> bytes:
        env_key = os.getenv("HEARTGUARD_SESSION_KEY")
        if env_key:
            return env_key.encode("utf-8")

        if self.key_path.exists():
            return self.key_path.read_bytes()

        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        return key

    def save(self, tokens: SessionTokens) -> None:
        data = {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "account_type": tokens.account_type,
            "metadata": tokens.metadata,
        }
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        cipher = Fernet(self._load_key())
        encrypted = cipher.encrypt(payload)
        self.storage_path.write_bytes(encrypted)
        LOGGER.debug("Tokens encrypted and saved to %s", self.storage_path)

    def load(self) -> SessionTokens | None:
        if not self.storage_path.exists():
            return None
        cipher = Fernet(self._load_key())
        try:
            decrypted = cipher.decrypt(self.storage_path.read_bytes())
        except InvalidToken:
            LOGGER.warning("Stored session could not be decrypted, clearing file")
            self.clear()
            return None

        try:
            data: dict[str, Any] = json.loads(decrypted.decode("utf-8"))
        except json.JSONDecodeError as exc:
            LOGGER.error("Invalid session payload: %s", exc)
            self.clear()
            return None

        return SessionTokens(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            account_type=data.get("account_type", ""),
            metadata=data.get("metadata", {}),
        )

    def clear(self) -> None:
        if self.storage_path.exists():
            self.storage_path.unlink()
            LOGGER.debug("Removed stored session file %s", self.storage_path)
