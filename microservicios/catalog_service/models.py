"""SQLAlchemy models for catalog entries."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text, func

from .db import db


class CatalogBase(db.Model):
    """Base mixin providing shared columns for catalog tables."""

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    org_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=func.now())

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<{self.__class__.__name__} id={self.id!r} name={self.name!r}>"


class CareSpecialty(CatalogBase):
    __tablename__ = "care_specialties"


class MedicalDevice(CatalogBase):
    __tablename__ = "medical_devices"


class MedicationClass(CatalogBase):
    __tablename__ = "medication_classes"


class InsuranceProvider(CatalogBase):
    __tablename__ = "insurance_providers"


class ServiceCode(CatalogBase):
    __tablename__ = "service_codes"


class DiagnosisCategory(CatalogBase):
    __tablename__ = "diagnosis_categories"


class ClinicalProgram(CatalogBase):
    __tablename__ = "clinical_programs"


class CareLocation(CatalogBase):
    __tablename__ = "care_locations"


class AppointmentType(CatalogBase):
    __tablename__ = "appointment_types"


class CommunicationTemplate(CatalogBase):
    __tablename__ = "communication_templates"
