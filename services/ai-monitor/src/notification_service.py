"""
Notification Service - Envía notificaciones a caregivers
"""
import logging
import requests
from typing import Dict, List
import config

logger = logging.getLogger(__name__)


class NotificationService:
    """Servicio para enviar notificaciones a caregivers"""
    
    def __init__(self):
        self.base_url = config.NOTIFICATION_SERVICE_URL
        self.enabled = config.ENABLE_NOTIFICATIONS
        self.session = requests.Session()
        
        if not self.enabled:
            logger.warning("Notifications are DISABLED")
        else:
            logger.info(f"Notification service initialized: {self.base_url}")
    
    def send_alert_notifications(
        self, 
        caregivers: List[Dict], 
        alert_info: Dict
    ) -> int:
        """
        Envía notificaciones a los cuidadores sobre una alerta
        
        Args:
            caregivers: Lista de cuidadores con preferencias
            alert_info: Información de la alerta
            
        Returns:
            Número de notificaciones enviadas exitosamente
        """
        if not self.enabled:
            logger.debug("Notifications disabled, skipping")
            return 0
        
        sent_count = 0
        
        for caregiver in caregivers:
            # Email
            if caregiver.get("notify_email"):
                if self._send_email(caregiver, alert_info):
                    sent_count += 1
            
            # SMS
            if caregiver.get("notify_sms") and caregiver.get("phone"):
                if self._send_sms(caregiver, alert_info):
                    sent_count += 1
            
            # Push notification
            if caregiver.get("notify_push"):
                if self._send_push(caregiver, alert_info):
                    sent_count += 1
        
        logger.info(f"Sent {sent_count} notifications for alert {alert_info.get('alert_id')}")
        return sent_count
    
    def _send_email(self, caregiver: Dict, alert_info: Dict) -> bool:
        """Envía notificación por email"""
        try:
            payload = {
                "to": caregiver["email"],
                "subject": f"⚠️ Alerta de Salud - {alert_info['alert_type']}",
                "body": self._format_email_body(caregiver, alert_info),
                "alert_id": alert_info.get("alert_id")
            }
            
            response = self.session.post(
                f"{self.base_url}/notifications/email",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Email sent to {caregiver['email']}")
                return True
            else:
                logger.warning(
                    f"Email failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _send_sms(self, caregiver: Dict, alert_info: Dict) -> bool:
        """Envía notificación por SMS"""
        try:
            payload = {
                "to": caregiver["phone"],
                "message": self._format_sms_message(alert_info),
                "alert_id": alert_info.get("alert_id")
            }
            
            response = self.session.post(
                f"{self.base_url}/notifications/sms",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"SMS sent to {caregiver['phone']}")
                return True
            else:
                logger.warning(
                    f"SMS failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    def _send_push(self, caregiver: Dict, alert_info: Dict) -> bool:
        """Envía notificación push"""
        try:
            payload = {
                "user_id": caregiver["user_id"],
                "title": f"⚠️ Alerta: {alert_info['alert_type']}",
                "body": alert_info["description"],
                "data": {
                    "alert_id": alert_info.get("alert_id"),
                    "patient_id": alert_info.get("patient_id"),
                    "severity": alert_info.get("severity"),
                    "type": alert_info.get("alert_type")
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/notifications/push",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Push notification sent to user {caregiver['user_id']}")
                return True
            else:
                logger.warning(
                    f"Push notification failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    def _format_email_body(self, caregiver: Dict, alert_info: Dict) -> str:
        """Formatea el cuerpo del email"""
        severity_emoji = {
            "low": "ℹ️",
            "medium": "⚠️",
            "high": "🚨",
            "critical": "🆘"
        }
        
        emoji = severity_emoji.get(alert_info.get("severity", "medium"), "⚠️")
        
        return f"""
Hola {caregiver['name']},

{emoji} Se ha detectado una alerta de salud para uno de tus pacientes.

Tipo de Alerta: {alert_info['alert_type']}
Severidad: {alert_info['severity'].upper()}
Descripción: {alert_info['description']}
Fecha/Hora: {alert_info['timestamp']}

Por favor, revisa la alerta en el panel de administración.

---
HeartGuard - Sistema de Monitoreo Cardiaco
Este es un mensaje automático, por favor no respondas a este correo.
        """.strip()
    
    def _format_sms_message(self, alert_info: Dict) -> str:
        """Formatea el mensaje SMS (máximo 160 caracteres)"""
        severity_emoji = {
            "low": "Info",
            "medium": "Atencion",
            "high": "URGENTE",
            "critical": "CRITICO"
        }
        
        severity_text = severity_emoji.get(alert_info.get("severity", "medium"), "Alerta")
        
        return (
            f"HeartGuard {severity_text}: {alert_info['alert_type']} - "
            f"{alert_info['description'][:80]}"
        )[:160]
    
    def close(self):
        """Cierra la sesión HTTP"""
        if self.session:
            self.session.close()
            logger.info("Notification service session closed")
