# HeartGuard Microservices Architecture Plan

## 1. Visión general
El dominio médico descrito en `db/init.sql` se segmenta en contextos delimitados (bounded contexts) que alinean responsabilidades de negocio con servicios Flask independientes. Cada servicio expone APIs REST bilingües (JSON/XML) y participa en flujos síncronos vía HTTP y asíncronos mediante RabbitMQ, operando sobre su propia base de datos ("database per service") dentro de una instancia PostgreSQL multi‐schema. El despliegue está orientado a la VM pública `34.70.7.33`, con puertos consecutivos a partir del 5000.

## 2. Diagrama de arquitectura
```
                   Internet / VPN
                   +--------------+
  Web (XML) ------>|              |
  Mobile (JSON) -->|   Gateway    |<---------------------------+
                   |   :5000      |                            |
                   +-------+------+                            |
                           |                                   |
            -------------------------------                     |
            |        |       |       |    |                    |
            v        v       v       v    v                    |
         Auth     Organization  User  Patient  Device          |
         :5001       :5002     :5003   :5004   :5005           |
            |           |        |        |        |           |
            |           |        |        |        |           |
            |           |        |        |        |           |
            v           v        v        v        v           |
          Postgres schemas: auth, organization, user, patient, device

            +-------------------+       +-------------------+
            | Inference :5007   |<----->| Alert :5008       |
            +---------+---------+       +-----+-------------+
                      |                         |
                      v                         v
                RabbitMQ (async bus) <----- Notification :5009
                      |
                      v
                 Audit :5011

            +---------------------------+
            | Media :5010 (GCS bucket)  |
            +-------------+-------------+
                          |
                          v
                 Google Cloud Storage

            +---------------------------+
            | Influx Service :5006      |
            +-------------+-------------+
                          |
                          v
                       InfluxDB

Otros componentes compartidos: Redis (rate limiting, tokens), Postgres (multischema), RabbitMQ, stack de métricas (Prometheus scraping `/metrics`).
```

## 3. Bounded contexts y responsabilidades
| Servicio | Tablas / entidades núcleo (desde `db/init.sql`) | Responsabilidades clave |
|----------|--------------------------------------------------|-------------------------|
| **Gateway (5000)** | N/A (solo configuración) | Validación JWT y RBAC central, CORS, rate limiting, routing hacia servicios backend, agregación de métricas, `/gateway/health`. |
| **Auth (5001)** | `users`, `roles`, `permissions`, `role_permission`, `user_roles`, `refresh_tokens`, `user_statuses`, `platforms`, `service_statuses` | Registro, autenticación, emisión/renovación de tokens, administración de roles y permisos globales. |
| **Organization (5002)** | `organizations`, `org_roles`, `org_invitations`, `org_contacts`, `org_settings`, `org_brands` | Gestión de la organización propietaria del sistema, invitaciones internas, branding y políticas. |
| **User (5003)** | `user_profiles`, `user_preferences`, `user_org_membership`, `user_devices` | Perfil del usuario de la aplicación, preferencias, asociación con la organización. |
| **Patient (5004)** | `patients`, `care_teams`, `care_team_member`, `caregiver_patient`, `patient_metrics`, `patient_goals` | Gestión del sujeto clínico, equipos de cuidado y cuidadores. |
| **Device (5005)** | `device_types`, `devices`, `signal_streams`, `timeseries_binding`, `device_assignments`, `device_health` | Inventario y configuración de dispositivos y su vinculación a series de tiempo. |
| **Influx Service (5006)** | Integración con InfluxDB (sin tablas SQL) | Abstracción de ingestión y consultas sobre series temporales, gestión de buckets y políticas de retención. |
| **Inference (5007)** | `models`, `model_versions`, `event_types`, `inferences` | Registro de modelos y resultados de inferencia; consumo de streams/eventos. |
| **Alert (5008)** | `alerts`, `alert_status`, `alert_assignment`, `alert_ack`, `alert_resolution`, `alert_channels`, `alert_levels`, `risk_levels` | Orquestación completa del ciclo de vida de alertas clínicas. |
| **Notification (5009)** | `push_devices`, `alert_delivery`, `delivery_statuses` | Entrega de notificaciones multicanal y seguimiento de estado. |
| **Media (5010)** | `media_assets`, `media_tags` | Gestión de archivos en GCS, URLs firmadas, metadatos. |
| **Audit (5011)** | `audit_logs` | Recepción de eventos auditables desde cola, persistencia y consulta. |

## 4. Estructura de carpetas
```
Microservicios/
├── PLAN.md
├── docker-compose.yml
├── .env.example
├── start_services.sh
├── stop_services.sh
├── validate_endpoints.sh
├── common/
│   ├── __init__.py
│   ├── config.py          # carga .env, utilidades comunes
│   ├── auth.py            # JWT utilities, RBAC helpers
│   ├── middleware.py      # logging, request_id, error handling
│   ├── serialization.py   # negociación JSON/XML
│   ├── errors.py          # excepciones y manejador uniforme
│   ├── responses.py       # plantillas estándar
│   └── observability.py   # métricas y trazas
├── gateway/
│   ├── app.py
│   ├── routes.py
│   ├── config.py
│   ├── requirements.txt
│   └── Dockerfile
├── auth_service/
│   └── ...
├── organization_service/
│   └── ...
├── user_service/
│   └── ...
├── patient_service/
│   └── ...
├── device_service/
│   └── ...
├── influx_service/
│   └── ...
├── inference_service/
│   └── ...
├── alert_service/
│   └── ...
├── notification_service/
│   └── ...
├── media_service/
│   └── ...
├── audit_service/
│   └── ...
└── schemas/
    ├── json/
    │   ├── user.json
    │   ├── organization.json
    │   ├── patient.json
    │   ├── device.json
    │   ├── alert.json
    │   ├── inference.json
    │   ├── media_item.json
    │   └── timeseries_point.json
    └── xsd/
        └── (mismos nombres .xsd)
```

## 5. Flujos de interacción
### 5.1 Flujos síncronos (HTTP)
1. **Autenticación**: cliente → Gateway → Auth (login/refresh). El Gateway recibe tokens y los guarda en encabezados para posteriores solicitudes.
2. **Gestión de organización**: admin web (XML) → Gateway → Organization (CRUD de configuración).
3. **Perfil de usuario**: app móvil (JSON) → Gateway → User.
4. **Gestión de pacientes y dispositivos**: clínico/admin → Gateway → Patient/Device Services.
5. **Consultas de series temporales**: servicio Device / cliente → Gateway → Influx Service (`/write`, `/query`).
6. **Descarga de media**: cliente → Gateway → Media (genera URL firmada, redirige).

### 5.2 Flujos asíncronos (RabbitMQ)
1. **Inferencia**: Device Service emite evento `signal_stream.bound` con metadata de `timeseries_binding`. Inference Service consume, ejecuta modelo y publica `inference.generated`.
2. **Alertas**: Inference Service publica `inference.alert_candidate`. Alert Service consume, crea alertas y envía `alert.created`.
3. **Notificaciones**: Alert Service publica `alert.notify`. Notification Service envía push/SMS/email según `alert_channels`, confirma `alert.delivery_update`.
4. **Auditoría**: Todos los servicios publican eventos `audit.log` en fanout exchange; Audit Service consume, valida y persiste en `audit_logs`.

## 6. Manejo uniforme de errores
- `common.errors` define excepciones (`ValidationError`, `AuthError`, `NotFoundError`, `ConflictError`, `RateLimitError`, `ServiceUnavailableError`).
- Middleware global registra errores con `request_id`, `user_id` y detalles, devolviendo respuesta homogénea:
```json
{
  "status": "error",
  "code": 400,
  "error": {
    "id": "HG-VAL-001",
    "message": "Datos inválidos",
    "details": [{"field": "email", "issue": "formato"}]
  }
}
```
XML equivalente mediante `dicttoxml`. Códigos HTTP alineados con RFC 7807 (a futuro se puede usar `application/problem+json`).

## 7. Seguridad
- **JWT**: HS256, `exp` (15 min) y refresh token (7 días). Claims incluyen `sub`, `roles`, `permissions`, `org_id`, `aud`.
- **Refresh tokens**: almacenados con hash en tabla `refresh_tokens` (Auth) y cacheados en Redis para revocación inmediata.
- **RBAC**: Gateway valida `roles`/`permissions` antes de enrutar; servicios aplican reglas de negocio específicas (p.ej. Patient Service exige `patient:write`).
- **CORS**: configurado con listas blancas por servicio (`ALLOWED_ORIGINS`). Gateway verifica `Origin` y añade encabezados `Access-Control-Allow-*`.
- **Rate limiting**: `flask-limiter` con backend Redis; límites por IP y por `user_id`.
- **Input sanitization**: validaciones con `marshmallow`, escapes y normalización; longitud máxima de payload (`MAX_CONTENT_LENGTH`).
- **TLS**: gestionado fuera de Docker (balanceador / ingress). Servicios escuchan en `0.0.0.0` solo dentro de red Docker.

## 8. Observabilidad
- **Logging estructurado**: `structlog` con `service`, `request_id`, `user_id`, `path`, `status`, `latency_ms`.
- **Request ID**: middleware genera UUID si el cliente no envía `X-Request-ID`.
- **Métricas**: `prometheus_flask_exporter` exponiendo `/metrics` (solo accesible dentro de red interna). Métricas clave: latencia por endpoint, tasa de errores, tamaño de payload, uso de cache.
- **Health Checks**: cada servicio tiene `/health` (liveness) y `/ready` (readiness). Gateway expone `/gateway/health`. Influx Service verifica conexión real (`client.ping()`).
- **Tracing (opcional)**: hooks para integrar OpenTelemetry (`OTEL_EXPORTER_OTLP_ENDPOINT`).

## 9. Gestión de configuración y credenciales
- `.env` carga variables específicas por servicio (puertos, secretos, URLs). Servicios leen mediante `python-dotenv` o inyección en contenedor.
- Credenciales sensibles (p.ej. `GOOGLE_APPLICATION_CREDENTIALS`) montadas como `docker secret` o volumen de solo lectura.

## 10. Pasos de despliegue en VM 34.70.7.33
1. Instalar Docker Engine y Docker Compose v2.
2. Clonar repositorio `HeartGuard` y copiar carpeta `Microservicios/` completa.
3. Crear archivo `.env` desde `.env.example` con valores reales.
4. Colocar credencial GCP (`service-account.json`) en `/etc/heartguard/gcp/sa.json` y ajustar permisos (600). El `docker-compose.yml` montará el archivo como secreto para `media_service`.
5. Abrir puertos 5000-5011 en firewall GCP (restringir por IP cuando sea posible).
6. Ejecutar `./start_services.sh` para construir e iniciar contenedores (`docker compose up -d --build`).
7. Verificar estado con `docker compose ps` y health checks (`curl http://34.70.7.33:5000/gateway/health`).
8. Configurar supervisión (systemd unit opcional) para reiniciar servicios.
9. Desde entorno local ejecutar `./validate_endpoints.sh --host 34.70.7.33` para validar disponibilidad JSON/XML.
10. Configurar backups: snapshots de Postgres (`pg_dump` por esquema), exportaciones de InfluxDB, versionado GCS.

## 11. Estrategia de datos y migraciones
- Cada servicio tiene esquema PostgreSQL independiente (`auth`, `organization`, `user`, `patient`, `device`, `inference`, `alert`, `notification`, `media`, `audit`). Docker compose incluye scripts de inicialización para crear esquemas y aplicar migraciones usando Alembic por servicio.
- Influx Service administra buckets (`heartguard_signals`, `heartguard_predictions`) mediante API.
- Migraciones versionadas en cada servicio (`migrations/` con Alembic).

## 12. Endpoints representativos y negociación de contenido
Cada servicio expone endpoints REST que aceptan/retornan JSON o XML según encabezado `Accept`. Ejemplo general:
```
GET /patients/{id}
Accept: application/json
Authorization: Bearer <token>
```
Respuesta JSON: `{"status":"success","data":{...}}`

Si `Accept: application/xml`, respuesta: `
<response>
  <status>success</status>
  <data>...</data>
</response>
`

Para escrituras (`POST/PUT/PATCH`) se valida `Content-Type` (JSON/XML) y se transforma internamente a diccionario normalizado previo a validación.

## 13. Operación del bus de eventos
- Exchanges por dominio: `inference.fanout`, `alert.direct`, `notification.topic`, `audit.fanout`.
- Mensajes en JSON estándar, incluyen cabeceras `content_type` y `x-request-id`.
- Retries gestionados mediante colas `retry` con TTL + DLX; errores definitivos van a cola `dead-letter`.

## 14. Estrategia de pruebas
- Tests unitarios: Pytest + coverage por servicio.
- Contract tests: JSON Schema/XSD validados contra respuestas.
- Smoke tests: script `validate_endpoints.sh`.
- Integración: pipelines CI ejecutan `docker compose run --rm <service> pytest`.

## 15. Consideraciones futuras
- Incorporar API Gateway dedicado (Kong/Traefik) si se requiere características avanzadas.
- Añadir OpenAPI generado (Swagger) con ejemplos JSON/XML.
- Integrar sistema de feature flags (p.ej. Unleash) si se amplía dominio.
- Hardening: limitar tamaño de archivos en Media, cifrado at rest (KMS) y rotación de secretos.

