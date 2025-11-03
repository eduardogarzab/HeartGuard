"""Organization related models."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ..extensions import db


class Organization(db.Model):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    memberships = db.relationship("UserOrgMembership", back_populates="organization", cascade="all, delete-orphan")
    invitations = db.relationship("OrgInvitation", back_populates="organization", cascade="all, delete-orphan")


class UserOrgMembership(db.Model):
    __tablename__ = "user_org_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "org_id", name="uq_user_org"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    role = Column(String(50), nullable=False, default="member")

    organization = db.relationship("Organization", back_populates="memberships")


class OrgInvitation(db.Model):
    __tablename__ = "org_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(512), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    organization = db.relationship("Organization", back_populates="invitations")


__all__ = ["Organization", "UserOrgMembership", "OrgInvitation"]
