"""Authentication controller bridging UI and API client."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..api.gateway_client import GatewayApiClient
from ..utils.token_storage import SessionTokens, TokenStorage

LOGGER = logging.getLogger(__name__)


@dataclass
class AuthSession:
    account_type: str
    user: dict[str, Any]
    access_token: str
    refresh_token: str


class AuthController:
    def __init__(self, api_client: GatewayApiClient, storage: TokenStorage) -> None:
        self.api_client = api_client
        self.storage = storage
        self.session: AuthSession | None = None

    def _create_session(self, payload: dict[str, Any]) -> AuthSession:
        account_type = payload.get("account_type") or payload.get("role") or "user"
        user_payload = payload.get("user") or payload.get("data") or {}
        access_token = payload.get("access_token", "")
        refresh_token = payload.get("refresh_token", "")

        self.api_client.set_tokens(access_token, refresh_token)
        session = AuthSession(
            account_type=account_type,
            user=user_payload,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        self.session = session

        self.storage.save(
            SessionTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                account_type=account_type,
                metadata=user_payload,
            )
        )
        return session

    def login(self, email: str, password: str, *, as_patient: bool = False) -> AuthSession:
        if as_patient:
            response = self.api_client.login_patient(email, password)
        else:
            response = self.api_client.login_user(email, password)
        return self._create_session(response)

    def register_user(self, name: str, email: str, password: str) -> dict[str, Any]:
        return self.api_client.register_user(name, email, password)

    def register_patient(
        self,
        name: str,
        email: str,
        password: str,
        org_id_or_code: str,
        birthdate: str,
        sex_code: str,
        risk_level_code: str | None = None,
    ) -> dict[str, Any]:
        return self.api_client.register_patient(
            name,
            email,
            password,
            org_id_or_code,
            birthdate,
            sex_code,
            risk_level_code,
        )

    def restore_session(self) -> AuthSession | None:
        tokens = self.storage.load()
        if not tokens:
            return None
        LOGGER.info("Restoring session for account type %s", tokens.account_type)
        self.api_client.set_tokens(tokens.access_token, tokens.refresh_token)
        if not self.api_client.verify_token():
            LOGGER.info("Stored token invalid, clearing session")
            self.storage.clear()
            return None
        payload = self.api_client.get_me()
        payload.setdefault("account_type", tokens.account_type)
        payload.setdefault("user", tokens.metadata)
        session = AuthSession(
            account_type=payload.get("account_type", tokens.account_type),
            user=payload.get("user", tokens.metadata),
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
        self.session = session
        return session

    def clear_session(self) -> None:
        LOGGER.info("Clearing active session")
        self.api_client.clear_tokens()
        self.storage.clear()
        self.session = None
