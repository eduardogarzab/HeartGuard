# HeartGuard Superadmin API (Go)

## Descripción

API de superadministración para HeartGuard: gestiona organizaciones, invitaciones, membresías, usuarios, API keys y auditoría.

- **Autenticación real** con JWT (access + refresh).
- **Redis** utilizado para refresh tokens y rate limiting.
- **Panel web** (HTML/CSS/JS) servido directamente desde el backend.

## Requisitos

- Go `1.22+`
- PostgreSQL `14+` (inicializada con `db/init.sql` y `db/seed.sql`)
- Redis (se levanta vía Docker Compose)
- Variables configuradas en `.env` (ver `.env.example` y README raíz)

## Variables principales

- `DATABASE_URL`
- `HTTP_ADDR`
- `JWT_SECRET`
- `ACCESS_TOKEN_TTL` (ej: `15m`)
- `REFRESH_TOKEN_TTL` (ej: `720h`)
- `REDIS_URL` (ej: `redis://localhost:6379/0`)
- `RATE_LIMIT_RPS` / `RATE_LIMIT_BURST`

## Setup rápido

```sh
cp .env.example .env
nano .env
make up         # levanta Postgres + Redis
make db-init
make db-seed
make tidy
make dev
```

**Reset completo** (Postgres + Redis + volúmenes + DB + datos seed):

```sh
make reset-all
```

## Health check

```sh
curl -i http://localhost:8080/healthz
```

## Panel web

- **URL:** [http://localhost:8080/](http://localhost:8080/)
- Login contra `/v1/auth/login`
- Uso de Bearer en `/v1/superadmin/*`
- Refresh automático en expiración
- Logout revoca el refresh token

## Autenticación

**Login:**
```http
POST /v1/auth/login
Body: {"email":"...","password":"..."}
Respuesta: access_token, refresh_token, user
```

**Refresh:**
```http
POST /v1/auth/refresh
Body: {"refresh_token":"..."}
Respuesta: access_token, refresh_token (rotados)
```

**Logout:**
```http
POST /v1/auth/logout
Body: {"refresh_token":"..."}
Respuesta: 204 No Content
```

## Protección de rutas

Todas las rutas bajo `/v1/superadmin` requieren:

```
Authorization: Bearer <access_token>
```

## Endpoints principales

- **Organizaciones:** CRUD
- **Invitaciones:** crear / consumir
- **Miembros:** añadir / eliminar
- **Usuarios:** listar / cambiar status
- **API keys:** crear / asignar permisos / revocar / listar
- **Auditoría:** listar logs (filtros: from, to, action)

## Smoke test

1. **Login:**
    ```sh
    curl -s -X POST http://localhost:8080/v1/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email":"admin@heartguard.com","password":"Admin#2025"}'
    ```
    Guarda los tokens:
    ```sh
    ACCESS_TOKEN="..."
    REFRESH_TOKEN="..."
    ```

2. **Listar organizaciones:**
    ```sh
    curl -s http://localhost:8080/v1/superadmin/organizations \
      -H "Authorization: Bearer $ACCESS_TOKEN"
    ```

3. **Crear organización:**
    ```sh
    curl -s -X POST http://localhost:8080/v1/superadmin/organizations \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"code":"FAM-TEST","name":"Familia Test"}'
    ```

4. **Auditoría:**
    ```sh
    curl -s http://localhost:8080/v1/superadmin/audit-logs \
      -H "Authorization: Bearer $ACCESS_TOKEN"
    ```

5. **Crear API key:**
    ```sh
    RAW=$(openssl rand -hex 32)
    curl -s -X POST http://localhost:8080/v1/superadmin/api-keys \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"label\":\"demo\",\"raw_key\":\"$RAW\"}"
    ```

6. **Refresh:**
    ```sh
    curl -s -X POST http://localhost:8080/v1/auth/refresh \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"
    ```

7. **Logout:**
    ```sh
    curl -s -X POST http://localhost:8080/v1/auth/logout \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}" -i
    ```

## Troubleshooting

- `invalid_credentials` → revisar email/password y que el usuario no esté bloqueado
- `invalid token` en refresh/logout → token expirado o revocado
- `DATABASE_URL is required` → `export $(grep -v '^#' .env | xargs)`
- Dependencias Go → `make tidy`
- Instalar jq en Ubuntu → `sudo apt install jq`
