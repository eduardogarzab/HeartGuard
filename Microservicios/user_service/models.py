from __future__ import annotations

import datetime as dt

from common.database import db


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    language = db.Column(db.String, nullable=True)
    timezone = db.Column(db.String, nullable=True)
    organization_id = db.Column(db.String, nullable=True)
    preferences = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
