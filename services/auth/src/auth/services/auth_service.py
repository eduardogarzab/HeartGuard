"""Orquestación de casos de uso de autenticación."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Tuple

import jwt

from ..errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from ..repositories import invitations, organizations, patients, users
from ..utils.security import hash_password, normalize_email, verify_password
from ..utils.tokens import decode_token, encode_token, ensure_token_type


class AuthService:
    """Servicios principales de autenticación y autorización."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        self.config = config
        self.jwt_secret = config["JWT_SECRET"]
        self.jwt_algorithm = config["JWT_ALGORITHM"]
        self.access_minutes = int(config["JWT_ACCESS_TOKEN_EXPIRES_MIN"])
        self.refresh_minutes = int(config["JWT_REFRESH_TOKEN_EXPIRES_MIN"])
        self.bcrypt_rounds = int(config["BCRYPT_ROUNDS"])

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------
    def register_user(self, *, name: str, email: str, password: str) -> dict[str, Any]:
        email_norm = normalize_email(email)
        if users.get_by_email(email_norm):
            raise ConflictError("El correo ya está registrado para un usuario")

        password_hash = self._hash_password(password)
        created = users.create_user(
            name=name.strip(),
            email=email_norm,
            password_hash=password_hash,
            status_code="active",
            role_code="user",
        )
        return {
            "user_id": created["id"],
            "email": created["email"],
            "name": created["name"],
            "message": "Registro exitoso",
        }

    def register_patient(
        self,
        *,
        name: str,
        email: str,
        password: str,
        org_id: str,
        org_code: str,
        birthdate: str | None,
        sex_code: str | None,
        risk_level_code: str | None,
    ) -> dict[str, Any]:
        """Registra un nuevo paciente. Acepta org_code o org_id."""
        email_norm = normalize_email(email)
        if patients.get_by_email(email_norm):
            raise ConflictError("El correo ya está registrado para un paciente")

        # Buscar organización por código si se proporciona
        if org_code:
            org = organizations.get_by_code(org_code)
            if not org:
                raise ValidationError(f"La organización con código '{org_code}' no existe")
            org_id = org["id"]
        elif org_id:
            org = organizations.get_by_id(org_id)
            if not org:
                raise ValidationError("La organización indicada no existe")
        else:
            raise ValidationError("Debe proporcionar org_id o org_code")

        password_hash = self._hash_password(password)
        try:
            created = patients.create_patient(
                org_id=org_id,
                name=name.strip(),
                email=email_norm,
                password_hash=password_hash,
                birthdate=birthdate,
                sex_code=sex_code,
                risk_level_code=risk_level_code,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        return {
            "patient_id": created["id"],
            "email": created["email"],
            "org_id": created["org_id"],
            "org_name": org["name"],
            "message": "Registro exitoso",
        }

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def login_user(self, *, email: str, password: str) -> dict[str, Any]:
        email_norm = normalize_email(email)
        record = users.get_by_email(email_norm)
        if not record:
            raise UnauthorizedError("Credenciales inválidas")

        if record["user_status_code"] != "active":
            raise ForbiddenError("La cuenta no está activa")

        if not verify_password(password, record["password_hash"]):
            raise UnauthorizedError("Credenciales inválidas")

        memberships = users.list_memberships(record["id"])
        access_token, refresh_token = self._issue_tokens_for_user(record, memberships)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": record["id"],
                "email": record["email"],
                "name": record["name"],
                "system_role": record["role_code"],
                "org_count": len(memberships),
            },
        }

    def login_patient(self, *, email: str, password: str) -> dict[str, Any]:
        email_norm = normalize_email(email)
        record = patients.get_by_email(email_norm)
        if not record:
            raise UnauthorizedError("Credenciales inválidas")

        if not verify_password(password, record["password_hash"]):
            raise UnauthorizedError("Credenciales inválidas")

        access_token, refresh_token = self._issue_tokens_for_patient(record)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "patient": {
                "id": record["id"],
                "email": record["email"],
                "name": record["name"],
                "org_name": record["org_name"],
                "risk_level": record.get("risk_level_code"),
            },
        }

    # ------------------------------------------------------------------
    # Invitaciones
    # ------------------------------------------------------------------
    def accept_invitation(self, *, token: str, user_id: str, user_email: str) -> dict[str, Any]:
        invitation = invitations.get_valid_invitation(token)
        if not invitation:
            raise NotFoundError("La invitación no es válida o ha expirado")

        if normalize_email(invitation["email"]) != normalize_email(user_email):
            raise ForbiddenError("La invitación no corresponde a este usuario")

        membership = invitations.create_membership(invitation["org_id"], user_id, invitation["role_code"])
        invitations.mark_invitation_used(invitation["id"])

        return {
            "message": f"Te uniste a {invitation['org_name']} como {invitation['role_code']}",
            "org_id": membership["org_id"],
            "org_name": invitation["org_name"],
            "role_code": invitation["role_code"],
        }

    # ------------------------------------------------------------------
    # Tokens
    # ------------------------------------------------------------------
    def refresh(self, *, refresh_token: str) -> dict[str, Any]:
        payload = self._decode_token(refresh_token, expected_type="refresh")

        account_type = payload.get("account_type")
        if account_type == "user":
            return {"access_token": self._refresh_user(payload)}
        if account_type == "patient":
            return {"access_token": self._refresh_patient(payload)}
        raise ValidationError("El refresh token no contiene un tipo de cuenta válido")

    def verify(self, *, access_token: str) -> dict[str, Any]:
        payload = self._decode_token(access_token, expected_type="access")
        return {"valid": True, "payload": payload}

    def account_details(self, *, access_token: str) -> dict[str, Any]:
        payload = self._decode_token(access_token, expected_type="access")
        account_type = payload.get("account_type")

        if account_type == "user":
            record = users.get_by_id(payload["user_id"])
            if not record:
                raise NotFoundError("Usuario no encontrado")
            memberships = users.list_memberships(record["id"])
            return {
                "account_type": "user",
                "data": {
                    "id": record["id"],
                    "email": record["email"],
                    "name": record["name"],
                    "system_role": record["role_code"],
                    "memberships": memberships,
                },
            }
        if account_type == "patient":
            record = patients.get_by_id(payload["patient_id"])
            if not record:
                raise NotFoundError("Paciente no encontrado")
            return {
                "account_type": "patient",
                "data": {
                    "id": record["id"],
                    "email": payload.get("email"),
                    "name": record["name"],
                    "org_id": record["org_id"],
                    "org_name": record["org_name"],
                    "birthdate": record.get("birthdate"),
                    "risk_level": record.get("risk_level_code"),
                },
            }

        raise ValidationError("Tipo de cuenta no soportado")

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _hash_password(self, password: str) -> str:
        password = password or ""
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres")
        return hash_password(password, self.bcrypt_rounds)

    def _serialize_memberships(self, memberships: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Convierte memberships a un formato serializable a JSON."""
        serialized = []
        for m in memberships:
            membership = {
                "org_id": m["org_id"],
                "org_code": m.get("org_code"),
                "org_name": m.get("org_name"),
                "role_code": m.get("role_code"),
                "role_label": m.get("role_label"),
            }
            # Convertir datetime a string ISO si existe
            if m.get("joined_at"):
                membership["joined_at"] = m["joined_at"].isoformat() if hasattr(m["joined_at"], "isoformat") else str(m["joined_at"])
            serialized.append(membership)
        return serialized

    def _issue_tokens_for_user(self, user: Mapping[str, Any], memberships: list[Mapping[str, Any]]) -> Tuple[str, str]:
        base_payload = {
            "user_id": user["id"],
            "account_type": "user",
            "email": user["email"],
            "name": user["name"],
            "system_role": user["role_code"],
            "org_memberships": self._serialize_memberships(memberships),
        }
        access_token = encode_token(
            base_payload,
            secret=self.jwt_secret,
            algorithm=self.jwt_algorithm,
            expires_minutes=self.access_minutes,
            token_type="access",
        )
        refresh_token = encode_token(
            {"user_id": user["id"], "account_type": "user"},
            secret=self.jwt_secret,
            algorithm=self.jwt_algorithm,
            expires_minutes=self.refresh_minutes,
            token_type="refresh",
        )
        return access_token, refresh_token

    def _issue_tokens_for_patient(self, patient: Mapping[str, Any]) -> Tuple[str, str]:
        base_payload = {
            "patient_id": patient["id"],
            "account_type": "patient",
            "email": patient["email"],
            "name": patient["name"],
            "org_id": patient["org_id"],
            "org_code": patient.get("org_code"),
            "org_name": patient.get("org_name"),
            "risk_level": patient.get("risk_level_code"),
        }
        access_token = encode_token(
            base_payload,
            secret=self.jwt_secret,
            algorithm=self.jwt_algorithm,
            expires_minutes=self.access_minutes,
            token_type="access",
        )
        refresh_token = encode_token(
            {"patient_id": patient["id"], "account_type": "patient"},
            secret=self.jwt_secret,
            algorithm=self.jwt_algorithm,
            expires_minutes=self.refresh_minutes,
            token_type="refresh",
        )
        return access_token, refresh_token

    def _decode_token(self, token: str, *, expected_type: str) -> dict[str, Any]:
        try:
            payload = decode_token(token, secret=self.jwt_secret, algorithms=[self.jwt_algorithm])
            ensure_token_type(payload, expected_type)
            return payload
        except jwt.ExpiredSignatureError as exc:
            raise UnauthorizedError("El token ha expirado") from exc
        except (jwt.InvalidTokenError, ValueError) as exc:
            raise UnauthorizedError("Token inválido") from exc

    def _refresh_user(self, payload: Mapping[str, Any]) -> str:
        record = users.get_by_id(payload["user_id"])
        if not record:
            raise NotFoundError("Usuario no encontrado")
        if record["user_status_code"] != "active":
            raise ForbiddenError("La cuenta no está activa")
        memberships = users.list_memberships(record["id"])
        access_token, _ = self._issue_tokens_for_user(record, memberships)
        return access_token

    def _refresh_patient(self, payload: Mapping[str, Any]) -> str:
        record = patients.get_by_id(payload["patient_id"])
        if not record:
            raise NotFoundError("Paciente no encontrado")
        access_token, _ = self._issue_tokens_for_patient(record)
        return access_token
