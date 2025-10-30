from __future__ import annotations

import datetime as dt

from common.database import db


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.String, primary_key=True)
    patient_id = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default="new")
    severity = db.Column(db.String, nullable=False, default="medium")
    event_type = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    assignments = db.relationship("AlertAssignment", back_populates="alert", cascade="all, delete-orphan")
    acknowledgements = db.relationship("AlertAcknowledgement", back_populates="alert", cascade="all, delete-orphan")
    resolutions = db.relationship("AlertResolution", back_populates="alert", cascade="all, delete-orphan")


class AlertAssignment(db.Model):
    __tablename__ = "alert_assignments"

    id = db.Column(db.String, primary_key=True)
    alert_id = db.Column(db.String, db.ForeignKey("alerts.id"), nullable=False)
    assignee_id = db.Column(db.String, nullable=False)
    assigned_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    alert = db.relationship("Alert", back_populates="assignments")


class AlertAcknowledgement(db.Model):
    __tablename__ = "alert_acknowledgements"

    id = db.Column(db.String, primary_key=True)
    alert_id = db.Column(db.String, db.ForeignKey("alerts.id"), nullable=False)
    acknowledged_by = db.Column(db.String, nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    notes = db.Column(db.String, nullable=True)

    alert = db.relationship("Alert", back_populates="acknowledgements")


class AlertResolution(db.Model):
    __tablename__ = "alert_resolutions"

    id = db.Column(db.String, primary_key=True)
    alert_id = db.Column(db.String, db.ForeignKey("alerts.id"), nullable=False)
    resolved_by = db.Column(db.String, nullable=True)
    resolution_reason = db.Column(db.String, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    alert = db.relationship("Alert", back_populates="resolutions")
