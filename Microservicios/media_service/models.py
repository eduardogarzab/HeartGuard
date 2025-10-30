from __future__ import annotations

import datetime as dt

from common.database import db


class MediaItem(db.Model):
    __tablename__ = "media_items"

    id = db.Column(db.String, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    mime_type = db.Column(db.String, nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    owner_id = db.Column(db.String, nullable=True)
    bucket = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

