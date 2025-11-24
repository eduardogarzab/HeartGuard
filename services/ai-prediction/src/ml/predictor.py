"""
Lógica de predicción y generación de alertas
"""
import logging
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime

from .model_loader import ModelLoader
from ..config import (
    MODEL_FEATURES,
    API_TO_MODEL_MAPPING,
    DEFAULT_THRESHOLD,
    SEVERITY_LEVELS,
    ALERT_TYPES
)

logger = logging.getLogger(__name__)


class HealthPredictor:
    """Predictor de problemas de salud usando el modelo ML"""
    
    def __init__(self):
        self.model_loader = ModelLoader()
    
    def predict(
        self,
        vital_signs: Dict[str, float],
        threshold: float = DEFAULT_THRESHOLD
    ) -> Dict:
        """
        Predice si hay un problema de salud basado en signos vitales
        
        Args:
            vital_signs: Diccionario con los signos vitales
                {
                    "gps_longitude": -99.1332,
                    "gps_latitude": 19.4326,
                    "heart_rate": 75,
                    "spo2": 98,
                    "systolic_bp": 120,
                    "diastolic_bp": 80,
                    "temperature": 36.7
                }
            threshold: Umbral de probabilidad para clasificar como problema
            
        Returns:
            Diccionario con la predicción:
                {
                    "has_problem": bool,
                    "probability": float,
                    "alerts": List[Dict],
                    "processed_at": str
                }
        """
        # Validar que el modelo esté cargado
        if not self.model_loader.is_loaded():
            raise RuntimeError("Modelo no está cargado")
        
        # Preparar features en el orden correcto
        features_df = self._prepare_features(vital_signs)
        
        # Realizar predicción
        model = self.model_loader.get_model()
        proba = model.predict_proba(features_df)[0][1]  # Probabilidad de clase 1 (problema)
        has_problem = proba >= threshold
        
        logger.info(
            f"Predicción: proba={proba:.3f}, threshold={threshold}, "
            f"has_problem={has_problem}"
        )
        
        # Generar alertas si hay problema
        alerts = []
        if has_problem:
            alerts = self._generate_alerts(vital_signs, proba)
        
        return {
            "has_problem": bool(has_problem),
            "probability": round(float(proba), 4),
            "alerts": alerts,
            "processed_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def batch_predict(
        self,
        readings: List[Dict],
        threshold: float = DEFAULT_THRESHOLD
    ) -> Dict:
        """
        Realiza predicciones en lote
        
        Args:
            readings: Lista de diccionarios con signos vitales
            threshold: Umbral de probabilidad
            
        Returns:
            Diccionario con predicciones y resumen:
                {
                    "predictions": List[Dict],
                    "summary": {
                        "total": int,
                        "problems_detected": int,
                        "avg_probability": float
                    }
                }
        """
        predictions = []
        total_proba = 0.0
        problems_count = 0
        
        for reading in readings:
            try:
                pred = self.predict(reading, threshold)
                predictions.append({
                    "timestamp": reading.get("timestamp"),
                    **pred
                })
                total_proba += pred["probability"]
                if pred["has_problem"]:
                    problems_count += 1
            except Exception as e:
                logger.error(f"Error en predicción de lote: {e}")
                predictions.append({
                    "timestamp": reading.get("timestamp"),
                    "error": str(e)
                })
        
        total = len(predictions)
        avg_proba = total_proba / total if total > 0 else 0.0
        
        return {
            "predictions": predictions,
            "summary": {
                "total": total,
                "problems_detected": problems_count,
                "avg_probability": round(avg_proba, 4)
            }
        }
    
    def _prepare_features(self, vital_signs: Dict[str, float]) -> pd.DataFrame:
        """
        Prepara las features en el formato correcto para el modelo
        
        Args:
            vital_signs: Diccionario con signos vitales (nombres de API)
            
        Returns:
            DataFrame con las features en el orden correcto
        """
        # Mapear nombres de API a nombres del modelo
        features_dict = {}
        for api_name, model_name in API_TO_MODEL_MAPPING.items():
            if api_name not in vital_signs:
                raise ValueError(f"Falta el campo requerido: {api_name}")
            features_dict[model_name] = vital_signs[api_name]
        
        # Crear DataFrame con el orden correcto de columnas
        df = pd.DataFrame([features_dict], columns=MODEL_FEATURES)
        
        return df
    
    def _generate_alerts(
        self,
        vital_signs: Dict[str, float],
        probability: float
    ) -> List[Dict]:
        """
        Genera alertas basadas en los signos vitales y la probabilidad
        
        Args:
            vital_signs: Diccionario con signos vitales
            probability: Probabilidad de problema detectado
            
        Returns:
            Lista de alertas
        """
        alerts = []
        severity = self._get_severity(probability)
        
        # Alerta general del modelo
        alerts.append({
            "type": "GENERAL_RISK",
            "severity": severity,
            "message": ALERT_TYPES["GENERAL_RISK"],
            "probability": round(probability, 4)
        })
        
        # Alertas específicas basadas en rangos clínicos
        hr = vital_signs.get("heart_rate", 0)
        spo2 = vital_signs.get("spo2", 0)
        sbp = vital_signs.get("systolic_bp", 0)
        dbp = vital_signs.get("diastolic_bp", 0)
        temp = vital_signs.get("temperature", 0)
        
        # Frecuencia cardíaca anormal
        if hr < 60 or hr > 100:
            alerts.append({
                "type": "ARRHYTHMIA",
                "severity": "high" if hr < 50 or hr > 120 else "medium",
                "message": ALERT_TYPES["ARRHYTHMIA"],
                "value": hr,
                "unit": "bpm"
            })
        
        # Saturación de oxígeno baja
        if spo2 < 95:
            alerts.append({
                "type": "DESAT",
                "severity": "high" if spo2 < 90 else "medium",
                "message": ALERT_TYPES["DESAT"],
                "value": spo2,
                "unit": "%"
            })
        
        # Hipertensión
        if sbp >= 140 or dbp >= 90:
            alerts.append({
                "type": "HYPERTENSION",
                "severity": "high" if sbp >= 160 or dbp >= 100 else "medium",
                "message": ALERT_TYPES["HYPERTENSION"],
                "value": f"{sbp}/{dbp}",
                "unit": "mmHg"
            })
        
        # Hipotensión
        if sbp < 90 or dbp < 60:
            alerts.append({
                "type": "HYPOTENSION",
                "severity": "high",
                "message": ALERT_TYPES["HYPOTENSION"],
                "value": f"{sbp}/{dbp}",
                "unit": "mmHg"
            })
        
        # Fiebre
        if temp >= 38.0:
            alerts.append({
                "type": "FEVER",
                "severity": "high" if temp >= 39.0 else "medium",
                "message": ALERT_TYPES["FEVER"],
                "value": temp,
                "unit": "°C"
            })
        
        # Hipotermia
        if temp < 36.0:
            alerts.append({
                "type": "HYPOTHERMIA",
                "severity": "high" if temp < 35.0 else "medium",
                "message": ALERT_TYPES["HYPOTHERMIA"],
                "value": temp,
                "unit": "°C"
            })
        
        return alerts
    
    def _get_severity(self, probability: float) -> str:
        """
        Determina el nivel de severidad basado en la probabilidad
        
        Args:
            probability: Probabilidad del problema (0-1)
            
        Returns:
            Nivel de severidad: "low", "medium", "high"
        """
        for level, (min_p, max_p) in SEVERITY_LEVELS.items():
            if min_p <= probability < max_p:
                return level
        return "high"  # Por defecto si >= 1.0
