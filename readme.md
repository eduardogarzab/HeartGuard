# HeartGuard

Plataforma demo para monitoreo y alertas de riesgo cardiovascular. El repositorio combina infraestructura Docker para la base de datos, una API de superadministración escrita en Go y un panel web estático servido por el mismo backend.

## Vista general

-   **Repositorio monolítico:** servicios de datos (`db/`), backend (`backend/`) y assets web (`web/`).
-   **Base de datos:** PostgreSQL 14 + PostGIS, esquema y seeds listos para demos.
-   **Backend:** Panel administrativo cerrado (Go 1.22) con autenticación JWT y rate limiting en Redis, accesible únicamente desde localhost.
-   **Infra local:** `docker-compose` provee Postgres y Redis; el backend corre con `make dev`.

## Estructura

-   `db/` — scripts de inicialización (`init.sql`), seeds (`seed.sql`) y notas de operación.
-   `backend/` — API REST de superadministración + servidor de archivos estáticos bajo `/web`.
-   `web/` — HTML/CSS/JS que consume la API (servido por el backend).
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
6. **Smoke tests manuales (ejecutados desde localhost):**
   `sh
 curl -i http://localhost:8080/healthz
 curl -s -X POST http://localhost:8080/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@heartguard.com","password":"Admin#2025"}'
 `
7. **Panel web:** abre <http://localhost:8080/> y autentícate con usuarios de la tabla `users`.

* En caso de ejecutarlo en una VM remota, usa `ssh -L 8080:localhost:8080 usuario@ip_de_la_vm` para tunelizar el puerto.

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

## API y panel web

La documentación detallada de endpoints vive en `backend/README.md`, pero recuerda que ahora el backend sólo responde a peticiones hechas desde la propia máquina (`localhost`). Resumen:

-   Base URL: `http://localhost:8080` (configurable con `HTTP_ADDR`).
-   Rutas públicas: `/healthz`, `/v1/auth/login`, `/v1/auth/refresh`, `/v1/auth/logout`; todas requieren provenir de `127.0.0.1` o `::1`.
-   Rutas protegidas (`Authorization: Bearer <token>` y rol superadmin): `/v1/superadmin/**`.
-   Rate limiting: ventana de 1s con `RATE_LIMIT_RPS + RATE_LIMIT_BURST` por IP/método/path; encabezados `X-RateLimit-*` expuestos.
-   Acceso restringido: el servidor rechaza cualquier origen que no sea localhost, evitando exposición pública accidental.

## Base de datos

`db/` contiene todo lo necesario para reconstruir la BD:

-   `init.sql` crea el esquema `heartguard`, catálogos (reemplazando ENUMs) y tablas de RBAC, pacientes, invitaciones y auditoría.
-   `seed.sql` llena catálogos, inserta usuarios demo (incluye superadmin `admin@heartguard.com / Admin#2025`), organizaciones, invitaciones, servicios y logs.
-   `db/README.md` amplía sobre la estructura, roles y comandos avanzados.

## Testing y validaciones

-   `make test` ejecuta la suite de Go (`go test ./...`).
-   `make lint` corre `go vet`.
-   Para validar la conexión a la base, usa `make db-health` o `make db-psql`.

## Troubleshooting

-   **`DATABASE_URL is required` (al correr el backend):** exporta las variables de `.env` en la shell actual.
    ```sh
    export $(grep -v '^#' .env | xargs)
    ```
-   **Dependencias Go faltantes:** `make tidy` regenerará `go.sum`.
-   **Puerto 5432 ocupado:** ajusta el mapeo `5432:5432` en `docker-compose.yml` y las variables `PGPORT`/`DATABASE_URL`.
-   **Regenerar API key demo:** usa `openssl rand -hex 32` y pega el valor en `POST /v1/superadmin/api-keys`.
-   **Redis no responde:** revisa `make logs-redis` y confirma que `REDIS_URL` use el puerto correcto (`6379`).

## Próximos pasos sugeridos

-   Revisa `backend/README.md` para flujos de autenticación, endpoints y estructuras de respuesta.
-   Consulta `db/README.md` si necesitas extender el esquema o ajustar seeds para nuevos catálogos.
