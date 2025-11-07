"""Authentication models mirroring the Java DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class UserLoginData:
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    system_role: Optional[str] = None
    org_count: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "UserLoginData":
        if not data:
            return cls()
        return cls(
            id=str(data.get("id")) if data.get("id") is not None else None,
            email=data.get("email"),
            name=data.get("name"),
            system_role=data.get("system_role"),
            org_count=_to_int(data.get("org_count")),
        )


@dataclass(slots=True)
class PatientLoginData:
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    org_name: Optional[str] = None
    risk_level: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "PatientLoginData":
        if not data:
            return cls()
        return cls(
            id=str(data.get("id")) if data.get("id") is not None else None,
            email=data.get("email"),
            name=data.get("name"),
            org_name=data.get("org_name"),
            risk_level=data.get("risk_level"),
        )


@dataclass(slots=True)
class LoginResponse:
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    account_type: Optional[str] = None
    user: Optional[UserLoginData] = None
    patient: Optional[PatientLoginData] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "LoginResponse":
        payload = data or {}
        user_data = UserLoginData.from_dict(payload.get("user")) if payload.get("user") else None
        patient_data = (
            PatientLoginData.from_dict(payload.get("patient")) if payload.get("patient") else None
        )
        account_type = payload.get("account_type")
        if not account_type:
            if user_data:
                account_type = "user"
            elif patient_data:
                account_type = "patient"

        return cls(
            access_token=payload.get("access_token"),
            refresh_token=payload.get("refresh_token"),
            token_type=payload.get("token_type", "Bearer"),
            expires_in=_to_int(payload.get("expires_in")),
            account_type=account_type,
            user=user_data,
            patient=patient_data,
        )

    @property
    def full_name(self) -> str:
        if self.user and self.user.name:
            return self.user.name
        if self.patient and self.patient.name:
            return self.patient.name
        return ""  # pragma: no cover - fallback

    @property
    def email(self) -> Optional[str]:
        if self.user and self.user.email:
            return self.user.email
        if self.patient and self.patient.email:
            return self.patient.email
        return None

    @property
    def patient_id(self) -> Optional[str]:
        if self.patient and self.patient.id:
            return self.patient.id
        return None
