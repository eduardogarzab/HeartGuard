"""Helper para manejo de autenticación en pruebas Locust."""
import logging
from typing import Optional

import requests

from config import config

logger = logging.getLogger(__name__)


class AuthHelper:
    """Maneja la autenticación y renovación de tokens."""
    
    def __init__(self):
        self.staff_token: Optional[str] = None
        self.patient_token: Optional[str] = None
        self.staff_refresh_token: Optional[str] = None
        self.patient_refresh_token: Optional[str] = None
        self.staff_user_id: Optional[str] = None
        self.patient_user_id: Optional[str] = None
        self.staff_org_id: Optional[str] = None  # UUID de la organización del staff
        self.staff_org_code: Optional[str] = None  # Código de la organización (ej: FAM-001)
    
    def login_staff(self) -> Optional[str]:
        """
        Realiza login como usuario staff y almacena los tokens.
        
        Returns:
            Access token o None si falla
        """
        try:
            response = requests.post(
                f"{config.GATEWAY_HOST}/auth/login/user",
                json={
                    "email": config.STAFF_EMAIL,
                    "password": config.STAFF_PASSWORD
                },
                timeout=config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                self.staff_token = data.get("access_token")
                self.staff_refresh_token = data.get("refresh_token")
                
                # Obtener user_id del usuario autenticado
                try:
                    me_response = requests.get(
                        f"{config.GATEWAY_HOST}/auth/me",
                        headers={"Authorization": f"Bearer {self.staff_token}"},
                        timeout=config.REQUEST_TIMEOUT
                    )
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        self.staff_user_id = me_data.get("user_id")
                        logger.info(f"Staff user_id obtenido: {self.staff_user_id}")
                    
                    # Obtener org_id (UUID) de las membresías del usuario
                    org_response = requests.get(
                        f"{config.GATEWAY_HOST}/user/users/me/org-memberships",
                        headers={"Authorization": f"Bearer {self.staff_token}"},
                        timeout=config.REQUEST_TIMEOUT
                    )
                    if org_response.status_code == 200:
                        org_data = org_response.json()
                        memberships = org_data.get("data", {}).get("memberships", [])
                        if memberships:
                            # Tomar la primera organización (puede filtrar por config.TEST_ORG_CODE si necesario)
                            first_org = memberships[0]
                            self.staff_org_id = first_org.get("org_id")
                            self.staff_org_code = first_org.get("org_code")
                            logger.info(f"Staff org_id obtenido: {self.staff_org_id} ({self.staff_org_code})")
                except Exception as e:
                    logger.warning(f"No se pudo obtener user_id/org_id del staff: {e}")
                
                logger.info("Login staff exitoso")
                return self.staff_token
            else:
                logger.error(f"Login staff falló: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error en login staff: {e}")
            return None
    
    def login_patient(self) -> Optional[str]:
        """
        Realiza login como paciente y almacena los tokens.
        
        Returns:
            Access token o None si falla
        """
        try:
            response = requests.post(
                f"{config.GATEWAY_HOST}/auth/login/patient",
                json={
                    "email": config.PATIENT_EMAIL,
                    "password": config.PATIENT_PASSWORD
                },
                timeout=config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                self.patient_token = data.get("access_token")
                self.patient_refresh_token = data.get("refresh_token")
                
                # Obtener user_id del paciente autenticado
                try:
                    me_response = requests.get(
                        f"{config.GATEWAY_HOST}/auth/me",
                        headers={"Authorization": f"Bearer {self.patient_token}"},
                        timeout=config.REQUEST_TIMEOUT
                    )
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        self.patient_user_id = me_data.get("user_id") or me_data.get("patient_id")
                        logger.info(f"Patient user_id obtenido: {self.patient_user_id}")
                except Exception as e:
                    logger.warning(f"No se pudo obtener user_id del paciente: {e}")
                
                logger.info("Login paciente exitoso")
                return self.patient_token
            else:
                logger.error(f"Login paciente falló: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error en login paciente: {e}")
            return None
    
    def get_staff_headers(self) -> dict:
        """
        Retorna headers con token de staff.
        
        Returns:
            Dict con headers de autorización
        """
        if not self.staff_token:
            self.login_staff()
        
        return {
            "Authorization": f"Bearer {self.staff_token}",
            "Content-Type": "application/json"
        }
    
    def get_patient_headers(self) -> dict:
        """
        Retorna headers con token de paciente.
        
        Returns:
            Dict con headers de autorización
        """
        if not self.patient_token:
            self.login_patient()
        
        return {
            "Authorization": f"Bearer {self.patient_token}",
            "Content-Type": "application/json"
        }
    
    def refresh_staff_token(self) -> Optional[str]:
        """
        Refresca el token de staff.
        
        Returns:
            Nuevo access token o None si falla
        """
        if not self.staff_refresh_token:
            return self.login_staff()
        
        try:
            response = requests.post(
                f"{config.GATEWAY_HOST}/auth/refresh",
                json={"refresh_token": self.staff_refresh_token},
                timeout=config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                self.staff_token = data.get("access_token")
                return self.staff_token
            else:
                logger.warning("Refresh staff falló, haciendo login nuevamente")
                return self.login_staff()
        except Exception as e:
            logger.error(f"Error en refresh staff: {e}")
            return self.login_staff()
    
    def refresh_patient_token(self) -> Optional[str]:
        """
        Refresca el token de paciente.
        
        Returns:
            Nuevo access token o None si falla
        """
        if not self.patient_refresh_token:
            return self.login_patient()
        
        try:
            response = requests.post(
                f"{config.GATEWAY_HOST}/auth/refresh",
                json={"refresh_token": self.patient_refresh_token},
                timeout=config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                self.patient_token = data.get("access_token")
                return self.patient_token
            else:
                logger.warning("Refresh paciente falló, haciendo login nuevamente")
                return self.login_patient()
        except Exception as e:
            logger.error(f"Error en refresh paciente: {e}")
            return self.login_patient()


# Instancia global para reutilización
auth_helper = AuthHelper()
