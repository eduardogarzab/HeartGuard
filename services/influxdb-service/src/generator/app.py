"""Flask application entrypoint for Generator Service."""
import logging
from flask import Flask, jsonify, request

from .config import configure_app
from .db import DatabaseService
from .influx import InfluxDBService
from .worker import GeneratorWorker
from .xml import xml_response, xml_error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services
db_service = None
influx_service = None
worker = None


def wants_xml() -> bool:
    """Check if the client prefers XML response."""
    accept = request.headers.get('Accept', '')
    return 'application/xml' in accept or 'text/xml' in accept


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    configure_app(app)
    
    # Initialize services
    global db_service, influx_service, worker
    
    db_service = DatabaseService(app.config['DATABASE_URL'])
    influx_service = InfluxDBService(
        app.config['INFLUXDB_URL'],
        app.config['INFLUXDB_TOKEN'],
        app.config['INFLUXDB_ORG'],
        app.config['INFLUXDB_BUCKET']
    )
    
    # Connect to databases
    db_service.connect()
    influx_service.connect()
    
    # Create and start worker
    worker = GeneratorWorker(
        db_service,
        influx_service,
        app.config['GENERATION_INTERVAL']
    )
    worker.start()
    
    logger.info("=" * 60)
    logger.info("HeartGuard Real-time Data Generator Service")
    logger.info(f"Generation interval: {app.config['GENERATION_INTERVAL']} seconds")
    logger.info(f"InfluxDB URL: {app.config['INFLUXDB_URL']}")
    logger.info(f"InfluxDB Bucket: {app.config['INFLUXDB_BUCKET']}")
    logger.info("=" * 60)
    
    # Register routes
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        payload = {
            'status': 'healthy',
            'service': 'influxdb-service',
            'worker_running': worker.running if worker else False,
            'iteration': worker.iteration if worker else 0
        }
        if wants_xml():
            return xml_response(payload)
        return jsonify(payload), 200
    
    @app.route('/status', methods=['GET'])
    def status():
        """Detailed status endpoint."""
        patients = db_service.get_active_patients() if db_service else []
        payload = {
            'status': 'running',
            'service': 'influxdb-service',
            'worker': {
                'running': worker.running if worker else False,
                'iteration': worker.iteration if worker else 0,
                'interval_seconds': app.config['GENERATION_INTERVAL']
            },
            'database': {
                'connected': db_service.conn is not None if db_service else False,
                'active_patients': len(patients)
            },
            'influxdb': {
                'connected': influx_service.client is not None if influx_service else False,
                'url': app.config['INFLUXDB_URL'],
                'bucket': app.config['INFLUXDB_BUCKET']
            }
        }
        if wants_xml():
            return xml_response(payload)
        return jsonify(payload), 200
    
    @app.route('/patients', methods=['GET'])
    def get_patients():
        """Get list of active patients being monitored."""
        if not db_service:
            error_msg = 'Database service not initialized'
            if wants_xml():
                return xml_error_response('service_unavailable', error_msg, status=500)
            return jsonify({'error': error_msg}), 500
        
        patients = db_service.get_active_patients()
        payload = {
            'count': len(patients),
            'patients': [
                {
                    'id': p.id,
                    'name': p.name,
                    'email': p.email,
                    'risk_level': p.risk_level_code
                }
                for p in patients
            ]
        }
        if wants_xml():
            return xml_response(payload)
        return jsonify(payload), 200
    
    @app.route('/patients/<patient_id>/vital-signs', methods=['GET'])
    def get_patient_vital_signs(patient_id: str):
        """
        Get latest vital signs for a patient.
        
        Query Parameters:
            - device_id (optional): Filter by specific device
            - limit (optional): Number of records to return (default: 10, max: 100)
            - measurement (optional): InfluxDB measurement name (auto-detected from PostgreSQL if device_id provided)
        """
        if not influx_service:
            error_msg = 'InfluxDB service not initialized'
            if wants_xml():
                return xml_error_response('service_unavailable', error_msg, status=500)
            return jsonify({'error': error_msg}), 500
        
        if not db_service:
            error_msg = 'Database service not initialized'
            if wants_xml():
                return xml_error_response('service_unavailable', error_msg, status=500)
            return jsonify({'error': error_msg}), 500
        
        # Get query parameters
        device_id = request.args.get('device_id')
        limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 records
        measurement = request.args.get('measurement')
        
        # Auto-detect measurement from PostgreSQL if device_id provided
        if device_id and not measurement:
            try:
                measurement = db_service.get_measurement_for_device(patient_id, device_id)
                if not measurement:
                    logger.warning(f"No binding found for patient {patient_id}, device {device_id}")
                    measurement = 'vital_signs'  # fallback
            except Exception as e:
                logger.error(f"Error getting measurement from database: {e}")
                measurement = 'vital_signs'  # fallback
        
        # Default measurement if not specified
        if not measurement:
            measurement = 'vital_signs'
        
        try:
            readings = influx_service.query_patient_vital_signs(
                patient_id=patient_id,
                device_id=device_id,
                limit=limit,
                measurement=measurement
            )
            
            payload = {
                'patient_id': patient_id,
                'device_id': device_id,
                'measurement': measurement,
                'count': len(readings),
                'readings': readings
            }
            if wants_xml():
                return xml_response(payload)
            return jsonify(payload), 200
            
        except Exception as e:
            logger.error(f"Error fetching vital signs for patient {patient_id}: {e}")
            if wants_xml():
                return xml_error_response('query_failed', str(e), status=500)
            return jsonify({
                'error': 'query_failed',
                'message': str(e)
            }), 500
    
    # Cleanup on shutdown
    def cleanup_on_shutdown():
        """Cleanup resources on application shutdown."""
        logger.info("Shutting down application...")
        if worker:
            worker.stop()
        if influx_service:
            influx_service.disconnect()
        if db_service:
            db_service.disconnect()
    
    import atexit
    atexit.register(cleanup_on_shutdown)
    
    return app


# Create app instance for Flask CLI
app = create_app()
