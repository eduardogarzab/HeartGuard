"""Signal routes blueprint."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from flask import Blueprint, current_app, g, request

from repository import signals as signals_repo
from responses import err, ok
from utils.auth import token_required
from utils.payloads import parse_body

bp = Blueprint("signals", __name__, url_prefix="/v1/signals")


def _parse_recorded_at(value: Any) -> datetime:
    if value in (None, ""):
        return datetime.now(tz=timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            cleaned = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
        except ValueError as exc:
            raise ValueError("recorded_at debe estar en formato ISO 8601") from exc
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    raise ValueError("recorded_at inválido")


@bp.post("")
@token_required
def register_signal():
    try:
        payload: Dict[str, Any] = parse_body()
    except ValueError as exc:
        return err(str(exc), code="invalid_payload", status=400)

    required = ["patient_id", "signal_type", "value", "unit"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return err(
            "Campos requeridos faltantes",
            code="missing_fields",
            status=400,
            details={"fields": missing},
        )

    patient_id = str(payload["patient_id"])
    signal_type = str(payload["signal_type"])
    unit = str(payload["unit"])

    try:
        value = float(payload["value"])
    except (TypeError, ValueError):
        return err("value debe ser numérico", code="invalid_value", status=400)

    try:
        recorded_at = _parse_recorded_at(payload.get("recorded_at"))
    except ValueError as exc:
        return err(str(exc), code="invalid_recorded_at", status=400)

    try:
        record = signals_repo.create_signal(
            patient_id=patient_id,
            org_id=g.org_id,
            signal_type=signal_type,
            value=value,
            unit=unit,
            recorded_at=recorded_at,
            created_by=g.user_id,
        )
    except Exception as exc:  # pragma: no cover - defensive
        current_app.logger.exception(
            "Error registrando señal",
            extra={
                "event": "signal_error",
                "user_id": g.user_id,
                "org_id": g.org_id,
                "patient_id": patient_id,
                "signal_type": signal_type,
            },
        )
        return err("No se pudo registrar la señal", code="signal_creation_failed", status=500)

    current_app.logger.info(
        "Signal registrada",
        extra={
            "event": "signal_recorded",
            "user_id": g.user_id,
            "org_id": g.org_id,
            "patient_id": patient_id,
            "signal_type": signal_type,
        },
    )
    return ok(record, status=201)


@bp.get("")
@token_required
def list_patient_signals():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return err("patient_id es requerido", code="missing_patient", status=400)

    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return err("Parámetros de paginación inválidos", code="invalid_pagination", status=400)

    limit = max(min(limit, 500), 1)
    offset = max(offset, 0)

    items = signals_repo.list_signals(
        patient_id=str(patient_id),
        org_id=g.org_id,
        limit=limit,
        offset=offset,
    )
    return ok({"items": items, "pagination": {"limit": limit, "offset": offset, "count": len(items)}})


@bp.get("/<signal_id>")
@token_required
def retrieve_signal(signal_id: str):
    record = signals_repo.get_signal(signal_id, g.org_id)
    if not record:
        return err("Señal no encontrada", code="signal_not_found", status=404)
    return ok(record)


@bp.delete("/<signal_id>")
@token_required
def remove_signal(signal_id: str):
    deleted = signals_repo.delete_signal(signal_id, g.org_id)
    if not deleted:
        return err("Señal no encontrada", code="signal_not_found", status=404)

    current_app.logger.info(
        "Signal eliminada",
        extra={
            "event": "signal_deleted",
            "user_id": g.user_id,
            "org_id": g.org_id,
            "signal_id": signal_id,
        },
    )
    return ok({"deleted": True, "signal_id": str(signal_id)})
