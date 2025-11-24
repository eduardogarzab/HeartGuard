"""Servicio de lógica de negocio para usuarios"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Tuple
from uuid import UUID

from ..extensions import get_db_cursor
from ..repositories.user_repo import UserRepository


class UserService:
    """Expone operaciones de alto nivel sobre usuarios"""

    def __init__(self) -> None:
        self.repo = UserRepository()

    def ensure_membership(self, org_id: str, user_id: str) -> Dict[str, Any]:
        """Permite validar membresía desde otros módulos."""
        return self._ensure_membership(org_id, user_id)

    # ------------------------------------------------------------------
    # Perfil y membresías básicas
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Invitaciones
    # ------------------------------------------------------------------
    def list_pending_invitations(self, user_id: str) -> List[Dict[str, Any]]:
        user_identity = self._get_user_identity(user_id)
        normalized_email = self._normalize_email(user_identity.get('email'))
        if not normalized_email:
            return []

        with get_db_cursor() as cursor:
            cursor.execute(
                self._pending_invitations_query(),
                (normalized_email,),
            )
            rows = cursor.fetchall() or []

        return [self._format_invitation(row) for row in rows]

    def accept_invitation(self, user_id: str, invite_id: str) -> Dict[str, Any]:
        user_identity = self._get_user_identity(user_id)
        normalized_email = self._normalize_email(user_identity.get('email'))
        if not normalized_email:
            raise ValueError("El usuario no tiene un correo asociado")

        with get_db_cursor() as cursor:
            invitation = self._fetch_invitation_for_user(cursor, invite_id, normalized_email, lock=True)
            if not invitation:
                raise ValueError("Invitación no encontrada")
            self._ensure_invitation_pending(invitation)

            cursor.execute(
                """
                    INSERT INTO user_org_membership (org_id, user_id, role_code)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (org_id, user_id)
                    DO UPDATE SET role_code = EXCLUDED.role_code
                    RETURNING org_id, user_id, role_code, joined_at
                """,
                (invitation['org_id'], user_id, invitation['role_code']),
            )
            membership_row = cursor.fetchone()
            if not membership_row:
                raise ValueError("No se pudo registrar la membresía")

            cursor.execute(
                """
                    UPDATE org_invitations
                    SET used_at = NOW(), revoked_at = NULL
                    WHERE id = %s
                    RETURNING used_at, revoked_at
                """,
                (invite_id,),
            )
            invite_status = cursor.fetchone()
            if not invite_status:
                raise ValueError("No se pudo actualizar la invitación")

            updated_invitation = self._fetch_invitation_for_user(cursor, invite_id, normalized_email)
            cursor.execute(
                self._membership_lookup_query(),
                (membership_row['org_id'], user_id),
            )
            membership_detail = cursor.fetchone()

        formatted_membership = self._format_membership(membership_detail) if membership_detail else {
            'org_id': str(membership_row['org_id']),
            'role_code': membership_row['role_code'],
            'org_code': None,
            'org_name': None,
            'role_label': None,
            'joined_at': self._serialize_datetime(membership_row.get('joined_at')),
        }

        formatted_invitation = self._format_invitation(updated_invitation) if updated_invitation else self._format_invitation({
            **invitation,
            'used_at': invite_status.get('used_at'),
            'revoked_at': invite_status.get('revoked_at'),
        })

        return {
            'invitation': formatted_invitation,
            'membership': formatted_membership,
        }

    def reject_invitation(self, user_id: str, invite_id: str) -> Dict[str, Any]:
        user_identity = self._get_user_identity(user_id)
        normalized_email = self._normalize_email(user_identity.get('email'))
        if not normalized_email:
            raise ValueError("El usuario no tiene un correo asociado")

        with get_db_cursor() as cursor:
            invitation = self._fetch_invitation_for_user(cursor, invite_id, normalized_email, lock=True)
            if not invitation:
                raise ValueError("Invitación no encontrada")
            self._ensure_invitation_pending(invitation)

            cursor.execute(
                """
                    UPDATE org_invitations
                    SET revoked_at = NOW()
                    WHERE id = %s
                    RETURNING used_at, revoked_at
                """,
                (invite_id,),
            )
            invite_status = cursor.fetchone()
            if not invite_status:
                raise ValueError("No se pudo actualizar la invitación")

            updated_invitation = self._fetch_invitation_for_user(cursor, invite_id, normalized_email)

        formatted_invitation = self._format_invitation(updated_invitation) if updated_invitation else self._format_invitation({
            **invitation,
            'used_at': invite_status.get('used_at'),
            'revoked_at': invite_status.get('revoked_at'),
        })

        return {
            'invitation': formatted_invitation,
        }

    # ------------------------------------------------------------------
    # Datos organizacionales
    # ------------------------------------------------------------------
    def get_org_dashboard(self, org_id: str, user_id: str) -> Dict[str, Any]:
        membership = self._ensure_membership(org_id, user_id)
        overview = self.repo.get_org_overview(org_id, user_id)
        metrics = self.repo.get_org_metrics(org_id, user_id)
        return {
            'organization': membership,
            'overview': self._format_org_overview(overview),
            'metrics': self._format_org_metrics(metrics),
        }

    def list_org_care_teams(self, org_id: str, user_id: str) -> Dict[str, Any]:
        membership = self._ensure_membership(org_id, user_id)
        rows = self.repo.list_org_care_teams(org_id, user_id)
        teams: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            team_id = str(row['care_team_id'])
            team = teams.setdefault(
                team_id,
                {
                    'id': team_id,
                    'name': row.get('care_team_name'),
                    'created_at': self._serialize_datetime(row.get('created_at')),
                    'members': [],
                },
            )
            if row.get('member_user_id'):
                team['members'].append({
                    'user_id': str(row['member_user_id']),
                    'name': row.get('member_name'),
                    'email': row.get('member_email'),
                    'profile_photo_url': row.get('member_profile_photo_url'),
                    'role': {
                        'code': row.get('member_role_code'),
                        'label': row.get('member_role_label'),
                    },
                })

        return {
            'organization': membership,
            'care_teams': list(teams.values()),
        }

    def list_org_care_team_patients(self, org_id: str, user_id: str) -> Dict[str, Any]:
        membership = self._ensure_membership(org_id, user_id)
        rows = self.repo.list_org_care_team_patients(org_id, user_id)
        teams: Dict[str, Any] = {}
        for row in rows:
            team_id = str(row['care_team_id'])
            team = teams.setdefault(
                team_id,
                {
                    'id': team_id,
                    'name': row.get('care_team_name'),
                    'patients': [],
                    'members': [],
                },
            )
            # Solo agregar pacientes si patient_id no es NULL
            if row.get('patient_id') is not None:
                team['patients'].append({
                    'id': str(row['patient_id']),
                    'name': row.get('patient_name'),
                    'email': row.get('patient_email'),
                    'risk_level': {
                        'code': row.get('risk_level_code'),
                        'label': row.get('risk_level_label'),
                    },
                })

        # Agregar miembros a los equipos
        member_rows = self.repo.list_org_care_teams(org_id, user_id)
        for row in member_rows:
            team_id = str(row['care_team_id'])
            if team_id in teams and row.get('member_user_id'):
                teams[team_id]['members'].append({
                    'user_id': str(row['member_user_id']),
                    'name': row.get('member_name'),
                    'email': row.get('member_email'),
                    'profile_photo_url': row.get('member_profile_photo_url'),
                    'role': {
                        'code': row.get('member_role_code'),
                        'label': row.get('member_role_label'),
                    },
                })

        return {
            'organization': membership,
            'care_teams': list(teams.values()),
        }

    def list_org_care_team_patients_locations(self, org_id: str, user_id: str) -> Dict[str, Any]:
        """Lista pacientes de care teams con sus ubicaciones."""
        membership = self._ensure_membership(org_id, user_id)
        rows = self.repo.list_org_care_team_patients_locations(org_id, user_id)
        
        teams: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            team_id = str(row['care_team_id'])
            team = teams.setdefault(
                team_id,
                {
                    'id': team_id,
                    'name': row.get('care_team_name'),
                    'patients': [],
                },
            )
            
            # Solo agregar pacientes que tienen ubicación
            if row.get('patient_id') and row.get('latitude') and row.get('longitude'):
                patient = {
                    'id': str(row['patient_id']),
                    'name': row.get('patient_name'),
                    'email': row.get('patient_email'),
                    'profile_photo_url': row.get('patient_profile_photo_url'),
                    'risk_level': {
                        'code': row.get('risk_level_code'),
                        'label': row.get('risk_level_label'),
                    },
                    'location': {
                        'latitude': float(row['latitude']),
                        'longitude': float(row['longitude']),
                        'last_update': row.get('last_update'),
                        'approximate': row.get('approximate', False),
                    },
                }
                
                # Agregar last_alert si existe
                if row.get('last_alert_code'):
                    patient['last_alert'] = {
                        'code': row.get('last_alert_code'),
                        'label': row.get('last_alert_label'),
                        'level': {
                            'code': row.get('alert_level_code'),
                            'label': row.get('alert_level_label'),
                        },
                    }
                
                team['patients'].append(patient)
        
        return {'care_teams': list(teams.values())}

    def get_org_patient_detail(self, org_id: str, patient_id: str, user_id: str) -> Dict[str, Any]:
        membership = self._ensure_membership(org_id, user_id)
        patient_record = self.repo.get_patient(org_id, patient_id)
        if not patient_record:
            raise ValueError("Paciente no encontrado en la organización indicada")
        return {
            'organization': membership,
            'patient': self._format_patient(patient_record),
        }

    def list_org_patient_alerts(
        self,
        org_id: str,
        patient_id: str,
        user_id: str,
        *,
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        membership = self._ensure_membership(org_id, user_id)
        patient_record = self.repo.get_patient(org_id, patient_id)
        if not patient_record:
            raise ValueError("Paciente no encontrado en la organización indicada")
        alerts = self.repo.list_patient_alerts(patient_id, limit, offset)
        return {
            'organization': membership,
            'patient': self._format_patient_summary(patient_record),
            'alerts': [self._format_alert(row) for row in alerts],
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(alerts),
            },
        }

    def list_org_patient_notes(
        self,
        org_id: str,
        patient_id: str,
        user_id: str,
        *,
        limit: int,
    ) -> Dict[str, Any]:
        membership = self._ensure_membership(org_id, user_id)
        patient_record = self.repo.get_patient(org_id, patient_id)
        if not patient_record:
            raise ValueError("Paciente no encontrado en la organización indicada")
        notes = self.repo.list_patient_notes(patient_id, limit)
        return {
            'organization': membership,
            'patient': self._format_patient_summary(patient_record),
            'notes': [self._format_note(row) for row in notes],
        }

    def get_org_metrics(self, org_id: str, user_id: str) -> Dict[str, Any]:
        membership = self._ensure_membership(org_id, user_id)
        overview = self.repo.get_org_overview(org_id, user_id)
        metrics = self.repo.get_org_metrics(org_id, user_id)
        return {
            'organization': membership,
            'overview': self._format_org_overview(overview),
            'metrics': self._format_org_metrics(metrics),
        }

    # ------------------------------------------------------------------
    # Flujos de cuidador
    # ------------------------------------------------------------------
    def list_caregiver_patients(self, user_id: str) -> Dict[str, Any]:
        rows = self.repo.list_caregiver_patients(user_id)
        patients = [self._format_caregiver_patient(row) for row in rows]
        return {
            'patients': patients,
        }

    def get_caregiver_patient_detail(self, patient_id: str, user_id: str) -> Dict[str, Any]:
        relationship = self._ensure_caregiver_access(patient_id, user_id)
        patient_record = self.repo.get_patient_by_id(patient_id)
        if not patient_record:
            raise ValueError("Paciente no encontrado")
        return {
            'patient': self._format_patient(patient_record),
            'relationship': self._format_relationship(relationship),
        }

    def list_caregiver_patient_alerts(
        self,
        patient_id: str,
        user_id: str,
        *,
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        relationship = self._ensure_caregiver_access(patient_id, user_id)
        patient_record = self.repo.get_patient_by_id(patient_id)
        if not patient_record:
            raise ValueError("Paciente no encontrado")
        alerts = self.repo.list_patient_alerts(patient_id, limit, offset)
        return {
            'patient': self._format_patient_summary(patient_record),
            'relationship': self._format_relationship(relationship),
            'alerts': [self._format_alert(row) for row in alerts],
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(alerts),
            },
        }

    def list_caregiver_patient_notes(
        self,
        patient_id: str,
        user_id: str,
        *,
        limit: int,
    ) -> Dict[str, Any]:
        relationship = self._ensure_caregiver_access(patient_id, user_id)
        patient_record = self.repo.get_patient_by_id(patient_id)
        if not patient_record:
            raise ValueError("Paciente no encontrado")
        notes = self.repo.list_patient_notes(patient_id, limit)
        return {
            'patient': self._format_patient_summary(patient_record),
            'relationship': self._format_relationship(relationship),
            'notes': [self._format_note(row) for row in notes],
        }

    def add_caregiver_patient_note(
        self,
        patient_id: str,
        user_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._ensure_caregiver_access(patient_id, user_id)

        event_code = str(payload.get('event_code', '')).strip()
        if not event_code:
            raise ValueError("Se requiere el campo event_code")

        onset = self._parse_datetime(payload.get('onset'), field='onset') or self._now()
        offset_at = self._parse_datetime(payload.get('offset_at'), field='offset_at')

        note_value = payload.get('note')
        if note_value is not None:
            note_value = str(note_value).strip() or None

        source = str(payload.get('source') or 'caregiver_note').strip() or 'caregiver_note'

        note_id = self.repo.create_patient_note(
            patient_id=patient_id,
            user_id=user_id,
            event_code=event_code,
            onset=onset,
            offset_at=offset_at,
            note=note_value,
            source=source,
        )
        if not note_id:
            raise ValueError("No se pudo crear la nota, verifica el evento solicitado")

        record = self.repo.get_patient_note(note_id)
        if not record:
            raise ValueError("No se pudo recuperar la nota recién creada")

        return {
            'note': self._format_note(record),
        }

    def get_caregiver_metrics(self, user_id: str) -> Dict[str, Any]:
        metrics = self.repo.get_caregiver_metrics(user_id)
        return {
            'metrics': {
                'active_patients': metrics.get('active_patients', 0),
                'alerts_last_14d': metrics.get('alerts_last_14d', 0),
            }
        }

    def list_event_types(self) -> Dict[str, Any]:
        event_types = self.repo.list_event_types()
        return {
            'event_types': [
                {
                    'code': row['code'],
                    'description': row['description']
                }
                for row in event_types
            ]
        }

    def list_caregiver_patient_devices(self, patient_id: str, user_id: str) -> Dict[str, Any]:
        """Lista los dispositivos activos asignados a un paciente (endpoint de caregiver)."""
        relationship = self._ensure_caregiver_access(patient_id, user_id)
        patient_record = self.repo.get_patient_by_id(patient_id)
        if not patient_record:
            raise ValueError("Paciente no encontrado")
        devices = self.repo.list_patient_devices(patient_id)
        return {
            'patient': self._format_patient_summary(patient_record),
            'relationship': self._format_relationship(relationship),
            'devices': [self._format_patient_device(row) for row in devices],
            'count': len(devices),
        }

    def list_org_patient_devices(self, org_id: str, patient_id: str, user_id: str) -> Dict[str, Any]:
        """Lista los dispositivos activos asignados a un paciente (endpoint de organización)."""
        membership = self._ensure_membership(org_id, user_id)
        patient_record = self.repo.get_patient(org_id, patient_id)
        if not patient_record:
            raise ValueError("Paciente no encontrado en la organización indicada")
        
        devices = self.repo.list_patient_devices(patient_id)
        return {
            'organization': membership,
            'patient': self._format_patient_summary(patient_record),
            'devices': [self._format_patient_device(row) for row in devices],
            'count': len(devices),
        }

    # ------------------------------------------------------------------
    # Dispositivos clínicos
    # ------------------------------------------------------------------
    def list_org_devices(
        self,
        org_id: str,
        user_id: str,
        params: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Lista dispositivos de una organización (sin filtro de care_team)."""
        membership = self._ensure_membership(org_id, user_id)

        active = self._parse_bool(params.get('active'), field='active') if 'active' in params else None
        connected = self._parse_bool(params.get('connected'), field='connected') if 'connected' in params else None
        patient_value = params.get('patient_id')
        patient_id = self._normalize_uuid(patient_value, field='patient_id') if patient_value else None
        limit = self._parse_limit(params.get('limit'), default=200, maximum=500, field='limit')
        offset = self._parse_offset(params.get('offset'), field='offset')

        rows = self.repo.list_org_devices(
            org_id,
            patient_id=patient_id,
            active=active,
            connected=connected,
            limit=limit,
            offset=offset,
        )
        devices = [self._format_org_device(row) for row in rows]

        return {
            'organization': membership,
            'devices': devices,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'returned': len(devices),
            },
        }

    def get_org_device_detail(
        self,
        org_id: str,
        device_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Obtiene detalle de un dispositivo de la organización."""
        membership = self._ensure_membership(org_id, user_id)
        record = self.repo.get_org_device(org_id, device_id)
        if not record:
            raise ValueError(f"Dispositivo {device_id} no encontrado en la organización {org_id}")

        return {
            'organization': membership,
            'device': self._format_org_device(record),
        }

    def list_device_streams(
        self,
        org_id: str,
        device_id: str,
        user_id: str,
        params: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Lista historial de streams de un dispositivo."""
        membership = self._ensure_membership(org_id, user_id)
        
        # Verificar que el dispositivo pertenece a la org
        device = self.repo.get_org_device(org_id, device_id)
        if not device:
            raise ValueError(f"Dispositivo {device_id} no encontrado en la organización {org_id}")

        limit = self._parse_limit(params.get('limit'), default=50, maximum=200, field='limit')
        offset = self._parse_offset(params.get('offset'), field='offset')

        rows = self.repo.list_device_streams(
            device_id,
            limit=limit,
            offset=offset,
        )
        streams = [self._format_device_stream(row) for row in rows]

        return {
            'organization': membership,
            'device': self._format_org_device(device),
            'streams': streams,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'returned': len(streams),
            },
        }

    def list_care_team_devices(
        self,
        org_id: str,
        care_team_id: str,
        user_id: str,
        params: Mapping[str, Any],
    ) -> Dict[str, Any]:
        membership, care_team = self._ensure_care_team_access(org_id, care_team_id, user_id)

        active = self._parse_bool(params.get('active'), field='active') if 'active' in params else None
        patient_value = params.get('patient_id')
        patient_id = self._normalize_uuid(patient_value, field='patient_id') if patient_value else None
        limit = self._parse_limit(params.get('limit'), default=200, maximum=500, field='limit')
        offset = self._parse_offset(params.get('offset'), field='offset')

        rows = self.repo.list_care_team_devices(
            org_id,
            care_team_id,
            patient_id=patient_id,
            active=active,
            limit=limit,
            offset=offset,
        )
        devices = [self._format_care_team_device(row) for row in rows]

        return {
            'organization': membership,
            'care_team': self._format_care_team_summary(care_team),
            'devices': devices,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'returned': len(devices),
            },
        }

    def get_care_team_device_detail(
        self,
        org_id: str,
        care_team_id: str,
        device_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        membership, care_team = self._ensure_care_team_access(org_id, care_team_id, user_id)
        record = self.repo.get_care_team_device(org_id, care_team_id, device_id)
        if not record:
            raise ValueError("Dispositivo no encontrado en el equipo indicado")

        return {
            'organization': membership,
            'care_team': self._format_care_team_summary(care_team),
            'device': self._format_care_team_device(record),
        }

    def list_care_team_device_streams(
        self,
        org_id: str,
        care_team_id: str,
        device_id: str,
        user_id: str,
        params: Mapping[str, Any],
    ) -> Dict[str, Any]:
        membership, care_team = self._ensure_care_team_access(org_id, care_team_id, user_id)
        device_record = self.repo.get_care_team_device(org_id, care_team_id, device_id)
        if not device_record:
            raise ValueError("Dispositivo no encontrado en el equipo indicado")

        limit = self._parse_limit(params.get('limit'), default=200, maximum=500, field='limit')
        offset = self._parse_offset(params.get('offset'), field='offset')

        rows = self.repo.list_care_team_device_streams(
            org_id,
            care_team_id,
            device_id,
            limit=limit,
            offset=offset,
        )
        streams = [self._format_device_stream(row) for row in rows]

        return {
            'organization': membership,
            'care_team': self._format_care_team_summary(care_team),
            'device': self._format_care_team_device(device_record),
            'streams': streams,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'returned': len(streams),
            },
        }

    def list_care_team_disconnected_devices(
        self,
        org_id: str,
        care_team_id: str,
        user_id: str,
        params: Mapping[str, Any],
    ) -> Dict[str, Any]:
        membership, care_team = self._ensure_care_team_access(org_id, care_team_id, user_id)

        limit = self._parse_limit(params.get('limit'), default=200, maximum=500, field='limit')
        offset = self._parse_offset(params.get('offset'), field='offset')

        rows = self.repo.list_care_team_disconnected_devices(
            org_id,
            care_team_id,
            limit=limit,
            offset=offset,
        )
        devices = [self._format_care_team_device(row) for row in rows]

        return {
            'organization': membership,
            'care_team': self._format_care_team_summary(care_team),
            'devices': devices,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'returned': len(devices),
            },
        }

    # ------------------------------------------------------------------
    # Dispositivos push
    # ------------------------------------------------------------------
    def list_push_devices(self, user_id: str) -> Dict[str, Any]:
        rows = self.repo.list_push_devices(user_id)
        devices = [self._format_push_device(row) for row in rows]
        return {
            'count': len(devices),
            'devices': devices,
        }

    def register_push_device(self, user_id: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        platform_code = str(payload.get('platform_code') or '').strip()
        if not platform_code:
            raise ValueError("Se requiere el campo platform_code")

        push_token = str(payload.get('push_token') or '').strip()
        if not push_token:
            raise ValueError("Se requiere el campo push_token")

        active_flag = None
        if 'active' in payload:
            active_flag = self._parse_bool(payload.get('active'), field='active')
            if active_flag is None:
                raise ValueError("El campo active debe ser true o false")
        active = active_flag if active_flag is not None else True

        last_seen_at = None
        if 'last_seen_at' in payload:
            last_seen_at = self._parse_datetime(payload.get('last_seen_at'), field='last_seen_at') or self._now()

        platform = self.repo.get_platform_by_code(platform_code)
        if not platform:
            raise ValueError("Plataforma no reconocida")

        platform_id = str(platform['id'])
        existing = self.repo.find_push_device_by_token(user_id, push_token, platform_id)

        if existing:
            updates: Dict[str, Any] = {
                'last_seen_at': last_seen_at or self._now(),
                'active': active,
            }
            updated_id = self.repo.update_push_device(user_id, str(existing['id']), updates)
            if not updated_id:
                raise ValueError("No se pudo actualizar el dispositivo existente")
            record = self.repo.get_push_device(user_id, updated_id)
            if not record:
                raise ValueError("No se pudo recuperar el dispositivo push")
            return {
                'device': self._format_push_device(record),
                'created': False,
            }

        created_id = self.repo.create_push_device(
            user_id,
            platform_id=platform_id,
            push_token=push_token,
            last_seen_at=last_seen_at,
            active=active,
        )
        if not created_id:
            raise ValueError("No se pudo registrar el dispositivo push")

        record = self.repo.get_push_device(user_id, created_id)
        if not record:
            raise ValueError("No se pudo recuperar el dispositivo push creado")

        return {
            'device': self._format_push_device(record),
            'created': True,
        }

    def update_push_device(self, user_id: str, device_id: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        existing = self.repo.get_push_device(user_id, device_id)
        if not existing:
            raise ValueError("Dispositivo push no encontrado")

        updates: Dict[str, Any] = {}

        if 'push_token' in payload:
            push_token = str(payload.get('push_token') or '').strip()
            if not push_token:
                raise ValueError("El campo push_token no puede estar vacío")
            updates['push_token'] = push_token

        if 'active' in payload:
            active_flag = self._parse_bool(payload.get('active'), field='active')
            if active_flag is None:
                raise ValueError("El campo active debe ser true o false")
            updates['active'] = active_flag

        if 'last_seen_at' in payload:
            parsed = self._parse_datetime(payload.get('last_seen_at'), field='last_seen_at')
            updates['last_seen_at'] = parsed or self._now()

        if 'platform_code' in payload:
            platform_code = str(payload.get('platform_code') or '').strip()
            if not platform_code:
                raise ValueError("El campo platform_code no puede estar vacío")
            platform = self.repo.get_platform_by_code(platform_code)
            if not platform:
                raise ValueError("Plataforma no reconocida")
            updates['platform_id'] = str(platform['id'])

        if not updates:
            raise ValueError("No hay cambios válidos para aplicar al dispositivo push")

        if 'push_token' in updates or 'platform_id' in updates:
            target_token = updates.get('push_token', existing['push_token'])
            current_platform_id = str(existing['platform_id']) if existing.get('platform_id') else None
            target_platform_id = updates.get('platform_id', current_platform_id)
            if target_platform_id:
                duplicate = self.repo.find_push_device_by_token(user_id, target_token, target_platform_id)
                if duplicate and str(duplicate['id']) != device_id:
                    raise ValueError("Ya existe un dispositivo push con el mismo token para la plataforma indicada")

        updated_id = self.repo.update_push_device(user_id, device_id, updates)
        if not updated_id:
            raise ValueError("No se pudo actualizar el dispositivo push")

        record = self.repo.get_push_device(user_id, updated_id)
        if not record:
            raise ValueError("No se pudo recuperar el dispositivo push actualizado")

        return {
            'device': self._format_push_device(record),
        }

    def delete_push_device(self, user_id: str, device_id: str) -> None:
        deleted = self.repo.delete_push_device(user_id, device_id)
        if not deleted:
            raise ValueError("Dispositivo push no encontrado")

    # ------------------------------------------------------------------
    # Ubicaciones para equipos de cuidado y cuidadores
    # ------------------------------------------------------------------
    def list_care_team_locations(self, user_id: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        type_param = str(params.get('type', 'all') or 'all').strip().lower()
        if type_param not in {'all', 'patients', 'members'}:
            raise ValueError("El parámetro type debe ser uno de: patients, members o all")

        include_patients = type_param in {'all', 'patients'}
        include_members = type_param in {'all', 'members'}

        org_id = self._normalize_uuid(params.get('org_id'), field='org_id')
        care_team_id = self._normalize_uuid(params.get('care_team_id'), field='care_team_id')

        alert_level = self._normalize_code(params.get('alert_level'), field='alert_level')
        updated_after = self._parse_datetime_param(params.get('updated_after'), field='updated_after')
        bbox = self._parse_bbox(params.get('bbox'))
        limit = self._parse_limit(params.get('limit'), default=500, maximum=1000, field='limit')

        patients: List[Dict[str, Any]] = []
        members: List[Dict[str, Any]] = []

        if include_patients:
            patient_rows = self.repo.list_care_team_patient_locations(
                user_id,
                org_id=org_id,
                care_team_id=care_team_id,
                alert_level=alert_level,
                updated_after=updated_after,
                bbox=bbox,
                limit=limit,
            )
            patients = [self._format_team_patient_location(row) for row in patient_rows]

        if include_members:
            member_rows = self.repo.list_care_team_member_locations(
                user_id,
                org_id=org_id,
                care_team_id=care_team_id,
                alert_level=alert_level,
                updated_after=updated_after,
                bbox=bbox,
                limit=limit,
            )
            members = [self._format_team_member_location(row) for row in member_rows]

        total = len(patients) + len(members)
        return {
            'count': total,
            'patients': patients,
            'members': members,
        }

    def list_caregiver_patient_locations(self, user_id: str, params: Mapping[str, Any]) -> Dict[str, Any]:
        updated_after = self._parse_datetime_param(params.get('updated_after'), field='updated_after')
        bbox = self._parse_bbox(params.get('bbox'))
        risk_level = self._normalize_code(params.get('risk_level'), field='risk_level')
        has_active_alerts = self._parse_bool(params.get('has_active_alerts'), field='has_active_alerts')
        include_without_location = bool(self._parse_bool(params.get('include_without_location'), field='include_without_location') or False)
        limit = self._parse_limit(params.get('limit'), default=500, maximum=1000, field='limit')
        offset = self._parse_offset(params.get('offset'), field='offset')

        sort_param = str(params.get('sort', 'recent') or 'recent').strip().lower()
        if sort_param not in {'recent', 'severity'}:
            raise ValueError("El parámetro sort debe ser recent o severity")

        rows = self.repo.list_caregiver_patient_locations(
            user_id,
            updated_after=updated_after,
            bbox=bbox,
            risk_level=risk_level,
            has_active_alerts=has_active_alerts,
            include_without_location=include_without_location,
            sort_by=sort_param,
            limit=limit,
            offset=offset,
        )

        patients = [self._format_caregiver_patient_location(row) for row in rows]
        return {
            'count': len(patients),
            'patients': patients,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'returned': len(patients),
            },
        }

    # ------------------------------------------------------------------
    # Helpers de validación y formateo
    # ------------------------------------------------------------------
    def _ensure_membership(self, org_id: str, user_id: str) -> Dict[str, Any]:
        membership = self.repo.get_membership(org_id, user_id)
        if not membership:
            raise PermissionError("No perteneces a la organización solicitada")
        return self._format_membership(membership)

    def _ensure_care_team_access(self, org_id: str, care_team_id: str, user_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        membership = self._ensure_membership(org_id, user_id)
        care_team = self.repo.get_care_team_membership(org_id, care_team_id, user_id)
        if not care_team:
            raise PermissionError("No perteneces al equipo de cuidado solicitado")
        return membership, care_team

    def _ensure_caregiver_access(self, patient_id: str, user_id: str) -> Dict[str, Any]:
        relationship = self.repo.get_caregiver_relationship(user_id, patient_id)
        if not relationship:
            raise PermissionError("No tienes relación de cuidador con este paciente")
        if not self._relationship_is_active(relationship):
            raise PermissionError("La relación de cuidador está inactiva")
        return relationship

    @staticmethod
    def _relationship_is_active(relationship: Dict[str, Any]) -> bool:
        ended_at = relationship.get('ended_at')
        if not ended_at:
            return True
        if not isinstance(ended_at, datetime):
            return False
        now = datetime.now(tz=ended_at.tzinfo) if ended_at.tzinfo else datetime.utcnow()
        comparison_now = now if ended_at.tzinfo else now.replace(tzinfo=None)
        comparison_end = ended_at if ended_at.tzinfo else ended_at.replace(tzinfo=None)
        return comparison_end > comparison_now

    @staticmethod
    def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if isinstance(value, datetime) else None

    def _format_profile(self, record: Dict[str, Any]) -> Dict[str, Any]:
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
            'created_at': self._serialize_datetime(record.get('created_at')),
            'updated_at': self._serialize_datetime(record.get('updated_at')),
        }

    def _format_membership(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'org_id': str(record['org_id']),
            'org_code': record.get('org_code'),
            'org_name': record.get('org_name'),
            'role_code': record['role_code'],
            'role_label': record.get('role_label'),
            'joined_at': self._serialize_datetime(record.get('joined_at')),
        }

    def _format_patient(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(record['id']),
            'name': record.get('person_name'),
            'email': record.get('email'),
            'birthdate': record.get('birthdate').isoformat() if record.get('birthdate') else None,
            'org_id': str(record['org_id']) if record.get('org_id') else None,
            'org_name': record.get('org_name'),
            'profile_photo_url': record.get('profile_photo_url'),
            'risk_level': {
                'code': record.get('risk_level_code'),
                'label': record.get('risk_level_label'),
            },
            'sex': {
                'code': record.get('sex_code'),
                'label': record.get('sex_label'),
            },
            'created_at': self._serialize_datetime(record.get('created_at')),
        }

    def _format_patient_summary(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(record['id']),
            'name': record.get('person_name'),
            'email': record.get('email'),
            'risk_level': {
                'code': record.get('risk_level_code'),
                'label': record.get('risk_level_label'),
            },
        }

    def _format_care_team_summary(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(record['care_team_id']),
            'name': record.get('care_team_name'),
            'organization': {
                'id': str(record['org_id']) if record.get('org_id') else None,
                'name': record.get('org_name'),
            },
            'role': {
                'code': record.get('role_code'),
                'label': record.get('role_label'),
            },
            'joined_at': self._serialize_datetime(record.get('joined_at')),
        }

    def _format_alert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(record['id']),
            'created_at': self._serialize_datetime(record.get('created_at')),
            'description': record.get('description'),
            'type': {
                'code': record.get('alert_type_code'),
                'label': record.get('alert_type_label'),
            },
            'level': {
                'code': record.get('level_code'),
                'label': record.get('level_label'),
            },
            'status': {
                'code': record.get('status_code'),
                'label': record.get('status_label'),
            },
        }

    def _format_note(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(record['id']),
            'event': {
                'code': record.get('event_code'),
                'label': record.get('event_label'),
            },
            'onset': self._serialize_datetime(record.get('onset')),
            'offset_at': self._serialize_datetime(record.get('offset_at')),
            'note': record.get('note'),
            'source': record.get('source'),
            'annotated_by': {
                'user_id': str(record['annotated_by_user_id']) if record.get('annotated_by_user_id') else None,
                'name': record.get('annotated_by_name'),
            },
        }

    def _format_patient_device(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea un dispositivo asignado a un paciente."""
        return {
            'id': str(record['device_id']),
            'serial': record.get('serial'),
            'brand': record.get('brand'),
            'model': record.get('model'),
            'device_type': {
                'code': record.get('device_type_code'),
                'label': record.get('device_type_label'),
            },
            'registered_at': self._serialize_datetime(record.get('registered_at')),
            'stream': {
                'id': str(record['stream_id']) if record.get('stream_id') else None,
                'started_at': self._serialize_datetime(record.get('stream_started_at')),
                'ended_at': self._serialize_datetime(record.get('stream_ended_at')),
                'is_active': record.get('stream_id') is not None and record.get('stream_ended_at') is None,
            } if record.get('stream_id') else None,
        }

    def _format_org_overview(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'total_patients': data.get('total_patients', 0),
            'total_care_teams': data.get('total_care_teams', 0),
            'total_caregivers': data.get('total_caregivers', 0),
            'alerts_last_7d': data.get('alerts_last_7d', 0),
            'open_alerts': data.get('open_alerts', 0),
            'latest_alert_at': self._serialize_datetime(data.get('latest_alert_at')),
        }

    def _format_org_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'total_alerts': data.get('total_alerts', 0),
            'max_alerts_by_patient': data.get('max_alerts_by_patient', 0),
            'avg_alerts_per_patient': float(data.get('avg_alerts_per_patient', 0) or 0),
        }

    def _format_caregiver_patient(self, record: Dict[str, Any]) -> Dict[str, Any]:
        relationship = {
            'code': record.get('relationship_code'),
            'label': record.get('relationship_label'),
            'is_primary': record.get('is_primary', False),
            'note': record.get('relationship_note'),
            'started_at': self._serialize_datetime(record.get('started_at')),
            'ended_at': self._serialize_datetime(record.get('ended_at')),
        }
        relationship['active'] = self._relationship_is_active({
            'ended_at': record.get('ended_at'),
        })
        return {
            'id': str(record['patient_id']),
            'name': record.get('patient_name'),
            'email': record.get('patient_email'),
            'organization': {
                'id': str(record['org_id']) if record.get('org_id') else None,
                'name': record.get('org_name'),
            },
            'risk_level': {
                'code': record.get('risk_level_code'),
                'label': record.get('risk_level_label'),
            },
            'relationship': relationship,
        }

    def _format_relationship(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'code': record.get('relationship_code'),
            'label': record.get('relationship_label'),
            'is_primary': record.get('is_primary', False),
            'note': record.get('relationship_note'),
            'started_at': self._serialize_datetime(record.get('started_at')),
            'ended_at': self._serialize_datetime(record.get('ended_at')),
            'active': self._relationship_is_active(record),
        }

    def _parse_datetime(self, value: Any, *, field: str) -> Optional[datetime]:
        if value in (None, ''):
            return None
        if isinstance(value, datetime):
            return value
        try:
            text = str(value).strip()
            if text.endswith('Z'):
                text = text[:-1] + '+00:00'
            return datetime.fromisoformat(text)
        except ValueError as exc:  # pragma: no cover - validación defensiva
            raise ValueError(f"Formato inválido para {field}, usa ISO 8601") from exc

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (float, int)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _format_team_patient_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        location = {
            'latitude': self._coerce_float(row.get('latitude')),
            'longitude': self._coerce_float(row.get('longitude')),
            'last_update': self._serialize_datetime(row.get('last_location_at')),
            'approximate': False,
        }
        alert = None
        if row.get('alert_id'):
            alert = {
                'id': str(row['alert_id']),
                'created_at': self._serialize_datetime(row.get('alert_created_at')),
                'code': row.get('alert_code'),
                'label': row.get('alert_label'),
                'level': {
                    'code': row.get('alert_level_code'),
                    'label': row.get('alert_level_label'),
                },
            }

        return {
            'id': str(row['patient_id']),
            'name': row.get('patient_name'),
            'email': row.get('patient_email'),
            'organization': {
                'id': str(row['org_id']) if row.get('org_id') else None,
                'name': row.get('org_name'),
            },
            'care_team': {
                'id': str(row['care_team_id']),
                'name': row.get('care_team_name'),
            },
            'risk_level': {
                'code': row.get('risk_level_code'),
                'label': row.get('risk_level_label'),
            },
            'location': location,
            'alert': alert,
        }

    def _format_team_member_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        latitude = self._coerce_float(row.get('centroid_latitude'))
        longitude = self._coerce_float(row.get('centroid_longitude'))
        approximate = latitude is not None and longitude is not None

        location = None
        if approximate:
            location = {
                'latitude': latitude,
                'longitude': longitude,
                'last_update': self._serialize_datetime(row.get('last_seen_at')),
                'approximate': True,
            }

        return {
            'id': str(row['member_user_id']),
            'name': row.get('member_name'),
            'email': row.get('member_email'),
            'organization': {
                'id': str(row['org_id']) if row.get('org_id') else None,
                'name': row.get('org_name'),
            },
            'care_team': {
                'id': str(row['care_team_id']),
                'name': row.get('care_team_name'),
            },
            'role': {
                'code': row.get('role_code'),
                'label': row.get('role_label'),
            },
            'location': location,
        }

    def _format_caregiver_patient_location(self, row: Dict[str, Any]) -> Dict[str, Any]:
        latitude = self._coerce_float(row.get('latitude'))
        longitude = self._coerce_float(row.get('longitude'))
        location = None
        if latitude is not None or longitude is not None:
            location = {
                'latitude': latitude,
                'longitude': longitude,
                'last_update': self._serialize_datetime(row.get('last_location_at')),
                'approximate': False,
            }

        alert = None
        if row.get('alert_code'):
            alert = {
                'code': row.get('alert_code'),
                'label': row.get('alert_label'),
                'level': {
                    'code': row.get('alert_level_code'),
                    'label': row.get('alert_level_label'),
                },
            }

        return {
            'id': str(row['patient_id']),
            'name': row.get('patient_name'),
            'email': row.get('patient_email'),
            'risk_level': {
                'code': row.get('risk_level_code'),
                'label': row.get('risk_level_label'),
            },
            'location': location,
            'last_alert': alert,
        }

    def _format_org_device(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea un dispositivo con información de owner y conexión actual.
        - owner: paciente owner_patient_id
        - current_patient: paciente con stream activo (puede ser diferente)
        - connected: boolean basado en active_stream_id
        """
        owner_id = row.get('owner_patient_id')
        current_patient_id = row.get('current_patient_id')
        
        return {
            'id': str(row['id']),
            'serial': row.get('serial'),
            'brand': row.get('brand'),
            'model': row.get('model'),
            'active': bool(row.get('active', False)),
            'registered_at': self._serialize_datetime(row.get('registered_at')),
            'connected': bool(row.get('active', False)) and row.get('active_stream_id') is not None,
            'type': {
                'code': row.get('device_type_code'),
                'label': row.get('device_type_label'),
            },
            'owner': {
                'id': str(owner_id) if owner_id else None,
                'name': row.get('owner_patient_name'),
                'email': row.get('owner_patient_email'),
            },
            'current_connection': {
                'patient_id': str(current_patient_id) if current_patient_id else None,
                'patient_name': row.get('current_patient_name'),
                'started_at': self._serialize_datetime(row.get('connection_started_at')),
            } if current_patient_id else None,
            'streams': {
                'total': int(row.get('total_streams') or 0),
                'last_started_at': self._serialize_datetime(row.get('last_started_at')),
            },
        }

    def _format_care_team_device(self, row: Dict[str, Any]) -> Dict[str, Any]:
        owner_id = row.get('owner_patient_id')
        return {
            'id': str(row['id']),
            'serial': row.get('serial'),
            'brand': row.get('brand'),
            'model': row.get('model'),
            'active': bool(row.get('active', False)),
            'registered_at': self._serialize_datetime(row.get('registered_at')),
            'type': {
                'code': row.get('device_type_code'),
                'label': row.get('device_type_label'),
            },
            'owner': {
                'id': str(owner_id) if owner_id else None,
                'name': row.get('patient_name'),
                'email': row.get('patient_email'),
            },
            'streams': {
                'last_started_at': self._serialize_datetime(row.get('last_started_at')),
                'last_ended_at': self._serialize_datetime(row.get('last_ended_at')),
                'count': int(row.get('total_streams') or 0),
            },
        }

    def _format_device_stream(self, row: Dict[str, Any]) -> Dict[str, Any]:
        patient_id = row.get('patient_id')
        return {
            'id': str(row['id']),
            'device_id': str(row['device_id']) if row.get('device_id') else None,
            'status': row.get('status'),
            'patient': {
                'id': str(patient_id) if patient_id else None,
                'name': row.get('patient_name'),
                'email': row.get('patient_email'),
            },
            'started_at': self._serialize_datetime(row.get('started_at')),
            'ended_at': self._serialize_datetime(row.get('ended_at')),
        }

    def _format_push_device(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': str(record['id']),
            'push_token': record.get('push_token'),
            'active': bool(record.get('active', False)),
            'last_seen_at': self._serialize_datetime(record.get('last_seen_at')),
            'platform': {
                'id': str(record['platform_id']) if record.get('platform_id') else None,
                'code': record.get('platform_code'),
                'label': record.get('platform_label'),
            },
        }

    def _parse_datetime_param(self, value: Any, *, field: str) -> Optional[datetime]:
        if value in (None, ''):
            return None
        try:
            parsed = self._parse_datetime(value, field=field)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return parsed

    def _get_user_identity(self, user_id: str) -> Dict[str, Any]:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                    SELECT id, email, name
                    FROM users
                    WHERE id = %s
                """,
                (user_id,),
            )
            record = cursor.fetchone()
        if not record:
            raise ValueError("Usuario no encontrado")
        return record

    @staticmethod
    def _normalize_email(email: Any) -> Optional[str]:
        if not email:
            return None
        return str(email).strip().lower() or None

    def _pending_invitations_query(self) -> str:
        return """
            SELECT
                inv.id,
                inv.org_id,
                inv.email,
                inv.role_code,
                inv.expires_at,
                inv.used_at,
                inv.revoked_at,
                inv.created_at,
                inv.created_by,
                org.code AS org_code,
                org.name AS org_name,
                creator.name AS invited_by_name,
                creator.email AS invited_by_email,
                roles.label AS role_label
            FROM org_invitations inv
            JOIN organizations org ON org.id = inv.org_id
            LEFT JOIN users creator ON creator.id = inv.created_by
            LEFT JOIN roles roles ON roles.code = inv.role_code
            WHERE lower(inv.email) = %s
              AND inv.revoked_at IS NULL
              AND inv.used_at IS NULL
              AND (inv.expires_at IS NULL OR inv.expires_at > NOW())
            ORDER BY inv.created_at DESC
        """

    def _invitation_lookup_query(self, lock: bool = False) -> str:
        if lock:
            # Para lock, usamos una subquery sin LEFT JOIN para evitar el error de PostgreSQL
            return """
                SELECT
                    inv.id,
                    inv.org_id,
                    inv.email,
                    inv.role_code,
                    inv.expires_at,
                    inv.used_at,
                    inv.revoked_at,
                    inv.created_at,
                    inv.created_by,
                    (SELECT code FROM organizations WHERE id = inv.org_id) AS org_code,
                    (SELECT name FROM organizations WHERE id = inv.org_id) AS org_name,
                    (SELECT name FROM users WHERE id = inv.created_by) AS invited_by_name,
                    (SELECT email FROM users WHERE id = inv.created_by) AS invited_by_email,
                    (SELECT label FROM roles WHERE code = inv.role_code) AS role_label
                FROM org_invitations inv
                WHERE inv.id = %s
                  AND lower(inv.email) = %s
                FOR UPDATE OF inv
            """
        return """
            SELECT
                inv.id,
                inv.org_id,
                inv.email,
                inv.role_code,
                inv.expires_at,
                inv.used_at,
                inv.revoked_at,
                inv.created_at,
                inv.created_by,
                org.code AS org_code,
                org.name AS org_name,
                creator.name AS invited_by_name,
                creator.email AS invited_by_email,
                roles.label AS role_label
            FROM org_invitations inv
            JOIN organizations org ON org.id = inv.org_id
            LEFT JOIN users creator ON creator.id = inv.created_by
            LEFT JOIN roles roles ON roles.code = inv.role_code
            WHERE inv.id = %s
              AND lower(inv.email) = %s
        """

    def _membership_lookup_query(self) -> str:
        return """
            SELECT
                m.org_id,
                m.user_id,
                m.role_code,
                COALESCE(r.label, m.role_code) AS role_label,
                m.joined_at,
                o.code AS org_code,
                o.name AS org_name
            FROM user_org_membership m
            JOIN organizations o ON o.id = m.org_id
            LEFT JOIN roles r ON r.code = m.role_code
            WHERE m.org_id = %s AND m.user_id = %s
        """

    def _fetch_invitation_for_user(self, cursor, invite_id: str, normalized_email: Optional[str], lock: bool = False) -> Optional[Dict[str, Any]]:
        if not normalized_email:
            return None
        cursor.execute(self._invitation_lookup_query(lock=lock), (invite_id, normalized_email))
        return cursor.fetchone()

    def _ensure_invitation_pending(self, invitation: Mapping[str, Any]) -> None:
        if invitation.get('used_at') is not None:
            raise ValueError("La invitación ya fue utilizada")
        if invitation.get('revoked_at') is not None:
            raise ValueError("La invitación ya fue revocada")
        expires_at = invitation.get('expires_at')
        if self._is_invitation_expired(expires_at):
            raise ValueError("La invitación ha expirado")

    def _format_invitation(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        used_at = record.get('used_at')
        revoked_at = record.get('revoked_at')
        expires_at = record.get('expires_at')
        status = 'pending'
        if used_at:
            status = 'accepted'
        elif revoked_at:
            status = 'revoked'
        elif self._is_invitation_expired(expires_at):
            status = 'expired'

        return {
            'id': str(record['id']),
            'email': self._normalize_email(record.get('email')),
            'status': status,
            'role': {
                'code': record.get('role_code'),
                'label': record.get('role_label'),
            },
            'organization': {
                'id': str(record['org_id']) if record.get('org_id') else None,
                'code': record.get('org_code'),
                'name': record.get('org_name'),
            },
            'invited_by': {
                'id': str(record['created_by']) if record.get('created_by') else None,
                'name': record.get('invited_by_name'),
                'email': self._normalize_email(record.get('invited_by_email')),
            },
            'expires_at': self._serialize_datetime(expires_at),
            'used_at': self._serialize_datetime(used_at),
            'revoked_at': self._serialize_datetime(revoked_at),
            'created_at': self._serialize_datetime(record.get('created_at')),
        }

    def _is_invitation_expired(self, expires_at: Any) -> bool:
        if not isinstance(expires_at, datetime):
            return False
        now = self._now()
        if expires_at.tzinfo and now.tzinfo:
            return expires_at <= now
        if expires_at.tzinfo and not now.tzinfo:
            return expires_at <= now.replace(tzinfo=expires_at.tzinfo)
        if not expires_at.tzinfo and now.tzinfo:
            comparable = expires_at.replace(tzinfo=now.tzinfo)
            return comparable <= now
        return expires_at <= now.replace(tzinfo=None)

    @staticmethod
    def _parse_limit(value: Any, *, default: int, maximum: int, field: str) -> int:
        if value in (None, ''):
            return default
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"El parámetro {field} debe ser un entero válido") from exc
        if parsed <= 0:
            raise ValueError(f"El parámetro {field} debe ser mayor a cero")
        if parsed > maximum:
            return maximum
        return parsed

    @staticmethod
    def _parse_offset(value: Any, *, field: str) -> int:
        if value in (None, ''):
            return 0
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"El parámetro {field} debe ser un entero válido") from exc
        if parsed < 0:
            raise ValueError(f"El parámetro {field} no puede ser negativo")
        return parsed

    @staticmethod
    def _parse_bool(value: Any, *, field: str) -> Optional[bool]:
        if value in (None, ''):
            return None
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {'true', '1', 'yes', 'si', 'sí'}:
            return True
        if text in {'false', '0', 'no'}:
            return False
        raise ValueError(f"El parámetro {field} debe ser true o false")

    @staticmethod
    def _normalize_code(value: Any, *, field: str) -> Optional[str]:
        if value in (None, ''):
            return None
        code = str(value).strip()
        if not code:
            raise ValueError(f"El parámetro {field} no puede estar vacío")
        return code.lower()

    @staticmethod
    def _normalize_uuid(value: Any, *, field: str) -> Optional[str]:
        if value in (None, ''):
            return None
        try:
            return str(UUID(str(value)))
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"El parámetro {field} debe ser un UUID válido") from exc

    @staticmethod
    def _parse_bbox(value: Any) -> Optional[Dict[str, float]]:
        if value in (None, ''):
            return None
        if isinstance(value, (list, tuple)):
            parts = [str(v) for v in value]
        else:
            parts = str(value).split(',')
        if len(parts) != 4:
            raise ValueError("El parámetro bbox debe tener cuatro valores separados por comas")
        try:
            min_lng, min_lat, max_lng, max_lat = [float(part.strip()) for part in parts]
        except (TypeError, ValueError) as exc:
            raise ValueError("El parámetro bbox debe contener valores numéricos válidos") from exc
        if min_lng >= max_lng or min_lat >= max_lat:
            raise ValueError("El parámetro bbox debe tener rangos válidos (min < max)")
        return {
            'min_lng': min_lng,
            'min_lat': min_lat,
            'max_lng': max_lng,
            'max_lat': max_lat,
        }
