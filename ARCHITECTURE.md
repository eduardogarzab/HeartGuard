# Arquitectura de Microservicios HeartGuard

Documentación de la arquitectura de microservicios de la plataforma HeartGuard.

## Visión General

HeartGuard utiliza una arquitectura de microservicios donde cada servicio tiene una responsabilidad específica y se comunica a través de HTTP/REST APIs.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Clientes                                 │
│  (Web Dashboard, Mobile App, Third-party Integrations)          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ HTTPS
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway :8000                             │
│  - Enrutamiento                                                  │
│  - CORS                                                          │
│  - Rate Limiting (futuro)                                        │
│  - Logging centralizado                                          │
└──────┬──────────────────────────────────────────────────────────┘
       │
       │ HTTP interno
       │
       ├─────────────────────┬──────────────────────┬──────────────
       │                     │                      │
       ↓                     ↓                      ↓
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│Auth Service │      │   Futuro    │      │   Futuro    │
│   :5001     │      │  Servicio   │      │  Servicio   │
│             │      │             │      │             │
│- Registro   │      │- Analytics  │      │- Alertas    │
│- Login      │      │- Reportes   │      │- Notif.     │
│- JWT        │      │             │      │             │
└─────┬───────┘      └─────┬───────┘      └─────┬───────┘
      │                    │                      │
      └────────────────────┴──────────────────────┘
                           │
                           ↓
                ┌──────────────────────┐
                │   PostgreSQL :5432   │
                │   (Base de Datos     │
                │    Compartida)       │
                └──────────────────────┘
```

## Componentes

### 1. API Gateway (Puerto 8000)

**Responsabilidad**: Punto de entrada único para todos los clientes.

**Tecnología**: Python/Flask

**Funciones**:
- Enrutamiento de peticiones a microservicios
- Gestión de CORS
- Logging de todas las peticiones
- Normalización de errores
- (Futuro) Rate limiting, caching, circuit breaker

**Endpoints expuestos**:
```
GET  /health/              → Health check del gateway
POST /auth/register/user   → Proxy a Auth Service
POST /auth/register/patient → Proxy a Auth Service
POST /auth/login/user      → Proxy a Auth Service
POST /auth/login/patient   → Proxy a Auth Service
GET  /auth/verify          → Proxy a Auth Service
GET  /auth/me              → Proxy a Auth Service
POST /auth/refresh         → Proxy a Auth Service
```

**Ubicación**: `services/gateway/`

**Documentación**: [Gateway README](services/gateway/README.md)

### 2. Auth Service (Puerto 5001)

**Responsabilidad**: Gestión de identidad, autenticación y autorización.

**Tecnología**: Python/Flask

**Funciones**:
- Registro de usuarios (staff) y pacientes
- Autenticación con JWT (HS256)
- Gestión de tokens (access + refresh)
- Verificación de tokens
- Manejo de invitaciones a organizaciones
- Separación de cuentas: usuarios vs pacientes

**Base de Datos**:
- Tabla `users` (staff: médicos, enfermeras, administradores)
- Tabla `patients` (pacientes del sistema)
- Tabla `user_org_membership` (relación usuario-organización)
- Tabla `org_invitations` (invitaciones pendientes)
- Tabla `roles` (roles del sistema: superadmin, user, org_admin, org_viewer)

**JWT Payloads**:

Usuario (staff):
```json
{
  "user_id": "uuid",
  "account_type": "user",
  "email": "doctor@hospital.com",
  "name": "Dr. Juan Pérez",
  "system_role": "user",
  "org_memberships": [
    {
      "org_id": "uuid",
      "org_name": "Hospital XYZ",
      "role_code": "org_admin"
    }
  ],
  "token_type": "access",
  "iat": 1234567890,
  "exp": 1234568790
}
```

Paciente:
```json
{
  "patient_id": "uuid",
  "account_type": "patient",
  "email": "paciente@example.com",
  "name": "María García",
  "org_id": "uuid",
  "org_code": "FAM-001",
  "org_name": "Familia García",
  "risk_level": "medium",
  "token_type": "access",
  "iat": 1234567890,
  "exp": 1234568790
}
```

**Ubicación**: `services/auth/`

**Documentación**: [Auth Service README](services/auth/README.md)

### 3. Superadmin API (Puerto 8080)

**Responsabilidad**: Panel de administración para superusuarios.

**Tecnología**: Go/Gin

**Funciones**:
- Gestión de usuarios y roles
- Gestión de organizaciones
- Vista de pacientes y dispositivos
- Logs de auditoría
- Panel de monitoreo
- Invitaciones a organizaciones

**Ubicación**: `backend/`

**Nota**: Este servicio NO debe ser expuesto públicamente. Solo accesible internamente o vía VPN.

### 4. Base de Datos PostgreSQL (Puerto 5432)

**Responsabilidad**: Almacenamiento persistente compartido.

**Tecnología**: PostgreSQL 14+

**Base de Datos**: `heartguard`

**Usuario**: `heartguard_app`

**Esquema Principal**:
- `users` - Usuarios del sistema (staff)
- `patients` - Pacientes
- `organizations` - Organizaciones/familias
- `roles` - Roles del sistema
- `user_org_membership` - Membresías de usuarios en organizaciones
- `org_invitations` - Invitaciones pendientes
- `devices` - Dispositivos IoT
- `alert_types` - Tipos de alertas
- `alerts` - Alertas generadas
- (más tablas...)

**Ubicación**: `db/`

## Flujos de Autenticación

### Flujo 1: Registro y Login de Usuario (Staff)

```
Cliente                Gateway              Auth Service         DB
  │                      │                      │                 │
  │ POST /auth/register/user                    │                 │
  ├─────────────────────>│                      │                 │
  │                      │ POST /auth/register/user               │
  │                      ├─────────────────────>│                 │
  │                      │                      │ INSERT users    │
  │                      │                      ├────────────────>│
  │                      │                      │<────────────────┤
  │                      │<─────────────────────┤                 │
  │<─────────────────────┤                      │                 │
  │ 201 Created          │                      │                 │
  │ {user_id, email}     │                      │                 │
  │                      │                      │                 │
  │ POST /auth/login/user │                     │                 │
  ├─────────────────────>│                      │                 │
  │                      │ POST /auth/login/user│                 │
  │                      ├─────────────────────>│                 │
  │                      │                      │ SELECT users    │
  │                      │                      │ + memberships   │
  │                      │                      ├────────────────>│
  │                      │                      │<────────────────┤
  │                      │                      │ Verify password │
  │                      │                      │ Generate JWT    │
  │                      │<─────────────────────┤                 │
  │<─────────────────────┤                      │                 │
  │ 200 OK               │                      │                 │
  │ {access_token,       │                      │                 │
  │  refresh_token}      │                      │                 │
```

### Flujo 2: Registro y Login de Paciente

```
Cliente                Gateway              Auth Service         DB
  │                      │                      │                 │
  │ POST /auth/register/patient                 │                 │
  ├─────────────────────>│                      │                 │
  │                      │ POST /auth/register/patient            │
  │                      ├─────────────────────>│                 │
  │                      │                      │ INSERT patients │
  │                      │                      ├────────────────>│
  │                      │                      │<────────────────┤
  │                      │<─────────────────────┤                 │
  │<─────────────────────┤                      │                 │
  │ 201 Created          │                      │                 │
  │ {patient_id, org}    │                      │                 │
  │                      │                      │                 │
  │ POST /auth/login/patient                    │                 │
  ├─────────────────────>│                      │                 │
  │                      │ POST /auth/login/patient               │
  │                      ├─────────────────────>│                 │
  │                      │                      │ SELECT patients │
  │                      │                      │ + org           │
  │                      │                      ├────────────────>│
  │                      │                      │<────────────────┤
  │                      │                      │ Verify password │
  │                      │                      │ Generate JWT    │
  │                      │<─────────────────────┤                 │
  │<─────────────────────┤                      │                 │
  │ 200 OK               │                      │                 │
  │ {access_token,       │                      │                 │
  │  refresh_token}      │                      │                 │
```

### Flujo 3: Request Autenticado

```
Cliente                Gateway              Auth Service       Other Service
  │                      │                      │                 │
  │ GET /some/endpoint   │                      │                 │
  │ Authorization:       │                      │                 │
  │ Bearer <token>       │                      │                 │
  ├─────────────────────>│                      │                 │
  │                      │ GET /auth/verify     │                 │
  │                      ├─────────────────────>│                 │
  │                      │                      │ Verify JWT      │
  │                      │<─────────────────────┤                 │
  │                      │ {valid: true, ...}   │                 │
  │                      │                      │                 │
  │                      │ GET /some/endpoint   │                 │
  │                      ├────────────────────────────────────────>│
  │                      │                      │                 │
  │                      │<────────────────────────────────────────┤
  │<─────────────────────┤                      │                 │
```

## Seguridad

### Autenticación

- **JWT con HS256**: Tokens firmados con clave secreta compartida
- **Access Token**: 15 minutos de duración
- **Refresh Token**: 7 días de duración
- **Passwords**: Hasheadas con bcrypt (12 rounds)

### Autorización

Sistema de roles en dos niveles:

**Roles de Sistema** (columna `users.role_code`):
- `superadmin`: Acceso total al sistema, panel de superadmin
- `user`: Usuario estándar (médico, enfermera, etc.)

**Roles de Organización** (columna `user_org_membership.role_code`):
- `org_admin`: Administrador de la organización
- `org_viewer`: Solo lectura en la organización

### CORS

- Gateway tiene CORS habilitado
- En producción configurar lista específica de orígenes permitidos

### HTTPS

- En producción usar proxy reverso (nginx/traefik) con certificados SSL/TLS
- Desactivar HTTP, solo HTTPS

## Configuración de Puertos

| Servicio | Puerto | Expuesto Públicamente |
|----------|--------|----------------------|
| Gateway | 8000 | ✅ Sí (único punto de entrada) |
| Auth Service | 5001 | ❌ No (solo interno) |
| Superadmin API | 8080 | ❌ No (solo VPN/intranet) |
| PostgreSQL | 5432 | ❌ No (solo interno) |

## Variables de Entorno

### Gateway
```env
FLASK_DEBUG=0
FLASK_SECRET_KEY=<random-secret>
GATEWAY_SERVICE_TIMEOUT=10
AUTH_SERVICE_URL=http://localhost:5001
```

### Auth Service
```env
FLASK_DEBUG=0
FLASK_APP=src/auth/app.py
DATABASE_URL=postgresql://user:pass@localhost:5432/heartguard
JWT_SECRET=<random-secret>
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=604800
```

### Superadmin API (Go)
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=heartguard_app
DB_PASSWORD=<password>
DB_NAME=heartguard
JWT_SECRET=<same-as-auth-service>
PORT=8080
```

## Despliegue

### Desarrollo

```bash
# 1. Iniciar Base de Datos
docker-compose up -d postgres

# 2. Iniciar Auth Service
cd services/auth
make dev

# 3. Iniciar Gateway
cd services/gateway
make dev

# 4. Iniciar Superadmin (opcional)
cd backend
make run
```

### Producción con Docker

```bash
# Usar docker-compose.yml en la raíz del proyecto
docker-compose up -d

# Servicios disponibles:
# - gateway: http://localhost:8000
# - auth: http://localhost:5001 (interno)
# - superadmin: http://localhost:8080 (interno)
# - postgres: localhost:5432 (interno)
```

### Producción con Kubernetes

Ver [k8s/](../k8s/) para manifiestos de Kubernetes.

## Monitoreo y Observabilidad

### Logs

Todos los servicios logean a stdout en formato estructurado:

```
2025-11-02 23:40:33 INFO [gateway] GET /health/ 200 5ms
2025-11-02 23:40:34 INFO [auth] POST /auth/login/user 200 45ms user_id=xyz
```

### Métricas (Futuro)

- Prometheus para recolección de métricas
- Grafana para dashboards
- Métricas clave:
  - Latencia (p50, p95, p99)
  - Throughput (requests/segundo)
  - Tasa de error
  - Disponibilidad

### Tracing (Futuro)

- Jaeger o Zipkin para tracing distribuido
- Correlación de requests entre servicios

## Testing

### Unit Tests

Cada servicio tiene sus propias pruebas:

```bash
# Gateway
cd services/gateway && make test

# Auth Service
cd services/auth && pytest

# Superadmin
cd backend && go test ./...
```

### Integration Tests

Scripts de pruebas end-to-end:

```bash
# Probar Gateway
cd services/gateway && ./test_gateway.sh

# Probar Auth Service
cd services/auth && ./test_auth_service.sh
```

### Load Testing (Futuro)

```bash
# Usar k6, locust o similar
k6 run load-test.js
```

## Troubleshooting

### Gateway no puede conectar a Auth Service

```bash
# Verificar que Auth Service esté corriendo
curl http://localhost:5001/health/

# Verificar variable de entorno
echo $AUTH_SERVICE_URL

# Ver logs del Gateway
tail -f /tmp/gateway.log
```

### Auth Service falla al conectar a DB

```bash
# Verificar PostgreSQL
docker ps | grep postgres

# Probar conexión
PGPASSWORD=dev_change_me psql -h localhost -U heartguard_app -d heartguard -c "SELECT 1;"

# Ver logs
docker logs <postgres-container-id>
```

### JWT inválido entre servicios

```bash
# Verificar que JWT_SECRET sea el mismo en Auth Service y otros servicios
echo $JWT_SECRET  # En cada servicio

# Verificar expiración de tokens
# Access tokens: 15 min
# Refresh tokens: 7 días
```

## Roadmap

### Q1 2026
- [ ] Implementar servicio de Alertas (notificaciones push, email, SMS)
- [ ] Implementar servicio de Analytics (reportes, dashboards)
- [ ] Agregar rate limiting al Gateway
- [ ] Implementar cache distribuido (Redis)

### Q2 2026
- [ ] Implementar servicio de Streaming (datos en tiempo real de dispositivos)
- [ ] Agregar circuit breaker al Gateway
- [ ] Implementar tracing distribuido (Jaeger)
- [ ] Despliegue en Kubernetes

### Q3 2026
- [ ] Implementar servicio de ML/AI (predicción de riesgos)
- [ ] Agregar métricas con Prometheus
- [ ] Implementar API GraphQL (opcional)
- [ ] Certificación ISO 27001

## Contribuir

Ver [CONTRIBUTING.md](../CONTRIBUTING.md) en la raíz del proyecto.

## Licencia

Propiedad de HeartGuard. Todos los derechos reservados.
