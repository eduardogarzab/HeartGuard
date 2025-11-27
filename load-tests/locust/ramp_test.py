"""
Ramp Test: Observar degradación gradual cuando la carga crece y decrece.

Objetivo:
- Identificar punto donde surgen fallos o latencias elevadas
- Observar comportamiento bajo carga creciente/decreciente
- Validar recuperación después de carga alta

Parámetros:
- Usuarios máximos: 100
- Spawn rate: 5 usuarios/seg
- Duración: 15 minutos (ramp up + plateau + ramp down)

Ejecución:
    locust -f ramp_test.py --host=http://129.212.181.53:8080 --users=100 --spawn-rate=5 --run-time=15m
    
Fases:
    1. Ramp Up: 0 -> 100 usuarios en 20 segundos
    2. Plateau: 100 usuarios por 10 minutos
    3. Ramp Down: 100 -> 0 usuarios (natural decay)
"""
from locust import HttpUser, task, between, events, LoadTestShape
from auth_helper import auth_helper
from config import config
import logging

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicializa autenticación antes de comenzar las pruebas."""
    logger.info("Iniciando ramp test...")
    auth_helper.login_staff()
    auth_helper.login_patient()


class RampLoadShape(LoadTestShape):
    """
    Define la forma de carga para el ramp test.
    
    Fases:
    - 0-3 min: Ramp up de 0 a 100 usuarios
    - 3-13 min: Mantener 100 usuarios
    - 13-15 min: Ramp down de 100 a 20 usuarios
    """
    
    stages = [
        # Ramp Up: 0 -> 100 usuarios en 3 minutos
        {"duration": 60, "users": 20, "spawn_rate": 5},
        {"duration": 120, "users": 50, "spawn_rate": 5},
        {"duration": 180, "users": 100, "spawn_rate": 5},
        
        # Plateau: Mantener 100 usuarios por 10 minutos
        {"duration": 780, "users": 100, "spawn_rate": 5},
        
        # Ramp Down: 100 -> 20 usuarios en 2 minutos
        {"duration": 840, "users": 50, "spawn_rate": 10},
        {"duration": 900, "users": 20, "spawn_rate": 10},
    ]
    
    def tick(self):
        """Define cuántos usuarios deben estar activos en cada momento."""
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None


class RampTestUser(HttpUser):
    """
    Usuario para ramp test - mix balanceado de operaciones.
    
    Incluye lecturas y escrituras para observar comportamiento integral.
    """
    wait_time = between(1, 3)
    host = config.GATEWAY_HOST
    
    def on_start(self):
        """Inicialización del usuario."""
        self.staff_headers = auth_helper.get_staff_headers()
        self.patient_headers = auth_helper.get_patient_headers()
    
    # ========== Health Checks (10%) ==========
    
    @task(5)
    def health_check(self):
        """Health check del gateway."""
        self.client.get("/health/", name="[HEALTH] Gateway")
    
    @task(2)
    def realtime_health(self):
        """Health check realtime."""
        self.client.get("/realtime/health", name="[HEALTH] Realtime")
    
    @task(2)
    def ai_health(self):
        """Health check IA."""
        self.client.get("/ai/health", name="[HEALTH] AI")
    
    # ========== Lecturas Críticas (40%) ==========
    
    @task(10)
    def patient_dashboard(self):
        """Dashboard de paciente."""
        self.client.get(
            "/patient/dashboard",
            headers=self.patient_headers,
            name="[READ] Patient Dashboard"
        )
    
    @task(8)
    def org_dashboard(self):
        """Dashboard de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/dashboard",
            headers=self.staff_headers,
            name="[READ] Org Dashboard"
        )
    
    @task(7)
    def patient_alerts(self):
        """Alertas de paciente."""
        self.client.get(
            "/patient/alerts",
            headers=self.patient_headers,
            params={"status": "active", "limit": 20},
            name="[READ] Patient Alerts"
        )
    
    @task(6)
    def org_care_teams(self):
        """Care teams."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-teams",
            headers=self.staff_headers,
            name="[READ] Org Care Teams"
        )
    
    @task(5)
    def patient_devices(self):
        """Dispositivos de paciente."""
        self.client.get(
            "/patient/devices",
            headers=self.patient_headers,
            name="[READ] Patient Devices"
        )
    
    @task(4)
    def user_me(self):
        """Información de usuario."""
        self.client.get(
            "/user/users/me",
            headers=self.staff_headers,
            name="[READ] User Me"
        )
    
    # ========== Lecturas Complementarias (25%) ==========
    
    @task(5)
    def patient_profile(self):
        """Perfil de paciente."""
        self.client.get(
            "/patient/profile",
            headers=self.patient_headers,
            name="[READ] Patient Profile"
        )
    
    @task(4)
    def patient_caregivers(self):
        """Cuidadores."""
        self.client.get(
            "/patient/caregivers",
            headers=self.patient_headers,
            name="[READ] Patient Caregivers"
        )
    
    @task(4)
    def org_devices(self):
        """Dispositivos de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/devices",
            headers=self.staff_headers,
            name="[READ] Org Devices"
        )
    
    @task(3)
    def org_patient_detail(self):
        """Detalle de paciente de la organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}",
            headers=self.staff_headers,
            name="[READ] Org Patient Detail"
        )
    
    @task(3)
    def patient_latest_location(self):
        """Última ubicación."""
        self.client.get(
            "/patient/location/latest",
            headers=self.patient_headers,
            name="[READ] Patient Latest Location"
        )
    
    @task(2)
    def org_metrics(self):
        """Métricas de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/metrics",
            headers=self.staff_headers,
            name="[READ] Org Metrics"
        )
    
    # ========== Escrituras (20%) ==========
    
    @task(6)
    def acknowledge_alert(self):
        """Reconocer alerta."""
        from datetime import datetime, timezone
        self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/acknowledge",
            headers=self.staff_headers,
            json={
                "acknowledged_by": auth_helper.staff_user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            name="[WRITE] Acknowledge Alert"
        )
    
    @task(4)
    def resolve_alert(self):
        """Resolver alerta."""
        from datetime import datetime, timezone
        self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/resolve",
            headers=self.staff_headers,
            json={
                "resolved_by": auth_helper.staff_user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            name="[WRITE] Resolve Alert"
        )
    
    @task(3)
    def org_patient_notes(self):
        """Obtener notas del paciente a nivel de org."""
        from datetime import datetime, timezone
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/notes",
            headers=self.staff_headers,
            name="[READ] Org Patient Notes"
        )
    
    @task(2)
    def update_profile(self):
        """Actualizar perfil."""
        import random
        self.client.patch(
            "/user/users/me",
            headers=self.staff_headers,
            json={
                "name": f"Test User {random.randint(1000, 9999)}"
            },
            name="[WRITE] Update Profile"
        )
    
    # ========== Catálogos y Servicios (5%) ==========
    
    @task(2)
    def event_types(self):
        """Tipos de eventos."""
        self.client.get(
            "/user/event-types",
            headers=self.staff_headers,
            name="[CATALOG] Event Types"
        )
    
    @task(1)
    def realtime_status(self):
        """Estado de realtime."""
        self.client.get(
            "/realtime/status",
            headers=self.staff_headers,
            name="[SERVICE] Realtime Status"
        )
    
    @task(1)
    def ai_model_info(self):
        """Info del modelo IA."""
        self.client.get(
            "/ai/model/info",
            headers=self.staff_headers,
            name="[SERVICE] AI Model Info"
        )
