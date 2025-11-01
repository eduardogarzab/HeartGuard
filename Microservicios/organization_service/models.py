"""Database models for the organization service."""
from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy.dialects.postgresql import UUID

from common.database import db


def _utcnow() -> datetime:
    """Return a timezone-aware UTC datetime.

    SQLite (used in tests) stores naive datetimes, so we fall back to naive when
    SQLAlchemy gives us one.
    """

    return datetime.now(timezone.utc)


class Organization(db.Model):
    """Represents an organization, mapping to the 'organizations' table."""

    __tablename__ = 'organizations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(60), unique=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    invitations = db.relationship('OrgInvitation', back_populates='organization', cascade='all, delete-orphan')

    def to_dict(self) -> dict[str, str]:
        """Serializes the organization object to a dictionary."""

        created = self.created_at
        if isinstance(created, datetime):
            created_value = created if created.tzinfo else created.replace(tzinfo=timezone.utc)
        else:  # pragma: no cover - defensive, SQLAlchemy always returns datetime
            created_value = _utcnow()

        return {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'created_at': created_value.isoformat(),
        }


class User(db.Model):
    """Minimal user model to satisfy foreign key constraints for invitations."""

    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class OrgRole(db.Model):
    """Organization-level role."""

    __tablename__ = 'org_roles'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)

    invitations = db.relationship('OrgInvitation', back_populates='role')

    def to_dict(self) -> dict[str, str]:
        return {
            'id': str(self.id),
            'code': self.code,
            'label': self.label,
        }


class UserOrgMembership(db.Model):
    """Association between users and organizations used for authorization."""

    __tablename__ = 'user_org_membership'

    org_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), primary_key=True)
    org_role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('org_roles.id'), nullable=False)
    joined_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    role = db.relationship('OrgRole', lazy='joined')


class OrgInvitationQuery:
    """Typed helper query for invitations."""

    @staticmethod
    def for_org(org_id: uuid.UUID | str | None):
        query = OrgInvitation.query
        if org_id:
            org_uuid = uuid.UUID(str(org_id))
            query = query.filter(OrgInvitation.org_id == org_uuid)
        return query.order_by(OrgInvitation.created_at.desc())


class OrgInvitation(db.Model):
    """Invitation for a user to join an organization."""

    __tablename__ = 'org_invitations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    email = db.Column(db.String(150))
    org_role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('org_roles.id', ondelete='RESTRICT'), nullable=False)
    token = db.Column(db.String(120), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    expires_at = db.Column(db.TIMESTAMP, nullable=False)
    used_at = db.Column(db.TIMESTAMP)
    revoked_at = db.Column(db.TIMESTAMP)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    organization = db.relationship('Organization', back_populates='invitations')
    role = db.relationship('OrgRole', back_populates='invitations')

    @property
    def status(self) -> str:
        """Derive the invitation status mirroring backend behaviour."""

        if self.revoked_at:
            return 'revoked'
        if self.used_at:
            return 'used'

        expires = self._coerce_datetime(self.expires_at)
        if expires <= _utcnow():
            return 'expired'
        return 'pending'

    @staticmethod
    def _coerce_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def to_dict(self) -> dict[str, object]:
        """Serialize invitation according to frontend expectations."""

        created = self._coerce_datetime(self.created_at) or _utcnow()
        expires = self._coerce_datetime(self.expires_at)
        used = self._coerce_datetime(self.used_at)
        revoked = self._coerce_datetime(self.revoked_at)

        return {
            'id': str(self.id),
            'org_id': str(self.org_id),
            'email': self.email,
            'role': self.role.code if self.role else None,
            'status': self.status,
            'token': self.token,
            'created_at': created.isoformat(),
            'expires_at': expires.isoformat() if expires else None,
            'used_at': used.isoformat() if used else None,
            'revoked_at': revoked.isoformat() if revoked else None,
            'org_role_id': str(self.org_role_id),
            'created_by': str(self.created_by) if self.created_by else None,
        }

