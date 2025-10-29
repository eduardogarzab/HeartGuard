"""Repository layer for catalog tables."""
from __future__ import annotations

from typing import Any, Dict, List, Type

from flask import g
from sqlalchemy import or_

from .db import db
from .models import (
    AppointmentType,
    CareLocation,
    CareSpecialty,
    ClinicalProgram,
    CommunicationTemplate,
    DiagnosisCategory,
    InsuranceProvider,
    MedicalDevice,
    MedicationClass,
    ServiceCode,
)

CatalogModel = Type[CareSpecialty]


class PermissionDenied(Exception):
    """Raised when the caller does not have enough privileges."""


class CatalogNotFound(Exception):
    """Raised when a catalog or entry is not found."""


class CatalogRepository:
    """Repository handling catalog CRUD operations."""

    _catalog_map: Dict[str, CatalogModel] = {
        "care_specialties": CareSpecialty,
        "medical_devices": MedicalDevice,
        "medication_classes": MedicationClass,
        "insurance_providers": InsuranceProvider,
        "service_codes": ServiceCode,
        "diagnosis_categories": DiagnosisCategory,
        "clinical_programs": ClinicalProgram,
        "care_locations": CareLocation,
        "appointment_types": AppointmentType,
        "communication_templates": CommunicationTemplate,
    }

    def __init__(self, session=None):
        self.session = session or db.session

    def _get_model(self, catalog_name: str) -> CatalogModel:
        try:
            return self._catalog_map[catalog_name]
        except KeyError as exc:
            raise CatalogNotFound(f"Unknown catalog '{catalog_name}'") from exc

    def list_entries(self, catalog_name: str, org_id: str) -> List[Dict[str, Any]]:
        model = self._get_model(catalog_name)
        rows = (
            self.session.query(model)
            .filter(or_(model.org_id.is_(None), model.org_id == org_id))
            .order_by(model.name.asc())
            .all()
        )
        return [self._serialize(row) for row in rows]

    def get_entry(self, catalog_name: str, entry_id: str, org_id: str) -> Dict[str, Any]:
        model = self._get_model(catalog_name)
        entry = (
            self.session.query(model)
            .filter(model.id == entry_id)
            .filter(or_(model.org_id.is_(None), model.org_id == org_id))
            .one_or_none()
        )
        if not entry:
            raise CatalogNotFound("Catalog entry not found")
        return self._serialize(entry)

    def create_entry(self, catalog_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_admin()
        model = self._get_model(catalog_name)
        entry = model(
            name=payload["name"],
            description=payload.get("description"),
            org_id=payload.get("org_id", g.org_id),
        )
        self.session.add(entry)
        self.session.commit()
        return self._serialize(entry)

    def update_entry(self, catalog_name: str, entry_id: str, payload: Dict[str, Any], org_id: str) -> Dict[str, Any]:
        self._ensure_admin()
        model = self._get_model(catalog_name)
        entry = (
            self.session.query(model)
            .filter(model.id == entry_id)
            .filter(or_(model.org_id.is_(None), model.org_id == org_id))
            .one_or_none()
        )
        if not entry:
            raise CatalogNotFound("Catalog entry not found")

        if "name" in payload:
            entry.name = payload["name"]
        if "description" in payload:
            entry.description = payload["description"]
        if "org_id" in payload:
            entry.org_id = payload["org_id"]

        self.session.commit()
        return self._serialize(entry)

    def delete_entry(self, catalog_name: str, entry_id: str, org_id: str) -> None:
        self._ensure_admin()
        model = self._get_model(catalog_name)
        entry = (
            self.session.query(model)
            .filter(model.id == entry_id)
            .filter(or_(model.org_id.is_(None), model.org_id == org_id))
            .one_or_none()
        )
        if not entry:
            raise CatalogNotFound("Catalog entry not found")

        self.session.delete(entry)
        self.session.commit()

    @staticmethod
    def _ensure_admin() -> None:
        payload = getattr(g, "token_payload", {}) or {}
        roles = payload.get("roles")
        if isinstance(roles, str):
            roles = [roles]
        if not roles:
            roles = []
        role = payload.get("role")
        if role and role not in roles:
            roles.append(role)

        allowed = {"admin", "superadmin"}
        if not any(r in allowed for r in roles):
            raise PermissionDenied("Administrator privileges required")

    @staticmethod
    def _serialize(entry: Any) -> Dict[str, Any]:
        return {
            "id": entry.id,
            "name": entry.name,
            "description": entry.description,
            "org_id": entry.org_id,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }
