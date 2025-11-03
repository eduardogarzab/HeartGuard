"""Care team related models."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ..extensions import db


class CareTeam(db.Model):
    __tablename__ = "care_teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = db.relationship("CareTeamMember", back_populates="care_team", cascade="all, delete-orphan")
    patient_assignments = db.relationship("PatientCareTeam", back_populates="care_team", cascade="all, delete-orphan")


class CareTeamMember(db.Model):
    __tablename__ = "care_team_members"
    __table_args__ = (
        UniqueConstraint("care_team_id", "user_id", name="uq_team_user"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    care_team_id = Column(UUID(as_uuid=True), ForeignKey("care_teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(50), nullable=False, default="member")

    care_team = db.relationship("CareTeam", back_populates="members")


class PatientCareTeam(db.Model):
    __tablename__ = "patient_care_teams"
    __table_args__ = (
        UniqueConstraint("care_team_id", "patient_id", name="uq_team_patient"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    care_team_id = Column(UUID(as_uuid=True), ForeignKey("care_teams.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    care_team = db.relationship("CareTeam", back_populates="patient_assignments")


__all__ = ["CareTeam", "CareTeamMember", "PatientCareTeam"]
