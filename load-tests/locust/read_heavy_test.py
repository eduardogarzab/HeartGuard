"""
Read-Heavy Test: Validar comportamiento con predominancia de operaciones de lectura.

Objetivo:
- Medir rendimiento de operaciones GET intensivas
- Validar cache y optimizaciones de lectura
- Simular usuarios consultando dashboards y catálogos

Parámetros:
- Usuarios: 50
- Spawn rate: 5 usuarios/seg
- Duración: 10 minutos

Ejecución:
    locust -f read_heavy_test.py --host=http://129.212.181.53:8080 --users=50 --spawn-rate=5 --run-time=10m
"""
from locust import HttpUser, task, between, events
from auth_helper import auth_helper
from config import config
import logging

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicializa autenticación antes de comenzar las pruebas."""
    logger.info("Iniciando read-heavy test...")
    auth_helper.login_staff()
    auth_helper.login_patient()


class ReadHeavyUser(HttpUser):
    """
    Usuario que predominantemente realiza operaciones de lectura.
    
    Ratio 95% lecturas, 5% verificaciones.
    """
    wait_time = between(0.5, 2)
    host = config.GATEWAY_HOST
    
    def on_start(self):
        """Inicialización del usuario."""
        self.staff_headers = auth_helper.get_staff_headers()
        self.patient_headers = auth_helper.get_patient_headers()
    
    # ========== Lecturas de Paciente (35%) ==========
    
    @task(10)
    def patient_dashboard(self):
        """Dashboard del paciente."""
        self.client.get(
            "/patient/dashboard",
            headers=self.patient_headers,
            name="[READ] Patient Dashboard"
        )
    
    @task(8)
    def patient_profile(self):
        """Perfil del paciente."""
        self.client.get(
            "/patient/profile",
            headers=self.patient_headers,
            name="[READ] Patient Profile"
        )
    
    @task(7)
    def patient_alerts(self):
        """Alertas del paciente."""
        self.client.get(
            "/patient/alerts",
            headers=self.patient_headers,
            params={"status": "active", "limit": 20},
            name="[READ] Patient Alerts"
        )
    
    @task(6)
    def patient_devices(self):
        """Dispositivos del paciente."""
        self.client.get(
            "/patient/devices",
            headers=self.patient_headers,
            name="[READ] Patient Devices"
        )
    
    @task(5)
    def patient_caregivers(self):
        """Cuidadores del paciente."""
        self.client.get(
            "/patient/caregivers",
            headers=self.patient_headers,
            name="[READ] Patient Caregivers"
        )
    
    @task(4)
    def patient_care_team(self):
        """Equipo de cuidado."""
        self.client.get(
            "/patient/care-team",
            headers=self.patient_headers,
            name="[READ] Patient Care Team"
        )
    
    @task(5)
    def patient_latest_location(self):
        """Última ubicación."""
        self.client.get(
            "/patient/location/latest",
            headers=self.patient_headers,
            name="[READ] Patient Latest Location"
        )
    
    @task(3)
    def patient_locations(self):
        """Historial de ubicaciones."""
        self.client.get(
            "/patient/locations",
            headers=self.patient_headers,
            params={"limit": 50},
            name="[READ] Patient Locations"
        )
    
    @task(4)
    def patient_readings(self):
        """Historial de lecturas."""
        self.client.get(
            "/patient/readings",
            headers=self.patient_headers,
            params={"limit": 30},
            name="[READ] Patient Readings"
        )
    
    # ========== Lecturas de Usuario/Staff (35%) ==========
    
    @task(8)
    def user_me(self):
        """Información del usuario."""
        self.client.get(
            "/user/users/me",
            headers=self.staff_headers,
            name="[READ] User Me"
        )
    
    @task(6)
    def user_memberships(self):
        """Membresías de organización."""
        self.client.get(
            "/user/users/me/org-memberships",
            headers=self.staff_headers,
            name="[READ] User Memberships"
        )
    
    @task(5)
    def user_invitations(self):
        """Invitaciones pendientes."""
        self.client.get(
            "/user/users/me/invitations",
            headers=self.staff_headers,
            name="[READ] User Invitations"
        )
    
    @task(9)
    def org_dashboard(self):
        """Dashboard de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/dashboard",
            headers=self.staff_headers,
            name="[READ] Org Dashboard"
        )
    
    @task(7)
    def org_care_teams(self):
        """Care teams de la organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-teams",
            headers=self.staff_headers,
            name="[READ] Org Care Teams"
        )
    
    @task(6)
    def org_care_team_patients(self):
        """Pacientes por care team."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-team-patients",
            headers=self.staff_headers,
            name="[READ] Org Care Team Patients"
        )
    
    @task(5)
    def org_care_team_patients_locations(self):
        """Ubicaciones de pacientes por care team."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-team-patients/locations",
            headers=self.staff_headers,
            name="[READ] Org Care Team Patients Locations"
        )
    
    @task(7)
    def org_devices(self):
        """Dispositivos de la organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/devices",
            headers=self.staff_headers,
            name="[READ] Org Devices"
        )
    
    @task(4)
    def org_device_detail(self):
        """Detalle de dispositivo."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/devices/{config.TEST_DEVICE_ID}",
            headers=self.staff_headers,
            name="[READ] Org Device Detail"
        )
    
    @task(5)
    def org_patient_detail(self):
        """Detalle de paciente."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}",
            headers=self.staff_headers,
            name="[READ] Org Patient Detail"
        )
    
    @task(6)
    def org_patient_alerts(self):
        """Alertas de paciente."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts",
            headers=self.staff_headers,
            params={"limit": 20},
            name="[READ] Org Patient Alerts"
        )
    
    @task(4)
    def org_metrics(self):
        """Métricas de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/metrics",
            headers=self.staff_headers,
            name="[READ] Org Metrics"
        )
    
    # ========== Lecturas Adicionales de Organización (15%) ==========
    
    @task(6)
    def org_patient_alerts_list(self):
        """Lista de alertas de paciente a nivel org."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts",
            headers=self.staff_headers,
            name="[READ] Org Patient Alerts List"
        )
    
    @task(5)
    def org_patient_notes(self):
        """Notas de paciente a nivel org."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/notes",
            headers=self.staff_headers,
            name="[READ] Org Patient Notes"
        )
    
    @task(4)
    def org_patient_devices_list(self):
        """Dispositivos del paciente a nivel org."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/devices",
            headers=self.staff_headers,
            name="[READ] Org Patient Devices"
        )
    
    @task(3)
    def org_care_team_patients_list(self):
        """Lista de pacientes por care team."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-team-patients",
            headers=self.staff_headers,
            name="[READ] Org Care Team Patients List"
        )
    
    @task(3)
    def org_user_memberships(self):
        """Membresías del usuario actual."""
        self.client.get(
            "/user/users/me/org-memberships",
            headers=self.staff_headers,
            name="[READ] User Org Memberships"
        )
    
    # ========== Lecturas de Catálogos (10%) ==========
    
    @task(3)
    def event_types(self):
        """Tipos de eventos."""
        self.client.get(
            "/user/event-types",
            headers=self.staff_headers,
            name="[READ] Event Types"
        )
    
    @task(2)
    def realtime_status(self):
        """Estado del servicio realtime."""
        self.client.get(
            "/realtime/status",
            headers=self.staff_headers,
            name="[READ] Realtime Status"
        )
    
    @task(2)
    def realtime_patients(self):
        """Pacientes monitoreados."""
        self.client.get(
            "/realtime/patients",
            headers=self.staff_headers,
            name="[READ] Realtime Patients"
        )
    
    @task(2)
    def ai_model_info(self):
        """Información del modelo de IA."""
        self.client.get(
            "/ai/model/info",
            headers=self.staff_headers,
            name="[READ] AI Model Info"
        )
    
    # ========== Verificaciones mínimas (5%) ==========
    
    @task(2)
    def health_check(self):
        """Health check."""
        self.client.get("/health/", name="[READ] Health")
    
    @task(1)
    def verify_token(self):
        """Verificar token."""
        self.client.get(
            "/auth/verify",
            headers=self.staff_headers,
            name="[READ] Auth Verify"
        )
