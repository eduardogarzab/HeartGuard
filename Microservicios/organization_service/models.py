"""Database models for the organization service."""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.database import db


class Organization(db.Model):
    """Represents an organization, mapping to the 'organizations' table."""
    __tablename__ = 'organizations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(60), unique=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    def to_dict(self):
        """Serializes the organization object to a dictionary."""
        return {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
        }
