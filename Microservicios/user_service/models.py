"""Database models for the user service."""
from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import UUID

from common.database import db


class UserStatus(db.Model):
    """Catalog of lifecycle statuses for a user."""

    __tablename__ = "user_statuses"
    __table_args__ = {"extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class OrgRole(db.Model):
    """Roles that a user can hold within an organization."""

    __tablename__ = "org_roles"
    __table_args__ = {"extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class User(db.Model):
    """Represents an authenticated platform user."""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    user_status_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user_statuses.id"), nullable=False)
    two_factor_enabled = db.Column(db.Boolean, nullable=False, default=False)
    profile_photo_url = db.Column(db.Text)
    language = db.Column(db.String(16))
    timezone = db.Column(db.String(64))
    theme = db.Column(db.String(32))
    notifications_email = db.Column(db.Boolean, nullable=False, default=True)
    notifications_sms = db.Column(db.Boolean, nullable=False, default=False)
    notifications_push = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    status = db.relationship("UserStatus", lazy="joined")


class UserOrgMembership(db.Model):
    """Association between users and organizations with their role."""

    __tablename__ = "user_org_membership"
    __table_args__ = {"extend_existing": True}

    org_id = db.Column(UUID(as_uuid=True), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    org_role_id = db.Column(UUID(as_uuid=True), db.ForeignKey("org_roles.id"), nullable=False)
    joined_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

    user = db.relationship("User", lazy="joined", primaryjoin="UserOrgMembership.user_id == User.id")
    role = db.relationship("OrgRole", lazy="joined")
