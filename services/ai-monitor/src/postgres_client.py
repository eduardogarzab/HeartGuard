"""
PostgreSQL Client - Gestiona alertas y notificaciones
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
from datetime import datetime
from . import config

logger = logging.getLogger(__name__)


class PostgresClient:
    """Cliente para operaciones en PostgreSQL"""
    
    def __init__(self):
        self.conn = None
        self.enabled = True
        try:
            self.connect()
        except Exception as e:
            logger.warning(f"PostgreSQL no disponible: {e}")
            logger.warning("El servicio continuará sin almacenar alertas en PostgreSQL")
            self.enabled = False
    
    def connect(self):
        """Establece conexión a PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=config.POSTGRES_HOST,
                port=config.POSTGRES_PORT,
                database=config.POSTGRES_DB,
                user=config.POSTGRES_USER,
                password=config.POSTGRES_PASSWORD
            )
            logger.info("PostgreSQL connection established")
            self.enabled = True
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            self.enabled = False
            raise
    
    def ensure_connection(self):
        """Verifica y reestablece conexión si es necesario"""
        if not self.enabled:
            return False
        
        try:
            if self.conn is None or self.conn.closed:
                self.connect()
            else:
                # Test connection
                with self.conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            self.enabled = False
            return False
    
    def create_alert(
        self, 
        patient_id: str, 
        alert_type: str, 
        severity: str,
        description: str,
        timestamp: str,
        gps_latitude: float,
        gps_longitude: float,
        model_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Crea una alerta en la base de datos
        
        Args:
            patient_id: UUID del paciente
            alert_type: Código del tipo de alerta (ARRHYTHMIA, DESAT, etc.)
            severity: Nivel de severidad (low, medium, high, critical)
            description: Descripción de la alerta
            timestamp: Timestamp del evento (ISO format)
            gps_latitude: Latitud GPS
            gps_longitude: Longitud GPS
            model_id: UUID del modelo que generó la alerta (opcional)
            
        Returns:
            UUID de la alerta creada o None si falla
        """
        if not self.ensure_connection():
            logger.warning("PostgreSQL no disponible, alerta no almacenada")
            return None
        
        try:
            with self.conn.cursor() as cur:
                # Insertar alerta
                cur.execute("""
                    INSERT INTO alerts (
                        patient_id,
                        type_id,
                        alert_level_id,
                        status_id,
                        created_at,
                        description,
                        location,
                        created_by_model_id
                    )
                    VALUES (
                        %s::uuid,
                        (SELECT id FROM alert_types WHERE code = %s),
                        (SELECT id FROM alert_levels WHERE code = %s),
                        (SELECT id FROM alert_status WHERE code = 'created'),
                        %s::timestamp,
                        %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                        %s::uuid
                    )
                    RETURNING id
                """, (
                    patient_id,
                    alert_type,
                    severity,
                    timestamp,
                    description,
                    gps_longitude,
                    gps_latitude,
                    model_id
                ))
                
                alert_id = cur.fetchone()[0]
                self.conn.commit()
                
                logger.info(
                    f"Alert created: {alert_id} - {alert_type} "
                    f"for patient {patient_id}"
                )
                return str(alert_id)
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating alert: {e}")
            return None
    
    def get_patient_caregivers(self, patient_id: str) -> List[Dict]:
        """
        Obtiene los cuidadores de un paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Lista de cuidadores con sus preferencias de notificación
        """
        self.ensure_connection()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT
                        u.id as user_id,
                        u.name,
                        u.email,
                        cp.phone,
                        cp.notify_email,
                        cp.notify_sms,
                        cp.notify_push
                    FROM caregiver_patients cp
                    JOIN users u ON u.id = cp.caregiver_id
                    WHERE cp.patient_id = %s::uuid
                      AND cp.is_active = true
                      AND u.user_status_id = (
                          SELECT id FROM user_statuses WHERE code = 'active'
                      )
                """, (patient_id,))
                
                caregivers = cur.fetchall()
                return [dict(row) for row in caregivers]
                
        except Exception as e:
            logger.error(f"Error getting caregivers for patient {patient_id}: {e}")
            return []
    
    def get_alert_pending_count(self, patient_id: str) -> int:
        """
        Obtiene el número de alertas pendientes para un paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Número de alertas pendientes
        """
        self.ensure_connection()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM alerts
                    WHERE patient_id = %s::uuid
                      AND status_id IN (
                          SELECT id FROM alert_status 
                          WHERE code IN ('created', 'notified')
                      )
                """, (patient_id,))
                
                count = cur.fetchone()[0]
                return count
                
        except Exception as e:
            logger.error(f"Error getting pending alerts count: {e}")
            return 0
    
    def mark_alert_notified(self, alert_id: str) -> bool:
        """
        Marca una alerta como notificada
        
        Args:
            alert_id: UUID de la alerta
            
        Returns:
            True si se actualizó correctamente
        """
        self.ensure_connection()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE alerts
                    SET status_id = (
                        SELECT id FROM alert_status WHERE code = 'notified'
                    )
                    WHERE id = %s::uuid
                """, (alert_id,))
                
                self.conn.commit()
                return True
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error marking alert as notified: {e}")
            return False
    
    def close(self):
        """Cierra la conexión a PostgreSQL"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("PostgreSQL connection closed")
