"""Servicio de lógica de negocio para usuarios"""
from __future__ import annotations

from typing import Any, Dict, List

from ..repositories.user_repo import UserRepository


class UserService:
    """Expone operaciones de alto nivel sobre usuarios"""

    def __init__(self) -> None:
        self.repo = UserRepository()

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        record = self.repo.get_user_profile(user_id)
        if not record:
            raise ValueError("Usuario no encontrado")
        return self._format_profile(record)

    def update_profile(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}

        if 'name' in payload:
            name = (payload.get('name') or '').strip()
            if not name:
                raise ValueError("El nombre no puede estar vacío")
            updates['name'] = name

        if 'profile_photo_url' in payload:
            profile_photo = payload.get('profile_photo_url')
            if profile_photo is None:
                updates['profile_photo_url'] = None
            else:
                profile_str = str(profile_photo).strip()
                updates['profile_photo_url'] = profile_str or None

        if 'two_factor_enabled' in payload:
            updates['two_factor_enabled'] = bool(payload.get('two_factor_enabled', False))

        if not updates:
            raise ValueError("No hay cambios válidos para aplicar")

        result = self.repo.update_user_profile(user_id, updates)
        if not result:
            raise ValueError("No se pudo actualizar el usuario")

        return self.get_profile(user_id)

    def list_org_memberships(self, user_id: str) -> List[Dict[str, Any]]:
        memberships = self.repo.list_memberships(user_id)
        return [self._format_membership(row) for row in memberships]

    def get_org_membership(self, org_id: str, user_id: str) -> Dict[str, Any]:
        record = self.repo.get_membership(org_id, user_id)
        if not record:
            raise ValueError("Membresía no encontrada")
        return self._format_membership(record)

    @staticmethod
    def _format_profile(record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(record['id']),
            'name': record['name'],
            'email': record['email'],
            'role_code': record['role_code'],
            'status': {
                'code': record.get('status_code'),
                'label': record.get('status_label'),
            },
            'two_factor_enabled': record.get('two_factor_enabled', False),
            'profile_photo_url': record.get('profile_photo_url'),
            'created_at': record['created_at'].isoformat() if record.get('created_at') else None,
            'updated_at': record['updated_at'].isoformat() if record.get('updated_at') else None,
        }

    @staticmethod
    def _format_membership(record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'org_id': str(record['org_id']),
            'org_code': record.get('org_code'),
            'org_name': record.get('org_name'),
            'role_code': record['role_code'],
            'role_label': record.get('role_label'),
            'joined_at': record['joined_at'].isoformat() if record.get('joined_at') else None,
        }
