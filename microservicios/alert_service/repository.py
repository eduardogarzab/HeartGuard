import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import NoResultFound

from .db import db
from .models import (
    Alert,
    AlertDelivery,
    AlertLevel,
    AlertStatus,
    AlertType,
    DeliveryStatus,
    GroundTruthLabel,
)


def _as_uuid(value: Any) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


class AlertRepository:
    def __init__(self, session=None) -> None:
        self.session = session or db.session

    def _filter_by_org(self, model, org_id: Any):
        normalized_org_id = _as_uuid(org_id)
        return self.session.query(model).filter(model.org_id == normalized_org_id)

    def _get_alert(self, alert_id: str, org_id: str) -> Alert:
        alert_uuid = _as_uuid(alert_id)
        query = self._filter_by_org(Alert, org_id).filter(Alert.id == alert_uuid)
        alert = query.one_or_none()
        if not alert:
            raise NoResultFound("Alert not found")
        return alert

    def get_alerts(self, org_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Alert]:
        query = self._filter_by_org(Alert, org_id)
        filters = filters or {}

        if "patient_id" in filters:
            query = query.filter(Alert.patient_id == _as_uuid(filters["patient_id"]))
        if "status_id" in filters:
            query = query.filter(Alert.alert_status_id == _as_uuid(filters["status_id"]))
        if "type_id" in filters:
            query = query.filter(Alert.alert_type_id == _as_uuid(filters["type_id"]))
        if "level_id" in filters:
            query = query.filter(Alert.alert_level_id == _as_uuid(filters["level_id"]))

        return query.order_by(Alert.created_at.desc()).all()

    def get_active_alerts_by_patient(self, org_id: str, patient_id: str) -> List[Alert]:
        return (
            self._filter_by_org(Alert, org_id)
            .filter(Alert.patient_id == _as_uuid(patient_id), Alert.is_active.is_(True))
            .order_by(Alert.created_at.desc())
            .all()
        )

    def create_alert(self, org_id: str, data: Dict[str, Any]) -> Alert:
        alert = Alert(org_id=_as_uuid(org_id), **data)
        self.session.add(alert)
        self.session.commit()
        return alert

    def update_alert(self, alert_id: str, org_id: str, data: Dict[str, Any]) -> Alert:
        alert = self._get_alert(alert_id, org_id)
        for key, value in data.items():
            setattr(alert, key, value)
        self.session.commit()
        return alert

    def delete_alert(self, alert_id: str, org_id: str) -> None:
        alert = self._get_alert(alert_id, org_id)
        self.session.delete(alert)
        self.session.commit()

    def create_delivery(self, alert_id: str, org_id: str, data: Dict[str, Any]) -> AlertDelivery:
        self._get_alert(alert_id, org_id)
        delivery = AlertDelivery(org_id=_as_uuid(org_id), alert_id=_as_uuid(alert_id), **data)
        self.session.add(delivery)
        self.session.commit()
        return delivery

    def create_ground_truth_label(
        self, alert_id: str, org_id: str, data: Dict[str, Any]
    ) -> GroundTruthLabel:
        self._get_alert(alert_id, org_id)
        label = GroundTruthLabel(org_id=_as_uuid(org_id), alert_id=_as_uuid(alert_id), **data)
        self.session.add(label)
        self.session.commit()
        return label

    def list_alert_types(self, org_id: str) -> List[AlertType]:
        return self._filter_by_org(AlertType, org_id).all()

    def list_alert_levels(self, org_id: str) -> List[AlertLevel]:
        return self._filter_by_org(AlertLevel, org_id).all()

    def list_alert_statuses(self, org_id: str) -> List[AlertStatus]:
        return self._filter_by_org(AlertStatus, org_id).all()

    def list_delivery_statuses(self, org_id: str) -> List[DeliveryStatus]:
        return self._filter_by_org(DeliveryStatus, org_id).all()


def serialize_alert(alert: Alert) -> Dict[str, Any]:
    return {
        "id": str(alert.id),
        "org_id": str(alert.org_id),
        "patient_id": str(alert.patient_id),
        "alert_type_id": str(alert.alert_type_id),
        "alert_level_id": str(alert.alert_level_id),
        "alert_status_id": str(alert.alert_status_id),
        "message": alert.message,
        "payload": alert.payload or {},
        "is_active": alert.is_active,
        "created_at": alert.created_at.isoformat(),
        "updated_at": alert.updated_at.isoformat(),
    }


def serialize_delivery(delivery: AlertDelivery) -> Dict[str, Any]:
    return {
        "id": str(delivery.id),
        "alert_id": str(delivery.alert_id),
        "org_id": str(delivery.org_id),
        "delivery_status_id": str(delivery.delivery_status_id),
        "channel": delivery.channel,
        "recipient": delivery.recipient,
        "delivered_at": delivery.delivered_at.isoformat() if delivery.delivered_at else None,
        "payload": delivery.payload or {},
        "created_at": delivery.created_at.isoformat(),
    }


def serialize_label(label: GroundTruthLabel) -> Dict[str, Any]:
    return {
        "id": str(label.id),
        "alert_id": str(label.alert_id),
        "org_id": str(label.org_id),
        "label": label.label,
        "notes": label.notes,
        "created_at": label.created_at.isoformat(),
    }


__all__ = [
    "AlertRepository",
    "serialize_alert",
    "serialize_delivery",
    "serialize_label",
]
