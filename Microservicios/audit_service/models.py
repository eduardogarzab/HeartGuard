from __future__ import annotations

import datetime as dt

from common.database import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.String, primary_key=True)
    actor_id = db.Column(db.String, nullable=False)
    action = db.Column(db.String, nullable=False)
    resource = db.Column(db.String, nullable=True)
    metadata = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
