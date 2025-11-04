# Admin Service - Documentación Completa

Servicio de administración para usuarios con rol `org_admin`. Proporciona endpoints para gestionar organizaciones, pacientes, equipos de cuidado, cuidadores y alertas. **Todas las respuestas son en formato XML**.

## 📋 Tabla de Contenidos

- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación y Desarrollo](#instalación-y-desarrollo)
- [Autenticación](#autenticación)
- [Endpoints](#endpoints)
  - [Organizaciones](#organizaciones)
  - [Staff](#staff-miembros-de-organización)
  - [Pacientes](#pacientes)
  - [Equipos de Cuidado](#equipos-de-cuidado-care-teams)
  - [Cuidadores](#cuidadores-caregivers)
  - [Alertas](#alertas)
- [Códigos de Error](#códigos-de-error)
- [Testing](#testing)

---

## 🏗️ Estructura del Proyecto

```
admin/
├── src/admin/
│   ├── app.py                    # Factory de aplicación Flask
│   ├── auth.py                   # Verificación JWT y decorador require_org_admin
│   ├── xml.py                    # Serialización XML y respuestas
│   ├── request_utils.py          # Parser de payloads (JSON/XML/form)
│   │
│   ├── routes/                   # Blueprints de Flask (8 módulos)
│   │   ├── organizations.py      # Listar y obtener detalles de organizaciones
│   │   ├── dashboard.py          # Dashboard con métricas y KPIs
│   │   ├── staff.py              # Gestión de miembros y roles
│   │   ├── patients.py           # CRUD de pacientes
│   │   ├── care_teams.py         # Equipos de cuidado y asignaciones
│   │   ├── caregivers.py         # Relaciones cuidador-paciente
│   │   ├── alerts.py             # Gestión de alertas
│   │   └── health.py             # Health check
│   │
│   └── repositories/             # Capa de acceso a datos (7 repositorios)
│       ├── organization_repo.py
│       ├── staff_repo.py
│       ├── patient_repo.py
│       ├── care_team_repo.py
│       ├── caregiver_repo.py
│       ├── alert_repo.py
│       └── dashboard_repo.py
│
├── tests/                        # Tests unitarios
├── Makefile                      # Comandos de desarrollo
├── test_admin_service.sh         # Suite de pruebas de integración
└── requirements.txt
```

---

## 🚀 Instalación y Desarrollo

### Instalación

```bash
# Instalar dependencias
make install

# O manualmente
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Desarrollo

```bash
# Modo desarrollo (hot-reload en puerto 5002)
make dev

# Ejecutar tests
make test

# Limpiar archivos temporales
make clean
```

### Desde el Makefile Maestro

```bash
# Desde /services
make start-admin        # Iniciar admin-service
make restart-admin      # Reiniciar admin-service
make logs-admin         # Ver logs
make test-admin         # Ejecutar tests
```

---

## 🔐 Autenticación

**Todos los endpoints requieren autenticación JWT** con rol `org_admin` en la organización.

### Headers Requeridos

```http
Authorization: Bearer <JWT_TOKEN>
Accept: application/xml
Content-Type: application/json  # Para POST/PATCH/PUT
```

### Obtener Token JWT

```bash
# Login con auth-service
curl -X POST http://localhost:5001/auth/login/user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ana.ruiz@heartguard.com",
    "password": "Demo#2025"
  }'

# Respuesta
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "f2d80568-7d45-4d75-80e3-b85c1b1f2497"
}
```

### Validación de Permisos

El decorador `@require_org_admin` verifica:
1. **Token JWT válido** (vía auth-service)
2. **Usuario pertenece a la organización** (tabla `user_org_membership`)
3. **Usuario tiene rol `org_admin`** en esa organización

---

## 📡 Endpoints

**Base URL**: `http://localhost:8080/admin` (vía Gateway)  
**Formato de Respuesta**: XML

---

## 🏢 Organizaciones

### 1. Listar Organizaciones del Usuario

Lista todas las organizaciones a las que pertenece el usuario autenticado con rol `org_admin`.

```http
GET /admin/organizations/
```

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Accept: application/xml
```

**Respuesta Exitosa (200):**

```xml
<response>
  <organizations>
    <organization>
      <id>393b7d02-d3f8-48e5-829f-e03eb8c13541</id>
      <code>FAM-001</code>
      <name>Familia García</name>
      <role_code>org_admin</role_code>
      <joined_at>2025-09-03 22:18:31.616751</joined_at>
    </organization>
    <organization>
      <id>a1234567-89ab-cdef-0123-456789abcdef</id>
      <code>HOSP-001</code>
      <name>Hospital Central</name>
      <role_code>org_admin</role_code>
      <joined_at>2025-10-15 10:30:00.000000</joined_at>
    </organization>
  </organizations>
</response>
```

**Ejemplo de Uso:**

```bash
curl -X GET "http://localhost:8080/admin/organizations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"
```

---

### 2. Obtener Detalle de Organización

Obtiene información detallada de una organización específica con estadísticas.

```http
GET /admin/organizations/{org_id}
```

**Parámetros:**
- `org_id` (path, UUID) - ID de la organización

**Respuesta Exitosa (200):**

```xml
<response>
  <organization>
    <id>393b7d02-d3f8-48e5-829f-e03eb8c13541</id>
    <code>FAM-001</code>
    <name>Familia García</name>
    <created_at>2025-11-02 22:18:31.360815</created_at>
  </organization>
  <stats>
    <member_count>2</member_count>
    <patient_count>10</patient_count>
    <care_team_count>3</care_team_count>
    <caregiver_count>5</caregiver_count>
    <alert_count>8</alert_count>
  </stats>
</response>
```

**Ejemplo de Uso:**

```bash
curl -X GET "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"
```

---

### 3. Dashboard de Organización

Dashboard completo con métricas y KPIs de los últimos 30 días.

```http
GET /admin/organizations/{org_id}/dashboard
```

**Query Parameters:**
- `period_days` (opcional, default: 30) - Período en días para las métricas

**Respuesta Exitosa (200):**

```xml
<dashboard>
  <organization>
    <id>393b7d02-d3f8-48e5-829f-e03eb8c13541</id>
    <code>FAM-001</code>
    <name>Familia García</name>
    <created_at>2025-11-02 22:18:31.360815</created_at>
  </organization>
  
  <stats>
    <member_count>2</member_count>
    <patient_count>10</patient_count>
    <care_team_count>3</care_team_count>
    <caregiver_count>5</caregiver_count>
    <alert_count>8</alert_count>
  </stats>
  
  <period_days>30</period_days>
  
  <risk_levels>
    <risk_level>
      <code>high</code>
      <label>Alto</label>
      <count>3</count>
    </risk_level>
    <risk_level>
      <code>medium</code>
      <label>Medio</label>
      <count>5</count>
    </risk_level>
    <risk_level>
      <code>low</code>
      <label>Bajo</label>
      <count>2</count>
    </risk_level>
  </risk_levels>
  
  <device_status>
    <status>
      <code>active</code>
      <label>Activos</label>
      <count>8</count>
    </status>
    <status>
      <code>disconnected</code>
      <label>Desconectados</label>
      <count>2</count>
    </status>
  </device_status>
  
  <alert_outcomes>
    <alert_outcome>
      <code>Resolved</code>
      <label>Resolved</label>
      <count>15</count>
    </alert_outcome>
    <alert_outcome>
      <code>Escalated</code>
      <label>Escalated</label>
      <count>3</count>
    </alert_outcome>
  </alert_outcomes>
  
  <response_stats>
    <avg_ack_seconds>1200.5</avg_ack_seconds>
    <avg_resolve_seconds>3600.25</avg_resolve_seconds>
  </response_stats>
  
  <alerts_created>23</alerts_created>
  
  <invitation_status>
    <status>
      <code>pending</code>
      <label>pending</label>
      <count>2</count>
    </status>
    <status>
      <code>used</code>
      <label>used</label>
      <count>5</count>
    </status>
  </invitation_status>
</dashboard>
```

**Ejemplo de Uso:**

```bash
# Dashboard de últimos 30 días (default)
curl -X GET "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/dashboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"

# Dashboard de últimos 7 días
curl -X GET "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/dashboard?period_days=7" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"
```

---

## 👥 Staff (Miembros de Organización)

### 4. Listar Miembros del Staff

Lista todos los miembros de la organización con sus roles.

```http
GET /admin/organizations/{org_id}/staff/
```

**Respuesta Exitosa (200):**

```xml
<response>
  <staff_members>
    <staff_member>
      <user_id>f2d80568-7d45-4d75-80e3-b85c1b1f2497</user_id>
      <name>Ana Ruiz</name>
      <email>ana.ruiz@heartguard.com</email>
      <role_code>org_admin</role_code>
      <role_label>Admin de Organización</role_label>
      <joined_at>2025-09-03 22:18:31.616751</joined_at>
    </staff_member>
    <staff_member>
      <user_id>a9876543-21ba-fedc-0987-654321fedcba</user_id>
      <name>Carlos López</name>
      <email>carlos.lopez@heartguard.com</email>
      <role_code>org_viewer</role_code>
      <role_label>Observador de Organización</role_label>
      <joined_at>2025-10-01 15:30:00.000000</joined_at>
    </staff_member>
  </staff_members>
</response>
```

---

### 5. Crear Invitación

Crea una invitación para un nuevo miembro del staff.

```http
POST /admin/organizations/{org_id}/staff/invitations
```

**Body (JSON):**

```json
{
  "email": "nuevo.doctor@heartguard.com",
  "role_code": "org_admin",
  "expires_in_days": 7
}
```

**Respuesta Exitosa (201):**

```xml
<response>
  <invitation>
    <id>12345678-90ab-cdef-1234-567890abcdef</id>
    <email>nuevo.doctor@heartguard.com</email>
    <role_code>org_admin</role_code>
    <token>INV-DEMO-2025-XYZ123</token>
    <expires_at>2025-11-11 22:00:00.000000</expires_at>
    <created_at>2025-11-04 22:00:00.000000</created_at>
  </invitation>
</response>
```

**Ejemplo de Uso:**

```bash
curl -X POST "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/staff/invitations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/xml" \
  -d '{
    "email": "nuevo.doctor@heartguard.com",
    "role_code": "org_admin",
    "expires_in_days": 7
  }'
```

---

### 6. Actualizar Rol de Miembro

Actualiza el rol de un miembro existente del staff.

```http
PATCH /admin/organizations/{org_id}/staff/{user_id}
```

**Body (JSON):**

```json
{
  "role_code": "org_viewer"
}
```

**Respuesta Exitosa (200):**

```xml
<response>
  <message>Staff member role updated successfully</message>
  <staff_member>
    <user_id>a9876543-21ba-fedc-0987-654321fedcba</user_id>
    <role_code>org_viewer</role_code>
    <updated_at>2025-11-04 22:15:00.000000</updated_at>
  </staff_member>
</response>
```

---

## 🏥 Pacientes

### 7. Listar Pacientes

Lista todos los pacientes de la organización.

```http
GET /admin/organizations/{org_id}/patients/
```

**Query Parameters:**
- `risk_level` (opcional) - Filtrar por nivel de riesgo: `low`, `medium`, `high`
- `limit` (opcional, default: 100) - Número máximo de resultados
- `offset` (opcional, default: 0) - Offset para paginación

**Respuesta Exitosa (200):**

```xml
<response>
  <patients>
    <patient>
      <id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</id>
      <person_name>María Delgado</person_name>
      <email>maria.delgado@patients.heartguard.com</email>
      <birthdate>1978-03-22</birthdate>
      <org_id>393b7d02-d3f8-48e5-829f-e03eb8c13541</org_id>
      <org_name>Familia García</org_name>
      <risk_level_code>high</risk_level_code>
      <risk_level_label>Alto</risk_level_label>
      <created_at>2025-07-05 22:18:31.651880</created_at>
    </patient>
    <patient>
      <id>ae15cd87-5ac2-4f90-8712-184b02c541a5</id>
      <person_name>Valeria Ortiz</person_name>
      <email>valeria.ortiz@patients.heartguard.com</email>
      <birthdate>1992-07-15</birthdate>
      <org_id>393b7d02-d3f8-48e5-829f-e03eb8c13541</org_id>
      <org_name>Familia García</org_name>
      <risk_level_code>low</risk_level_code>
      <risk_level_label>Bajo</risk_level_label>
      <created_at>2025-09-18 22:18:31.651880</created_at>
    </patient>
  </patients>
</response>
```

**Ejemplo de Uso:**

```bash
# Listar todos los pacientes
curl -X GET "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/patients/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"

# Filtrar pacientes de alto riesgo
curl -X GET "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/patients/?risk_level=high" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"
```

---

### 8. Crear Paciente

Crea un nuevo paciente en la organización.

```http
POST /admin/organizations/{org_id}/patients/
```

**Body (JSON):**

```json
{
  "person_name": "Juan Pérez",
  "email": "juan.perez@patients.heartguard.com",
  "password": "SecurePass123!",
  "birthdate": "1985-03-20",
  "sex_code": "M",
  "risk_level_code": "medium"
}
```

**Campos:**
- `person_name` (requerido) - Nombre completo
- `email` (requerido) - Email único del paciente
- `password` (requerido) - Contraseña inicial
- `birthdate` (requerido) - Fecha de nacimiento (YYYY-MM-DD)
- `sex_code` (opcional) - Código de sexo: `M`, `F`, `O`
- `risk_level_code` (opcional) - Nivel de riesgo: `low`, `medium`, `high`

**Respuesta Exitosa (201):**

```xml
<response>
  <patient>
    <id>d1b59cc7-9e71-4f11-9411-1eaca7dba465</id>
    <org_id>393b7d02-d3f8-48e5-829f-e03eb8c13541</org_id>
    <org_name>Familia García</org_name>
    <person_name>Juan Pérez</person_name>
    <email>juan.perez@patients.heartguard.com</email>
    <birthdate>1985-03-20</birthdate>
    <sex_code>M</sex_code>
    <sex_label>Masculino</sex_label>
    <risk_level_code>medium</risk_level_code>
    <risk_level_label>Medio</risk_level_label>
    <profile_photo_url />
    <created_at>2025-11-04 01:08:26.950497</created_at>
  </patient>
</response>
```

**Ejemplo de Uso:**

```bash
curl -X POST "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/patients/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/xml" \
  -d '{
    "person_name": "Juan Pérez",
    "email": "juan.perez@patients.heartguard.com",
    "password": "SecurePass123!",
    "birthdate": "1985-03-20",
    "sex_code": "M",
    "risk_level_code": "medium"
  }'
```

---

### 9. Obtener Detalle de Paciente

Obtiene información completa de un paciente específico.

```http
GET /admin/organizations/{org_id}/patients/{patient_id}
```

**Respuesta Exitosa (200):**

```xml
<response>
  <patient>
    <id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</id>
    <person_name>María Delgado</person_name>
    <email>maria.delgado@patients.heartguard.com</email>
    <birthdate>1978-03-22</birthdate>
    <org_id>393b7d02-d3f8-48e5-829f-e03eb8c13541</org_id>
    <org_name>Familia García</org_name>
    <sex_code>F</sex_code>
    <sex_label>Femenino</sex_label>
    <risk_level_code>high</risk_level_code>
    <risk_level_label>Alto</risk_level_label>
    <profile_photo_url />
    <created_at>2025-07-05 22:18:31.651880</created_at>
  </patient>
</response>
```

---

### 10. Actualizar Paciente

Actualiza información de un paciente existente.

```http
PATCH /admin/organizations/{org_id}/patients/{patient_id}
```

**Body (JSON):**

```json
{
  "person_name": "María Delgado García",
  "risk_level_code": "medium"
}
```

**Campos Opcionales:**
- `person_name`
- `email`
- `birthdate`
- `sex_code`
- `risk_level_code`

**Respuesta Exitosa (200):**

```xml
<response>
  <message>Patient updated successfully</message>
  <patient>
    <id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</id>
    <person_name>María Delgado García</person_name>
    <risk_level_code>medium</risk_level_code>
    <updated_at>2025-11-04 22:30:00.000000</updated_at>
  </patient>
</response>
```

---

### 11. Eliminar Paciente

Elimina un paciente de la organización (soft delete).

```http
DELETE /admin/organizations/{org_id}/patients/{patient_id}
```

**Respuesta Exitosa (200):**

```xml
<response>
  <message>Patient deleted successfully</message>
  <patient_id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</patient_id>
</response>
```

---

## 🏥 Equipos de Cuidado (Care Teams)

### 12. Listar Equipos de Cuidado

Lista todos los equipos de cuidado de la organización.

```http
GET /admin/organizations/{org_id}/care-teams/
```

**Respuesta Exitosa (200):**

```xml
<response>
  <care_teams>
    <care_team>
      <id>1ad17404-323c-4469-86eb-aef83336d1c9</id>
      <org_id>393b7d02-d3f8-48e5-829f-e03eb8c13541</org_id>
      <name>Equipo Cardiología Familiar</name>
      <created_at>2025-06-15 22:18:31.841163</created_at>
    </care_team>
    <care_team>
      <id>60ff9531-1f81-462e-a40a-befcc0dde97c</id>
      <org_id>393b7d02-d3f8-48e5-829f-e03eb8c13541</org_id>
      <name>Equipo Telemetría</name>
      <created_at>2025-07-20 10:15:00.000000</created_at>
    </care_team>
  </care_teams>
</response>
```

---

### 13. Crear Equipo de Cuidado

Crea un nuevo equipo de cuidado.

```http
POST /admin/organizations/{org_id}/care-teams/
```

**Body (JSON):**

```json
{
  "name": "Equipo Cardiología Test"
}
```

**Respuesta Exitosa (201):**

```xml
<response>
  <care_team>
    <id>bd74a961-b09f-4236-b838-88d62514e832</id>
    <org_id>393b7d02-d3f8-48e5-829f-e03eb8c13541</org_id>
    <name>Equipo Cardiología Test</name>
    <created_at>2025-11-04 01:20:19.069023</created_at>
  </care_team>
</response>
```

---

### 14. Listar Miembros de un Equipo

Obtiene los miembros de un equipo de cuidado específico.

```http
GET /admin/organizations/{org_id}/care-teams/{team_id}/members
```

**Respuesta Exitosa (200):**

```xml
<response>
  <care_team>
    <id>1ad17404-323c-4469-86eb-aef83336d1c9</id>
    <name>Equipo Cardiología Familiar</name>
  </care_team>
  <members>
    <member>
      <user_id>f2d80568-7d45-4d75-80e3-b85c1b1f2497</user_id>
      <name>Ana Ruiz</name>
      <email>ana.ruiz@heartguard.com</email>
      <role_code>specialist</role_code>
      <role_label>Especialista</role_label>
      <joined_at>2025-06-20 10:00:00.000000</joined_at>
    </member>
    <member>
      <user_id>a9876543-21ba-fedc-0987-654321fedcba</user_id>
      <name>Carlos López</name>
      <email>carlos.lopez@heartguard.com</email>
      <role_code>doctor</role_code>
      <role_label>Doctor/a</role_label>
      <joined_at>2025-07-01 09:30:00.000000</joined_at>
    </member>
  </members>
</response>
```

---

### 15. Asignar Paciente a Equipo

Asigna un paciente a un equipo de cuidado.

```http
POST /admin/organizations/{org_id}/care-teams/{team_id}/patients
```

**Body (JSON):**

```json
{
  "patient_id": "8c9436b4-f085-405f-a3d2-87cb1d1cf097"
}
```

**Respuesta Exitosa (201):**

```xml
<response>
  <message>Patient assigned to care team successfully</message>
  <assignment>
    <care_team_id>1ad17404-323c-4469-86eb-aef83336d1c9</care_team_id>
    <patient_id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</patient_id>
    <assigned_at>2025-11-04 22:45:00.000000</assigned_at>
  </assignment>
</response>
```

---

## 👨‍👩‍👧‍👦 Cuidadores (Caregivers)

### 16. Listar Tipos de Relación

Obtiene los tipos de relación disponibles para cuidadores.

```http
GET /admin/organizations/{org_id}/caregivers/relationship-types
```

**Respuesta Exitosa (200):**

```xml
<response>
  <relationship_types>
    <relationship_type>
      <id>d6ac00a6-aa28-4229-acfa-92974f9bc8f8</id>
      <code>parent</code>
      <label>Padre/Madre</label>
    </relationship_type>
    <relationship_type>
      <id>b0f626dc-5444-4784-9879-81f287b1cfc8</id>
      <code>spouse</code>
      <label>Esposo/a</label>
    </relationship_type>
    <relationship_type>
      <id>10490f2b-421e-4745-9eef-365ef7b01a95</id>
      <code>sibling</code>
      <label>Hermano/a</label>
    </relationship_type>
    <relationship_type>
      <id>6076143c-3ea4-430e-a738-a7fb89d51959</id>
      <code>child</code>
      <label>Hijo/a</label>
    </relationship_type>
    <relationship_type>
      <id>7c78364d-5c5b-4445-bd07-28ee6eff0119</id>
      <code>friend</code>
      <label>Amigo/a</label>
    </relationship_type>
  </relationship_types>
</response>
```

---

### 17. Listar Asignaciones de Cuidadores

Lista todas las asignaciones de cuidadores a pacientes.

```http
GET /admin/organizations/{org_id}/caregivers/assignments
```

**Query Parameters:**
- `patient_id` (opcional) - Filtrar por paciente específico

**Respuesta Exitosa (200):**

```xml
<response>
  <caregiver_assignments>
    <assignment>
      <patient_id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</patient_id>
      <patient_name>María Delgado</patient_name>
      <caregiver_user_id>12345678-90ab-cdef-1234-567890abcdef</caregiver_user_id>
      <caregiver_name>José Delgado</caregiver_name>
      <caregiver_email>jose.delgado@example.com</caregiver_email>
      <relationship_type_code>spouse</relationship_type_code>
      <relationship_type_label>Esposo/a</relationship_type_label>
      <is_primary>true</is_primary>
      <started_at>2025-07-10 10:00:00.000000</started_at>
      <note>Contacto principal de emergencia</note>
    </assignment>
  </caregiver_assignments>
</response>
```

---

### 18. Crear Asignación de Cuidador

Asigna un cuidador a un paciente.

```http
POST /admin/organizations/{org_id}/caregivers/assignments
```

**Body (JSON):**

```json
{
  "patient_id": "8c9436b4-f085-405f-a3d2-87cb1d1cf097",
  "user_id": "12345678-90ab-cdef-1234-567890abcdef",
  "relationship_type_code": "spouse",
  "is_primary": true,
  "note": "Contacto principal de emergencia"
}
```

**Campos:**
- `patient_id` (requerido) - ID del paciente
- `user_id` (requerido) - ID del usuario cuidador
- `relationship_type_code` (requerido) - Tipo de relación: `parent`, `spouse`, `sibling`, `child`, `friend`
- `is_primary` (opcional, default: false) - Si es cuidador primario
- `note` (opcional) - Notas adicionales

**Respuesta Exitosa (201):**

```xml
<response>
  <message>Caregiver assignment created successfully</message>
  <assignment>
    <patient_id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</patient_id>
    <caregiver_user_id>12345678-90ab-cdef-1234-567890abcdef</caregiver_user_id>
    <relationship_type_code>spouse</relationship_type_code>
    <is_primary>true</is_primary>
    <started_at>2025-11-04 23:00:00.000000</started_at>
  </assignment>
</response>
```

---

## 🚨 Alertas

### 19. Listar Alertas

Lista todas las alertas de la organización.

```http
GET /admin/organizations/{org_id}/alerts/
```

**Query Parameters:**
- `status_code` (opcional) - Filtrar por estado: `created`, `notified`, `ack`, `resolved`, `closed`
- `level_code` (opcional) - Filtrar por nivel: `low`, `medium`, `high`, `critical`
- `patient_id` (opcional) - Filtrar por paciente
- `limit` (opcional, default: 100)
- `offset` (opcional, default: 0)

**Respuesta Exitosa (200):**

```xml
<response>
  <alerts>
    <alert>
      <id>c20277df-7c2f-417c-902e-776bf4bf74c3</id>
      <created_at>2025-11-02 20:26:31.913680</created_at>
      <description>Posible fibrilación detectada por CardioNet</description>
      <patient_id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</patient_id>
      <patient_name>María Delgado</patient_name>
      <type_code>ARRHYTHMIA</type_code>
      <type_description>Ritmo cardiaco anómalo</type_description>
      <level_code>high</level_code>
      <level_label>Alto</level_label>
      <status_code>resolved</status_code>
      <status_description>Resuelta</status_description>
    </alert>
    <alert>
      <id>aaaaaaaa-1111-1111-1111-000000000001</id>
      <created_at>2025-11-02 19:18:32.009546</created_at>
      <description>Desaturación de oxígeno detectada</description>
      <patient_id>ae15cd87-5ac2-4f90-8712-184b02c541a5</patient_id>
      <patient_name>Valeria Ortiz</patient_name>
      <type_code>DESAT</type_code>
      <type_description>Desaturación de oxígeno</type_description>
      <level_code>medium</level_code>
      <level_label>Medio</level_label>
      <status_code>ack</status_code>
      <status_description>Reconocida por usuario</status_description>
    </alert>
  </alerts>
</response>
```

**Ejemplo de Uso:**

```bash
# Todas las alertas
curl -X GET "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/alerts/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"

# Solo alertas críticas no resueltas
curl -X GET "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/alerts/?level_code=critical&status_code=created" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"
```

---

### 20. Obtener Detalle de Alerta

Obtiene información completa de una alerta específica.

```http
GET /admin/organizations/{org_id}/alerts/{alert_id}
```

**Respuesta Exitosa (200):**

```xml
<response>
  <alert>
    <id>c20277df-7c2f-417c-902e-776bf4bf74c3</id>
    <created_at>2025-11-02 20:26:31.913680</created_at>
    <description>Posible fibrilación detectada por CardioNet</description>
    <patient_id>8c9436b4-f085-405f-a3d2-87cb1d1cf097</patient_id>
    <patient_name>María Delgado</patient_name>
    <type_code>ARRHYTHMIA</type_code>
    <type_description>Ritmo cardiaco anómalo</type_description>
    <level_code>high</level_code>
    <level_label>Alto</level_label>
    <status_code>resolved</status_code>
    <status_description>Resuelta</status_description>
    <model_name>CardioNet Arrhythmia v1.3.0</model_name>
    <inference_score>0.873</inference_score>
  </alert>
  <acknowledgements>
    <ack>
      <ack_by_user_id>f2d80568-7d45-4d75-80e3-b85c1b1f2497</ack_by_user_id>
      <ack_by_name>Ana Ruiz</ack_by_name>
      <ack_at>2025-11-02 20:40:00.000000</ack_at>
      <note>Revisando telemetría en tiempo real</note>
    </ack>
  </acknowledgements>
  <resolution>
    <resolved_by_user_id>f2d80568-7d45-4d75-80e3-b85c1b1f2497</resolved_by_user_id>
    <resolved_by_name>Ana Ruiz</resolved_by_name>
    <resolved_at>2025-11-02 21:30:00.000000</resolved_at>
    <outcome>Resolved</outcome>
    <note>Paciente estable, seguimiento de rutina</note>
  </resolution>
</response>
```

---

### 21. Acusar Recibo de Alerta

Marca una alerta como reconocida (acknowledged).

```http
POST /admin/organizations/{org_id}/alerts/{alert_id}/ack
```

**Body (JSON):**

```json
{
  "note": "Revisando paciente ahora"
}
```

**Respuesta Exitosa (200):**

```xml
<response>
  <message>Alert acknowledged successfully</message>
  <acknowledgement>
    <alert_id>c20277df-7c2f-417c-902e-776bf4bf74c3</alert_id>
    <ack_by_user_id>f2d80568-7d45-4d75-80e3-b85c1b1f2497</ack_by_user_id>
    <ack_at>2025-11-04 23:15:00.000000</ack_at>
    <note>Revisando paciente ahora</note>
  </acknowledgement>
</response>
```

---

### 22. Resolver Alerta

Marca una alerta como resuelta.

```http
POST /admin/organizations/{org_id}/alerts/{alert_id}/resolve
```

**Body (JSON):**

```json
{
  "outcome": "Resolved",
  "note": "Paciente estabilizado tras intervención"
}
```

**Campos:**
- `outcome` (requerido) - Resultado: `Resolved`, `Escalated`, `Stabilized`, `False Positive`
- `note` (opcional) - Notas sobre la resolución

**Respuesta Exitosa (200):**

```xml
<response>
  <message>Alert resolved successfully</message>
  <resolution>
    <alert_id>c20277df-7c2f-417c-902e-776bf4bf74c3</alert_id>
    <resolved_by_user_id>f2d80568-7d45-4d75-80e3-b85c1b1f2497</resolved_by_user_id>
    <resolved_at>2025-11-04 23:30:00.000000</resolved_at>
    <outcome>Resolved</outcome>
    <note>Paciente estabilizado tras intervención</note>
  </resolution>
</response>
```

---

## ❌ Códigos de Error

Todas las respuestas de error siguen el mismo formato XML:

### Error 400 - Bad Request

```xml
<response>
  <error>
    <code>bad_request</code>
    <message>Missing required field: person_name</message>
  </error>
</response>
```

### Error 401 - Unauthorized

```xml
<response>
  <error>
    <code>unauthorized</code>
    <message>Missing or invalid authentication token</message>
  </error>
</response>
```

### Error 403 - Forbidden

```xml
<response>
  <error>
    <code>forbidden</code>
    <message>User does not have org_admin role for this organization</message>
  </error>
</response>
```

### Error 404 - Not Found

```xml
<response>
  <error>
    <code>not_found</code>
    <message>Patient not found or does not belong to this organization</message>
  </error>
</response>
```

### Error 409 - Conflict

```xml
<response>
  <error>
    <code>conflict</code>
    <message>Patient with this email already exists</message>
  </error>
</response>
```

### Error 500 - Internal Server Error

```xml
<response>
  <error>
    <code>internal_error</code>
    <message>An unexpected error occurred. Please try again.</message>
  </error>
</response>
```

---

## 🧪 Testing

### Suite de Pruebas de Integración

El servicio incluye un script completo de pruebas end-to-end:

```bash
# Ejecutar suite completa
./test_admin_service.sh

# O desde el Makefile
make test
```

**Cobertura de Tests:**

1. ✅ Autenticación y autorización
2. ✅ Listar organizaciones
3. ✅ Detalle de organización
4. ✅ Dashboard con métricas
5. ✅ Crear paciente (XML)
6. ✅ Listar pacientes
7. ✅ Detalle de paciente
8. ✅ Crear equipo de cuidado
9. ✅ Listar equipos
10. ✅ Tipos de relación de cuidadores
11. ✅ Listar alertas
12. ✅ Validación de permisos (401, 403)

### Usuarios de Prueba (seed.sql)

```bash
# Usuario org_admin
Email: ana.ruiz@heartguard.com
Password: Demo#2025
Org: FAM-001 (Familia García)

# Usuario org_viewer
Email: sofia.care@heartguard.com
Password: Demo#2025
Org: CLIN-001
```

### Ejemplo de Flujo de Testing

```bash
# 1. Iniciar servicios
cd /home/azureuser/HeartGuard/services
make start

# 2. Login y obtener token
TOKEN=$(curl -s -X POST http://localhost:5001/auth/login/user \
  -H "Content-Type: application/json" \
  -d '{"email":"ana.ruiz@heartguard.com","password":"Demo#2025"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Listar organizaciones
curl -X GET "http://localhost:8080/admin/organizations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"

# 4. Ver dashboard
curl -X GET "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/dashboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/xml"

# 5. Crear paciente
curl -X POST "http://localhost:8080/admin/organizations/393b7d02-d3f8-48e5-829f-e03eb8c13541/patients/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/xml" \
  -d '{
    "person_name": "Test Patient",
    "email": "test@example.com",
    "password": "Test123!",
    "birthdate": "1990-01-01"
  }'
```

---

## 📚 Recursos Adicionales

- **Arquitectura**: `/services/README.md` - Documentación del sistema completo
- **Gateway**: `/services/gateway/README.md` - Documentación del API Gateway
- **Auth Service**: `/services/auth/README.md` - Documentación de autenticación
- **Base de Datos**: `/db/init.sql` y `/db/seed.sql` - Schema y datos de prueba

---

## 🤝 Soporte

Para reportar bugs o solicitar features, contacta al equipo de desarrollo.

**Version**: 1.0.0  
**Última actualización**: Noviembre 2025
