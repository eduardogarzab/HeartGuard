"""
Soak Test: Evaluar estabilidad sostenida y detectar fugas de recursos.

Objetivo:
- Detectar degradación acumulativa de rendimiento
- Identificar memory leaks y fugas de recursos
- Validar estabilidad prolongada bajo carga constante

Parámetros:
- Usuarios: 20
- Spawn rate: 2 usuarios/seg
- Duración: 1 hora (configurable)

Ejecución:
    # 1 hora (recomendado)
    locust -f soak_test.py --host=http://129.212.181.53:8080 --users=20 --spawn-rate=2 --run-time=1h
    
    # 2 horas (más exhaustivo)
    locust -f soak_test.py --host=http://129.212.181.53:8080 --users=20 --spawn-rate=2 --run-time=2h
    
    # 4 horas (overnight)
    locust -f soak_test.py --host=http://129.212.181.53:8080 --users=20 --spawn-rate=2 --run-time=4h

Monitorear:
    - Latencias promedio (no deben incrementar con el tiempo)
    - Uso de memoria del gateway y servicios
    - Tasa de errores (debe mantenerse estable)
    - Conexiones activas
"""
from locust import HttpUser, task, between, events
from auth_helper import auth_helper
from config import config
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicializa autenticación antes de comenzar las pruebas."""
    logger.info("=" * 60)
    logger.info("INICIANDO SOAK TEST")
    logger.info(f"Start Time: {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 60)
    auth_helper.login_staff()
    auth_helper.login_patient()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log final del soak test."""
    logger.info("=" * 60)
    logger.info("SOAK TEST COMPLETADO")
    logger.info(f"End Time: {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"Total Requests: {environment.stats.total.num_requests}")
    logger.info(f"Total Failures: {environment.stats.total.num_failures}")
    logger.info(f"Failure Rate: {environment.stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"Average Response Time: {environment.stats.total.avg_response_time:.2f}ms")
    logger.info(f"Max Response Time: {environment.stats.total.max_response_time:.2f}ms")
    logger.info(f"Requests/sec: {environment.stats.total.total_rps:.2f}")
    logger.info("=" * 60)


class SoakTestUser(HttpUser):
    """
    Usuario para soak test - carga constante moderada.
    
    Simula patrones de uso realistas prolongados.
    """
    wait_time = between(2, 5)  # Wait más largo para carga sostenida
    host = config.GATEWAY_HOST
    
    def on_start(self):
        """Inicialización del usuario."""
        self.staff_headers = auth_helper.get_staff_headers()
        self.patient_headers = auth_helper.get_patient_headers()
        self.request_count = 0
    
    def on_stop(self):
        """Cleanup al finalizar."""
        logger.info(f"Usuario completó {self.request_count} requests")
    
    # ========== Health & Connectivity (15%) ==========
    
    @task(8)
    def health_check(self):
        """Health check periódico."""
        self.client.get("/health/", name="[SOAK] Health")
        self.request_count += 1
    
    @task(3)
    def auth_verify(self):
        """Verificar autenticación."""
        response = self.client.get(
            "/auth/verify",
            headers=self.staff_headers,
            name="[SOAK] Auth Verify"
        )
        self.request_count += 1
        
        # Renovar token si es necesario
        if response.status_code == 401:
            logger.info("Token expirado, renovando...")
            auth_helper.refresh_staff_token()
            self.staff_headers = auth_helper.get_staff_headers()
    
    @task(2)
    def realtime_health(self):
        """Health realtime."""
        self.client.get("/realtime/health", name="[SOAK] Realtime Health")
        self.request_count += 1
    
    @task(2)
    def ai_health(self):
        """Health IA."""
        self.client.get("/ai/health", name="[SOAK] AI Health")
        self.request_count += 1
    
    # ========== Dashboard & Monitoring (30%) ==========
    
    @task(12)
    def patient_dashboard(self):
        """Dashboard de paciente - operación más frecuente."""
        self.client.get(
            "/patient/dashboard",
            headers=self.patient_headers,
            name="[SOAK] Patient Dashboard"
        )
        self.request_count += 1
    
    @task(10)
    def org_dashboard(self):
        """Dashboard de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/dashboard",
            headers=self.staff_headers,
            name="[SOAK] Org Dashboard"
        )
        self.request_count += 1
    
    @task(8)
    def patient_alerts(self):
        """Monitoreo de alertas."""
        self.client.get(
            "/patient/alerts",
            headers=self.patient_headers,
            params={"status": "active", "limit": 15},
            name="[SOAK] Patient Alerts"
        )
        self.request_count += 1
    
    # ========== Profile & Settings (20%) ==========
    
    @task(8)
    def patient_profile(self):
        """Perfil de paciente."""
        self.client.get(
            "/patient/profile",
            headers=self.patient_headers,
            name="[SOAK] Patient Profile"
        )
        self.request_count += 1
    
    @task(7)
    def user_me(self):
        """Información de usuario."""
        self.client.get(
            "/user/users/me",
            headers=self.staff_headers,
            name="[SOAK] User Me"
        )
        self.request_count += 1
    
    @task(5)
    def user_memberships(self):
        """Membresías."""
        self.client.get(
            "/user/users/me/org-memberships",
            headers=self.staff_headers,
            name="[SOAK] User Memberships"
        )
        self.request_count += 1
    
    # ========== Devices & Monitoring (15%) ==========
    
    @task(7)
    def patient_devices(self):
        """Dispositivos de paciente."""
        self.client.get(
            "/patient/devices",
            headers=self.patient_headers,
            name="[SOAK] Patient Devices"
        )
        self.request_count += 1
    
    @task(5)
    def org_devices(self):
        """Dispositivos de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/devices",
            headers=self.staff_headers,
            name="[SOAK] Org Devices"
        )
        self.request_count += 1
    
    @task(3)
    def patient_latest_location(self):
        """Ubicación actual."""
        self.client.get(
            "/patient/location/latest",
            headers=self.patient_headers,
            name="[SOAK] Patient Location"
        )
        self.request_count += 1
    
    # ========== Care Team & Caregivers (10%) ==========
    
    @task(5)
    def patient_caregivers(self):
        """Cuidadores del paciente."""
        self.client.get(
            "/patient/caregivers",
            headers=self.patient_headers,
            name="[SOAK] Patient Caregivers"
        )
        self.request_count += 1
    
    @task(4)
    def patient_care_team(self):
        """Equipo de cuidado."""
        self.client.get(
            "/patient/care-team",
            headers=self.patient_headers,
            name="[SOAK] Patient Care Team"
        )
        self.request_count += 1
    
    @task(3)
    def org_care_teams(self):
        """Care teams de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-teams",
            headers=self.staff_headers,
            name="[SOAK] Org Care Teams"
        )
        self.request_count += 1
    
    # ========== Writes - Occasional (5%) ==========
    
    @task(2)
    def acknowledge_alert(self):
        """Reconocer alerta ocasionalmente."""
        self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/acknowledge",
            headers=self.staff_headers,
            json={
                "acknowledged_by": auth_helper.staff_user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            name="[SOAK] Acknowledge Alert"
        )
        self.request_count += 1
    
    @task(1)
    def create_note(self):
        """Crear nota ocasionalmente."""
        self.client.post(
            f"/user/caregiver/patients/{config.TEST_PATIENT_ID}/notes",
            headers=self.staff_headers,
            json={
                "content": f"Soak test observation at {datetime.now(timezone.utc).isoformat()}",
                "note_type": "observation"
            },
            name="[SOAK] Create Note"
        )
        self.request_count += 1
    
    # ========== Data Retrieval (5%) ==========
    
    @task(2)
    def patient_readings(self):
        """Lecturas históricas."""
        self.client.get(
            "/patient/readings",
            headers=self.patient_headers,
            params={"limit": 25},
            name="[SOAK] Patient Readings"
        )
        self.request_count += 1
    
    @task(2)
    def patient_locations_history(self):
        """Historial de ubicaciones."""
        self.client.get(
            "/patient/locations",
            headers=self.patient_headers,
            params={"limit": 20},
            name="[SOAK] Patient Locations"
        )
        self.request_count += 1
    
    @task(1)
    def org_metrics(self):
        """Métricas de organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/metrics",
            headers=self.staff_headers,
            name="[SOAK] Org Metrics"
        )
        self.request_count += 1
