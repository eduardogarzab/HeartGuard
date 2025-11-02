# HeartGuard Superadmin

Servicio en Go que renderiza el panel de superadministración de HeartGuard completamente del lado del servidor (SSR). Utiliza sesiones firmadas (JWT corto almacenado en cookie HttpOnly), Redis para rate limiting y revocaciones de sesión, y PostgreSQL/PostGIS como persistencia.

## Stack

-   Go 1.22 (`chi` para routing, `zap` para logging, `pgx` para Postgres y `go-redis` para Redis).
-   html/template con `internal/ui.Renderer` para componer vistas SSR.
-   Redis para sesiones, flash messages y rate limiting per-IP.
-   PostgreSQL 14 + PostGIS (schema `heartguard`).
-   Archivos estáticos (`ui/assets`) servidos desde el mismo proceso.
-   Middleware de seguridad: `LoopbackOnly`, cabeceras seguras, CSRF compatible con formularios `multipart/form-data` y `application/x-www-form-urlencoded`.

## Variables de entorno

| Variable            | Descripción                                                    |
| ------------------- | -------------------------------------------------------------- |
| `DATABASE_URL`      | DSN completo (usa `sslmode=disable` en local).                 |
| `HTTP_ADDR`         | Dirección:puerto del servidor (ej. `:8080`).                   |
| `ENV`               | `dev` ⇒ `zap.NewDevelopment`, `prod` ⇒ `zap.NewProduction`.    |
| `JWT_SECRET`        | Clave simétrica (≥32 bytes).                                   |
| `ACCESS_TOKEN_TTL`  | TTL del token de sesión (15m por defecto).                     |
| `REFRESH_TOKEN_TTL` | TTL de refresh tokens (se usan para revocaciones anticipadas). |
| `REDIS_URL`         | DSN `redis://host:port/db`.                                    |
| `RATE_LIMIT_RPS`    | Requests por segundo antes de aplicar burst.                   |
| `RATE_LIMIT_BURST`  | Créditos extra por ventana de 1s.                              |

El arranque falla si `DATABASE_URL`, `JWT_SECRET` o `REDIS_URL` están vacíos.

## Ejecutar en local

```sh
cp .env.example .env
make up             # Postgres + Redis
make db-init
make db-seed
make tidy
make dev            # go run ./cmd/superadmin-api
```

Comandos útiles:

-   `make lint` ⇒ `go vet ./...`
-   `make build` ⇒ binario Linux (`GOOS=linux`, `GOARCH=amd64`).
-   `make reset-all` ⇒ reinicia contenedores y vuelve a aplicar init/seed.

## Health y observabilidad

-   `GET /healthz` responde `200 OK` cuando `Repo.Ping` contra Postgres es exitoso.
-   Logging estructurado (`zap`) con nivel según `ENV`.
-   Middleware de rate limiting expone `Retry-After` y `X-RateLimit-*` cuando se alcanza el límite.

## Autenticación y sesiones

1. **Formulario** `GET /login`

-   Genera token CSRF invitado. Si la sesión ya está activa, redirige a `/superadmin/dashboard`.

2. **Inicio de sesión** `POST /login`

-   Verifica CSRF, busca usuario por email, compara hashes bcrypt y confirma rol `superadmin`.
-   Emite cookie `hg_session` (JWT corto) + registra flash de bienvenida.

3. **Logout** `POST /logout`

-   Requiere CSRF válido. Almacena el JTI en lista de revocación en Redis y limpia la cookie.

La cookie de sesión es HttpOnly/SameSite Strict. Los formularios internos incluyen `input name="_csrf"` obtenido vía middleware; las protecciones CSRF aplican también a formularios `multipart/form-data` (por ejemplo, cargas de CSV para exports).

## Rutas y vistas SSR

Todas las rutas están bajo `/superadmin` y exigen sesión con rol `superadmin`. Los templates viven en `templates/superadmin/`. A continuación un resumen actualizado de módulos y vistas:

| Ruta base             | Vista(s)                                              | Contenido                                                                   |
| --------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------- |
| `/dashboard`          | `dashboard.html`                                      | Métricas, actividad reciente y export CSV (`/dashboard/export`).            |
| `/organizations`      | `organizations_list.html`, `organization_detail.html` | Alta rápida, detalle, baja lógica y gestión de miembros.                    |
| `/patients`           | `patients.html`                                       | CRUD de pacientes demo con validaciones reforzadas.                         |
| `/locations/patients` | `patient_locations.html`                              | Registro manual y timeline tabular de ubicaciones (sin componente de mapa). |
| `/care-teams`         | `care_teams.html`                                     | Gestión integral de equipos, miembros y pacientes asociados.                |
| `/caregivers`         | `caregivers.html`                                     | Assignments cuidador-paciente, tipos de relación y auditoría asociada.      |
| `/ground-truth`       | `ground_truth.html`                                   | Etiquetas de verdad terreno para datasets de entrenamiento.                 |
| `/devices`            | `devices.html`                                        | Inventario de dispositivos físicos.                                         |
| `/push-devices`       | `push_devices.html`                                   | Tokens push con asignaciones a usuarios/orgs.                               |
| `/signal-streams`     | `signal_streams.html`, `timeseries_bindings.html`     | CRUD de streams, bindings y etiquetas por binding.                          |
| `/models`             | `models.html`                                         | Catálogo de modelos ML demo.                                                |
| `/event-types`        | `event_types.html`                                    | Administración de tipos de evento clínico.                                  |
| `/inferences`         | `inferences.html`                                     | Registro de inferencias con metadatos.                                      |
| `/alerts`             | `alerts.html`                                         | Creación, asignaciones, ACKs, resoluciones y entregas.                      |
| `/invitations`        | `invitations.html`                                    | Invitaciones, filtros por organización, cancelación.                        |
| `/users`              | `users.html`                                          | Listado de usuarios y cambio de estatus (`active`, `pending`, `blocked`).   |
| `/roles`              | `roles.html`                                          | Alta/baja de roles, asignación de permisos y usuarios.                      |
| `/catalogs`           | `catalogs.html`                                       | CRUD unificado para catálogos parametrizables (`?catalog=...`).             |
| `/audit`              | `audit.html`                                          | Visor con filtros de acciones y entidades.                                  |
| `/settings/system`    | `settings.html`                                       | Configuración global (branding, contacto, mensajes de mantenimiento).       |

> Los breadcrumbs y flashes se resuelven a través de `ui.ViewData` y utilidades CSS en `ui/assets/css/app.css`.

## Assets estáticos

`ui/assets` contiene el CSS y JS del panel. El router expone `/ui-assets/*` con `http.FileServer`. Personaliza estilos en `ui/assets/css/app.css`; el módulo de ubicaciones de pacientes no depende de librerías de mapas de terceros.

## Auditoría

Las operaciones de mutación (creación/actualización/eliminación) invocan `Handlers.writeAudit`, que delega en `audit.Write` para persistir eventos en `audit_logs`. Los códigos human-friendly se definen en `operationLabels` y se usan en la vista de auditoría.

## Pruebas y mantenimiento

-   `go fmt ./...` mantiene el formato estándar (recuerda ejecutarlo antes de subir cambios).
-   Para inspeccionar consultas, utiliza `make db-psql` o habilita logging en Postgres.

## Preguntas frecuentes

-   **¿Dónde encuentro los templates?** `backend/templates/layout.html`, `backend/templates/login.html` y `backend/templates/superadmin/*.html`.
-   **¿Cómo cambio el logo/colores?** Ajusta los campos en `/superadmin/settings/system`; los valores se guardan en `system_settings`.
-   **`csrf inválido` en login:** borra cookies previas (`hg_guest_csrf`) y vuelve a cargar `/login` para obtener un token nuevo.
