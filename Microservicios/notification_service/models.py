from __future__ import annotations

import datetime as dt

from common.database import db


class PushDevice(db.Model):
    __tablename__ = "push_devices"

    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    platform = db.Column(db.String, nullable=False)
    token = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)


class AlertDelivery(db.Model):
    __tablename__ = "alert_deliveries"

    id = db.Column(db.String, primary_key=True)
    alert_id = db.Column(db.String, nullable=False)
    device_id = db.Column(db.String, db.ForeignKey("push_devices.id"), nullable=False)
    status = db.Column(db.String, nullable=False, default="sent")
    sent_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    device = db.relationship("PushDevice")
