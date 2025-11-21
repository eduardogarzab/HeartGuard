"""Flask application entrypoint for Generator Service."""
import logging
from flask import Flask, jsonify

from .config import configure_app
from .db import DatabaseService
from .influx import InfluxDBService
from .worker import GeneratorWorker

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
        return jsonify({
            'status': 'healthy',
            'service': 'realtime-data-generator',
            'worker_running': worker.running if worker else False,
            'iteration': worker.iteration if worker else 0
        }), 200
    
    @app.route('/status', methods=['GET'])
    def status():
        """Detailed status endpoint."""
        patients = db_service.get_active_patients() if db_service else []
        return jsonify({
            'status': 'running',
            'service': 'realtime-data-generator',
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
        }), 200
    
    @app.route('/patients', methods=['GET'])
    def get_patients():
        """Get list of active patients being monitored."""
        if not db_service:
            return jsonify({'error': 'Database service not initialized'}), 500
        
        patients = db_service.get_active_patients()
        return jsonify({
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
        }), 200
    
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
