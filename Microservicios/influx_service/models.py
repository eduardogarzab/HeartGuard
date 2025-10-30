from __future__ import annotations

import datetime as dt

from common.database import db


class InfluxBucket(db.Model):
    __tablename__ = "influx_buckets"

    name = db.Column(db.String, primary_key=True)
    retention_days = db.Column(db.Integer, nullable=False, default=30)
    org = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)


class TimeseriesPoint(db.Model):
    __tablename__ = "timeseries_points"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bucket = db.Column(db.String, db.ForeignKey("influx_buckets.name"), nullable=False)
    measurement = db.Column(db.String, nullable=False)
    tags = db.Column(db.JSON, nullable=False, default=dict)
    fields = db.Column(db.JSON, nullable=False, default=dict)
    received_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    bucket_rel = db.relationship("InfluxBucket")
