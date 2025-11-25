<<<<<<< Updated upstream
"""
AI Service Client - Comunica con el servicio de predicción de IA
"""
import logging
import requests
from typing import Dict, Optional
import config

logger = logging.getLogger(__name__)


class AIServiceClient:
    """Cliente para el servicio de predicción de IA"""
    
    def __init__(self, jwt_token: Optional[str] = None):
        self.base_url = config.AI_SERVICE_URL
        self.jwt_token = jwt_token
        self.session = requests.Session()
        logger.info(f"AI Service client initialized: {self.base_url}")
    
    def set_jwt_token(self, token: str):
        """Actualiza el JWT token"""
        self.jwt_token = token
    
    def predict_health(self, vital_signs: Dict) -> Optional[Dict]:
        """
        Envía signos vitales al modelo de IA para predicción
        
        Args:
            vital_signs: Dict con los signos vitales del paciente
            
        Returns:
            Dict con la predicción del modelo o None si falla
        """
        try:
            # Preparar payload para el modelo
            payload = {
                "gps_longitude": float(vital_signs["gps_longitude"]),
                "gps_latitude": float(vital_signs["gps_latitude"]),
                "heart_rate": float(vital_signs["heart_rate"]),
                "spo2": float(vital_signs["spo2"]),
                "systolic_bp": float(vital_signs["systolic_bp"]),
                "diastolic_bp": float(vital_signs["diastolic_bp"]),
                "temperature": float(vital_signs["temperature"])
            }
            
            # Headers con autenticación
            headers = {
                "Content-Type": "application/json",
                "X-Internal-Key": config.INTERNAL_SERVICE_KEY
            }
            # El internal key tiene precedencia sobre JWT
            # Si no hay internal key, usar JWT si está disponible
            if not config.INTERNAL_SERVICE_KEY and self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            # Llamar al servicio de IA
            response = self.session.post(
                f"{self.base_url}/predict",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                prediction = response.json()
                logger.debug(f"Prediction received for patient {vital_signs['patient_id']}")
                return {
                    **prediction,
                    "timestamp": vital_signs["timestamp"],
                    "patient_id": vital_signs["patient_id"],
                    "gps_latitude": vital_signs["gps_latitude"],
                    "gps_longitude": vital_signs["gps_longitude"]
                }
            else:
                logger.error(
                    f"AI Service error: {response.status_code} - {response.text}"
                )
                return None
                
        except requests.exceptions.Timeout:
            logger.error("AI Service timeout")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to AI Service")
            return None
        except Exception as e:
            logger.error(f"Error calling AI Service: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Verifica si el servicio de IA está operativo
        
        Returns:
            True si está operativo, False en caso contrario
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                is_healthy = data.get("status") == "healthy"
                model_loaded = data.get("model", {}).get("loaded", False)
                
                if is_healthy and model_loaded:
                    logger.info("AI Service is healthy and model is loaded")
                    return True
                else:
                    logger.warning(
                        f"AI Service status: {data.get('status')}, "
                        f"model loaded: {model_loaded}"
                    )
                    return False
            else:
                logger.warning(f"AI Service health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"AI Service health check error: {e}")
            return False
    
    def close(self):
        """Cierra la sesión HTTP"""
        if self.session:
            self.session.close()
            logger.info("AI Service client session closed")
=======
"""
AI Service Client - Comunica con el servicio de predicción de IA
"""
import logging
import requests
from typing import Dict, Optional
import config

logger = logging.getLogger(__name__)


class AIServiceClient:
    """Cliente para el servicio de predicción de IA"""
    
    def __init__(self, jwt_token: Optional[str] = None):
        self.base_url = config.AI_SERVICE_URL
        self.jwt_token = jwt_token
        self.session = requests.Session()
        logger.info(f"AI Service client initialized: {self.base_url}")
    
    def set_jwt_token(self, token: str):
        """Actualiza el JWT token"""
        self.jwt_token = token
    
    def predict_health(self, vital_signs: Dict) -> Optional[Dict]:
        """
        Envía signos vitales al modelo de IA para predicción
        
        Args:
            vital_signs: Dict con los signos vitales del paciente
            
        Returns:
            Dict con la predicción del modelo o None si falla
        """
        try:
            # Preparar payload para el modelo
            payload = {
                "gps_longitude": float(vital_signs["gps_longitude"]),
                "gps_latitude": float(vital_signs["gps_latitude"]),
                "heart_rate": float(vital_signs["heart_rate"]),
                "spo2": float(vital_signs["spo2"]),
                "systolic_bp": float(vital_signs["systolic_bp"]),
                "diastolic_bp": float(vital_signs["diastolic_bp"]),
                "temperature": float(vital_signs["temperature"])
            }
            
            # Headers con autenticación
            headers = {
                "Content-Type": "application/json",
                "X-Internal-Key": config.INTERNAL_SERVICE_KEY
            }
            # El internal key tiene precedencia sobre JWT
            # Si no hay internal key, usar JWT si está disponible
            if not config.INTERNAL_SERVICE_KEY and self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            # Llamar al servicio de IA
            response = self.session.post(
                f"{self.base_url}/predict",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                prediction = response.json()
                logger.debug(f"Prediction received for patient {vital_signs['patient_id']}")
                return {
                    **prediction,
                    "timestamp": vital_signs["timestamp"],
                    "patient_id": vital_signs["patient_id"],
                    "gps_latitude": vital_signs["gps_latitude"],
                    "gps_longitude": vital_signs["gps_longitude"]
                }
            else:
                logger.error(
                    f"AI Service error: {response.status_code} - {response.text}"
                )
                return None
                
        except requests.exceptions.Timeout:
            logger.error("AI Service timeout")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to AI Service")
            return None
        except Exception as e:
            logger.error(f"Error calling AI Service: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Verifica si el servicio de IA está operativo
        
        Returns:
            True si está operativo, False en caso contrario
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                is_healthy = data.get("status") == "healthy"
                model_loaded = data.get("model", {}).get("loaded", False)
                
                if is_healthy and model_loaded:
                    logger.info("AI Service is healthy and model is loaded")
                    return True
                else:
                    logger.warning(
                        f"AI Service status: {data.get('status')}, "
                        f"model loaded: {model_loaded}"
                    )
                    return False
            else:
                logger.warning(f"AI Service health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"AI Service health check error: {e}")
            return False
    
    def close(self):
        """Cierra la sesión HTTP"""
        if self.session:
            self.session.close()
            logger.info("AI Service client session closed")
>>>>>>> Stashed changes
