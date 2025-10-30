"""Database models for the patient service."""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.database import db


class Patient(db.Model):
    """Represents a patient, mapping to the 'patients' table."""
    __tablename__ = 'patients'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'))
    person_name = db.Column(db.String(120), nullable=False)
    birthdate = db.Column(db.Date)
    sex_id = db.Column(UUID(as_uuid=True), db.ForeignKey('sexes.id'))
    risk_level_id = db.Column(UUID(as_uuid=True), db.ForeignKey('risk_levels.id'))
    profile_photo_url = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    def to_dict(self):
        """Serializes the patient object to a dictionary."""
        return {
            'id': str(self.id),
            'org_id': str(self.org_id) if self.org_id else None,
            'person_name': self.person_name,
            'birthdate': self.birthdate.isoformat() if self.birthdate else None,
            'sex_id': str(self.sex_id) if self.sex_id else None,
            'risk_level_id': str(self.risk_level_id) if self.risk_level_id else None,
            'profile_photo_url': self.profile_photo_url,
            'created_at': self.created_at.isoformat(),
        }
