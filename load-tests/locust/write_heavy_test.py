"""
Write-Heavy Test: Validar operaciones POST idempotentes bajo concurrencia moderada.

Objetivo:
- Validar operaciones de escritura/actualización
- Verificar consistencia bajo concurrencia
- Medir latencias de operaciones POST/PATCH

Parámetros:
- Usuarios: 30
- Spawn rate: 3 usuarios/seg
- Duración: 8 minutos

Ejecución:
    locust -f write_heavy_test.py --host=http://129.212.181.53:8080 --users=30 --spawn-rate=3 --run-time=8m
"""
from locust import HttpUser, task, between, events
from auth_helper import auth_helper
from config import config
import logging
import random
import string
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicializa autenticación antes de comenzar las pruebas."""
    logger.info("Iniciando write-heavy test...")
    auth_helper.login_staff()
    auth_helper.login_patient()


def random_string(length=8):
    """Genera string aleatorio."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


class WriteHeavyUser(HttpUser):
    """
    Usuario que predominantemente realiza operaciones de escritura.
    
    Ratio 70% escrituras, 30% lecturas de verificación.
    """
    wait_time = between(1, 3)
    host = config.GATEWAY_HOST
    
    def on_start(self):
        """Inicialización del usuario."""
        self.staff_headers = auth_helper.get_staff_headers()
        self.patient_headers = auth_helper.get_patient_headers()
    
    # ========== Operaciones de Escritura - Alertas (25%) ==========
    
    @task(8)
    def acknowledge_patient_alert(self):
        """Reconocer alerta de paciente (POST idempotente)."""
        self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/acknowledge",
            headers=self.staff_headers,
            json={
                "acknowledged_by": auth_helper.staff_user_id,
                "notes": f"Alert acknowledged at {datetime.now(timezone.utc).isoformat()}"
            },
            name="[WRITE] Acknowledge Patient Alert"
        )
    
    @task(6)
    def resolve_patient_alert(self):
        """Resolver alerta de paciente (POST idempotente)."""
        self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/resolve",
            headers=self.staff_headers,
            json={
                "resolved_by": auth_helper.staff_user_id,
                "resolution_notes": f"Resolved at {datetime.now(timezone.utc).isoformat()}"
            },
            name="[WRITE] Resolve Patient Alert"
        )
    
    @task(5)
    def acknowledge_patient_alert_again(self):
        """Reconocer misma alerta otra vez (POST idempotente)."""
        self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/acknowledge",
            headers=self.staff_headers,
            json={
                "acknowledged_by": auth_helper.staff_user_id,
                "notes": f"Alert re-ack {datetime.now(timezone.utc).isoformat()}"
            },
            name="[WRITE] Acknowledge Patient Alert Again"
        )
    
    @task(4)
    def resolve_patient_alert_again(self):
        """Resolver misma alerta otra vez (POST idempotente)."""
        self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/resolve",
            headers=self.staff_headers,
            json={
                "resolved_by": auth_helper.staff_user_id,
                "resolution_notes": f"Re-resolved {datetime.now(timezone.utc).isoformat()}"
            },
            name="[WRITE] Resolve Patient Alert Again"
        )
    
    # ========== Operaciones de Escritura - Perfil (20%) ==========
    
    @task(10)
    def update_user_profile(self):
        """Actualizar perfil de usuario (PATCH) - campos válidos: name, profile_photo_url, two_factor_enabled."""
        self.client.patch(
            "/user/users/me",
            headers=self.staff_headers,
            json={
                "name": f"Ana Ruiz {random.randint(1, 100)}"
            },
            name="[WRITE] Update User Profile"
        )
    
    @task(7)
    def read_patient_dashboard(self):
        """Leer dashboard del paciente (GET) - reemplaza update_patient_profile que no existe."""
        self.client.get(
            "/patient/dashboard",
            headers=self.patient_headers,
            name="[READ] Patient Dashboard"
        )
    
    # ========== Operaciones de Escritura - Push Devices (15%) ==========
    
    @task(8)
    def register_push_device(self):
        """Registrar dispositivo push (POST) - campos requeridos: platform_code, push_token."""
        self.client.post(
            "/user/users/me/push-devices",
            headers=self.staff_headers,
            json={
                "push_token": f"token-{random_string(32)}",
                "platform_code": random.choice(["ios", "android"])
            },
            name="[WRITE] Register Push Device"
        )
    
    @task(5)
    def update_push_device(self):
        """Actualizar dispositivo push existente (PATCH) - usa active en lugar de enabled."""
        self.client.patch(
            f"/user/users/me/push-devices/{config.TEST_PUSH_DEVICE_ID}",
            headers=self.staff_headers,
            json={
                "active": random.choice([True, False])
            },
            name="[WRITE] Update Push Device"
        )
    
    # ========== Operaciones de Escritura - Admin (15%) ==========
    
    @task(5)
    def admin_acknowledge_alert(self):
        """Admin reconoce alerta (POST)."""
        self.client.post(
            f"/admin/organizations/{auth_helper.staff_org_id}/alerts/{config.TEST_ALERT_ID}/ack",
            headers=self.staff_headers,
            json={
                "acknowledged_by": auth_helper.staff_user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            name="[WRITE] Admin Acknowledge Alert"
        )
    
    @task(4)
    def admin_resolve_alert(self):
        """Admin resuelve alerta (POST)."""
        self.client.post(
            f"/admin/organizations/{auth_helper.staff_org_id}/alerts/{config.TEST_ALERT_ID}/resolve",
            headers=self.staff_headers,
            json={
                "resolved_by": auth_helper.staff_user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            name="[WRITE] Admin Resolve Alert"
        )
    
    @task(3)
    def admin_acknowledge_alert_again(self):
        """Admin reconoce la misma alerta de nuevo (POST)."""
        self.client.post(
            f"/admin/organizations/{auth_helper.staff_org_id}/alerts/{config.TEST_ALERT_ID}/ack",
            headers=self.staff_headers,
            json={
                "acknowledged_by": auth_helper.staff_user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            name="[WRITE] Admin Acknowledge Alert Again"
        )
    
    # ========== Lecturas de Verificación (30%) ==========
    
    @task(8)
    def verify_patient_alerts(self):
        """Verificar alertas de paciente."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts",
            headers=self.staff_headers,
            params={"limit": 10},
            name="[READ] Verify Patient Alerts"
        )
    
    @task(6)
    def verify_user_profile(self):
        """Verificar perfil de usuario."""
        self.client.get(
            "/user/users/me",
            headers=self.staff_headers,
            name="[READ] Verify User Profile"
        )
    
    @task(5)
    def verify_patient_profile(self):
        """Verificar perfil de paciente."""
        self.client.get(
            "/patient/profile",
            headers=self.patient_headers,
            name="[READ] Verify Patient Profile"
        )
    
    @task(4)
    def verify_push_devices(self):
        """Verificar dispositivos push."""
        self.client.get(
            "/user/users/me/push-devices",
            headers=self.staff_headers,
            name="[READ] Verify Push Devices"
        )
    
    @task(4)
    def verify_invitations(self):
        """Verificar invitaciones."""
        self.client.get(
            "/user/users/me/invitations",
            headers=self.staff_headers,
            name="[READ] Verify Invitations"
        )
    
    @task(3)
    def verify_org_patient_notes(self):
        """Verificar notas de paciente a nivel org."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/notes",
            headers=self.staff_headers,
            name="[READ] Verify Org Patient Notes"
        )
