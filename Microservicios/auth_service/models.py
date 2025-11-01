"""Database models for the authentication service."""
from __future__ import annotations

import uuid

import bcrypt
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError

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

    def get_roles(self) -> list[str]:
        """Fetch user roles from user_role table."""
        try:
            # Query to join user_role and roles tables
            result = db.session.execute(
                db.text("""
                    SELECT r.name 
                    FROM user_role ur
                    JOIN roles r ON ur.role_id = r.id
                    WHERE ur.user_id = :user_id
                """),
                {'user_id': str(self.id)}
            )
            roles = [row[0] for row in result]
            # Default to 'user' if no roles found
            return roles if roles else ['user']
        except SQLAlchemyError:
            db.session.rollback()
            return ['user']

    def get_organizations(self) -> list[dict]:
        """Fetch user organizations and their roles."""
        try:
            result = db.session.execute(
                db.text("""
                    SELECT 
                        o.id,
                        o.code,
                        o.name,
                        orgr.code as role_code,
                        orgr.label as role_name
                    FROM user_org_membership uom
                    JOIN organizations o ON uom.org_id = o.id
                    JOIN org_roles orgr ON uom.org_role_id = orgr.id
                    WHERE uom.user_id = :user_id
                    ORDER BY o.name
                """),
                {'user_id': str(self.id)}
            )
            orgs = []
            for row in result:
                orgs.append({
                    'id': str(row[0]),
                    'code': row[1],
                    'name': row[2],
                    'role_code': row[3],
                    'role_name': row[4]
                })
            return orgs
        except SQLAlchemyError:
            db.session.rollback()
            return []

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
