"""Database models for the authentication service."""
from __future__ import annotations

import bcrypt
from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.database import db


class Role(db.Model):
    """Global role assigned to a user via ``user_role``."""

    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())


class UserRole(db.Model):
    """Association table between users and global roles."""

    __tablename__ = "user_role"
    __table_args__ = {"extend_existing": True}

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), primary_key=True)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey("roles.id"), primary_key=True)
    assigned_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    role = db.relationship("Role", lazy="joined")


class Organization(db.Model):
    """Top-level tenant entity."""

    __tablename__ = "organizations"
    __table_args__ = {"extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(60), nullable=False, unique=True)
    name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())


class OrgRole(db.Model):
    """Roles specific to an organization."""

    __tablename__ = "org_roles"
    __table_args__ = {"extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(40), nullable=False, unique=True)
    label = db.Column(db.String(80), nullable=False)


class UserOrgMembership(db.Model):
    """Maps users to organizations and their respective org role."""

    __tablename__ = "user_org_membership"
    __table_args__ = {"extend_existing": True}

    org_id = db.Column(UUID(as_uuid=True), db.ForeignKey("organizations.id"), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), primary_key=True)
    org_role_id = db.Column(UUID(as_uuid=True), db.ForeignKey("org_roles.id"), nullable=False)
    joined_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    organization = db.relationship("Organization", lazy="joined")
    org_role = db.relationship("OrgRole", lazy="joined")


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
        """Hashes and sets the user's password using bcrypt."""
        salt = bcrypt.gensalt(rounds=10)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Checks if the provided password matches the stored hash.
        
        Supports both:
        - PostgreSQL crypt() format (starts with $2a$, $2b$, $2y$)
        - Python bcrypt format
        """
        try:
            # password_hash from DB might be str, ensure it's bytes for bcrypt
            hash_bytes = self.password_hash.encode('utf-8') if isinstance(self.password_hash, str) else self.password_hash
            password_bytes = password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False

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
