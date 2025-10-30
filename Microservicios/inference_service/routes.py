"""Inference service orchestrating ML model metadata and inference records."""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

from flask import Blueprint, request

from common.auth import require_auth
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("inference", __name__)

MODELS: Dict[str, Dict] = {
    "model-ecg-risk": {
        "id": "model-ecg-risk",
        "name": "ECG Risk Classifier",
        "version": "1.0.0",
        "status": "active",
    }
}

EVENT_TYPES: List[Dict] = [
    {"id": "evt-1", "name": "tachycardia", "severity": "high"},
    {"id": "evt-2", "name": "bradycardia", "severity": "medium"},
]

INFERENCES: List[Dict] = []


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "inference", "status": "healthy", "models": len(MODELS)})


@bp.route("/models", methods=["GET"])
@require_auth(optional=True)
def list_models() -> "Response":
    return render_response({"models": list(MODELS.values())}, meta={"total": len(MODELS)})


@bp.route("/models", methods=["POST"])
@require_auth(required_roles=["admin"])
def register_model() -> "Response":
    payload, _ = parse_request_data(request)
    model_id = payload.get("id")
    if not model_id:
        raise APIError("id is required", status_code=400, error_id="HG-INFERENCE-MODEL")
    MODELS[model_id] = {
        "id": model_id,
        "name": payload.get("name", model_id),
        "version": payload.get("version", "1.0.0"),
        "status": payload.get("status", "active"),
    }
    return render_response({"model": MODELS[model_id]}, status_code=201)


@bp.route("/events", methods=["GET"])
@require_auth(optional=True)
def list_event_types() -> "Response":
    return render_response({"event_types": EVENT_TYPES}, meta={"total": len(EVENT_TYPES)})


@bp.route("/inferences", methods=["POST"])
@require_auth(optional=True)
def record_inference() -> "Response":
    payload, _ = parse_request_data(request)
    model_id = payload.get("model_id")
    if model_id not in MODELS:
        raise APIError("Unknown model", status_code=404, error_id="HG-INFERENCE-MODEL")
    inference = {
        "id": f"inf-{len(INFERENCES) + 1}",
        "model_id": model_id,
        "patient_id": payload.get("patient_id"),
        "event_type": payload.get("event_type"),
        "score": payload.get("score", 0.0),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    INFERENCES.append(inference)
    return render_response({"inference": inference}, status_code=201)


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/inference")
