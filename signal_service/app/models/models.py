# signal_service/app/models/models.py
import datetime
from sqlalchemy import (Column, String, Integer, DateTime, ForeignKey, Text,
                          create_engine)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DeviceKey(Base):
    __tablename__ = 'device_keys'

    id = Column(Integer, primary_key=True)
    device_uuid = Column(String(36), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, nullable=False) # Assuming patient_id is an integer
    hashed_api_key = Column(String(128), nullable=False)
    status = Column(String(50), nullable=False, default='active') # e.g., 'active', 'revoked'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship to SignalStream
    signal_streams = relationship("SignalStream", back_populates="device")

class SignalStream(Base):
    __tablename__ = 'signal_streams'

    id = Column(Integer, primary_key=True)
    org_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    device_key_id = Column(Integer, ForeignKey('device_keys.id'), nullable=False)
    stream_type = Column(String(50), nullable=False) # e.g., 'heart_rate', 'blood_pressure'
    status = Column(String(50), nullable=False, default='active') # e.g., 'active', 'inactive'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    device = relationship("DeviceKey", back_populates="signal_streams")
    timeseries_data = relationship("TimeseriesData", back_populates="stream")

class TimeseriesData(Base):
    __tablename__ = 'timeseries_data'

    # TimescaleDB requires a primary key that includes the time column.
    timestamp = Column(DateTime(timezone=True), primary_key=True)
    stream_id = Column(Integer, ForeignKey('signal_streams.id'), primary_key=True)
    value = Column(String, nullable=False) # Using String to be flexible (e.g., "80", "120/80")

    # Relationship to SignalStream
    stream = relationship("SignalStream", back_populates="timeseries_data")

# --- TimescaleDB Hypertable DDL ---
# The following SQL commands should be executed on the database after the tables are created
# to enable TimescaleDB's features for the timeseries_data table.

# 1. Create the extension (if not already created)
# CREATE EXTENSION IF NOT EXISTS timescaledb;

# 2. Convert the table to a hypertable, partitioned by the 'timestamp' column.
# SELECT create_hypertable('timeseries_data', 'timestamp');

# 3. (Optional but recommended) Add compression to save space.
# ALTER TABLE timeseries_data SET (
#   timescaledb.compress,
#   timescaledb.compress_segmentby = 'stream_id'
# );

# 4. (Optional but recommended) Set up a data retention policy to drop old data.
# For example, to drop data older than 6 months:
# SELECT add_retention_policy('timeseries_data', INTERVAL '6 months');
