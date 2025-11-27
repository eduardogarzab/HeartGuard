"""Background worker for continuous data generation."""
import threading
import time
import logging
from datetime import datetime

from .data_generator import VitalSignsGenerator
from .db import DatabaseService
from .influx import InfluxDBService

logger = logging.getLogger(__name__)


class GeneratorWorker:
    """Background worker that continuously generates and sends vital signs data."""
    
    def __init__(self, db_service: DatabaseService, influx_service: InfluxDBService, 
                 interval: int):
        self.db_service = db_service
        self.influx_service = influx_service
        self.interval = interval
        self.generator = VitalSignsGenerator()
        self.running = False
        self.thread = None
        self.iteration = 0
    
    def start(self):
        """Start the background worker."""
        if self.running:
            logger.warning("Worker already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Generator worker started (interval: {self.interval}s)")
    
    def stop(self):
        """Stop the background worker."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=self.interval + 1)
        logger.info("Generator worker stopped")
    
    def _run(self):
        """Main worker loop."""
        while self.running:
            try:
                self.iteration += 1
                logger.info(f"--- Iteration {self.iteration} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
                
                self._generate_and_send_data()
                
                logger.debug(f"Sleeping for {self.interval} seconds...")
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(self.interval)
    
    def _generate_and_send_data(self):
        """
        Generate and send data for all active patients using stream configurations.
        This version uses the full PostgreSQL metadata to properly tag InfluxDB data.
        """
        # Get stream configurations instead of just patients
        stream_configs = self.db_service.get_patient_device_streams()
        
        if not stream_configs:
            logger.warning("No stream configurations found in database. Run init_sync_data.sql first.")
            return
        
        successful = 0
        skipped = 0
        
        for stream_config in stream_configs:
            try:
                # Generate reading for this patient
                reading = self.generator.generate_reading(stream_config.patient_id)
                
                # Write using the new method with full stream configuration
                self.influx_service.write_vital_signs_from_stream(stream_config, reading)
                successful += 1
                
            except Exception as e:
                logger.error(
                    f"Error processing stream {stream_config.stream_id} "
                    f"for patient {stream_config.patient_name}: {e}"
                )
                skipped += 1
        
        logger.info(
            f"Data generation: {successful} successful, {skipped} skipped "
            f"(total streams: {len(stream_configs)})"
        )

