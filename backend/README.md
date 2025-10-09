# HeartGuard Superadmin

Servicio en Go que renderiza el panel de superadministración de HeartGuard completamente del lado del servidor (SSR). Utiliza sesiones firmadas (JWT corto almacenado en cookie HttpOnly), Redis para rate limiting y PostgreSQL/PostGIS como persistencia.

> ℹ️ La antigua API JSON permanece en el repositorio bajo el build tag `rest_api_legacy` únicamente como referencia histórica. No participa en el binario por defecto.

## Stack

-   Go 1.22 (`chi` para routing, `zap` para logging, `pgx` para Postgres y `go-redis` para Redis).
-   html/template con `internal/ui.Renderer` para componer vistas SSR.
-   Redis para sesiones, flash messages y rate limiting per-IP.
-   PostgreSQL 14 + PostGIS (schema `heartguard`).
-   Archivos estáticos (`ui/assets`) servidos desde el mismo proceso.

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
-   `make test` ⇒ `go test ./...`
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

La cookie de sesión es HttpOnly/SameSite Strict. Los formularios internos incluyen `input name="_csrf"` obtenido vía middleware.

## Módulos del panel SSR

Todas las rutas están bajo `/superadmin` y exigen sesión con rol `superadmin`. Los templates viven en `templates/superadmin/`.

| Ruta                             | Vista                      | Descripción breve                                                 |
| -------------------------------- | -------------------------- | ----------------------------------------------------------------- |
| `/superadmin/dashboard`          | `dashboard.html`           | Métricas resumidas, actividad reciente y estado de invitaciones.  |
| `/superadmin/organizations`      | `organizations_list.html`  | Listado, alta rápida y navegación a detalle.                      |
| `/superadmin/organizations/{id}` | `organization_detail.html` | Miembros, invitaciones activas y acciones de alta/baja.           |
| `/superadmin/invitations`        | `invitations.html`         | Gestión de invitaciones con filtro por organización.              |
| `/superadmin/users`              | `users.html`               | Buscador + cambio de estatus (`active`, `pending`, `blocked`).    |
| `/superadmin/roles`              | `roles.html`               | Alta y baja de roles globales.                                    |
| `/superadmin/catalogs/{slug}`    | `catalogs.html`            | CRUD sobre catálogos permitidos (`allowedCatalogs`).              |
| `/superadmin/api-keys`           | `api_keys.html`            | Creación, permisos y revocación de API Keys.                      |
| `/superadmin/settings/system`    | `settings.html`            | Edición de configuración global (marca, contacto, mantenimiento). |
| `/superadmin/audit`              | `audit.html`               | Consulta filtrable del log de auditoría.                          |

> Los breadcrumbs y flashes se resuelven a través de `ui.ViewData` y utilidades CSS en `ui/assets/css/app.css`.

## Assets estáticos

`ui/assets` contiene el CSS y JS del panel. El router expone `/ui-assets/*` con `http.FileServer`. Personaliza estilos en `ui/assets/css/app.css`.

## Auditoría

Las operaciones de mutación (creación/actualización/eliminación) invocan `Handlers.writeAudit`, que delega en `audit.Write` para persistir eventos en `audit_logs`. Los códigos human-friendly se definen en `operationLabels` y se usan en la vista de auditoría.

## Pruebas y mantenimiento

-   `go test ./...` ejecuta la suite del repositorio (pendiente de habilitar en CI).
-   `go fmt ./...` mantiene el formato estándar (recuerda ejecutarlo antes de subir cambios).
-   Para inspeccionar consultas, utiliza `make db-psql` o habilita logging en Postgres.

## Legacy REST API

Los antiguos handlers JSON viven en `internal/superadmin/handlers.go` y sólo se compilan si el binario se construye con `-tags rest_api_legacy`. Esto permite consultarlos como referencia sin exponerse en producción.

## Preguntas frecuentes

-   **¿Dónde encuentro los templates?** `backend/templates/layout.html`, `backend/templates/login.html` y `backend/templates/superadmin/*.html`.
-   **¿Puedo seguir consumiendo la API JSON?** Sólo compilando con `go build -tags rest_api_legacy`; el router principal no monta esas rutas.
-   **¿Cómo cambio el logo/colores?** Ajusta los campos en `/superadmin/settings/system`; los valores se guardan en `system_settings`.
-   **`csrf inválido` en login:** borra cookies previas (`hg_guest_csrf`) y vuelve a cargar `/login` para obtener un token nuevo.
