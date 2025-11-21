"""InfluxDB operations for Generator Service."""
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Dict
import logging

from .data_generator import Patient

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
