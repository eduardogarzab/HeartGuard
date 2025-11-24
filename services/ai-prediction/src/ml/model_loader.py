"""
Cargador del modelo de Machine Learning
Maneja la carga, caché y validación del modelo RandomForest
"""
import joblib
import logging
from pathlib import Path
from typing import Optional
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)


class ModelLoader:
    """Singleton para cargar y cachear el modelo ML"""
    
    _instance: Optional['ModelLoader'] = None
    _model: Optional[RandomForestClassifier] = None
    _model_path: Optional[Path] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self, model_path: Path) -> RandomForestClassifier:
        """
        Carga el modelo desde disco (con caché)
        
        Args:
            model_path: Ruta al archivo .pkl del modelo
            
        Returns:
            Modelo RandomForest cargado
            
        Raises:
            FileNotFoundError: Si el archivo del modelo no existe
            Exception: Si hay error cargando el modelo
        """
        # Si ya está cargado y es el mismo path, retornar del caché
        if self._model is not None and self._model_path == model_path:
            logger.info(f"Usando modelo en caché: {model_path}")
            return self._model
        
        # Validar que el archivo existe
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
        
        try:
            logger.info(f"Cargando modelo desde: {model_path}")
            self._model = joblib.load(model_path)
            self._model_path = model_path
            
            # Validar que es un RandomForestClassifier
            if not isinstance(self._model, RandomForestClassifier):
                raise TypeError(
                    f"El modelo debe ser RandomForestClassifier, "
                    f"obtenido: {type(self._model)}"
                )
            
            logger.info(
                f"Modelo cargado exitosamente: "
                f"{self._model.n_estimators} estimadores, "
                f"{self._model.n_features_in_} features"
            )
            
            return self._model
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            raise
    
    def get_model(self) -> Optional[RandomForestClassifier]:
        """
        Retorna el modelo cargado (si existe)
        
        Returns:
            Modelo o None si no está cargado
        """
        return self._model
    
    def reload_model(self, model_path: Path) -> RandomForestClassifier:
        """
        Fuerza la recarga del modelo (útil para actualizaciones)
        
        Args:
            model_path: Ruta al archivo .pkl del modelo
            
        Returns:
            Modelo recargado
        """
        logger.info("Forzando recarga del modelo...")
        self._model = None
        self._model_path = None
        return self.load_model(model_path)
    
    def is_loaded(self) -> bool:
        """Verifica si hay un modelo cargado"""
        return self._model is not None
    
    def get_model_info(self) -> dict:
        """
        Retorna información del modelo cargado
        
        Returns:
            Diccionario con información del modelo
        """
        if not self.is_loaded():
            return {"loaded": False}
        
        return {
            "loaded": True,
            "model_path": str(self._model_path),
            "model_type": type(self._model).__name__,
            "n_estimators": self._model.n_estimators,
            "n_features": self._model.n_features_in_,
            "max_depth": self._model.max_depth,
            "random_state": self._model.random_state
        }
