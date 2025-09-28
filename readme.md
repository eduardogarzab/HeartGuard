# HeartGuard

## Descripción

Proyecto de demo: plataforma de monitoreo y alertas de riesgo cardiovascular.

Este monorepo contiene:

-   **Base de datos:** PostgreSQL + PostGIS
-   **Backend Superadmin:** Go (sirve también el panel web HTML/CSS/JS)
-   **Redis:** sesiones, refresh tokens y ratelimiting

## Estructura

-   `db/` — SQL de inicialización y semillas
-   `backend/` — Superadmin API en Go + panel web
-   `docker-compose.yml` — Postgres + Redis para desarrollo
-   `Makefile` — Comandos DB + backend (unificado)
-   `.env.example` — Variables de entorno de ejemplo
-   `.env` — Copia editable (**NO subir a git**)

## Requisitos

-   Docker + Docker Compose
-   Make
-   Go 1.22+
-   (Opcional) psql y jq

## Variables de entorno (principales)

**Base de datos:**

-   `PGSUPER`, `PGSUPER_PASS`, `PGHOST`, `PGPORT`
-   `DBNAME`, `DBUSER`, `DBPASS`
-   `DATABASE_URL`

**Backend / Auth / Redis:**

-   `ENV` (`dev`|`prod`)
-   `HTTP_ADDR` (ej: `:8080`)
-   `JWT_SECRET`
-   `ACCESS_TOKEN_TTL` (ej: `15m`)
-   `REFRESH_TOKEN_TTL` (ej: `720h`)
-   `REDIS_URL` (ej: `redis://localhost:6379/0`)
-   `RATE_LIMIT_RPS` (ej: `10`)
-   `RATE_LIMIT_BURST` (ej: `20`)

> **Nota:** La autenticación demo fue eliminada. Ya no se usa `X-Demo-Superadmin` ni tokens fijos.

## Pasos desde cero

1. **Variables:**
    ```sh
    cp .env.example .env
    nano .env
    ```
2. **Levantar servicios (Postgres + Redis):**
    ```sh
    make up
    ```
3. **Inicializar DB:**
    ```sh
    make db-init
    make db-seed
    make db-health
    ```
4. **Ejecutar backend:**
    ```sh
    make tidy # instala dependencias Go (solo primera vez)
    make dev
    ```
5. **Probar health:**
    ```sh
    curl -i http://localhost:8080/healthz
    ```
6. **Abrir el panel web:**
    ```
    http://localhost:8080/
    ```
    Inicia sesión con un usuario real de la tabla `users`.

## Flujo de autenticación (con curl)

1. **Login:**

    ```sh
    curl -s -X POST http://localhost:8080/v1/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email":"admin@heartguard.com","password":"Admin#2025"}'
    ```

    ```sh
    ACCESS_TOKEN="pega_access_token"
    REFRESH_TOKEN="pega_refresh_token"
    ```

2. **Rutas protegidas (ejemplo listar orgs):**

    ```sh
    curl -s http://localhost:8080/v1/superadmin/organizations \
      -H "Authorization: Bearer $ACCESS_TOKEN"
    ```

3. **Refresh de access:**

    ```sh
    curl -s -X POST http://localhost:8080/v1/auth/refresh \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"
    ```

4. **Logout (revoca refresh):**
    ```sh
    curl -s -X POST http://localhost:8080/v1/auth/logout \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}" -i
    ```

## Comandos útiles (`Makefile`)

-   `make up` / `down` / `logs` → controla Docker (Postgres/Redis)
-   `make db-init` / `db-seed` / `db-reset` / `db-health` / `db-psql`
-   `make tidy` / `dev` / `run` / `build` → backend Go
-   `make reset-all` → limpia todo (Postgres, Redis, volúmenes, DB)

## Troubleshooting

-   **"DATABASE_URL is required":**
    ```sh
    export $(grep -v '^#' .env | xargs)
    ```
-   **"missing go.sum entry":**
    ```sh
    make tidy
    ```
-   **Puerto 5432 ocupado:**
    Cambia el mapeo en `docker-compose.yml` y actualiza `PGPORT`/`DATABASE_URL` en `.env`
-   **Ver logs de Postgres:**
    ```sh
    make logs
    ```
-   **Generar raw_key (>= 32 chars):**
    ```sh
    openssl rand -hex 32
    ```
