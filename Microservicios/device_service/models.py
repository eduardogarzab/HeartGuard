"""Database models for the device service."""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.database import db


class Device(db.Model):
    """Represents a device, mapping to the 'devices' table."""
    __tablename__ = 'devices'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'))
    serial = db.Column(db.String(80), unique=True, nullable=False)
    brand = db.Column(db.String(80))
    model = db.Column(db.String(80))
    device_type_id = db.Column(UUID(as_uuid=True), db.ForeignKey('device_types.id'), nullable=False)
    owner_patient_id = db.Column(UUID(as_uuid=True), db.ForeignKey('patients.id'))
    registered_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        """Serializes the device object to a dictionary."""
        return {
            'id': str(self.id),
            'org_id': str(self.org_id) if self.org_id else None,
            'serial': self.serial,
            'brand': self.brand,
            'model': self.model,
            'device_type_id': str(self.device_type_id),
            'owner_patient_id': str(self.owner_patient_id) if self.owner_patient_id else None,
            'registered_at': self.registered_at.isoformat(),
            'active': self.active,
        }
