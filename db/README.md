# HeartGuard Database (PostgreSQL + PostGIS)

Esquema relacional que soporta la plataforma HeartGuard: catálogos configurables, RBAC, auditoría, métricas, ubicaciones geográficas y objetos clínicos básicos. Todo el ciclo de vida (creación, seeds y health checks) se orquesta con el `Makefile` raíz.

## Stack y extensiones

-   PostgreSQL 14+
-   PostGIS (`CREATE EXTENSION ... SCHEMA heartguard`)
-   pgcrypto (UUID, `gen_random_uuid`, `crypt`)
-   Docker opcional (`docker-compose.yml` expone el contenedor `postgis/postgis:14-3.2`)

## Estructura de archivos

```
db/
├── init.sql   # Crea schema heartguard, roles, tablas, funciones
├── seed.sql   # Llena catálogos, roles, usuarios demo, auditoría, métricas
└── README.md  # Este documento
```

> El directorio `migrations/` contiene scripts de migración para actualizar esquemas existentes sin perder datos.

## Configuración desde `.env`

| Variable            | Uso                                         |
| ------------------- | ------------------------------------------- |
| `PGSUPER`           | Superusuario (por defecto `postgres`).      |
| `PGSUPER_PASS`      | Contraseña del superusuario.                |
| `PGHOST` / `PGPORT` | Host/puerto (en Docker: `127.0.0.1:5432`).  |
| `DBNAME`            | Nombre de la base destino (`heartguard`).   |
| `DBUSER`/`DBPASS`   | Rol de aplicación (`heartguard_app`).       |
| `DATABASE_URL`      | DSN usado por el backend y comandos `db-*`. |

El `Makefile` exporta automáticamente los valores al cargar `.env`.

## Ciclo de vida

| Paso | Comando          | Descripción                                                                                         |
| ---- | ---------------- | --------------------------------------------------------------------------------------------------- |
| 1    | `make up`        | Levanta Postgres/Redis vía Docker Compose.                                                          |
| 2    | `make db-init`   | Ejecuta `init.sql`: crea esquema, roles y funciones.                                                |
| 3    | `make db-seed`   | Aplica `seed.sql`: catálogos, usuarios demo, invitaciones, métricas.                                |
| 4    | `make db-health` | Queries de validación (`SELECT postgis_version()`, conteos de catálogos, existencia de superadmin). |
| 5    | `make db-psql`   | Acceso interactivo usando `DATABASE_URL`.                                                           |
| -    | `make db-reset`  | Equivalente a `dropdb` + init + seed.                                                               |
| -    | `make reset-all` | Baja contenedores, borra volúmenes y reconstruye todo.                                              |

## Componentes del esquema

### Catálogos parametrizables

Tablas como `user_statuses`, `alert_channels`, `alert_levels`, `service_statuses`, `org_roles`, etc. Se gestionan vía los endpoints `/v1/superadmin/catalogs/*`. Las funciones `heartguard.sp_catalog_*` estandarizan CRUD y evitan el uso de enums fijos.

### Seguridad y multi-tenant

-   `roles`, `permissions`, `role_permission`
-   `users`, `user_role`
-   `organizations`, `org_roles`, `user_org_membership`
-   Refresh tokens (`refresh_tokens`), revocaciones (`session_revocations`) y API keys (`api_keys`, `api_key_permission`)

### Ubicaciones y movilidad

-   `patient_locations` almacena localizaciones manuales o importadas para pacientes demo, conservando metadatos (`source`, `accuracy_m`, `recorded_at`) para reporting.

### Dominio clínico demo

Incluye entidades base (`patients`, `care_teams`, `caregiver_patient`, `alert_types`, `event_types`) útiles para métricas y vistas futuras.

**Normalización:** La tabla `alerts` obtiene `org_id` derivándolo de `patients.org_id` mediante JOIN en los stored procedures, respetando la Tercera Forma Normal (3FN) y eliminando dependencias transitivas.

### Auditoría y métricas

-   `audit_logs` almacena eventos generados por el backend (`ORG_CREATE`, `APIKEY_CREATE`, etc.).
-   Procedimientos `sp_metrics_*` devuelven agregados para el dashboard (overview, actividad reciente, breakdowns).

## Seeds incluidos

`seed.sql` crea un entorno demo completo:

-   Usuario superadmin (`admin@heartguard.com` / `Admin#2025`).
-   Organizaciones (`FAM-001`, `CLIN-001`, `OPS-001`).
-   Usuarios adicionales con distintos roles globales y estados (`active`, `pending`, `blocked`).
-   Invitaciones demo en varios estados (pendiente, usada, revocada).
-   Servicios y health checks históricos.
-   Auditoría de los últimos días.
-   Ubicaciones de prueba para pacientes (coordenadas con metadatos de fuente y precisión).

La semilla es idempotente: usa `ON CONFLICT DO NOTHING` o actualizaciones para asegurar que re-ejecutar `make db-seed` mantenga la coherencia.

## Consultas útiles

```sql
-- Catálogo de roles de organización
SELECT code, label FROM heartguard.org_roles ORDER BY code;

-- Usuarios y roles globales
SELECT u.email, r.name
FROM users u
JOIN user_role ur ON ur.user_id = u.id
JOIN roles r ON r.id = ur.role_id;

-- Auditoría reciente
SELECT action, entity, ts FROM audit_logs ORDER BY ts DESC LIMIT 20;

-- Tokens de invitación pendientes
SELECT token, expires_at FROM org_invitations WHERE used_at IS NULL AND revoked_at IS NULL;
```

## Health check

`make db-health` ejecuta:

-   `SELECT 1` (ping general).
-   `SHOW search_path` (debe incluir `heartguard`).
-   `SELECT postgis_version();` (verifica extensión).
-   Conteos de catálogos (`roles`, `permissions`, `user_statuses`, `alert_levels`).
-   Verificación del usuario `admin@heartguard.com`.

Si alguna consulta falla, el comando devuelve un error (`ON_ERROR_STOP=1`).

## Usuario superadmin demo

-   Email: `admin@heartguard.com`
-   Password: `Admin#2025`
-   Rol global: `superadmin`

Se crea/actualiza en cada seed. Modifica la sección correspondiente de `seed.sql` para cambiar credenciales en PRODUCCIÓN.

## Buenas prácticas

-   Mantén `.env` fuera de control de versiones; usa `.env.example` como referencia.
-   Para integraciones CI/CD, considera dividir `init.sql` en migraciones incrementales.
-   PostGIS está habilitado desde el inicio para evitar migraciones posteriores aunque no todas las tablas lo utilicen aún.
-   Controla los tiempos de espera (`statement_timeout`, `idle_in_transaction_session_timeout`) que `init.sql` establece al final del script.
-   **Normalización 3FN:** Evita duplicar datos derivables; la tabla `alerts` ya no almacena `org_id` directamente, se obtiene mediante JOIN con `patients`.

## Migraciones

Para aplicar cambios a bases existentes sin perder datos:

```bash
# Ejecutar migración específica
psql $DATABASE_URL -f db/migrations/001_remove_alerts_org_id.sql
```

Las migraciones disponibles:

-   `001_remove_alerts_org_id.sql`: Elimina columna redundante `org_id` de `alerts` y actualiza stored procedures para obtenerla mediante JOIN.

## Problemas comunes

-   **`permission denied` al ejecutar seeds:** confirma que `PGSUPER` tenga privilegios sobre la base o reconstruye con `make reset-all`.
-   **`sp_catalog_resolve` arroja excepción:** el catálogo no existe; revisa la lista soportada en `init.sql`.
-   **`postgis_version()` falla:** reinstala extensión dentro del contenedor: `docker compose exec postgres psql -c 'CREATE EXTENSION postgis;'`.
