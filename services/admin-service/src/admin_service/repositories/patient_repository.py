"""Repository for patient persistence."""

from __future__ import annotations

from typing import Iterable, Optional
from uuid import UUID

from ..extensions import db
from ..models.patient import Patient


class PatientRepository:
    """Patient data access helpers."""

    @staticmethod
    def list_by_org(org_id: UUID) -> Iterable[Patient]:
        return Patient.query.filter_by(org_id=org_id).all()

    @staticmethod
    def create(**kwargs) -> Patient:
        patient = Patient(**kwargs)
        db.session.add(patient)
        db.session.commit()
        return patient

    @staticmethod
    def get_by_id(patient_id: UUID) -> Optional[Patient]:
        return Patient.query.filter_by(id=patient_id).first()

    @staticmethod
    def update(patient: Patient, **kwargs) -> Patient:
        for key, value in kwargs.items():
            setattr(patient, key, value)
        db.session.commit()
        return patient


__all__ = ["PatientRepository"]
