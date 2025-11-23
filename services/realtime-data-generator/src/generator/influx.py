"""InfluxDB operations for Generator Service."""
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Dict
import logging

from .data_generator import Patient, StreamConfig

logger = logging.getLogger(__name__)


class InfluxDBService:
    """Service for InfluxDB operations."""
    
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.write_api = None
    
    def connect(self):
        """Connect to InfluxDB."""
        try:
            logger.info(f"Connecting to InfluxDB at {self.url}...")
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            logger.info("InfluxDB connection established")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from InfluxDB."""
        if self.client:
            try:
                self.client.close()
                logger.info("InfluxDB connection closed")
            except Exception as e:
                logger.error(f"Error closing InfluxDB connection: {e}")
    
    def write_vital_signs(self, patient: Patient, reading: Dict):
        """
        DEPRECATED: Legacy method for backward compatibility.
        Use write_vital_signs_from_stream() instead.
        
        Write vital signs to InfluxDB.
        Each measurement is tagged with patient_id and org_id.
        """
        try:
            timestamp = reading['timestamp']
            
            # Create a point for vital signs
            point = Point("vital_signs") \
                .tag("patient_id", patient.id) \
                .tag("patient_name", patient.name) \
                .tag("org_id", patient.org_id or "none") \
                .tag("risk_level", patient.risk_level_code or "unknown") \
                .field("gps_longitude", reading['gps_longitude']) \
                .field("gps_latitude", reading['gps_latitude']) \
                .field("heart_rate", reading['heart_rate']) \
                .field("spo2", reading['spo2']) \
                .field("systolic_bp", reading['systolic_bp']) \
                .field("diastolic_bp", reading['diastolic_bp']) \
                .field("temperature", reading['temperature']) \
                .time(timestamp, WritePrecision.NS)
            
            self.write_api.write(
                bucket=self.bucket,
                org=self.org,
                record=point
            )
            
            logger.debug(
                f"Wrote vital signs for patient {patient.name} (ID: {patient.id}): "
                f"HR={reading['heart_rate']}, SpO2={reading['spo2']}, "
                f"BP={reading['systolic_bp']}/{reading['diastolic_bp']}, "
                f"Temp={reading['temperature']}°C"
            )
        except Exception as e:
            logger.error(f"Error writing to InfluxDB for patient {patient.id}: {e}")
    
    def write_vital_signs_from_stream(self, stream_config: StreamConfig, reading: Dict):
        """
        Write vital signs to InfluxDB using full stream configuration.
        This method uses the PostgreSQL metadata to properly tag the data.
        
        GPS Coordinates Priority:
        1. Use GPS from stream_config.custom_tags (from patient_locations table)
        2. Fall back to generated GPS from reading if not in PostgreSQL
        
        Args:
            stream_config: StreamConfig with device_id, stream_id, and binding info
            reading: Dictionary with vital signs data and timestamp
        """
        try:
            timestamp = reading['timestamp']
            
            # Check if GPS coordinates come from PostgreSQL (patient_locations)
            gps_long = reading['gps_longitude']
            gps_lat = reading['gps_latitude']
            
            if 'gps_longitude_pg' in stream_config.custom_tags:
                try:
                    gps_long = float(stream_config.custom_tags['gps_longitude_pg'])
                    gps_lat = float(stream_config.custom_tags['gps_latitude_pg'])
                    logger.debug(f"Using GPS from patient_locations: ({gps_long}, {gps_lat})")
                except (ValueError, TypeError):
                    logger.warning("Invalid GPS from PostgreSQL, using generated values")
            
            # Create a point using the measurement from binding
            point = Point(stream_config.measurement) \
                .tag("patient_id", stream_config.patient_id) \
                .tag("patient_name", stream_config.patient_name) \
                .tag("device_id", stream_config.device_id) \
                .tag("stream_id", stream_config.stream_id) \
                .tag("org_id", stream_config.org_id or "none") \
                .tag("signal_type", stream_config.signal_type_code) \
                .tag("risk_level", stream_config.risk_level_code or "unknown") \
                .field("gps_longitude", gps_long) \
                .field("gps_latitude", gps_lat) \
                .field("heart_rate", reading['heart_rate']) \
                .field("spo2", reading['spo2']) \
                .field("systolic_bp", reading['systolic_bp']) \
                .field("diastolic_bp", reading['diastolic_bp']) \
                .field("temperature", reading['temperature']) \
                .time(timestamp, WritePrecision.NS)
            
            # Add custom tags from timeseries_binding_tag (excluding GPS which are fields)
            for tag_key, tag_value in stream_config.custom_tags.items():
                if not tag_key.startswith('gps_'):  # Skip GPS tags, already added as fields
                    point = point.tag(tag_key, tag_value)
            
            # Write using bucket and org from stream config
            self.write_api.write(
                bucket=stream_config.influx_bucket,
                org=stream_config.influx_org,
                record=point
            )
            
            logger.debug(
                f"Wrote vital signs for patient {stream_config.patient_name} "
                f"(device: {stream_config.device_serial}, stream: {stream_config.stream_id}): "
                f"HR={reading['heart_rate']}, SpO2={reading['spo2']}, "
                f"BP={reading['systolic_bp']}/{reading['diastolic_bp']}, "
                f"Temp={reading['temperature']}°C, GPS=({gps_long:.4f}, {gps_lat:.4f})"
            )
        except Exception as e:
            logger.error(
                f"Error writing to InfluxDB for stream {stream_config.stream_id}: {e}"
            )

