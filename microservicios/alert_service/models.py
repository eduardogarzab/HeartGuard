import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from .db import db


class JSONBType(TypeDecorator):
    """A database-agnostic JSONB type that uses JSONB on PostgreSQL and JSON on others."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    @declared_attr
    def __tablename__(cls) -> str:  # type: ignore[misc]
        return cls.__name__.lower()


class AlertType(BaseModel):
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)

    alerts = relationship("Alert", back_populates="alert_type")


class AlertLevel(BaseModel):
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    alerts = relationship("Alert", back_populates="alert_level")


class AlertStatus(BaseModel):
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    alerts = relationship("Alert", back_populates="alert_status")


class DeliveryStatus(BaseModel):
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    deliveries = relationship("AlertDelivery", back_populates="delivery_status")


class Alert(BaseModel):
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    alert_type_id = Column(
        UUID(as_uuid=True), ForeignKey("alerttype.id", ondelete="RESTRICT"), nullable=False
    )
    alert_level_id = Column(
        UUID(as_uuid=True), ForeignKey("alertlevel.id", ondelete="RESTRICT"), nullable=False
    )
    alert_status_id = Column(
        UUID(as_uuid=True), ForeignKey("alertstatus.id", ondelete="RESTRICT"), nullable=False
    )
    message = Column(Text, nullable=False)
    payload = Column(JSONBType, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    alert_type = relationship("AlertType", back_populates="alerts")
    alert_level = relationship("AlertLevel", back_populates="alerts")
    alert_status = relationship("AlertStatus", back_populates="alerts")
    deliveries = relationship("AlertDelivery", back_populates="alert", cascade="all,delete")
    ground_truth_labels = relationship(
        "GroundTruthLabel", back_populates="alert", cascade="all,delete"
    )


class AlertDelivery(BaseModel):
    alert_id = Column(
        UUID(as_uuid=True), ForeignKey("alert.id", ondelete="CASCADE"), nullable=False
    )
    delivery_status_id = Column(
        UUID(as_uuid=True),
        ForeignKey("deliverystatus.id", ondelete="RESTRICT"),
        nullable=False,
    )
    channel = Column(String(50), nullable=False)
    recipient = Column(String(255), nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    payload = Column(JSONBType, nullable=True)

    alert = relationship("Alert", back_populates="deliveries")
    delivery_status = relationship("DeliveryStatus", back_populates="deliveries")


class GroundTruthLabel(BaseModel):
    alert_id = Column(
        UUID(as_uuid=True), ForeignKey("alert.id", ondelete="CASCADE"), nullable=False
    )
    label = Column(String(120), nullable=False)
    notes = Column(Text, nullable=True)

    alert = relationship("Alert", back_populates="ground_truth_labels")


__all__ = [
    "Alert",
    "AlertType",
    "AlertLevel",
    "AlertStatus",
    "AlertDelivery",
    "DeliveryStatus",
    "GroundTruthLabel",
]
