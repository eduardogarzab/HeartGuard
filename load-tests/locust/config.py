"""Configuración centralizada para las pruebas Locust."""
from dataclasses import dataclass


@dataclass
class Config:
    """Configuración del gateway y servicios."""
    
    # Gateway base URL
    GATEWAY_HOST = "http://129.212.181.53:8080"
    
    # Credenciales de prueba para autenticación
    # Usuario staff
    STAFF_EMAIL = "ana.ruiz@heartguard.com"
    STAFF_PASSWORD = "Demo#2025"
    
    # Paciente
    PATIENT_EMAIL = "maria.delgado@patients.heartguard.com"
    PATIENT_PASSWORD = "Paciente#2025"
    
    # IDs de prueba (según seed.sql)
    # Organizaciones
    TEST_ORG_CODE = "FAM-001"  # Familia García (usado en endpoints que requieren org_id)
    TEST_ORG_CODE_2 = "CLIN-001"  # Clínica Central
    
    # Pacientes (UUIDs del seed.sql)
    TEST_PATIENT_ID = "8c9436b4-f085-405f-a3d2-87cb1d1cf097"  # María Delgado
    TEST_PATIENT_ID_2 = "fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21"  # José Hernández
    TEST_PATIENT_ID_3 = "ae15cd87-5ac2-4f90-8712-184b02c541a5"  # Valeria Ortiz
    
    # Care Teams (UUIDs del seed.sql)
    TEST_CARE_TEAM_ID = "1ad17404-323c-4469-86eb-aef83336d1c9"  # Equipo Cardiología Familiar
    TEST_CARE_TEAM_ID_2 = "a9c83e54-30e5-4487-abb5-1f97a10cca17"  # Unidad Telemetría Clínica
    
    # Devices (UUIDs del seed.sql)
    TEST_DEVICE_ID = "1ec46655-ba0c-4e2a-b315-dc6bbcbeda7d"  # HG-ECG-001 (María)
    TEST_DEVICE_ID_2 = "e085ff18-d8bd-46f6-b34c-26bb0b797a14"  # HG-PUL-201 (José)
    
    # Alertas (UUIDs del seed.sql)
    TEST_ALERT_ID = "c20277df-7c2f-417c-902e-776bf4bf74c3"  # Alerta de arritmia (María)
    TEST_ALERT_ID_2 = "e9154dc9-73eb-4306-bfe2-eaa0d7de9dd0"  # Alerta de desaturación (José)
    
    # Invitaciones (tokens del seed.sql)
    # INVITE-DEMO-001 = pending (válida para aceptar/rechazar)
    # INVITE-DEMO-002 = used (ya aceptada)
    # INVITE-DEMO-003 = revoked (revocada)
    TEST_INVITATION_TOKEN = "INVITE-DEMO-001"  # Invitación pendiente
    
    # Push Devices (UUIDs del seed.sql)
    TEST_PUSH_DEVICE_ID = "d27a6e1b-8def-423e-8d49-e59113d00ac5"  # Ana Ruiz - iOS
    TEST_PUSH_DEVICE_ID_2 = "b8ffa975-0c3f-426e-8fa8-c18f259b939f"  # Martin Ops - Android
    
    # NOTA: Para endpoints que requieren user_id, se debe obtener dinámicamente
    # después del login, ya que los IDs de usuarios son auto-generados
    
    # Timeouts
    REQUEST_TIMEOUT = 30
    
    # Configuración de carga por tipo de prueba
    BASELINE_USERS = 10
    BASELINE_SPAWN_RATE = 2
    
    SMOKE_USERS = 5
    SMOKE_SPAWN_RATE = 5
    
    READ_HEAVY_USERS = 50
    READ_HEAVY_SPAWN_RATE = 5
    
    WRITE_HEAVY_USERS = 30
    WRITE_HEAVY_SPAWN_RATE = 3
    
    RAMP_MAX_USERS = 100
    RAMP_SPAWN_RATE = 5
    
    SPIKE_USERS = 200
    SPIKE_SPAWN_RATE = 50
    
    SOAK_USERS = 20
    SOAK_SPAWN_RATE = 2
    SOAK_DURATION_HOURS = 1
    
    BREAKPOINT_MAX_USERS = 500
    BREAKPOINT_SPAWN_RATE = 10


config = Config()
