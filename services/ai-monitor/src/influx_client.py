"""
InfluxDB Client - Lee signos vitales de InfluxDB
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.query_api import QueryApi
from . import config

logger = logging.getLogger(__name__)


class InfluxDBService:
    """Servicio para leer datos de InfluxDB"""
    
    def __init__(self):
        self.client = InfluxDBClient(
            url=config.INFLUXDB_URL,
            token=config.INFLUXDB_TOKEN,
            org=config.INFLUXDB_ORG
        )
        self.query_api: QueryApi = self.client.query_api()
        logger.info(f"InfluxDB client initialized: {config.INFLUXDB_URL}")
    
    def get_latest_vital_signs(
        self, 
        patient_id: str, 
        lookback_minutes: int = 5
    ) -> Optional[Dict]:
        """
        Obtiene los signos vitales más recientes de un paciente
        
        Args:
            patient_id: UUID del paciente
            lookback_minutes: Ventana de búsqueda en minutos
            
        Returns:
            Dict con los signos vitales o None si no hay datos
        """
        try:
            # Query para obtener el último conjunto completo de signos vitales
            # Los datos están almacenados como: measurement=signal_name, field=value
            query = f'''
                from(bucket: "{config.INFLUXDB_BUCKET}")
                  |> range(start: -{lookback_minutes}m)
                  |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
                  |> filter(fn: (r) => r["_field"] == "value")
                  |> filter(fn: (r) => 
                      r["_measurement"] == "heart_rate" or 
                      r["_measurement"] == "spo2" or
                      r["_measurement"] == "systolic_bp" or
                      r["_measurement"] == "diastolic_bp" or
                      r["_measurement"] == "temperature" or
                      r["_measurement"] == "gps_latitude" or
                      r["_measurement"] == "gps_longitude"
                  )
                  |> last()
                  |> pivot(rowKey:["_time"], columnKey: ["_measurement"], valueColumn: "_value")
            '''
            
            tables = self.query_api.query(query)
            
            if not tables or len(tables) == 0:
                logger.warning(f"No data found for patient {patient_id}")
                return None
            
            # Procesar el resultado
            for table in tables:
                for record in table.records:
                    # Log para debugging
                    logger.info(f"DEBUG - Record values for patient {patient_id}: {list(record.values.keys())}")
                    
                    vital_signs = {
                        "patient_id": patient_id,
                        "timestamp": record.get_time().isoformat(),
                        "heart_rate": record.values.get("heart_rate"),
                        "spo2": record.values.get("spo2"),
                        "systolic_bp": record.values.get("systolic_bp"),
                        "diastolic_bp": record.values.get("diastolic_bp"),
                        "temperature": record.values.get("temperature"),
                        "gps_latitude": record.values.get("gps_latitude"),
                        "gps_longitude": record.values.get("gps_longitude")
                    }
                    
                    logger.info(f"DEBUG - Vital signs extracted: {vital_signs}")
                    
                    # Validar que tengamos todos los campos necesarios
                    if all(vital_signs.get(k) is not None for k in [
                        "heart_rate", "spo2", "systolic_bp", 
                        "diastolic_bp", "temperature", 
                        "gps_latitude", "gps_longitude"
                    ]):
                        logger.debug(f"Vital signs retrieved for patient {patient_id}")
                        return vital_signs
                    else:
                        logger.warning(f"Incomplete vital signs for patient {patient_id}")
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error querying InfluxDB for patient {patient_id}: {e}")
            return None
    
    def get_active_patients(self, lookback_minutes: int = 10) -> List[str]:
        """
        Obtiene lista de pacientes con datos recientes
        
        Args:
            lookback_minutes: Ventana de búsqueda en minutos
            
        Returns:
            Lista de patient_ids
        """
        try:
            query = f'''
                from(bucket: "{config.INFLUXDB_BUCKET}")
                  |> range(start: -{lookback_minutes}m)
                  |> filter(fn: (r) => r["_measurement"] == "heart_rate")
                  |> filter(fn: (r) => r["_field"] == "value")
                  |> group(columns: ["patient_id"])
                  |> distinct(column: "patient_id")
            '''
            
            tables = self.query_api.query(query)
            patient_ids = []
            
            for table in tables:
                for record in table.records:
                    patient_id = record.values.get("patient_id")
                    if patient_id and patient_id not in patient_ids:
                        patient_ids.append(patient_id)
            
            logger.info(f"Found {len(patient_ids)} active patients")
            return patient_ids
            
        except Exception as e:
            logger.error(f"Error getting active patients: {e}")
            return []
    
    def close(self):
        """Cierra la conexión a InfluxDB"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB client closed")
