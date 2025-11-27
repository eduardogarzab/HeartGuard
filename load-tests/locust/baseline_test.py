"""
Baseline Test: Confirmar latencias estables bajo carga ligera.

Objetivo:
- Validar que los flujos principales funcionan correctamente
- Medir latencias base en condiciones normales
- Establecer métricas de referencia

Parámetros:
- Usuarios: 10
- Spawn rate: 2 usuarios/seg
- Duración: 5 minutos

Ejecución:
    locust -f baseline_test.py --host=http://129.212.181.53:8080 --users=10 --spawn-rate=2 --run-time=5m
"""
from locust import HttpUser, task, between, events
from auth_helper import auth_helper
from config import config
import logging

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicializa autenticación antes de comenzar las pruebas."""
    logger.info("Iniciando autenticación para baseline test...")
    auth_helper.login_staff()
    auth_helper.login_patient()
    logger.info("Autenticación completada")


class BaselineUser(HttpUser):
    """
    Usuario que ejecuta flujos principales con carga ligera.
    
    Incluye operaciones de lectura y escritura en proporciones realistas.
    """
    wait_time = between(1, 3)
    host = config.GATEWAY_HOST
    
    def on_start(self):
        """Inicialización del usuario."""
        self.staff_headers = auth_helper.get_staff_headers()
        self.patient_headers = auth_helper.get_patient_headers()
    
    @task(10)
    def health_check(self):
        """Health check - operación más frecuente."""
        self.client.get("/health/", name="/health")
    
    @task(8)
    def get_patient_dashboard(self):
        """Dashboard de paciente - lectura frecuente."""
        self.client.get(
            "/patient/dashboard",
            headers=self.patient_headers,
            name="/patient/dashboard"
        )
    
    @task(8)
    def get_patient_profile(self):
        """Perfil de paciente."""
        self.client.get(
            "/patient/profile",
            headers=self.patient_headers,
            name="/patient/profile"
        )
    
    @task(6)
    def get_patient_alerts(self):
        """Alertas de paciente."""
        self.client.get(
            "/patient/alerts",
            headers=self.patient_headers,
            params={"status": "active", "limit": 10},
            name="/patient/alerts"
        )
    
    @task(6)
    def get_patient_devices(self):
        """Dispositivos del paciente."""
        self.client.get(
            "/patient/devices",
            headers=self.patient_headers,
            name="/patient/devices"
        )
    
    @task(5)
    def get_patient_caregivers(self):
        """Cuidadores del paciente."""
        self.client.get(
            "/patient/caregivers",
            headers=self.patient_headers,
            name="/patient/caregivers"
        )
    
    @task(5)
    def get_patient_care_team(self):
        """Equipo de cuidado."""
        self.client.get(
            "/patient/care-team",
            headers=self.patient_headers,
            name="/patient/care-team"
        )
    
    @task(4)
    def get_patient_latest_location(self):
        """Última ubicación del paciente."""
        self.client.get(
            "/patient/location/latest",
            headers=self.patient_headers,
            name="/patient/location/latest"
        )
    
    @task(7)
    def get_user_me(self):
        """Información del usuario autenticado."""
        self.client.get(
            "/user/users/me",
            headers=self.staff_headers,
            name="/user/users/me"
        )
    
    @task(5)
    def get_user_memberships(self):
        """Membresías de organización."""
        self.client.get(
            "/user/users/me/org-memberships",
            headers=self.staff_headers,
            name="/user/users/me/org-memberships"
        )
    
    @task(6)
    def get_org_dashboard(self):
        """Dashboard de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/dashboard",
            headers=self.staff_headers,
            name="/user/orgs/[org_id]/dashboard"
        )
    
    @task(4)
    def get_org_care_teams(self):
        """Care teams de la organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-teams",
            headers=self.staff_headers,
            name="/user/orgs/[org_id]/care-teams"
        )
    
    @task(5)
    def get_org_devices(self):
        """Dispositivos de la organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/devices",
            headers=self.staff_headers,
            name="/user/orgs/[org_id]/devices"
        )
    
    @task(3)
    def get_caregiver_patients(self):
        """Pacientes del cuidador."""
        self.client.get(
            "/user/caregiver/patients",
            headers=self.staff_headers,
            name="/user/caregiver/patients"
        )
    
    @task(2)
    def verify_token(self):
        """Verificación de token."""
        self.client.get(
            "/auth/verify",
            headers=self.staff_headers,
            name="/auth/verify"
        )
    
    @task(3)
    def get_realtime_status(self):
        """Estado del servicio de realtime."""
        self.client.get(
            "/realtime/status",
            headers=self.staff_headers,
            name="/realtime/status"
        )
    
    @task(2)
    def get_ai_model_info(self):
        """Información del modelo de IA."""
        self.client.get(
            "/ai/model/info",
            headers=self.staff_headers,
            name="/ai/model/info"
        )
    
    @task(1)
    def get_patient_readings(self):
        """Lecturas del paciente - operación menos frecuente."""
        self.client.get(
            "/patient/readings",
            headers=self.patient_headers,
            params={"limit": 20},
            name="/patient/readings"
        )
