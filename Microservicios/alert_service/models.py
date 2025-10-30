"""Database models for the alert service."""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.database import db


class Alert(db.Model):
    """Represents an alert, mapping to the 'alerts' table."""
    __tablename__ = 'alerts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # No ForeignKey for microservices - we just store the UUID reference
    patient_id = db.Column(UUID(as_uuid=True), nullable=False)
    type_id = db.Column(UUID(as_uuid=True), nullable=False)
    created_by_model_id = db.Column(UUID(as_uuid=True))
    source_inference_id = db.Column(UUID(as_uuid=True))
    alert_level_id = db.Column(UUID(as_uuid=True), nullable=False)
    status_id = db.Column(UUID(as_uuid=True), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    description = db.Column(db.Text)
    # location = db.Column(Geometry(geometry_type='POINT', srid=4326)) # PostGIS support needed
    duplicate_of_alert_id = db.Column(UUID(as_uuid=True))

    def to_dict(self):
        """Serializes the alert object to a dictionary."""
        return {
            'id': str(self.id),
            'patient_id': str(self.patient_id),
            'type_id': str(self.type_id),
            'alert_level_id': str(self.alert_level_id),
            'status_id': str(self.status_id),
            'created_at': self.created_at.isoformat(),
            'description': self.description,
        }
