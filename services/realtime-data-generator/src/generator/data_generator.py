"""Core data generation logic for vital signs."""
import random
from datetime import datetime, timezone
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Patient:
    """Patient information from PostgreSQL"""
    id: str
    name: str
    email: str
    org_id: str
    risk_level_code: str
    created_at: datetime


@dataclass
class StreamConfig:
    """Stream configuration from PostgreSQL for InfluxDB binding"""
    patient_id: str
    patient_name: str
    patient_email: str
    org_id: str
    org_name: Optional[str]
    risk_level_code: Optional[str]
    device_id: str
    device_serial: str
    stream_id: str
    signal_type_code: str
    binding_id: str
    influx_org: str
    influx_bucket: str
    measurement: str
    retention_hint: Optional[str]
    custom_tags: Dict[str, str]


class VitalSignsGenerator:
    """
    Generates realistic synthetic vital signs based on the provided dataset ranges.
    Data ranges from the Excel file:
    - GPS Longitude: -100.56 to -100.21 (Monterrey area)
    - GPS Latitude: 25.52 to 25.84 (Monterrey area)
    - Heart Rate: 45-92 bpm
    - SpO2: 91-100%
    - Systolic BP: 102-154 mmHg
    - Diastolic BP: 59-94 mmHg
    - Temperature: 36.14-37.02°C
    """
    
    # GPS coordinates for Monterrey area
    GPS_LONG_MIN = -100.56
    GPS_LONG_MAX = -100.21
    GPS_LAT_MIN = 25.52
    GPS_LAT_MAX = 25.84
    
    # Vital signs normal ranges
    HEART_RATE_MIN = 45
    HEART_RATE_MAX = 92
    
    SPO2_MIN = 91
    SPO2_MAX = 100
    
    SYSTOLIC_BP_MIN = 102
    SYSTOLIC_BP_MAX = 154
    
    DIASTOLIC_BP_MIN = 59
    DIASTOLIC_BP_MAX = 94
    
    TEMP_MIN = 36.14
    TEMP_MAX = 37.02
    
    def __init__(self):
        """Initialize generator with patient-specific baselines"""
        self.patient_baselines = {}
    
    def get_or_create_baseline(self, patient_id: str) -> Dict:
        """
        Get or create baseline vital signs for a patient.
        Each patient has slightly different normal values.
        """
        if patient_id not in self.patient_baselines:
            # Create patient-specific baseline within normal ranges
            self.patient_baselines[patient_id] = {
                'heart_rate': random.randint(65, 80),
                'spo2': random.randint(96, 99),
                'systolic_bp': random.randint(110, 130),
                'diastolic_bp': random.randint(70, 85),
                'temperature': round(random.uniform(36.4, 36.8), 2),
                'gps_long': round(random.uniform(self.GPS_LONG_MIN, self.GPS_LONG_MAX), 2),
                'gps_lat': round(random.uniform(self.GPS_LAT_MIN, self.GPS_LAT_MAX), 2),
            }
        return self.patient_baselines[patient_id]
    
    def generate_reading(self, patient_id: str) -> Dict:
        """
        Generate one reading of vital signs for a patient.
        Uses baseline and adds small random variations.
        """
        baseline = self.get_or_create_baseline(patient_id)
        
        # Generate values with small variations from baseline
        heart_rate = max(self.HEART_RATE_MIN, min(self.HEART_RATE_MAX, 
            baseline['heart_rate'] + random.randint(-10, 10)))
        
        spo2 = max(self.SPO2_MIN, min(self.SPO2_MAX, 
            baseline['spo2'] + random.randint(-5, 2)))
        
        systolic_bp = max(self.SYSTOLIC_BP_MIN, min(self.SYSTOLIC_BP_MAX, 
            baseline['systolic_bp'] + random.randint(-15, 15)))
        
        diastolic_bp = max(self.DIASTOLIC_BP_MIN, min(self.DIASTOLIC_BP_MAX, 
            baseline['diastolic_bp'] + random.randint(-10, 10)))
        
        temperature = max(self.TEMP_MIN, min(self.TEMP_MAX, 
            round(baseline['temperature'] + random.uniform(-0.3, 0.3), 2)))
        
        # GPS coordinates with small movements (simulating patient movement)
        gps_long = round(baseline['gps_long'] + random.uniform(-0.01, 0.01), 4)
        gps_lat = round(baseline['gps_lat'] + random.uniform(-0.01, 0.01), 4)
        
        return {
            'gps_longitude': gps_long,
            'gps_latitude': gps_lat,
            'heart_rate': heart_rate,
            'spo2': spo2,
            'systolic_bp': systolic_bp,
            'diastolic_bp': diastolic_bp,
            'temperature': temperature,
            'timestamp': datetime.now(timezone.utc)
        }
