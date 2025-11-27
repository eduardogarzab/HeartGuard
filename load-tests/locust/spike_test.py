"""
Spike Test: Simular picos súbitos de tráfico para validar elasticidad.

Objetivo:
- Comprobar resistencia ante picos súbitos de carga
- Validar mecanismos de rate limiting
- Observar recuperación después del spike

Parámetros:
- Usuarios base: 20
- Usuarios spike: 200
- Duración: 8 minutos

Ejecución:
    locust -f spike_test.py --host=http://129.212.181.53:8080
    
Fases:
    1. Baseline: 20 usuarios (2 min)
    2. Spike: 200 usuarios súbitos (2 min)
    3. Recovery: 20 usuarios (4 min)
"""
from locust import HttpUser, task, between, events, LoadTestShape
from auth_helper import auth_helper
from config import config
import logging

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicializa autenticación antes de comenzar las pruebas."""
    logger.info("Iniciando spike test...")
    auth_helper.login_staff()
    auth_helper.login_patient()


class SpikeLoadShape(LoadTestShape):
    """
    Define la forma de carga para el spike test.
    
    Fases:
    - 0-2 min: Baseline 20 usuarios
    - 2-4 min: SPIKE a 200 usuarios súbitamente
    - 4-8 min: Recovery a 20 usuarios
    """
    
    stages = [
        # Baseline: 20 usuarios estables
        {"duration": 120, "users": 20, "spawn_rate": 5},
        
        # SPIKE: Súbito incremento a 200 usuarios
        {"duration": 240, "users": 200, "spawn_rate": 50},
        
        # Recovery: Retorno a 20 usuarios
        {"duration": 480, "users": 20, "spawn_rate": 20},
    ]
    
    def tick(self):
        """Define cuántos usuarios deben estar activos en cada momento."""
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                logger.info(f"Spike Test - Time: {run_time}s, Users: {stage['users']}")
                return tick_data
        
        return None


class SpikeTestUser(HttpUser):
    """
    Usuario para spike test.
    
    Ejecuta operaciones críticas para validar comportamiento bajo spike.
    """
    wait_time = between(0.5, 2)
    host = config.GATEWAY_HOST
    
    def on_start(self):
        """Inicialización del usuario."""
        self.staff_headers = auth_helper.get_staff_headers()
        self.patient_headers = auth_helper.get_patient_headers()
    
    # ========== Operaciones Críticas (60%) ==========
    
    @task(15)
    def patient_dashboard(self):
        """Dashboard de paciente - operación más crítica."""
        with self.client.get(
            "/patient/dashboard",
            headers=self.patient_headers,
            catch_response=True,
            name="[CRITICAL] Patient Dashboard"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
    
    @task(12)
    def org_dashboard(self):
        """Dashboard de organización."""
        with self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/dashboard",
            headers=self.staff_headers,
            catch_response=True,
            name="[CRITICAL] Org Dashboard"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
    
    @task(10)
    def patient_alerts(self):
        """Alertas de paciente."""
        with self.client.get(
            "/patient/alerts",
            headers=self.patient_headers,
            params={"status": "active", "limit": 10},
            catch_response=True,
            name="[CRITICAL] Patient Alerts"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
    
    @task(8)
    def health_check(self):
        """Health check."""
        with self.client.get("/health/", catch_response=True, name="[CRITICAL] Health") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(7)
    def user_me(self):
        """Información de usuario."""
        with self.client.get(
            "/user/users/me",
            headers=self.staff_headers,
            catch_response=True,
            name="[CRITICAL] User Me"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
    
    @task(8)
    def auth_verify(self):
        """Verificación de autenticación."""
        with self.client.get(
            "/auth/verify",
            headers=self.staff_headers,
            catch_response=True,
            name="[CRITICAL] Auth Verify"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
    
    # ========== Operaciones de Alta Demanda (25%) ==========
    
    @task(6)
    def patient_devices(self):
        """Dispositivos de paciente."""
        self.client.get(
            "/patient/devices",
            headers=self.patient_headers,
            name="[HIGH] Patient Devices"
        )
    
    @task(5)
    def org_care_teams(self):
        """Care teams."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-teams",
            headers=self.staff_headers,
            name="[HIGH] Org Care Teams"
        )
    
    @task(4)
    def org_patient_detail(self):
        """Detalle de paciente de la organización."""
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}",
            headers=self.staff_headers,
            name="[HIGH] Org Patient Detail"
        )
    
    @task(3)
    def patient_latest_location(self):
        """Última ubicación."""
        self.client.get(
            "/patient/location/latest",
            headers=self.patient_headers,
            name="[HIGH] Patient Location"
        )
    
    # ========== Escrituras Bajo Spike (10%) ==========
    
    @task(3)
    def acknowledge_alert(self):
        """Reconocer alerta - validar escrituras bajo spike."""
        from datetime import datetime, timezone
        with self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/acknowledge",
            headers=self.staff_headers,
            json={
                "acknowledged_by": auth_helper.staff_user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            catch_response=True,
            name="[WRITE] Acknowledge Alert"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited - Expected during spike")
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
    
    @task(2)
    def org_patient_notes(self):
        """Obtener notas del paciente."""
        from datetime import datetime, timezone
        self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/notes",
            headers=self.staff_headers,
            name="[READ] Org Patient Notes"
        )
    
    # ========== Servicios Auxiliares (5%) ==========
    
    @task(2)
    def realtime_status(self):
        """Estado realtime."""
        self.client.get(
            "/realtime/status",
            headers=self.staff_headers,
            name="[AUX] Realtime Status"
        )
    
    @task(1)
    def ai_model_info(self):
        """Info modelo IA."""
        self.client.get(
            "/ai/model/info",
            headers=self.staff_headers,
            name="[AUX] AI Model Info"
        )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log final del spike test."""
    logger.info("Spike test completado")
    logger.info(f"Total requests: {environment.stats.total.num_requests}")
    logger.info(f"Total failures: {environment.stats.total.num_failures}")
    logger.info(f"Average response time: {environment.stats.total.avg_response_time}ms")
