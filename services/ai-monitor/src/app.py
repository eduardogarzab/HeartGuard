"""
Flask Application Wrapper - AI Monitor Service
Proporciona endpoints HTTP mientras ejecuta el worker en background
"""
import logging
import sys
import threading
from flask import Flask, jsonify
from flask_cors import CORS

import config
from monitor import AIMonitorWorker

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Crear app Flask
app = Flask(__name__)
CORS(app)

# Worker global
worker = None
worker_thread = None


def start_worker_background():
    """Inicia el worker en un thread de background"""
    global worker
    try:
        logger.info("Iniciando AI Monitor Worker en background...")
        worker = AIMonitorWorker(use_signals=False)  # No usar signals en thread
        worker.start()
    except Exception as e:
        logger.error(f"Error en worker: {e}", exc_info=True)


@app.before_request
def log_request():
    """Log de todas las requests"""
    from flask import request
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Verifica que el servicio esté funcionando
    """
    global worker
    
    status = {
        "status": "healthy",
        "message": "AI Monitor Service operativo",
        "worker": {
            "running": worker.running if worker else False,
            "initialized": worker is not None
        },
        "config": {
            "monitor_interval": config.MONITOR_INTERVAL,
            "lookback_window": config.LOOKBACK_WINDOW,
            "batch_size": config.BATCH_SIZE,
            "notifications_enabled": config.ENABLE_NOTIFICATIONS
        },
        "version": "1.0.0"
    }
    
    return jsonify(status), 200


@app.route('/status', methods=['GET'])
def worker_status():
    """
    Status detallado del worker
    """
    global worker
    
    if not worker:
        return jsonify({
            "status": "not_initialized",
            "message": "Worker no ha sido inicializado"
        }), 503
    
    return jsonify({
        "status": "running" if worker.running else "stopped",
        "running": worker.running,
        "config": {
            "influxdb_url": config.INFLUXDB_URL,
            "postgres_host": config.POSTGRES_HOST,
            "ai_service_url": config.AI_SERVICE_URL,
            "monitor_interval": config.MONITOR_INTERVAL
        }
    }), 200


@app.route('/stop', methods=['POST'])
def stop_worker():
    """
    Detiene el worker (solo para testing/admin)
    """
    global worker
    
    if not worker:
        return jsonify({
            "status": "error",
            "message": "Worker no está inicializado"
        }), 400
    
    worker.running = False
    
    return jsonify({
        "status": "success",
        "message": "Worker detenido"
    }), 200


def init_app():
    """Inicializa la aplicación y el worker"""
    global worker_thread
    
    logger.info("=" * 60)
    logger.info("Inicializando AI Monitor Service")
    logger.info("=" * 60)
    
    # Iniciar worker en thread de background
    worker_thread = threading.Thread(target=start_worker_background, daemon=True)
    worker_thread.start()
    
    logger.info("✅ AI Monitor Service inicializado")
    logger.info("=" * 60)


# Inicializar al importar
init_app()


if __name__ == "__main__":
    app.run(
        host=config.FLASK_HOST if hasattr(config, 'FLASK_HOST') else '0.0.0.0',
        port=config.FLASK_PORT if hasattr(config, 'FLASK_PORT') else 5008,
        debug=config.FLASK_DEBUG if hasattr(config, 'FLASK_DEBUG') else False
    )
