"""Database models and query helpers for the patient service."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, List

import uuid

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID

from common.database import db


class Patient(db.Model):
    """Represents a patient, mapping to the 'patients' table."""

    __tablename__ = 'patients'
    __table_args__ = {'extend_existing': True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # No ForeignKey for microservices - we just store the UUID reference
    org_id = db.Column(UUID(as_uuid=True))
    person_name = db.Column(db.String(120), nullable=False)
    birthdate = db.Column(db.Date)
    sex_id = db.Column(UUID(as_uuid=True))
    risk_level_id = db.Column(UUID(as_uuid=True))
    profile_photo_url = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the patient object to a dictionary."""

        created_at = _datetime_to_iso(self.created_at)
        return {
            'id': str(self.id),
            'org_id': str(self.org_id) if self.org_id else None,
            'person_name': self.person_name,
            'birthdate': self.birthdate.isoformat() if self.birthdate else None,
            'sex_id': str(self.sex_id) if self.sex_id else None,
            'risk_level_id': str(self.risk_level_id) if self.risk_level_id else None,
            'profile_photo_url': self.profile_photo_url,
            'created_at': created_at,
        }


class Sex(db.Model):
    """Catalog of biological sex options."""

    __tablename__ = 'sexes'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(8), unique=True, nullable=False)
    label = db.Column(db.String(40), nullable=False)


class RiskLevel(db.Model):
    """Catalog of risk levels for patients."""

    __tablename__ = 'risk_levels'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(20), unique=True, nullable=False)
    label = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Integer)


class AlertLevel(db.Model):
    """Catalog for alert severity levels."""

    __tablename__ = 'alert_levels'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class AlertStatus(db.Model):
    """Catalog for alert workflow statuses."""

    __tablename__ = 'alert_status'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.Text)


class Alert(db.Model):
    """Clinical alert generated for a patient."""

    __tablename__ = 'alerts'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(UUID(as_uuid=True), db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    alert_level_id = db.Column(UUID(as_uuid=True), db.ForeignKey('alert_levels.id', ondelete='RESTRICT'), nullable=False)
    status_id = db.Column(UUID(as_uuid=True), db.ForeignKey('alert_status.id', ondelete='RESTRICT'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())


@dataclass
class PatientAlertSummary:
    """DTO describing a recent alert of a patient."""

    severity: str
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, str]:
        return {
            'severity': self.severity,
            'status': self.status,
            'created_at': self.created_at,
        }


@dataclass
class PatientSummary:
    """Aggregated view for patient list payloads."""

    id: uuid.UUID
    org_id: uuid.UUID | None
    name: str
    gender: str
    age: int | None
    risk_level: str | None
    risk_level_label: str | None
    admission_date: str | None
    updated_at: str | None
    alerts: List[PatientAlertSummary]

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            'id': str(self.id),
            'org_id': str(self.org_id) if self.org_id else None,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'risk_level': self.risk_level,
            'admission_date': self.admission_date,
            'updated_at': self.updated_at,
            'alerts': [alert.to_dict() for alert in self.alerts],
        }
        if self.risk_level_label:
            data['risk_level_label'] = self.risk_level_label
        return data


def _calculate_age(birthdate: date | None) -> int | None:
    """Return the patient's age in full years."""

    if birthdate is None:
        return None

    today = date.today()
    years = today.year - birthdate.year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        years -= 1
    return max(years, 0)


def _datetime_to_iso(value: datetime | None) -> str | None:
    """Normalize datetimes to ISO-8601 strings in UTC."""

    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat()


class PatientQuery:
    """Typed helpers for patient queries used by the API."""

    RECENT_ALERT_LIMIT = 5

    @classmethod
    def list_with_details(cls, org_id: uuid.UUID | None = None) -> List[Dict[str, Any]]:
        """Return serialized patients enriched with catalog data and alerts."""

        query = (
            db.session.query(
                Patient.id.label('id'),
                Patient.org_id.label('org_id'),
                Patient.person_name.label('name'),
                Patient.birthdate.label('birthdate'),
                Patient.created_at.label('created_at'),
                Sex.code.label('sex_code'),
                Sex.label.label('sex_label'),
                RiskLevel.code.label('risk_code'),
                RiskLevel.label.label('risk_label'),
                func.coalesce(func.max(Alert.created_at), Patient.created_at).label('updated_at'),
            )
            .outerjoin(Sex, Sex.id == Patient.sex_id)
            .outerjoin(RiskLevel, RiskLevel.id == Patient.risk_level_id)
            .outerjoin(Alert, Alert.patient_id == Patient.id)
        )

        if org_id:
            query = query.filter(Patient.org_id == org_id)

        query = query.group_by(
            Patient.id,
            Patient.org_id,
            Patient.person_name,
            Patient.birthdate,
            Patient.created_at,
            Sex.code,
            Sex.label,
            RiskLevel.code,
            RiskLevel.label,
        ).order_by(Patient.person_name.asc())

        rows = query.all()
        patient_ids = [row.id for row in rows]

        alerts_by_patient: dict[uuid.UUID, List[PatientAlertSummary]] = defaultdict(list)
        if patient_ids:
            ranked_alerts = (
                db.session.query(
                    Alert.patient_id.label('patient_id'),
                    Alert.created_at.label('created_at'),
                    AlertLevel.code.label('level_code'),
                    AlertStatus.code.label('status_code'),
                    func.row_number()
                    .over(partition_by=Alert.patient_id, order_by=Alert.created_at.desc())
                    .label('rank'),
                )
                .join(AlertLevel, AlertLevel.id == Alert.alert_level_id)
                .join(AlertStatus, AlertStatus.id == Alert.status_id)
                .filter(Alert.patient_id.in_(patient_ids))
            ).subquery()

            recent_alerts = (
                db.session.query(ranked_alerts)
                .filter(ranked_alerts.c.rank <= cls.RECENT_ALERT_LIMIT)
                .order_by(ranked_alerts.c.patient_id, ranked_alerts.c.created_at.desc())
                .all()
            )

            for alert in recent_alerts:
                alerts_by_patient[alert.patient_id].append(
                    PatientAlertSummary(
                        severity=alert.level_code,
                        status=alert.status_code,
                        created_at=_datetime_to_iso(alert.created_at) or '',
                    )
                )

        summaries: List[Dict[str, Any]] = []
        for row in rows:
            summary = PatientSummary(
                id=row.id,
                org_id=row.org_id,
                name=row.name,
                gender=row.sex_label or row.sex_code or 'Sin dato',
                age=_calculate_age(row.birthdate),
                risk_level=row.risk_code,
                risk_level_label=row.risk_label,
                admission_date=_datetime_to_iso(row.created_at),
                updated_at=_datetime_to_iso(row.updated_at),
                alerts=alerts_by_patient.get(row.id, []),
            )
            summaries.append(summary.to_dict())

        return summaries
