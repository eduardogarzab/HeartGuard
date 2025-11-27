"""Proxy para el servicio de predicciones de IA."""
from __future__ import annotations

import logging

from flask import Blueprint, request

from ..services import ai_client

logger = logging.getLogger(__name__)

bp = Blueprint("ai_proxy", __name__, url_prefix="/ai")


@bp.route("/health", methods=["GET"])
def health():
    """Health check del servicio de IA."""
    return ai_client.forward_request(
        method="GET",
        path="/health",
        headers=dict(request.headers),
    )


@bp.route("/predict", methods=["POST"])
def predict():
    """Endpoint de predicción individual."""
    return ai_client.forward_request(
        method="POST",
        path="/predict",
        headers=dict(request.headers),
        data=request.get_data(),
    )


@bp.route("/batch-predict", methods=["POST"])
def batch_predict():
    """Endpoint de predicción en lote."""
    return ai_client.forward_request(
        method="POST",
        path="/batch-predict",
        headers=dict(request.headers),
        data=request.get_data(),
    )


@bp.route("/model/info", methods=["GET"])
def model_info():
    """Información del modelo."""
    return ai_client.forward_request(
        method="GET",
        path="/model/info",
        headers=dict(request.headers),
    )


@bp.route("/model/reload", methods=["POST"])
def model_reload():
    """Recargar el modelo."""
    return ai_client.forward_request(
        method="POST",
        path="/model/reload",
        headers=dict(request.headers),
    )
