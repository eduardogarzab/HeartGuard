"""Authorization helpers for Admin Service."""
from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable

import requests
from flask import Response, current_app, request

from .xml import xml_error_response


@dataclass
class OrgMembership:
    org_id: str
    org_role: str
    org_code: str | None = None
    org_name: str | None = None


@dataclass
class AuthContext:
    user_id: str
    email: str
    name: str
    memberships: list[OrgMembership]


def require_org_admin(func: Callable[..., Any]) -> Callable[..., Response]:
    """Ensure request is authenticated as org_admin for given org."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Response:
        token = _bearer_token()
        if not token:
            return xml_error_response("missing_token", "Authorization header required", status=401)

        verification = _verify_token(token)
        if not verification.get("valid"):
            return xml_error_response("invalid_token", "Provided token is invalid", status=401)

        payload = verification.get("payload", {})
        if payload.get("account_type") != "user":
            return xml_error_response("forbidden", "This endpoint is only for staff accounts", status=403)

        memberships = _extract_memberships(payload)
        if not memberships:
            return xml_error_response("forbidden", "User does not belong to any organization", status=403)

        admin_memberships = [m for m in memberships if m.org_role == "org_admin"]
        if not admin_memberships:
            return xml_error_response("forbidden", "User is not an organization administrator", status=403)

        org_id = kwargs.get("org_id") or _org_id_from_patient(kwargs.get("patient_id"))
        if org_id and org_id not in {m.org_id for m in admin_memberships}:
            return xml_error_response(
                "forbidden",
                "User is not org_admin of the requested organization",
                status=403,
            )

        request.auth_context = AuthContext(  # type: ignore[attr-defined]
            user_id=payload.get("user_id"),
            email=payload.get("email"),
            name=payload.get("name"),
            memberships=memberships,
        )
        return func(*args, **kwargs)

    return wrapper


def _bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return None


def _verify_token(token: str) -> dict[str, Any]:
    url = f"{current_app.config['AUTH_SERVICE_URL'].rstrip('/')}/auth/verify"
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=current_app.config["ADMIN_SERVICE_TIMEOUT"],
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {"valid": False}


def _extract_memberships(payload: dict[str, Any]) -> list[OrgMembership]:
    memberships: list[OrgMembership] = []
    for entry in payload.get("org_memberships", []):
        memberships.append(
            OrgMembership(
                org_id=entry.get("org_id"),
                org_role=entry.get("role_code"),
                org_code=entry.get("org_code"),
                org_name=entry.get("org_name"),
            )
        )
    return memberships


def _org_id_from_patient(patient_id: str | None) -> str | None:
    if not patient_id:
        return None
    from .repositories.patients import PatientsRepository

    repo = PatientsRepository()
    patient = repo.get_patient(patient_id)
    return patient["org_id"] if patient else None
