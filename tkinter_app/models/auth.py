"""Modelos de autenticación equivalentes a los usados en la app Java."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class UserLoginData:
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    system_role: Optional[str] = None
    org_count: Optional[str] = None


@dataclass
class PatientLoginData:
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    org_name: Optional[str] = None
    risk_level: Optional[str] = None


@dataclass
class LoginResponse:
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    account_type: Optional[str] = None
    user: Optional[UserLoginData] = None
    patient: Optional[PatientLoginData] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        if self.user and self.user.name:
            return self.user.name
        if self.patient and self.patient.name:
            return self.patient.name
        return "Unknown"

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

    @staticmethod
    def from_api(payload: Dict[str, Any]) -> "LoginResponse":
        user_data = payload.get("user") or {}
        patient_data = payload.get("patient") or {}
        response = LoginResponse(
            access_token=payload.get("access_token"),
            refresh_token=payload.get("refresh_token"),
            token_type=payload.get("token_type", "Bearer"),
            expires_in=payload.get("expires_in"),
            account_type=payload.get("account_type"),
            raw=payload,
        )
        if user_data:
            response.user = UserLoginData(
                id=user_data.get("id"),
                email=user_data.get("email"),
                name=user_data.get("name"),
                system_role=user_data.get("system_role"),
                org_count=user_data.get("org_count"),
            )
            response.account_type = response.account_type or "user"
        if patient_data:
            response.patient = PatientLoginData(
                id=patient_data.get("id"),
                email=patient_data.get("email"),
                name=patient_data.get("name"),
                org_name=patient_data.get("org_name"),
                risk_level=patient_data.get("risk_level"),
            )
            response.account_type = response.account_type or "patient"
        return response
