"""Modelos para la vista de pacientes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PatientProfile:
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    birthdate: Optional[str] = None
    risk_level: Optional[str] = None
    org_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatientProfile":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            email=data.get("email"),
            birthdate=data.get("birthdate"),
            risk_level=data.get("risk_level"),
            org_name=data.get("org_name") or data.get("organization"),
        )


@dataclass
class Alert:
    id: Optional[str]
    status: Optional[str]
    message: Optional[str]
    created_at: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alert":
        return cls(
            id=data.get("id"),
            status=data.get("status"),
            message=data.get("message") or data.get("description"),
            created_at=data.get("created_at"),
        )


def parse_alerts(payload: Dict[str, Any]) -> List[Alert]:
    data = payload.get("data") or {}
    alerts = data.get("alerts") if isinstance(data, dict) else None
    if alerts is None:
        alerts = payload.get("alerts")
    result: List[Alert] = []
    if isinstance(alerts, list):
        for item in alerts:
            if isinstance(item, dict):
                result.append(Alert.from_dict(item))
    return result
