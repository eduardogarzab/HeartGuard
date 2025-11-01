"""Database models for the patient service."""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID
import uuid

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


class CaregiverPatient(db.Model):
    """Represents the caregiver-patient relationship."""
    __tablename__ = 'caregiver_patient'
    __table_args__ = {'extend_existing': True}

    patient_id = db.Column(UUID(as_uuid=True), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), primary_key=True)
    rel_type_id = db.Column(UUID(as_uuid=True))
    is_primary = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    ended_at = db.Column(db.TIMESTAMP)
    note = db.Column(db.Text)


class UserOrgMembership(db.Model):
    """Represents user membership in an organization."""
    __tablename__ = 'user_org_membership'
    __table_args__ = {'extend_existing': True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(UUID(as_uuid=True), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), nullable=False)
    org_role_id = db.Column(UUID(as_uuid=True))
    joined_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    left_at = db.Column(db.TIMESTAMP)


class UserRole(db.Model):
    """Represents user global roles."""
    __tablename__ = 'user_role'
    __table_args__ = {'extend_existing': True}

    user_id = db.Column(UUID(as_uuid=True), primary_key=True)
    role_id = db.Column(UUID(as_uuid=True), primary_key=True)


class Role(db.Model):
    """Represents global roles."""
    __tablename__ = 'roles'
    __table_args__ = {'extend_existing': True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)


class OrgRole(db.Model):
    """Represents organization-level roles."""
    __tablename__ = 'org_roles'
    __table_args__ = {'extend_existing': True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(50), unique=True, nullable=False)
    label = db.Column(db.String(120))
