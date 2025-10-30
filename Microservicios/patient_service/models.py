from __future__ import annotations

import datetime as dt

from common.database import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.String, primary_key=True)
    mrn = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    birth_date = db.Column(db.String, nullable=True)
    sex = db.Column(db.String, nullable=True)
    organization_id = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    care_teams = db.relationship("CareTeam", back_populates="patient", cascade="all, delete-orphan")
    caregiver_links = db.relationship("CaregiverLink", back_populates="patient", cascade="all, delete-orphan")


class CareTeam(db.Model):
    __tablename__ = "care_teams"

    id = db.Column(db.String, primary_key=True)
    patient_id = db.Column(db.String, db.ForeignKey("patients.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    patient = db.relationship("Patient", back_populates="care_teams")
    members = db.relationship("CareTeamMember", back_populates="team", cascade="all, delete-orphan")


class CareTeamMember(db.Model):
    __tablename__ = "care_team_members"

    id = db.Column(db.String, primary_key=True)
    team_id = db.Column(db.String, db.ForeignKey("care_teams.id"), nullable=False)
    user_id = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)

    team = db.relationship("CareTeam", back_populates="members")


class CaregiverLink(db.Model):
    __tablename__ = "caregiver_links"

    id = db.Column(db.String, primary_key=True)
    caregiver_id = db.Column(db.String, nullable=False)
    patient_id = db.Column(db.String, db.ForeignKey("patients.id"), nullable=False)
    relationship = db.Column(db.String, nullable=True)

    patient = db.relationship("Patient", back_populates="caregiver_links")
