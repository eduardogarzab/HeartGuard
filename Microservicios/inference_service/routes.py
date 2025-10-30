"""Inference service orchestrating ML model metadata and inference records."""
from __future__ import annotations

import datetime as dt
import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

from .models import InferenceEventType, InferenceModel, RecordedInference

bp = Blueprint("inference", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "inference", "status": "healthy", "models": InferenceModel.query.count()})


@bp.route("/models", methods=["GET"])
@require_auth(optional=True)
def list_models() -> "Response":
    models = [
        _serialize_model(model)
        for model in InferenceModel.query.order_by(InferenceModel.created_at.desc()).all()
    ]
    return render_response({"models": models}, meta={"total": len(models)})


@bp.route("/models", methods=["POST"])
@require_auth(required_roles=["admin"])
def register_model() -> "Response":
    payload, _ = parse_request_data(request)
    model_id = payload.get("id")
    if not model_id:
        raise APIError("id is required", status_code=400, error_id="HG-INFERENCE-MODEL")
    model = InferenceModel(
        id=model_id,
        name=payload.get("name", model_id),
        version=payload.get("version", "1.0.0"),
        status=payload.get("status", "active"),
        created_at=dt.datetime.utcnow(),
    )
    db.session.merge(model)
    db.session.commit()
    return render_response({"model": _serialize_model(model)}, status_code=201)


@bp.route("/events", methods=["GET"])
@require_auth(optional=True)
def list_event_types() -> "Response":
    events = [
        {"id": event.id, "name": event.name, "severity": event.severity}
        for event in InferenceEventType.query.all()
    ]
    return render_response({"event_types": events}, meta={"total": len(events)})


@bp.route("/inferences", methods=["POST"])
@require_auth(optional=True)
def record_inference() -> "Response":
    payload, _ = parse_request_data(request)
    model_id = payload.get("model_id")
    model = InferenceModel.query.get(model_id)
    if not model:
        raise APIError("Unknown model", status_code=404, error_id="HG-INFERENCE-MODEL")
    inference = RecordedInference(
        id=f"inf-{uuid.uuid4()}",
        model=model,
        patient_id=payload.get("patient_id"),
        event_type=payload.get("event_type"),
        score=float(payload.get("score", 0.0)),
        created_at=dt.datetime.utcnow(),
    )
    db.session.add(inference)
    db.session.commit()
    return render_response({"inference": _serialize_inference(inference)}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/inference")
    with app.app_context():
        _seed_defaults()


def _serialize_model(model: InferenceModel) -> dict:
    return {
        "id": model.id,
        "name": model.name,
        "version": model.version,
        "status": model.status,
        "created_at": (model.created_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _serialize_inference(inference: RecordedInference) -> dict:
    return {
        "id": inference.id,
        "model_id": inference.model_id,
        "patient_id": inference.patient_id,
        "event_type": inference.event_type,
        "score": inference.score,
        "created_at": (inference.created_at or dt.datetime.utcnow()).isoformat() + "Z",
    }


def _seed_defaults() -> None:
    if InferenceModel.query.count() == 0:
        model = InferenceModel(
            id="model-ecg-risk",
            name="ECG Risk Classifier",
            version="1.0.0",
            status="active",
        )
        db.session.add(model)
    if InferenceEventType.query.count() == 0:
        db.session.add_all(
            [
                InferenceEventType(id="evt-1", name="tachycardia", severity="high"),
                InferenceEventType(id="evt-2", name="bradycardia", severity="medium"),
            ]
        )
    db.session.commit()
