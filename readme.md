# HeartGuard

Plataforma demo para monitoreo y alertas de riesgo cardiovascular. El repositorio combina infraestructura Docker para la base de datos, un backend Go SSR con panel de superadministración y assets web servidos desde el mismo proceso.

## Vista general

-   **Repositorio monolítico:** servicios de datos (`db/`), backend SSR (`backend/`) y assets compartidos (`backend/ui/assets`).
-   **Base de datos:** PostgreSQL 14 + PostGIS, esquema y seeds listos para demos.
-   **Backend:** Panel administrativo SSR (Go 1.22) con sesiones JWT en cookie, Redis y PostgreSQL. Todas las rutas quedan restringidas a localhost por middleware.
-   **Infra local:** `docker-compose` provee Postgres y Redis; el backend corre con `make dev`.

## Estructura

-   `db/` — scripts de inicialización (`init.sql`), seeds (`seed.sql`) y notas de operación.
-   `backend/` — Backend SSR de superadministración y servidor de archivos estáticos (`backend/ui/assets`).
-   `docker-compose.yml` — Postgres + Redis para desarrollo.
-   `Makefile` — wrappers para migraciones, seeds y tareas de Go.
-   `.env.example` — plantilla con todas las variables necesarias para clonar el entorno.

## Requisitos previos

-   Docker y Docker Compose v2.
-   GNU Make.
-   Go `1.22+` (para compilar/ejecutar el backend localmente).
-   Opcional: `psql`, `openssl`, `curl`, `jq`.

## Variables de entorno

Duplica `.env.example` a `.env` y ajusta según tu entorno.

| Categoría             | Claves                                                | Comentarios                                                                |
| --------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------- |
| Postgres (superuser)  | `PGSUPER`, `PGSUPER_PASS`, `PGHOST`, `PGPORT`         | Usados por `make db-*` para crear la base.                                 |
| Postgres (app)        | `DBNAME`, `DBUSER`, `DBPASS`, `DATABASE_URL`          | `DATABASE_URL` se utiliza tanto por el backend como por scripts de health. |
| Backend/HTTP          | `ENV`, `HTTP_ADDR`                                    | `ENV` admite `dev` o `prod`; el valor controla logging.                    |
| Auth JWT              | `JWT_SECRET`, `ACCESS_TOKEN_TTL`, `REFRESH_TOKEN_TTL` | El secreto debe tener ≥32 bytes en producción.                             |
| Redis & Rate limiting | `REDIS_URL`, `RATE_LIMIT_RPS`, `RATE_LIMIT_BURST`     | Redis es obligatorio: refresh tokens y rate limiting por IP/endpoint.      |

## Puesta en marcha

1. **Clonar el repositorio:**
    ```sh
    git clone https://github.com/eduardogarzab/HeartGuard.git
    cd HeartGuard
    ```
2. **Preparar variables:**
    ```sh
    cp .env.example .env
    # edita con tus credenciales
    ```
3. **Arrancar Postgres + Redis:**
    ```sh
    make up
    ```
4. **Esperar servicios y crear esquema:**
    ```sh
    make compose-wait     # opcional, espera a Postgres/Redis dentro de Docker
    make db-init
    make db-seed
    make db-health
    ```
5. **Instalar dependencias Go y correr modo dev:**
    ```sh
    make tidy             # solo la primera vez
    make dev
    ```
6. **Verificaciones rápidas (desde localhost):**
    ```sh
    curl -i http://localhost:8080/healthz
    ```
7. **Panel web:** abre <http://localhost:8080/> (redirige a `/login` si no hay sesión) e inicia sesión con las credenciales sembradas (`admin@heartguard.com / Admin#2025`).

-   En caso de ejecutarlo en una VM remota, usa `ssh -L 8080:localhost:8080 usuario@ip_de_la_vm` para tunelizar el puerto.

## Comandos clave del `Makefile`

| Comando              | Acción                                                                         |
| -------------------- | ------------------------------------------------------------------------------ |
| `make up` / `down`   | Levanta o detiene los contenedores de Postgres y Redis.                        |
| `make logs`          | Sigue los logs de Postgres (`logs-redis`, `logs-all` disponibles).             |
| `make compose-wait`  | Espera a que Postgres/Redis estén listos (usa `pg_isready` y `redis-cli`).     |
| `make db-init`       | Ejecuta `db/init.sql` con el superusuario configurado.                         |
| `make db-seed`       | Ejecuta `db/seed.sql` con datos demo.                                          |
| `make db-health`     | Checks rápidos: ping, `search_path`, conteos de catálogos.                     |
| `make db-reset`      | Dropea y reconstruye la base (usa `db-drop`, `db-init`, `db-seed`).            |
| `make tidy`          | `go mod tidy` dentro de `backend/`.                                            |
| `make dev`           | Ejecuta `go run ./cmd/superadmin-api` con variables leídas de `.env`.          |
| `make lint` / `test` | `go vet` y `go test ./...` respectivamente.                                    |
| `make reset-all`     | Detiene contenedores, borra volúmenes, vuelve a levantar y re-inicializa todo. |

## Panel de superadministración

-   Base URL: `http://localhost:8080` (ajustable con `HTTP_ADDR`).
-   Rutas públicas: `/`, `/login`, `/healthz` y assets en `/ui-assets/*`.
-   Rutas protegidas: `/superadmin/**` (requieren sesión y rol `superadmin`).
-   Rate limiting: ventana rolling de 1s (`RATE_LIMIT_RPS` + `RATE_LIMIT_BURST`), con encabezados `X-RateLimit-*`.
-   Middleware `LoopbackOnly` garantiza que las peticiones provengan de `127.0.0.1` o `::1`.

## Base de datos

`db/` contiene todo lo necesario para reconstruir la BD:

-   `init.sql` crea el esquema `heartguard`, catálogos (reemplazando ENUMs) y tablas de RBAC, pacientes, invitaciones y auditoría.
-   `seed.sql` llena catálogos, inserta usuarios demo (incluye superadmin `admin@heartguard.com / Admin#2025`), organizaciones, invitaciones, servicios y logs.
-   `db/README.md` amplía sobre la estructura, roles y comandos avanzados.

## Testing y validaciones

-   `make test` ejecuta la suite Go (`go test ./...`).
-   `make lint` corre `go vet`.
-   `go fmt ./...` mantiene el formato antes de subir cambios.
-   Para validar la conexión a la base, usa `make db-health` o `make db-psql`.

## Troubleshooting

-   **`DATABASE_URL is required` (al correr el backend):** exporta las variables de `.env` en la shell actual.
    ```sh
    export $(grep -v '^#' .env | xargs)
    ```
-   **Dependencias Go faltantes:** `make tidy` regenerará `go.sum`.
-   **Puerto 5432 ocupado:** ajusta el mapeo `5432:5432` en `docker-compose.yml` y las variables `PGPORT`/`DATABASE_URL`.
-   **Regenerar API key demo:** usa `/superadmin/api-keys` en el panel para generar una nueva y guarda el secreto mostrado.
-   **Redis no responde:** revisa `make logs-redis` y confirma que `REDIS_URL` use el puerto correcto (`6379`).

## Próximos pasos sugeridos

-   Revisa `backend/README.md` para flujos de autenticación, arquitectura SSR y rutas del panel.
-   Consulta `db/README.md` si necesitas extender el esquema o ajustar seeds para nuevos catálogos.
