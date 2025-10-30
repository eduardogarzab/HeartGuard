from __future__ import annotations

import datetime as dt

from common.database import db


class DeviceType(db.Model):
    __tablename__ = "device_types"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    manufacturer = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    devices = db.relationship("Device", back_populates="device_type", cascade="all, delete-orphan")


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.String, primary_key=True)
    device_type_id = db.Column(db.String, db.ForeignKey("device_types.id"), nullable=False)
    serial_number = db.Column(db.String, unique=True, nullable=False)
    assigned_patient_id = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False, default="inventory")
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    device_type = db.relationship("DeviceType", back_populates="devices")
    streams = db.relationship("SignalStream", back_populates="device", cascade="all, delete-orphan")


class SignalStream(db.Model):
    __tablename__ = "signal_streams"

    id = db.Column(db.String, primary_key=True)
    device_id = db.Column(db.String, db.ForeignKey("devices.id"), nullable=False)
    signal_type = db.Column(db.String, nullable=False)
    sampling_rate = db.Column(db.Integer, nullable=False, default=1)

    device = db.relationship("Device", back_populates="streams")
    bindings = db.relationship("TimeseriesBinding", back_populates="stream", cascade="all, delete-orphan")


class TimeseriesBinding(db.Model):
    __tablename__ = "timeseries_bindings"

    id = db.Column(db.String, primary_key=True)
    stream_id = db.Column(db.String, db.ForeignKey("signal_streams.id"), nullable=False)
    influx_measurement = db.Column(db.String, nullable=False)
    bucket = db.Column(db.String, nullable=False)
    org = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    stream = db.relationship("SignalStream", back_populates="bindings")
