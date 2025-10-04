# HeartGuard Superadmin API

Servicio escrito en Go que expone el panel administrativo y la API de superadministración de HeartGuard. Autentica con JWT (access/refresh), aplica rate limiting con Redis y persiste datos en PostgreSQL/PostGIS.

## Stack

-   Go 1.22 (`chi` como router HTTP, `zap` para logging, `pgx` para Postgres y `go-redis` para Redis).
-   Redis para cachear refresh tokens, listas de revocación (`jwt:deny:*`) y rate limiting per-IP.
-   PostgreSQL 14 + PostGIS (`heartguard` schema).
-   Archivos estáticos en `web/` servidos desde el mismo binario.

## Requisitos y configuración

| Variable            | Descripción                                                                     |
| ------------------- | ------------------------------------------------------------------------------- |
| `DATABASE_URL`      | DSN completo (usa `sslmode=disable` en local).                                  |
| `HTTP_ADDR`         | Address:port que escucha el servidor (ej. `:8080`).                             |
| `ENV`               | `dev` → logging verboso con `zap.NewDevelopment`, `prod` → `zap.NewProduction`. |
| `JWT_SECRET`        | Clave simétrica (≥32 bytes recomendados).                                       |
| `ACCESS_TOKEN_TTL`  | Duración del access token (`15m` por defecto).                                  |
| `REFRESH_TOKEN_TTL` | Duración del refresh token (`720h` por defecto).                                |
| `REDIS_URL`         | DSN `redis://host:port/db`.                                                     |
| `RATE_LIMIT_RPS`    | Requests por segundo permitidos antes de aplicar burst.                         |
| `RATE_LIMIT_BURST`  | Créditos extra por segundo.                                                     |

Todas las variables se cargan en `config.Load()`. El proceso aborta si `DATABASE_URL`, `JWT_SECRET` o `REDIS_URL` están vacíos.

## Ejecutar en local

```sh
cp .env.example .env
make up             # Postgres + Redis
make db-init
make db-seed
make tidy
make dev            # go run ./cmd/superadmin-api
```

Comandos adicionales:

-   `make lint` → `go vet ./...`
-   `make test` → `go test ./...`
-   `make build` → binario Linux (`GOOS=linux`, `GOARCH=amd64`).
-   `make reset-all` → reinicia contenedores, volúmenes y re-ejecuta init/seed.

## Health & observabilidad

-   `GET /healthz` responde `200 OK` cuando `Repo.Ping` contra Postgres tiene éxito.
-   Logging estructurado (JSON en prod) via `zap`. El logger se inyecta en handlers y auditoría.
-   Rate limiting: middleware calcula `rps + burst` por IP/método/path; devuelve `429` y encabezados `Retry-After`, `X-RateLimit-*`.

## Autenticación y sesiones

1. **Login** `POST /v1/auth/login`

    - Body `{"email":"admin@heartguard.com","password":"Admin#2025"}`.
    - Respuesta `200` ⇒ `{access_token, refresh_token, user}`.
    - Passwords comparados con bcrypt (`pgcrypto` los genera en los seeds).

2. **Uso del token**

    - Encabezado requerido: `Authorization: Bearer <access_token>`.
    - Middleware `RequireSuperadmin` valida JWT, revisa deny-list en Redis y confirma rol `superadmin` en Postgres.

3. **Rotación** `POST /v1/auth/refresh`

    - Requiere `{"refresh_token":"..."}`.
    - Revoca el refresh anterior, emite uno nuevo (rotación obligatoria) y un nuevo access token.

4. **Logout** `POST /v1/auth/logout`
    - Revoca el refresh token recibido (y lo borra de Redis).

Redis se usa como caché de tokens (`rt:<sha256>`) pero el origen de verdad es la tabla `refresh_tokens` en Postgres.

## Referencia de endpoints

Base URL: `http://localhost:8080` (configurable con `HTTP_ADDR`). Los cuerpos usan JSON y `Content-Type: application/json`.

### Autenticación

| Método | Ruta               | Descripción                                            | Request body                      | Respuesta                                                                       |
| ------ | ------------------ | ------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------- |
| `POST` | `/v1/auth/login`   | Autentica por email/password (usuarios no bloqueados). | `{ "email": "", "password": "" }` | `200` ⇒ `{ access_token, refresh_token, user }`; `401` ⇒ `invalid_credentials`. |
| `POST` | `/v1/auth/refresh` | Rota refresh token y devuelve nuevo par de tokens.     | `{ "refresh_token": "" }`         | `200` ⇒ `{ access_token, refresh_token }`; `401` ⇒ `invalid_token`.             |
| `POST` | `/v1/auth/logout`  | Revoca refresh token activo.                           | `{ "refresh_token": "" }`         | `204 No Content`; `400` ⇒ `invalid_token`.                                      |

### Organizaciones y membresías

| Método   | Ruta                                                 | Descripción                        | Notas                                                                            |
| -------- | ---------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------- |
| `POST`   | `/v1/superadmin/organizations`                       | Crea organización.                 | Body `{code (uppercase,2-60), name (3-160)}`. Devuelve `201` con `Organization`. |
| `GET`    | `/v1/superadmin/organizations`                       | Lista organizaciones (orden desc). | Query `limit` (1-200), `offset`.                                                 |
| `GET`    | `/v1/superadmin/organizations/{id}`                  | Obtiene detalle.                   | `404` si no existe.                                                              |
| `PATCH`  | `/v1/superadmin/organizations/{id}`                  | Actualiza code/name.               | Body parcial `{code?, name?}`.                                                   |
| `DELETE` | `/v1/superadmin/organizations/{id}`                  | Elimina organización.              | `204` o `404`.                                                                   |
| `GET`    | `/v1/superadmin/organizations/{id}/members`          | Lista miembros y roles.            | `limit/offset` soportados.                                                       |
| `POST`   | `/v1/superadmin/organizations/{id}/members`          | Añade miembro con rol.             | Body `{user_id uuid, org_role_id uuid}`. `204` en éxito.                         |
| `DELETE` | `/v1/superadmin/organizations/{id}/members/{userId}` | Remueve miembro.                   | `204` o `404`.                                                                   |

### Invitaciones

| Método   | Ruta                                         | Descripción                                   | Notas                                                                                                |
| -------- | -------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `GET`    | `/v1/superadmin/invitations`                 | Lista invitaciones (estado calculado).        | Query opcional `org_id`, `limit`, `offset`.                                                          |
| `POST`   | `/v1/superadmin/invitations`                 | Crea invitación y token.                      | Body `{org_id uuid, org_role_id uuid/code, email?, ttl_hours (1-720)}`. Devuelve `201` con detalles. |
| `POST`   | `/v1/superadmin/invitations/{token}/consume` | Marca invitación como usada y crea membresía. | Body `{user_id uuid}`. `204` o `400 invalid_token`.                                                  |
| `DELETE` | `/v1/superadmin/invitations/{id}`            | Revoca invitación.                            | `204` o `404`.                                                                                       |

### Catálogos

`catalog` admite: `user_statuses`, `signal_types`, `alert_channels`, `alert_levels`, `sexes`, `platforms`, `service_statuses`, `delivery_statuses`, `batch_export_statuses`, `org_roles`.

| Método   | Ruta                                     | Descripción                                                               |
| -------- | ---------------------------------------- | ------------------------------------------------------------------------- |
| `GET`    | `/v1/superadmin/catalogs/{catalog}`      | Lista items (`limit/offset`).                                             |
| `POST`   | `/v1/superadmin/catalogs/{catalog}`      | Crea item (`code`, `label`, `weight?`). `alert_levels` requiere `weight`. |
| `PATCH`  | `/v1/superadmin/catalogs/{catalog}/{id}` | Actualiza campos indicados.                                               |
| `DELETE` | `/v1/superadmin/catalogs/{catalog}/{id}` | Elimina item.                                                             |

### Métricas y búsqueda

| Método  | Ruta                                            | Descripción                                                           |
| ------- | ----------------------------------------------- | --------------------------------------------------------------------- |
| `GET`   | `/v1/superadmin/metrics/overview`               | Resumen de usuarios, organizaciones, invitaciones, etc.               |
| `GET`   | `/v1/superadmin/metrics/activity`               | Últimas acciones (`limit` 1-50, default 8).                           |
| `GET`   | `/v1/superadmin/metrics/users/status-breakdown` | Conteo por status de usuario.                                         |
| `GET`   | `/v1/superadmin/metrics/invitations/breakdown`  | Conteo por estado de invitaciones.                                    |
| `GET`   | `/v1/superadmin/users`                          | Búsqueda simple (`q` en email/nombre). Retorna memberships embebidos. |
| `PATCH` | `/v1/superadmin/users/{id}/status`              | Cambia status (`active`, `blocked`, `pending`).                       |

### API Keys

| Método   | Ruta                                       | Descripción                                                                                                                                |
| -------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `POST`   | `/v1/superadmin/api-keys`                  | Crea API key. Body `{label, raw_key (≥24 chars), expires_at?, owner_user_id?}`; calcula hash SHA-256 del `raw_key`. Devuelve `{id, hash}`. |
| `POST`   | `/v1/superadmin/api-keys/{id}/permissions` | Reemplaza permisos asociados. Body `{permissions: [code]}`.                                                                                |
| `DELETE` | `/v1/superadmin/api-keys/{id}`             | Revoca (marca `revoked_at`).                                                                                                               |
| `GET`    | `/v1/superadmin/api-keys`                  | Lista API keys (`active_only` bool, `limit`, `offset`).                                                                                    |

### Auditoría

| Método | Ruta                        | Descripción                                                                                 |
| ------ | --------------------------- | ------------------------------------------------------------------------------------------- |
| `GET`  | `/v1/superadmin/audit-logs` | Lista logs ordenados desc. Filtros: `from` y/o `to` (RFC3339), `action`, `limit`, `offset`. |

## Secuencia recomendada (smoke test)

```sh
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@heartguard.com","password":"Admin#2025"}' \
  | jq -r '.access_token')

curl -s http://localhost:8080/v1/superadmin/organizations \
  -H "Authorization: Bearer $ACCESS_TOKEN"

RAW=$(openssl rand -hex 32)
curl -s -X POST http://localhost:8080/v1/superadmin/api-keys \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"label\":\"demo\",\"raw_key\":\"$RAW\"}"
```

## Manejador de errores

-   Errores se devuelven como `{"code":"","message":"","fields":{}}`.
-   Códigos comunes: `bad_request`, `validation_error`, `db_error`, `not_found`, `invalid_token`.
-   Validaciones usan `go-playground/validator` con mensajes por campo (mapa `fields`).

## Auditoría integrada

-   Cada mutación exitosa registra eventos en `audit_logs` vía `audit.Write`.
-   Eventos incluyen `actor_user_id`, `client_ip` (según `X-Forwarded-For`), acción (`ORG_CREATE`, `APIKEY_CREATE`, etc.) y detalles relevantes.

## Pruebas y mantenimiento

-   `go test ./...` cubre repositorio y lógica auxiliar.
-   Inyección de dependencias (`NewRepoWithPool`) facilita tests unitarios.
-   Para depurar consultas, habilita logs de Postgres y usa `db-psql`.

## FAQs

-   **`invalid_credentials`**: password incorrecto o usuario con status `blocked`.
-   **`invalid_token` en refresh/logout**: token expirado/rotado o ya revocado.
-   **`DATABASE_URL is required`**: exporta variables antes de correr `make dev`.
-   **`pq: catalogo no soportado`**: valida el slug enviado contra la lista de `catalogInfo`.
