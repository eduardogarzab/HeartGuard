"""
Break-point Test: Determinar umbral máximo antes de rechazo de solicitudes.

Objetivo:
- Encontrar el punto de quiebre del sistema
- Determinar capacidad máxima de usuarios concurrentes
- Identificar cuándo empiezan los errores masivos

Parámetros:
- Usuarios máximos: 500 (incrementa hasta fallar)
- Spawn rate: 10 usuarios/seg
- Duración: Variable (hasta encontrar break-point)

Ejecución:
    locust -f breakpoint_test.py --host=http://129.212.181.53:8080
    
    Monitorear y detener cuando:
    - Tasa de errores > 50%
    - Latencias > 10 segundos
    - Timeouts masivos

Estrategia:
    Incremento gradual hasta encontrar el punto de quiebre
"""
from locust import HttpUser, task, between, events, LoadTestShape
from auth_helper import auth_helper
from config import config
import logging

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicializa autenticación antes de comenzar las pruebas."""
    logger.info("=" * 60)
    logger.info("INICIANDO BREAKPOINT TEST")
    logger.info("Objetivo: Encontrar el punto de quiebre del sistema")
    logger.info("=" * 60)
    auth_helper.login_staff()
    auth_helper.login_patient()


class BreakpointLoadShape(LoadTestShape):
    """
    Define la forma de carga para el breakpoint test.
    
    Incremento gradual hasta 500 usuarios:
    - Cada 2 minutos aumenta 50 usuarios
    - Permite observar degradación progresiva
    """
    
    stages = [
        {"duration": 120, "users": 50, "spawn_rate": 10},
        {"duration": 240, "users": 100, "spawn_rate": 10},
        {"duration": 360, "users": 150, "spawn_rate": 10},
        {"duration": 480, "users": 200, "spawn_rate": 10},
        {"duration": 600, "users": 250, "spawn_rate": 10},
        {"duration": 720, "users": 300, "spawn_rate": 10},
        {"duration": 840, "users": 350, "spawn_rate": 10},
        {"duration": 960, "users": 400, "spawn_rate": 10},
        {"duration": 1080, "users": 450, "spawn_rate": 10},
        {"duration": 1200, "users": 500, "spawn_rate": 10},
    ]
    
    def tick(self):
        """Define cuántos usuarios deben estar activos en cada momento."""
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                logger.info(f"Breakpoint Test - Time: {run_time}s, Target Users: {stage['users']}")
                return (stage["users"], stage["spawn_rate"])
        
        # Mantener 500 usuarios hasta finalizar manualmente
        return (500, 10)


class BreakpointTestUser(HttpUser):
    """
    Usuario para breakpoint test.
    
    Mix de operaciones para simular carga realista hasta el punto de quiebre.
    """
    wait_time = between(0.5, 1.5)  # Wait corto para maximizar carga
    host = config.GATEWAY_HOST
    
    def on_start(self):
        """Inicialización del usuario."""
        self.staff_headers = auth_helper.get_staff_headers()
        self.patient_headers = auth_helper.get_patient_headers()
        self.error_count = 0
        self.success_count = 0
    
    def on_stop(self):
        """Log al finalizar usuario."""
        total = self.success_count + self.error_count
        error_rate = (self.error_count / total * 100) if total > 0 else 0
        logger.info(f"Usuario finalizado - Success: {self.success_count}, Errors: {self.error_count}, Error Rate: {error_rate:.2f}%")
    
    # ========== Critical Path - High Load (50%) ==========
    
    @task(15)
    def patient_dashboard(self):
        """Dashboard de paciente."""
        with self.client.get(
            "/patient/dashboard",
            headers=self.patient_headers,
            catch_response=True,
            name="[BP] Patient Dashboard"
        ) as response:
            if response.status_code == 200:
                self.success_count += 1
                response.success()
            elif response.status_code == 429:
                self.error_count += 1
                response.failure("Rate Limited")
            elif response.status_code >= 500:
                self.error_count += 1
                response.failure(f"Server Error: {response.status_code}")
            else:
                self.error_count += 1
    
    @task(12)
    def org_dashboard(self):
        """Dashboard de organización."""
        with self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/dashboard",
            headers=self.staff_headers,
            catch_response=True,
            name="[BP] Org Dashboard"
        ) as response:
            if response.status_code == 200:
                self.success_count += 1
                response.success()
            elif response.status_code == 429:
                self.error_count += 1
                response.failure("Rate Limited")
            elif response.status_code >= 500:
                self.error_count += 1
                response.failure(f"Server Error: {response.status_code}")
            else:
                self.error_count += 1
    
    @task(10)
    def health_check(self):
        """Health check."""
        with self.client.get("/health/", catch_response=True, name="[BP] Health") as response:
            if response.status_code == 200:
                self.success_count += 1
                response.success()
            else:
                self.error_count += 1
                response.failure(f"Failed: {response.status_code}")
    
    @task(8)
    def patient_alerts(self):
        """Alertas de paciente."""
        with self.client.get(
            "/patient/alerts",
            headers=self.patient_headers,
            params={"limit": 10},
            catch_response=True,
            name="[BP] Patient Alerts"
        ) as response:
            if response.status_code == 200:
                self.success_count += 1
                response.success()
            elif response.status_code == 429:
                self.error_count += 1
                response.failure("Rate Limited")
            else:
                self.error_count += 1
    
    @task(5)
    def auth_verify(self):
        """Verificación de auth."""
        with self.client.get(
            "/auth/verify",
            headers=self.staff_headers,
            catch_response=True,
            name="[BP] Auth Verify"
        ) as response:
            if response.status_code == 200:
                self.success_count += 1
                response.success()
            else:
                self.error_count += 1
    
    # ========== Read Operations (30%) ==========
    
    @task(6)
    def user_me(self):
        """Usuario actual."""
        response = self.client.get(
            "/user/users/me",
            headers=self.staff_headers,
            name="[BP] User Me"
        )
        if response.status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @task(5)
    def patient_profile(self):
        """Perfil de paciente."""
        response = self.client.get(
            "/patient/profile",
            headers=self.patient_headers,
            name="[BP] Patient Profile"
        )
        if response.status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @task(4)
    def patient_devices(self):
        """Dispositivos."""
        response = self.client.get(
            "/patient/devices",
            headers=self.patient_headers,
            name="[BP] Patient Devices"
        )
        if response.status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @task(4)
    def org_care_teams(self):
        """Care teams."""
        response = self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/care-teams",
            headers=self.staff_headers,
            name="[BP] Org Care Teams"
        )
        if response.status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @task(3)
    def org_patient_detail(self):
        """Detalle de paciente de la organización."""
        response = self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}",
            headers=self.staff_headers,
            name="[BP] Org Patient Detail"
        )
        if response.status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @task(3)
    def patient_latest_location(self):
        """Ubicación actual."""
        response = self.client.get(
            "/patient/location/latest",
            headers=self.patient_headers,
            name="[BP] Patient Location"
        )
        if response.status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1
    
    # ========== Write Operations (15%) ==========
    
    @task(4)
    def acknowledge_alert(self):
        """Reconocer alerta."""
        from datetime import datetime, timezone
        response = self.client.post(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/alerts/{config.TEST_ALERT_ID}/acknowledge",
            headers=self.staff_headers,
            json={
                "acknowledged_by": auth_helper.staff_user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            name="[BP] Acknowledge Alert"
        )
        if response.status_code in [200, 201]:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @task(2)
    def org_patient_notes(self):
        """Obtener notas de paciente."""
        from datetime import datetime, timezone
        response = self.client.get(
            f"/user/orgs/{auth_helper.staff_org_id}/patients/{config.TEST_PATIENT_ID}/notes",
            headers=self.staff_headers,
            name="[BP] Org Patient Notes"
        )
        if response.status_code in [200, 201]:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @task(2)
    def update_profile(self):
        """Actualizar perfil."""
        import random
        response = self.client.patch(
            "/user/users/me",
            headers=self.staff_headers,
            json={"name": f"Test User {random.randint(1000, 9999)}"},
            name="[BP] Update Profile"
        )
        if response.status_code in [200, 204]:
            self.success_count += 1
        else:
            self.error_count += 1
    
    # ========== Services Check (5%) ==========
    
    @task(2)
    def realtime_status(self):
        """Estado realtime."""
        response = self.client.get(
            "/realtime/status",
            headers=self.staff_headers,
            name="[BP] Realtime Status"
        )
        if response.status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1
    
    @task(1)
    def ai_model_info(self):
        """Info modelo IA."""
        response = self.client.get(
            "/ai/model/info",
            headers=self.staff_headers,
            name="[BP] AI Model Info"
        )
        if response.status_code == 200:
            self.success_count += 1
        else:
            self.error_count += 1


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log final del breakpoint test."""
    logger.info("=" * 60)
    logger.info("BREAKPOINT TEST COMPLETADO")
    logger.info(f"Total Requests: {environment.stats.total.num_requests}")
    logger.info(f"Total Failures: {environment.stats.total.num_failures}")
    logger.info(f"Failure Rate: {environment.stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"Average Response Time: {environment.stats.total.avg_response_time:.2f}ms")
    logger.info(f"Max Response Time: {environment.stats.total.max_response_time:.2f}ms")
    logger.info(f"Requests/sec: {environment.stats.total.total_rps:.2f}")
    
    # Determinar si se alcanzó el breakpoint
    if environment.stats.total.fail_ratio > 0.5:
        logger.warning("⚠️  BREAKPOINT ALCANZADO: Tasa de errores > 50%")
    elif environment.stats.total.avg_response_time > 10000:
        logger.warning("⚠️  BREAKPOINT ALCANZADO: Latencia promedio > 10s")
    else:
        logger.info("ℹ️  Sistema aún operacional - considerar incrementar carga")
    
    logger.info("=" * 60)
