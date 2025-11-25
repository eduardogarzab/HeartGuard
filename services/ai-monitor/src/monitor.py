<<<<<<< Updated upstream
"""
AI Monitor Worker - Orquesta el flujo completo de monitoreo con IA
"""
import logging
import time
from datetime import datetime
from typing import Dict, List
import signal
import sys

from influx_client import InfluxDBService
from ai_client import AIServiceClient
from postgres_client import PostgresClient
from notification_service import NotificationService
from auth_client import AuthClient
import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai-monitor.log')
    ]
)

logger = logging.getLogger(__name__)


class AIMonitorWorker:
    """Worker principal que monitorea pacientes y genera alertas con IA"""
    
    def __init__(self, use_signals=True):
        self.running = False
        
        # Inicializar clientes
        logger.info("Initializing AI Monitor Worker...")
        
        self.influx_client = InfluxDBService()
        self.ai_client = AIServiceClient()
        self.postgres_client = PostgresClient()
        self.notification_service = NotificationService()
        self.auth_client = AuthClient()
        
        # Registrar handlers para shutdown graceful solo si estamos en main thread
        if use_signals:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("AI Monitor Worker initialized successfully")
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start(self):
        """Inicia el worker"""
        logger.info("Starting AI Monitor Worker...")
        
        # Verificar que el servicio de IA esté disponible
        if not self.ai_client.health_check():
            logger.error("AI Service is not healthy, cannot start worker")
            return
        
        # Obtener token de autenticación
        token = self.auth_client.get_service_token()
        if token:
            self.ai_client.set_jwt_token(token)
        else:
            logger.warning("Could not get auth token, proceeding without authentication")
        
        self.running = True
        cycle_count = 0
        
        logger.info(
            f"Worker started. Monitoring every {config.MONITOR_INTERVAL} seconds, "
            f"looking back {config.LOOKBACK_WINDOW} seconds"
        )
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"=== Monitoring Cycle #{cycle_count} ===")
                
                start_time = time.time()
                
                # Procesar pacientes activos
                stats = self._process_active_patients()
                
                elapsed_time = time.time() - start_time
                
                logger.info(
                    f"Cycle #{cycle_count} completed in {elapsed_time:.2f}s - "
                    f"Patients: {stats['patients_checked']}, "
                    f"Predictions: {stats['predictions_made']}, "
                    f"Alerts: {stats['alerts_created']}, "
                    f"Notifications: {stats['notifications_sent']}"
                )
                
                # Esperar antes del siguiente ciclo
                if self.running:
                    time.sleep(config.MONITOR_INTERVAL)
                    
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
                # Continuar después de un error
                if self.running:
                    time.sleep(config.MONITOR_INTERVAL)
        
        logger.info("Worker stopped")
        self._cleanup()
    
    def _process_active_patients(self) -> Dict:
        """
        Procesa todos los pacientes activos
        
        Returns:
            Estadísticas del ciclo
        """
        stats = {
            "patients_checked": 0,
            "predictions_made": 0,
            "alerts_created": 0,
            "notifications_sent": 0
        }
        
        # Obtener lista de pacientes con datos recientes
        lookback_minutes = config.LOOKBACK_WINDOW // 60
        patient_ids = self.influx_client.get_active_patients(lookback_minutes)
        
        logger.info(f"Found {len(patient_ids)} active patients")
        
        # Procesar en batches
        for i in range(0, len(patient_ids), config.BATCH_SIZE):
            batch = patient_ids[i:i + config.BATCH_SIZE]
            
            for patient_id in batch:
                try:
                    patient_stats = self._process_patient(patient_id)
                    
                    stats["patients_checked"] += 1
                    stats["predictions_made"] += patient_stats.get("predictions", 0)
                    stats["alerts_created"] += patient_stats.get("alerts", 0)
                    stats["notifications_sent"] += patient_stats.get("notifications", 0)
                    
                except Exception as e:
                    logger.error(f"Error processing patient {patient_id}: {e}")
                    continue
        
        return stats
    
    def _process_patient(self, patient_id: str) -> Dict:
        """
        Procesa un paciente individual
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Estadísticas del procesamiento
        """
        stats = {"predictions": 0, "alerts": 0, "notifications": 0}
        
        # 1. Obtener signos vitales más recientes de InfluxDB
        lookback_minutes = config.LOOKBACK_WINDOW // 60
        vital_signs = self.influx_client.get_latest_vital_signs(
            patient_id, 
            lookback_minutes
        )
        
        if not vital_signs:
            logger.debug(f"No recent vital signs for patient {patient_id}")
            return stats
        
        # 2. Llamar al modelo de IA para predicción
        prediction = self.ai_client.predict_health(vital_signs)
        
        if not prediction:
            logger.warning(f"Could not get prediction for patient {patient_id}")
            return stats
        
        stats["predictions"] = 1
        
        # 3. Si hay problema detectado, crear alertas
        has_problem = prediction.get("has_problem", False)
        if has_problem:
            probability = prediction.get("probability", 0)
            
            logger.info(
                f"Health problem detected for patient {patient_id} "
                f"(probability: {probability:.2%})"
            )
            
            alerts = prediction.get("alerts", [])
            created_alert_ids = []
            
            for alert in alerts:
                alert_id = self._create_alert(patient_id, alert, prediction)
                
                if alert_id:
                    created_alert_ids.append(alert_id)
                    stats["alerts"] += 1
            
            # 4. Notificar a caregivers si se crearon alertas
            if created_alert_ids:
                notifications_sent = self._notify_caregivers(
                    patient_id, 
                    alerts,
                    prediction
                )
                stats["notifications"] = notifications_sent
        else:
            logger.debug(
                f"No health problems detected for patient {patient_id} "
                f"(probability: {prediction.get('probability', 0):.2%})"
            )
        
        return stats
    
    def _create_alert(
        self, 
        patient_id: str, 
        alert: Dict, 
        prediction: Dict
    ) -> str:
        """
        Crea una alerta en PostgreSQL
        
        Args:
            patient_id: UUID del paciente
            alert: Información de la alerta del modelo
            prediction: Predicción completa del modelo
            
        Returns:
            UUID de la alerta creada o None
        """
        try:
            alert_id = self.postgres_client.create_alert(
                patient_id=patient_id,
                alert_type=alert["type"],
                severity=alert["severity"],
                description=alert["message"],
                timestamp=prediction["timestamp"],
                gps_latitude=prediction["gps_latitude"],
                gps_longitude=prediction["gps_longitude"],
                model_id=None  # TODO: Obtener model_id desde configuración
            )
            
            return alert_id
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    def _notify_caregivers(
        self, 
        patient_id: str, 
        alerts: List[Dict],
        prediction: Dict
    ) -> int:
        """
        Notifica a los cuidadores del paciente
        
        Args:
            patient_id: UUID del paciente
            alerts: Lista de alertas generadas
            prediction: Predicción del modelo
            
        Returns:
            Número de notificaciones enviadas
        """
        try:
            # Obtener caregivers del paciente
            caregivers = self.postgres_client.get_patient_caregivers(patient_id)
            
            if not caregivers:
                logger.warning(f"No caregivers found for patient {patient_id}")
                return 0
            
            logger.info(
                f"Notifying {len(caregivers)} caregivers for patient {patient_id}"
            )
            
            # Preparar información de la alerta para notificación
            # Usar la alerta más severa para el resumen
            most_severe = max(
                alerts, 
                key=lambda a: {
                    "low": 1, "medium": 2, "high": 3, "critical": 4
                }.get(a.get("severity", "low"), 0)
            )
            
            alert_info = {
                "patient_id": patient_id,
                "alert_type": most_severe["type"],
                "severity": most_severe["severity"],
                "description": most_severe["message"],
                "timestamp": prediction["timestamp"],
                "probability": prediction.get("probability", 0),
                "total_alerts": len(alerts)
            }
            
            # Enviar notificaciones
            sent_count = self.notification_service.send_alert_notifications(
                caregivers,
                alert_info
            )
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error notifying caregivers: {e}")
            return 0
    
    def _cleanup(self):
        """Limpia recursos antes de cerrar"""
        logger.info("Cleaning up resources...")
        
        try:
            self.influx_client.close()
        except:
            pass
        
        try:
            self.ai_client.close()
        except:
            pass
        
        try:
            self.postgres_client.close()
        except:
            pass
        
        try:
            self.notification_service.close()
        except:
            pass
        
        try:
            self.auth_client.close()
        except:
            pass
        
        logger.info("Cleanup complete")


def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("AI Monitor Service - HeartGuard")
    logger.info("=" * 60)
    
    worker = AIMonitorWorker()
    worker.start()


if __name__ == "__main__":
    main()
=======
"""
AI Monitor Worker - Orquesta el flujo completo de monitoreo con IA
"""
import logging
import time
from datetime import datetime
from typing import Dict, List
import signal
import sys

from influx_client import InfluxDBService
from ai_client import AIServiceClient
from postgres_client import PostgresClient
from notification_service import NotificationService
from auth_client import AuthClient
import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai-monitor.log')
    ]
)

logger = logging.getLogger(__name__)


class AIMonitorWorker:
    """Worker principal que monitorea pacientes y genera alertas con IA"""
    
    def __init__(self, use_signals=True):
        self.running = False
        
        # Inicializar clientes
        logger.info("Initializing AI Monitor Worker...")
        
        self.influx_client = InfluxDBService()
        self.ai_client = AIServiceClient()
        self.postgres_client = PostgresClient()
        self.notification_service = NotificationService()
        self.auth_client = AuthClient()
        
        # Registrar handlers para shutdown graceful solo si estamos en main thread
        if use_signals:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("AI Monitor Worker initialized successfully")
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start(self):
        """Inicia el worker"""
        logger.info("Starting AI Monitor Worker...")
        
        # Verificar que el servicio de IA esté disponible
        if not self.ai_client.health_check():
            logger.error("AI Service is not healthy, cannot start worker")
            return
        
        # Obtener token de autenticación
        token = self.auth_client.get_service_token()
        if token:
            self.ai_client.set_jwt_token(token)
        else:
            logger.warning("Could not get auth token, proceeding without authentication")
        
        self.running = True
        cycle_count = 0
        
        logger.info(
            f"Worker started. Monitoring every {config.MONITOR_INTERVAL} seconds, "
            f"looking back {config.LOOKBACK_WINDOW} seconds"
        )
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"=== Monitoring Cycle #{cycle_count} ===")
                
                start_time = time.time()
                
                # Procesar pacientes activos
                stats = self._process_active_patients()
                
                elapsed_time = time.time() - start_time
                
                logger.info(
                    f"Cycle #{cycle_count} completed in {elapsed_time:.2f}s - "
                    f"Patients: {stats['patients_checked']}, "
                    f"Predictions: {stats['predictions_made']}, "
                    f"Alerts: {stats['alerts_created']}, "
                    f"Notifications: {stats['notifications_sent']}"
                )
                
                # Esperar antes del siguiente ciclo
                if self.running:
                    time.sleep(config.MONITOR_INTERVAL)
                    
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
                # Continuar después de un error
                if self.running:
                    time.sleep(config.MONITOR_INTERVAL)
        
        logger.info("Worker stopped")
        self._cleanup()
    
    def _process_active_patients(self) -> Dict:
        """
        Procesa todos los pacientes activos
        
        Returns:
            Estadísticas del ciclo
        """
        stats = {
            "patients_checked": 0,
            "predictions_made": 0,
            "alerts_created": 0,
            "notifications_sent": 0
        }
        
        # Obtener lista de pacientes con datos recientes
        lookback_minutes = config.LOOKBACK_WINDOW // 60
        patient_ids = self.influx_client.get_active_patients(lookback_minutes)
        
        logger.info(f"Found {len(patient_ids)} active patients")
        
        # Procesar en batches
        for i in range(0, len(patient_ids), config.BATCH_SIZE):
            batch = patient_ids[i:i + config.BATCH_SIZE]
            
            for patient_id in batch:
                try:
                    patient_stats = self._process_patient(patient_id)
                    
                    stats["patients_checked"] += 1
                    stats["predictions_made"] += patient_stats.get("predictions", 0)
                    stats["alerts_created"] += patient_stats.get("alerts", 0)
                    stats["notifications_sent"] += patient_stats.get("notifications", 0)
                    
                except Exception as e:
                    logger.error(f"Error processing patient {patient_id}: {e}")
                    continue
        
        return stats
    
    def _process_patient(self, patient_id: str) -> Dict:
        """
        Procesa un paciente individual
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Estadísticas del procesamiento
        """
        stats = {"predictions": 0, "alerts": 0, "notifications": 0}
        
        # 1. Obtener signos vitales más recientes de InfluxDB
        lookback_minutes = config.LOOKBACK_WINDOW // 60
        vital_signs = self.influx_client.get_latest_vital_signs(
            patient_id, 
            lookback_minutes
        )
        
        if not vital_signs:
            logger.debug(f"No recent vital signs for patient {patient_id}")
            return stats
        
        # 2. Llamar al modelo de IA para predicción
        prediction = self.ai_client.predict_health(vital_signs)
        
        if not prediction:
            logger.warning(f"Could not get prediction for patient {patient_id}")
            return stats
        
        stats["predictions"] = 1
        
        # 3. Si hay problema detectado, crear alertas
        has_problem = prediction.get("has_problem", False)
        if has_problem:
            probability = prediction.get("probability", 0)
            
            logger.info(
                f"Health problem detected for patient {patient_id} "
                f"(probability: {probability:.2%})"
            )
            
            alerts = prediction.get("alerts", [])
            created_alert_ids = []
            
            for alert in alerts:
                alert_id = self._create_alert(patient_id, alert, prediction)
                
                if alert_id:
                    created_alert_ids.append(alert_id)
                    stats["alerts"] += 1
            
            # 4. Notificar a caregivers si se crearon alertas
            if created_alert_ids:
                notifications_sent = self._notify_caregivers(
                    patient_id, 
                    alerts,
                    prediction
                )
                stats["notifications"] = notifications_sent
        else:
            logger.debug(
                f"No health problems detected for patient {patient_id} "
                f"(probability: {prediction.get('probability', 0):.2%})"
            )
        
        return stats
    
    def _create_alert(
        self, 
        patient_id: str, 
        alert: Dict, 
        prediction: Dict
    ) -> str:
        """
        Crea una alerta en PostgreSQL
        
        Args:
            patient_id: UUID del paciente
            alert: Información de la alerta del modelo
            prediction: Predicción completa del modelo
            
        Returns:
            UUID de la alerta creada o None
        """
        try:
            alert_id = self.postgres_client.create_alert(
                patient_id=patient_id,
                alert_type=alert["type"],
                severity=alert["severity"],
                description=alert["message"],
                timestamp=prediction["timestamp"],
                gps_latitude=prediction["gps_latitude"],
                gps_longitude=prediction["gps_longitude"],
                model_id=None  # TODO: Obtener model_id desde configuración
            )
            
            return alert_id
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    def _notify_caregivers(
        self, 
        patient_id: str, 
        alerts: List[Dict],
        prediction: Dict
    ) -> int:
        """
        Notifica a los cuidadores del paciente
        
        Args:
            patient_id: UUID del paciente
            alerts: Lista de alertas generadas
            prediction: Predicción del modelo
            
        Returns:
            Número de notificaciones enviadas
        """
        try:
            # Obtener caregivers del paciente
            caregivers = self.postgres_client.get_patient_caregivers(patient_id)
            
            if not caregivers:
                logger.warning(f"No caregivers found for patient {patient_id}")
                return 0
            
            logger.info(
                f"Notifying {len(caregivers)} caregivers for patient {patient_id}"
            )
            
            # Preparar información de la alerta para notificación
            # Usar la alerta más severa para el resumen
            most_severe = max(
                alerts, 
                key=lambda a: {
                    "low": 1, "medium": 2, "high": 3, "critical": 4
                }.get(a.get("severity", "low"), 0)
            )
            
            alert_info = {
                "patient_id": patient_id,
                "alert_type": most_severe["type"],
                "severity": most_severe["severity"],
                "description": most_severe["message"],
                "timestamp": prediction["timestamp"],
                "probability": prediction.get("probability", 0),
                "total_alerts": len(alerts)
            }
            
            # Enviar notificaciones
            sent_count = self.notification_service.send_alert_notifications(
                caregivers,
                alert_info
            )
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error notifying caregivers: {e}")
            return 0
    
    def _cleanup(self):
        """Limpia recursos antes de cerrar"""
        logger.info("Cleaning up resources...")
        
        try:
            self.influx_client.close()
        except:
            pass
        
        try:
            self.ai_client.close()
        except:
            pass
        
        try:
            self.postgres_client.close()
        except:
            pass
        
        try:
            self.notification_service.close()
        except:
            pass
        
        try:
            self.auth_client.close()
        except:
            pass
        
        logger.info("Cleanup complete")


def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("AI Monitor Service - HeartGuard")
    logger.info("=" * 60)
    
    worker = AIMonitorWorker()
    worker.start()


if __name__ == "__main__":
    main()
>>>>>>> Stashed changes
