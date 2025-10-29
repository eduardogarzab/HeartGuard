"""Blueprint with CRUD operations for biometric signals."""

import logging
from decimal import Decimal
from typing import Any, Dict

from flask import Blueprint, g, request

from repository.signals import (
    create_signal,
    delete_signal,
    get_signal_by_id,
    list_signals_for_patient,
)
from responses import err, ok
from utils.auth import token_required
from utils.payloads import (
    PayloadError,
    handle_payload_error,
    parse_request_payload,
    validate_signal_payload,
)

logger = logging.getLogger(__name__)

bp = Blueprint("signals", __name__, url_prefix="/v1/signals")


def _enrich_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    if not signal:
        return signal
    value = signal.get("value")
    if isinstance(value, Decimal):
        value = float(value)

    def _format_dt(dt):
        return dt.isoformat() if hasattr(dt, "isoformat") and dt else dt

    return {
        **signal,
        "id": str(signal.get("id")),
        "patient_id": str(signal.get("patient_id")),
        "org_id": str(signal.get("org_id")),
        "value": value,
        "created_by": str(signal.get("created_by")) if signal.get("created_by") else None,
        "recorded_at": _format_dt(signal.get("recorded_at")),
        "created_at": _format_dt(signal.get("created_at")),
    }


@bp.post("")
@token_required
def register_signal():
    try:
        payload = parse_request_payload()
        data = validate_signal_payload(payload)
    except PayloadError as exc:
        return handle_payload_error(exc)

    org_id = g.org_id
    user_id = g.user_id

    record = create_signal(
        patient_id=data["patient_id"],
        org_id=org_id,
        signal_type=data["signal_type"],
        value=data["value"],
        unit=data["unit"],
        recorded_at=data["recorded_at"],
        created_by=user_id,
    )

    logger.info(
        "Señal registrada",
        extra={"patient_id": data["patient_id"], "org_id": org_id, "user_id": user_id},
    )

    return ok({"signal": _enrich_signal(record)}, status=201)


@bp.get("")
@token_required
def list_signals():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return err("Parámetro 'patient_id' es requerido", code="patient_id_missing", status=400)

    try:
        limit = int(request.args.get("limit", "100"))
        offset = int(request.args.get("offset", "0"))
    except ValueError:
        return err("Parámetros de paginación inválidos", code="pagination_invalid", status=400)
    if limit <= 0 or offset < 0:
        return err("Parámetros de paginación fuera de rango", code="pagination_range", status=400)

    records = list_signals_for_patient(
        patient_id=str(patient_id),
        org_id=g.org_id,
        limit=limit,
        offset=offset,
    )

    logger.info(
        "Consulta de señales",
        extra={"patient_id": patient_id, "org_id": g.org_id, "user_id": g.user_id},
    )

    return ok({"signals": [_enrich_signal(record) for record in records], "count": len(records)})


@bp.get("/<signal_id>")
@token_required
def retrieve_signal(signal_id):
    record = get_signal_by_id(signal_id=str(signal_id), org_id=g.org_id)
    if not record:
        return err("Señal no encontrada", code="signal_not_found", status=404)

    logger.info(
        "Detalle de señal consultado",
        extra={"signal_id": signal_id, "org_id": g.org_id, "user_id": g.user_id},
    )

    return ok({"signal": _enrich_signal(record)})


@bp.delete("/<signal_id>")
@token_required
def remove_signal(signal_id):
    record = get_signal_by_id(signal_id=str(signal_id), org_id=g.org_id)
    if not record:
        return err("Señal no encontrada", code="signal_not_found", status=404)

    deleted = delete_signal(signal_id=str(signal_id), org_id=g.org_id)
    if not deleted:
        return err("No se pudo eliminar la señal", code="delete_failed", status=409)

    logger.info(
        "Señal eliminada",
        extra={"signal_id": signal_id, "org_id": g.org_id, "user_id": g.user_id},
    )

    return ok({"signal": _enrich_signal(record)})
