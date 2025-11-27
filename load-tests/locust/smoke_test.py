"""
Smoke Test: Verificación rápida de disponibilidad extremo a extremo.

Objetivo:
- Confirmar que todos los servicios están activos
- Validar conectividad del gateway
- Verificar autenticación básica

Parámetros:
- Usuarios: 5
- Spawn rate: 5 usuarios/seg
- Duración: 1 minuto

Ejecución:
    locust -f smoke_test.py --host=http://129.212.181.53:8080 --users=5 --spawn-rate=5 --run-time=1m --headless
"""
from locust import HttpUser, task, between, events, SequentialTaskSet
from auth_helper import auth_helper
from config import config
import logging

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Inicializa autenticación antes de comenzar las pruebas."""
    logger.info("Iniciando smoke test - verificación de servicios...")
    auth_helper.login_staff()
    auth_helper.login_patient()


class SmokeTestSequence(SequentialTaskSet):
    """Secuencia de verificación de todos los servicios."""
    
    @task
    def check_gateway_health(self):
        """1. Verificar health del gateway."""
        with self.client.get("/health/", catch_response=True, name="1. Gateway Health") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Gateway health falló: {response.status_code}")
    
    @task
    def check_auth_verify(self):
        """2. Verificar servicio de autenticación."""
        headers = auth_helper.get_staff_headers()
        with self.client.get("/auth/verify", headers=headers, catch_response=True, name="2. Auth Verify") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Auth verify falló: {response.status_code}")
    
    @task
    def check_auth_me(self):
        """3. Verificar endpoint /me de autenticación."""
        headers = auth_helper.get_staff_headers()
        with self.client.get("/auth/me", headers=headers, catch_response=True, name="3. Auth Me") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Auth me falló: {response.status_code}")
    
    @task
    def check_user_service(self):
        """4. Verificar servicio de usuarios."""
        headers = auth_helper.get_staff_headers()
        with self.client.get("/user/", catch_response=True, name="4. User Service Info") as response:
            if response.status_code in [200, 404]:  # 404 es aceptable para info
                response.success()
            else:
                response.failure(f"User service falló: {response.status_code}")
    
    @task
    def check_user_me(self):
        """5. Verificar perfil de usuario."""
        headers = auth_helper.get_staff_headers()
        with self.client.get("/user/users/me", headers=headers, catch_response=True, name="5. User Me") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"User me falló: {response.status_code}")
    
    @task
    def check_patient_service(self):
        """6. Verificar servicio de pacientes."""
        headers = auth_helper.get_patient_headers()
        with self.client.get("/patient/health", headers=headers, catch_response=True, name="6. Patient Health") as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Patient health falló: {response.status_code}")
    
    @task
    def check_patient_dashboard(self):
        """7. Verificar dashboard de paciente."""
        headers = auth_helper.get_patient_headers()
        with self.client.get("/patient/dashboard", headers=headers, catch_response=True, name="7. Patient Dashboard") as response:
            if response.status_code in [200, 404]:  # 404 si no hay datos
                response.success()
            else:
                response.failure(f"Patient dashboard falló: {response.status_code}")
    
    @task
    def check_admin_service(self):
        """8. Verificar servicio de administración."""
        headers = auth_helper.get_staff_headers()
        with self.client.get(
            f"/admin/organizations/{auth_helper.staff_org_id}",
            headers=headers,
            catch_response=True,
            name="8. Admin Org Detail"
        ) as response:
            # 200: OK, 403: Forbidden (permisos), 404: Not found
            if response.status_code in [200, 403, 404]:
                response.success()
            else:
                response.failure(f"Admin service falló: {response.status_code}")
    
    @task
    def check_media_service(self):
        """9. Verificar servicio de media."""
        headers = auth_helper.get_staff_headers()
        with self.client.get("/media/health", headers=headers, catch_response=True, name="9. Media Health") as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Media health falló: {response.status_code}")
    
    @task
    def check_realtime_service(self):
        """10. Verificar servicio de realtime."""
        headers = auth_helper.get_staff_headers()
        with self.client.get("/realtime/health", headers=headers, catch_response=True, name="10. Realtime Health") as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Realtime health falló: {response.status_code}")
    
    @task
    def check_ai_service(self):
        """11. Verificar servicio de IA."""
        headers = auth_helper.get_staff_headers()
        with self.client.get("/ai/health", headers=headers, catch_response=True, name="11. AI Health") as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"AI health falló: {response.status_code}")


class SmokeTestUser(HttpUser):
    """Usuario para smoke test."""
    wait_time = between(0.5, 1)
    tasks = [SmokeTestSequence]
    host = config.GATEWAY_HOST
