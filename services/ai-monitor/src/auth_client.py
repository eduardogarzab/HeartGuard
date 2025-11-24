"""
Auth Client - Obtiene JWT tokens del servicio de autenticación
"""
import logging
import requests
from typing import Optional
import config

logger = logging.getLogger(__name__)


class AuthClient:
    """Cliente para obtener tokens de autenticación"""
    
    def __init__(self):
        self.base_url = config.AUTH_SERVICE_URL
        self.internal_key = config.INTERNAL_SERVICE_KEY
        self.session = requests.Session()
        self.current_token = None
        logger.info(f"Auth client initialized: {self.base_url}")
    
    def get_service_token(self) -> Optional[str]:
        """
        Obtiene un JWT token para comunicación entre servicios
        
        Returns:
            JWT token o None si falla
        """
        try:
            # Usar endpoint especial para servicios internos
            response = self.session.post(
                f"{self.base_url}/auth/token/service",
                json={
                    "service_name": "ai-monitor",
                    "internal_key": self.internal_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_token = data.get("access_token")
                logger.info("Service token obtained successfully")
                return self.current_token
            else:
                logger.error(
                    f"Failed to get service token: {response.status_code} - "
                    f"{response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error getting service token: {e}")
            return None
    
    def refresh_token_if_needed(self) -> Optional[str]:
        """
        Refresca el token si es necesario
        
        Returns:
            JWT token actual o renovado
        """
        # Por simplicidad, siempre obtener uno nuevo
        # En producción, verificar expiración antes
        return self.get_service_token()
    
    def close(self):
        """Cierra la sesión HTTP"""
        if self.session:
            self.session.close()
            logger.info("Auth client session closed")
