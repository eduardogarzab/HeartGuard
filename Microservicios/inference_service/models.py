from __future__ import annotations

import datetime as dt

from common.database import db


class InferenceModel(db.Model):
    __tablename__ = "inference_models"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    version = db.Column(db.String, nullable=False, default="1.0.0")
    status = db.Column(db.String, nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    inferences = db.relationship("RecordedInference", back_populates="model", cascade="all, delete-orphan")


class InferenceEventType(db.Model):
    __tablename__ = "inference_event_types"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    severity = db.Column(db.String, nullable=False)


class RecordedInference(db.Model):
    __tablename__ = "recorded_inferences"

    id = db.Column(db.String, primary_key=True)
    model_id = db.Column(db.String, db.ForeignKey("inference_models.id"), nullable=False)
    patient_id = db.Column(db.String, nullable=True)
    event_type = db.Column(db.String, nullable=True)
    score = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    model = db.relationship("InferenceModel", back_populates="inferences")
