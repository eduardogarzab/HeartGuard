"""Database models for the alert service."""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.database import db


class Alert(db.Model):
    """Represents an alert, mapping to the 'alerts' table."""
    __tablename__ = 'alerts'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(UUID(as_uuid=True), db.ForeignKey('patients.id'), nullable=False)
    type_id = db.Column(UUID(as_uuid=True), db.ForeignKey('alert_types.id'), nullable=False)
    created_by_model_id = db.Column(UUID(as_uuid=True), db.ForeignKey('models.id'))
    source_inference_id = db.Column(UUID(as_uuid=True), db.ForeignKey('inferences.id'))
    alert_level_id = db.Column(UUID(as_uuid=True), db.ForeignKey('alert_levels.id'), nullable=False)
    status_id = db.Column(UUID(as_uuid=True), db.ForeignKey('alert_status.id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    description = db.Column(db.Text)
    # location = db.Column(Geometry(geometry_type='POINT', srid=4326)) # PostGIS support needed
    duplicate_of_alert_id = db.Column(UUID(as_uuid=True), db.ForeignKey('alerts.id'))

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
