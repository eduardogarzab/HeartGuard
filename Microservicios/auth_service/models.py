"""Database models for the authentication service."""
from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.database import db


class User(db.Model):
    """Represents a user in the system, mapping to the 'users' table."""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    # No ForeignKey for microservices - we just store the UUID reference
    user_status_id = db.Column(UUID(as_uuid=True), nullable=False)
    two_factor_enabled = db.Column(db.Boolean, nullable=False, default=False)
    profile_photo_url = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    def set_password(self, password: str):
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Serializes the user object to a dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'user_status_id': str(self.user_status_id),
            'profile_photo_url': self.profile_photo_url,
            'created_at': self.created_at.isoformat(),
        }
