"""
Cliente de InfluxDB para consultas de datos en tiempo real
"""
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..config import get_config

logger = logging.getLogger(__name__)


class InfluxDBService:
    """Servicio para interactuar con InfluxDB"""
    
    def __init__(self):
        config = get_config()
        self.url = config.INFLUXDB_URL
        self.token = config.INFLUXDB_TOKEN
        self.org = config.INFLUXDB_ORG
        self.bucket = config.INFLUXDB_BUCKET
        self._client = None
        self._query_api = None
    
    @property
    def client(self) -> InfluxDBClient:
        """Obtiene o crea el cliente de InfluxDB"""
        if self._client is None:
            try:
                self._client = InfluxDBClient(
                    url=self.url,
                    token=self.token,
                    org=self.org
                )
                logger.info(f"✓ Cliente InfluxDB conectado: {self.url}")
            except Exception as e:
                logger.error(f"Error conectando a InfluxDB: {e}")
                raise
        return self._client
    
    @property
    def query_api(self) -> QueryApi:
        """Obtiene la API de consultas"""
        if self._query_api is None:
            self._query_api = self.client.query_api()
        return self._query_api
    
    def get_patient_realtime_data(
        self, 
        patient_id: str, 
        hours: int = 1,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtiene datos en tiempo real de un paciente
        
        Args:
            patient_id: UUID del paciente
            hours: Ventana de tiempo en horas (default: 1 hora)
            limit: Límite de puntos de datos (default: 100)
            
        Returns:
            Lista de puntos de datos con timestamp y valores
        """
        try:
            # Construir query de Flux
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["_measurement"] == "vital_signs")
                |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: true)
                |> limit(n: {limit})
            '''
            
            logger.debug(f"Ejecutando query InfluxDB para paciente {patient_id}")
            
            # Ejecutar query
            tables = self.query_api.query(query, org=self.org)
            
            # Procesar resultados
            results = []
            for table in tables:
                for record in table.records:
                    data_point = {
                        'timestamp': record.get_time().isoformat(),
                        'gps_longitude': record.values.get('gps_longitude'),
                        'gps_latitude': record.values.get('gps_latitude'),
                        'heart_rate': record.values.get('heart_rate'),
                        'spo2': record.values.get('spo2'),
                        'systolic_bp': record.values.get('systolic_bp'),
                        'diastolic_bp': record.values.get('diastolic_bp'),
                        'body_temperature': record.values.get('temperature'),
                        'heart_rate_alert': int(record.values.get('heart_rate_alert', 0)),
                        'spo2_alert': int(record.values.get('spo2_alert', 0)),
                        'bp_alert': int(record.values.get('bp_alert', 0)),
                        'temperature_alert': int(record.values.get('temperature_alert', 0)),
                    }
                    results.append(data_point)
            
            logger.info(f"✓ Obtenidos {len(results)} puntos de datos para paciente {patient_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error consultando InfluxDB para paciente {patient_id}: {e}")
            return []
    
    def get_patient_latest_vitals(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los últimos signos vitales de un paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Diccionario con los últimos valores o None
        """
        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -24h)
                |> filter(fn: (r) => r["_measurement"] == "vital_signs")
                |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: true)
                |> limit(n: 1)
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            for table in tables:
                for record in table.records:
                    return {
                        'timestamp': record.get_time().isoformat(),
                        'gps_longitude': record.values.get('gps_longitude'),
                        'gps_latitude': record.values.get('gps_latitude'),
                        'heart_rate': record.values.get('heart_rate'),
                        'spo2': record.values.get('spo2'),
                        'systolic_bp': record.values.get('systolic_bp'),
                        'diastolic_bp': record.values.get('diastolic_bp'),
                        'body_temperature': record.values.get('temperature'),
                        'heart_rate_alert': int(record.values.get('heart_rate_alert', 0)),
                        'spo2_alert': int(record.values.get('spo2_alert', 0)),
                        'bp_alert': int(record.values.get('bp_alert', 0)),
                        'temperature_alert': int(record.values.get('temperature_alert', 0)),
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo últimos vitales para paciente {patient_id}: {e}")
            return None
    
    def get_patient_vitals_summary(
        self, 
        patient_id: str, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Obtiene resumen estadístico de signos vitales
        
        Args:
            patient_id: UUID del paciente
            hours: Ventana de tiempo en horas
            
        Returns:
            Diccionario con estadísticas (promedio, min, max)
        """
        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["_measurement"] == "vital_signs")
                |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
                |> filter(fn: (r) => 
                    r["_field"] == "heart_rate" or 
                    r["_field"] == "spo2" or 
                    r["_field"] == "systolic_bp" or 
                    r["_field"] == "diastolic_bp" or
                    r["_field"] == "temperature"
                )
                |> group(columns: ["_field"])
            '''
            
            # Calcular estadísticas
            mean_query = query + '|> mean()'
            min_query = query + '|> min()'
            max_query = query + '|> max()'
            
            results = {
                'mean': {},
                'min': {},
                'max': {},
                'period_hours': hours
            }
            
            # Ejecutar queries
            for stat_type, stat_query in [('mean', mean_query), ('min', min_query), ('max', max_query)]:
                tables = self.query_api.query(stat_query, org=self.org)
                for table in tables:
                    for record in table.records:
                        field = record.values.get('_field')
                        value = record.values.get('_value')
                        if field and value is not None:
                            results[stat_type][field] = round(float(value), 2)
            
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de vitales para paciente {patient_id}: {e}")
            return {
                'mean': {},
                'min': {},
                'max': {},
                'period_hours': hours,
                'error': str(e)
            }
    
    def close(self):
        """Cierra la conexión con InfluxDB"""
        if self._client:
            self._client.close()
            logger.info("✓ Cliente InfluxDB cerrado")


# Instancia global del servicio
_influx_service = None


def get_influx_service() -> InfluxDBService:
    """Obtiene o crea la instancia global del servicio InfluxDB"""
    global _influx_service
    if _influx_service is None:
        _influx_service = InfluxDBService()
    return _influx_service
