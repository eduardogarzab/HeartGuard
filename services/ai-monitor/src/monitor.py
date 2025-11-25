"""
AI Monitor Worker - Monitorea signos vitales y genera alertas
Lee datos de InfluxDB, los envía al modelo de IA y crea alertas en PostgreSQL
"""
import logging
import time
import signal
import sys
from typing import Optional, Dict
from datetime import datetime

import config
from influx_client import InfluxDBService
from postgres_client import PostgresClient
from ai_client import AIServiceClient

logger = logging.getLogger(__name__)


class AIMonitorWorker:
    """
    Worker que monitorea signos vitales de pacientes en tiempo real.
    
    Flujo:
    1. Obtiene lista de pacientes activos de InfluxDB
    2. Para cada paciente, obtiene los signos vitales más recientes
    3. Envía los signos vitales al modelo de IA para predicción
    4. Si hay anomalía, crea una alerta en PostgreSQL
    """
    
    def __init__(self, use_signals: bool = True):
        """
        Inicializa el worker
        
        Args:
            use_signals: Si debe registrar handlers para señales del sistema
        """
        self.running = False
        self.use_signals = use_signals
        
        # Clientes
        self.influx_client: Optional[InfluxDBService] = None
        self.postgres_client: Optional[PostgresClient] = None
        self.ai_client: Optional[AIServiceClient] = None
        
        # Configuración
        self.interval = config.MONITOR_INTERVAL
        self.lookback_window = config.LOOKBACK_WINDOW // 60  # Convertir a minutos
        self.batch_size = config.BATCH_SIZE
        self.threshold = config.AI_PREDICTION_THRESHOLD
        
        logger.info("=" * 60)
        logger.info("AI Monitor Worker initialized")
        logger.info(f"  Monitor interval: {self.interval}s")
        logger.info(f"  Lookback window: {self.lookback_window}m")
        logger.info(f"  Batch size: {self.batch_size}")
        logger.info(f"  AI threshold: {self.threshold}")
        logger.info("=" * 60)
    
    def _setup_signals(self):
        """Configura handlers para señales del sistema"""
        if not self.use_signals:
            return
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _initialize_clients(self) -> bool:
        """
        Inicializa los clientes de servicios externos
        
        Returns:
            True si todos los clientes se inicializaron correctamente
        """
        try:
            # InfluxDB
            logger.info("Connecting to InfluxDB...")
            self.influx_client = InfluxDBService()
            
            # PostgreSQL
            logger.info("Connecting to PostgreSQL...")
            self.postgres_client = PostgresClient()
            
            # AI Service
            logger.info("Connecting to AI Service...")
            self.ai_client = AIServiceClient()
            
            # Verificar AI Service
            if not self.ai_client.health_check():
                logger.warning(
                    "AI Service no está disponible. "
                    "Las predicciones no funcionarán hasta que esté activo."
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing clients: {e}")
            return False
    
    def _cleanup(self):
        """Limpia recursos al terminar"""
        logger.info("Cleaning up resources...")
        
        if self.influx_client:
            self.influx_client.close()
        
        if self.postgres_client:
            self.postgres_client.close()
        
        if self.ai_client:
            self.ai_client.close()
        
        logger.info("Cleanup completed")
    
    def start(self):
        """Inicia el loop de monitoreo"""
        self._setup_signals()
        
        if not self._initialize_clients():
            logger.error("Failed to initialize clients, exiting")
            return
        
        self.running = True
        logger.info("Starting monitoring loop...")
        
        try:
            while self.running:
                cycle_start = time.time()
                
                try:
                    self._run_monitoring_cycle()
                except Exception as e:
                    logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
                
                # Esperar hasta el próximo ciclo
                elapsed = time.time() - cycle_start
                sleep_time = max(0, self.interval - elapsed)
                
                if sleep_time > 0:
                    logger.debug(f"Sleeping for {sleep_time:.1f}s until next cycle")
                    time.sleep(sleep_time)
                    
        finally:
            self._cleanup()
    
    def _run_monitoring_cycle(self):
        """Ejecuta un ciclo completo de monitoreo"""
        logger.info("-" * 40)
        logger.info(f"Starting monitoring cycle at {datetime.now().isoformat()}")
        
        # Obtener pacientes activos
        active_patients = self.influx_client.get_active_patients(
            lookback_minutes=self.lookback_window
        )
        
        if not active_patients:
            logger.info("No active patients found")
            return
        
        logger.info(f"Processing {len(active_patients)} active patients")
        
        # Procesar en batches
        alerts_created = 0
        patients_processed = 0
        
        for patient_id in active_patients:
            try:
                alert_created = self._process_patient(patient_id)
                if alert_created:
                    alerts_created += 1
                patients_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing patient {patient_id}: {e}")
        
        logger.info(
            f"Cycle completed: {patients_processed} patients processed, "
            f"{alerts_created} alerts created"
        )
    
    def _process_patient(self, patient_id: str) -> bool:
        """
        Procesa un paciente individual
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            True si se creó una alerta
        """
        # Obtener signos vitales
        vital_signs = self.influx_client.get_latest_vital_signs(
            patient_id=patient_id,
            lookback_minutes=self.lookback_window
        )
        
        if not vital_signs:
            logger.debug(f"No vital signs found for patient {patient_id}")
            return False
        
        # Obtener predicción del modelo de IA
        prediction = self.ai_client.predict_health(vital_signs)
        
        if not prediction:
            logger.warning(f"No prediction received for patient {patient_id}")
            return False
        
        # Evaluar predicción
        risk_probability = prediction.get("probability", 0)
        predicted_class = prediction.get("predicted_class", 0)
        
        logger.debug(
            f"Patient {patient_id}: probability={risk_probability:.3f}, "
            f"class={predicted_class}"
        )
        
        # Crear alerta si supera el threshold
        if risk_probability >= self.threshold and predicted_class == 1:
            return self._create_alert_from_prediction(
                patient_id=patient_id,
                vital_signs=vital_signs,
                prediction=prediction
            )
        
        return False
    
    def _create_alert_from_prediction(
        self, 
        patient_id: str,
        vital_signs: Dict,
        prediction: Dict
    ) -> bool:
        """
        Crea una alerta basada en la predicción del modelo
        
        Args:
            patient_id: UUID del paciente
            vital_signs: Signos vitales del paciente
            prediction: Predicción del modelo de IA
            
        Returns:
            True si la alerta se creó correctamente
        """
        probability = prediction.get("probability", 0)
        
        # Determinar severidad basada en probabilidad
        if probability >= 0.9:
            severity = "critical"
            alert_type = "AI_CRITICAL"
        elif probability >= 0.8:
            severity = "high"
            alert_type = "AI_HIGH_RISK"
        elif probability >= 0.7:
            severity = "medium"
            alert_type = "AI_MEDIUM_RISK"
        else:
            severity = "low"
            alert_type = "AI_LOW_RISK"
        
        # Construir descripción
        description = (
            f"Anomalía detectada por IA (probabilidad: {probability:.1%}). "
            f"FC: {vital_signs.get('heart_rate')} bpm, "
            f"SpO2: {vital_signs.get('spo2')}%, "
            f"PA: {vital_signs.get('systolic_bp')}/{vital_signs.get('diastolic_bp')} mmHg, "
            f"Temp: {vital_signs.get('temperature'):.1f}°C"
        )
        
        # Crear alerta en PostgreSQL
        alert_id = self.postgres_client.create_alert(
            patient_id=patient_id,
            alert_type=alert_type,
            severity=severity,
            description=description,
            timestamp=vital_signs.get("timestamp", datetime.now().isoformat()),
            gps_latitude=vital_signs.get("gps_latitude", 0),
            gps_longitude=vital_signs.get("gps_longitude", 0)
        )
        
        if alert_id:
            logger.info(
                f"🚨 Alert created: {alert_id} - {alert_type} ({severity}) "
                f"for patient {patient_id}"
            )
            return True
        
        return False


def main():
    """Entry point para ejecución standalone"""
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    logger.info("Starting AI Monitor Service (standalone mode)")
    
    worker = AIMonitorWorker(use_signals=True)
    worker.start()
    
    logger.info("AI Monitor Service stopped")


if __name__ == "__main__":
    main()
