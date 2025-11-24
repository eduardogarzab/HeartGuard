"""
Flask Application - Servicio de Predicción de IA
Endpoints para predicciones de salud usando RandomForest
"""
import logging
import sys
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

from .config import (
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG,
    MODEL_PATH,
    DEFAULT_THRESHOLD
)
from .ml.model_loader import ModelLoader
from .ml.predictor import HealthPredictor
from .middleware import require_auth, optional_auth

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Crear app Flask
app = Flask(__name__)
CORS(app)

# Inicializar predictor
predictor = HealthPredictor()
model_loader = ModelLoader()


@app.before_request
def log_request():
    """Log de todas las requests"""
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    Verifica que el servicio esté funcionando y el modelo cargado
    """
    model_info = model_loader.get_model_info()
    
    if not model_info.get("loaded", False):
        return jsonify({
            "status": "unhealthy",
            "message": "Modelo no cargado",
            "model": model_info
        }), 503
    
    return jsonify({
        "status": "healthy",
        "message": "Servicio de IA operativo",
        "model": model_info,
        "version": "1.0.0"
    }), 200


@app.route('/predict', methods=['POST'])
@require_auth
def predict():
    """
    Predice si hay un problema de salud basado en signos vitales
    
    Request Body:
        {
            "gps_longitude": float,
            "gps_latitude": float,
            "heart_rate": float,
            "spo2": float,
            "systolic_bp": float,
            "diastolic_bp": float,
            "temperature": float,
            "threshold": float (opcional, default 0.6)
        }
    
    Response:
        {
            "has_problem": bool,
            "probability": float,
            "alerts": [
                {
                    "type": str,
                    "severity": str,
                    "message": str,
                    "value": float (opcional),
                    "unit": str (opcional)
                }
            ],
            "processed_at": str
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Invalid request",
                "message": "Request body debe ser JSON"
            }), 400
        
        # Validar campos requeridos
        required_fields = [
            "gps_longitude", "gps_latitude", "heart_rate",
            "spo2", "systolic_bp", "diastolic_bp", "temperature"
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return jsonify({
                "error": "Missing fields",
                "message": f"Faltan campos requeridos: {', '.join(missing_fields)}"
            }), 400
        
        # Threshold opcional
        threshold = data.get("threshold", DEFAULT_THRESHOLD)
        
        # Validar rangos razonables
        if not (0.0 <= threshold <= 1.0):
            return jsonify({
                "error": "Invalid threshold",
                "message": "Threshold debe estar entre 0.0 y 1.0"
            }), 400
        
        # Realizar predicción
        result = predictor.predict(data, threshold)
        
        logger.info(
            f"Predicción exitosa: has_problem={result['has_problem']}, "
            f"proba={result['probability']}"
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return jsonify({
            "error": "Validation error",
            "message": str(e)
        }), 400
        
    except RuntimeError as e:
        logger.error(f"Error de runtime: {e}")
        return jsonify({
            "error": "Runtime error",
            "message": str(e)
        }), 500
        
    except Exception as e:
        logger.exception(f"Error inesperado en /predict: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": "Error procesando la predicción"
        }), 500


@app.route('/batch-predict', methods=['POST'])
@require_auth
def batch_predict():
    """
    Realiza predicciones en lote
    
    Request Body:
        {
            "readings": [
                {
                    "gps_longitude": float,
                    "gps_latitude": float,
                    "heart_rate": float,
                    "spo2": float,
                    "systolic_bp": float,
                    "diastolic_bp": float,
                    "temperature": float,
                    "timestamp": str (opcional)
                },
                ...
            ],
            "threshold": float (opcional, default 0.6)
        }
    
    Response:
        {
            "predictions": [
                {
                    "timestamp": str (opcional),
                    "has_problem": bool,
                    "probability": float,
                    "alerts": [...],
                    "processed_at": str
                },
                ...
            ],
            "summary": {
                "total": int,
                "problems_detected": int,
                "avg_probability": float
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or "readings" not in data:
            return jsonify({
                "error": "Invalid request",
                "message": "Se requiere campo 'readings' con array de lecturas"
            }), 400
        
        readings = data["readings"]
        
        if not isinstance(readings, list) or len(readings) == 0:
            return jsonify({
                "error": "Invalid readings",
                "message": "'readings' debe ser un array no vacío"
            }), 400
        
        # Límite de lecturas por request (evitar timeout)
        if len(readings) > 1000:
            return jsonify({
                "error": "Too many readings",
                "message": "Máximo 1000 lecturas por request"
            }), 400
        
        threshold = data.get("threshold", DEFAULT_THRESHOLD)
        
        # Realizar predicciones en lote
        result = predictor.batch_predict(readings, threshold)
        
        logger.info(
            f"Batch prediction exitoso: {result['summary']['total']} lecturas, "
            f"{result['summary']['problems_detected']} problemas detectados"
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Error en /batch-predict: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": "Error procesando predicciones en lote"
        }), 500


@app.route('/model/info', methods=['GET'])
@optional_auth
def model_info():
    """
    Retorna información sobre el modelo cargado
    """
    info = model_loader.get_model_info()
    return jsonify(info), 200


@app.route('/model/reload', methods=['POST'])
@require_auth
def reload_model():
    """
    Recarga el modelo desde disco
    Útil para actualizar el modelo sin reiniciar el servicio
    """
    try:
        model_loader.reload_model(MODEL_PATH)
        info = model_loader.get_model_info()
        
        logger.info("Modelo recargado exitosamente")
        
        return jsonify({
            "message": "Modelo recargado exitosamente",
            "model": info
        }), 200
        
    except Exception as e:
        logger.exception(f"Error recargando modelo: {e}")
        return jsonify({
            "error": "Reload failed",
            "message": str(e)
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handler para rutas no encontradas"""
    return jsonify({
        "error": "Not found",
        "message": "Endpoint no encontrado"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handler para errores internos"""
    logger.exception(f"Error interno del servidor: {e}")
    return jsonify({
        "error": "Internal server error",
        "message": "Error interno del servidor"
    }), 500


def init_app():
    """Inicializa la aplicación (carga el modelo)"""
    logger.info("=" * 60)
    logger.info("Inicializando HeartGuard AI Prediction Service")
    logger.info("=" * 60)
    
    # Crear directorio de modelos si no existe
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Verificar si el modelo existe
    if not MODEL_PATH.exists():
        logger.error(f"❌ Modelo no encontrado en: {MODEL_PATH}")
        logger.error("Por favor, copia el archivo modelo_salud_randomforest.pkl a:")
        logger.error(f"   {MODEL_PATH.parent}")
        sys.exit(1)
    
    # Cargar modelo
    try:
        model_loader.load_model(MODEL_PATH)
        logger.info("✅ Modelo cargado exitosamente")
        
        info = model_loader.get_model_info()
        logger.info(f"   - Estimadores: {info['n_estimators']}")
        logger.info(f"   - Features: {info['n_features']}")
        logger.info(f"   - Threshold por defecto: {DEFAULT_THRESHOLD}")
        
    except Exception as e:
        logger.exception(f"❌ Error cargando modelo: {e}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info(f"🚀 Servidor iniciando en {FLASK_HOST}:{FLASK_PORT}")
    logger.info("=" * 60)


if __name__ == '__main__':
    init_app()
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )
