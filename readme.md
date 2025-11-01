# HeartGuard

Plataforma demo para monitoreo y alertas de riesgo cardiovascular con **autenticación de pacientes** integrada. El repositorio combina infraestructura Docker para la base de datos, un backend Go SSR con panel de superadministración, API REST para pacientes y assets web servidos desde el mismo proceso.

## Vista general

-   **Repositorio monolítico:** servicios de datos (`db/`), backend SSR (`backend/`), templates (`backend/templates`) y assets compartidos (`backend/ui/assets`).
-   **Base de datos:** PostgreSQL 14 + PostGIS, esquema y seeds listos para demos (`heartguard` schema).
-   **Backend dual:** 
    - Panel administrativo SSR (Go 1.22) con autenticación basada en cookies JWT
-   **Infra local:** `docker-compose` expone Postgres y Redis; el backend se ejecuta con `make dev` cargando variables desde `.env`.
-   **Producción:** Desplegado en VPS con Docker Compose, Nginx reverse proxy, Let's Encrypt SSL y firewall IP-based.
-   **Front-end SSR:** Formularios con protección CSRF y validaciones lado servidor para todos los flujos; no hay mapas embebidos, los listados geográficos se gestionan vía tablas y formularios manuales.

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
-   Windows: PowerShell 5.1+ funciona con los mismos comandos (`make` requiere WSL, Git Bash o Make for Windows).

## Instalación de dependencias y herramientas

### 1. Docker y Docker Compose

**Windows:**

```powershell
# Descarga e instala Docker Desktop desde:
# https://docs.docker.com/desktop/install/windows-install/
# Docker Desktop incluye Docker Compose v2 automáticamente
```

**Linux (Ubuntu/Debian):**

```bash
# Actualizar repositorios
sudo apt-get update

# Instalar Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker (para no usar sudo)
sudo usermod -aG docker $USER
newgrp docker

# Instalar Docker Compose v2
sudo apt-get install docker-compose-plugin

# Verificar instalación
docker --version
docker compose version
```

**macOS:**

```bash
# Instalar Docker Desktop desde:
# https://docs.docker.com/desktop/install/mac-install/
# O usar Homebrew:
brew install --cask docker
```

### 2. GNU Make

**Windows:**

```powershell
# Opción 1: Usar WSL2 (recomendado)
wsl --install
# Dentro de WSL: sudo apt-get install make

# Opción 2: Instalar Make for Windows
choco install make
# O descargar desde: http://gnuwin32.sourceforge.net/packages/make.htm

# Opción 3: Usar Git Bash (incluye make)
# Descarga Git for Windows: https://git-scm.com/download/win
```

**Linux:**

```bash
sudo apt-get install build-essential  # Ubuntu/Debian
sudo yum groupinstall "Development Tools"  # CentOS/RHEL
```

**macOS:**

```bash
xcode-select --install  # Instala herramientas de línea de comandos
# O usar Homebrew:
brew install make
```

### 3. Go 1.22+

**Windows:**

```powershell
# Descargar instalador desde: https://go.dev/dl/
# O usar Chocolatey:
choco install golang --version=1.22.0

# Verificar instalación
go version
```

**Linux:**

```bash
# Descargar y extraer
wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz

# Agregar al PATH (en ~/.bashrc o ~/.zshrc)
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# Recargar configuración
source ~/.bashrc

# Verificar instalación
go version
```

**macOS:**

```bash
# Usar Homebrew:
brew install go@1.22

# O descargar desde: https://go.dev/dl/
```

### 4. PostgreSQL Client (psql) - Opcional

**Windows:**

```powershell
# Descargar PostgreSQL desde:
# https://www.postgresql.org/download/windows/
# O usar Chocolatey:
choco install postgresql --version=14.0
```

**Linux:**

```bash
sudo apt-get install postgresql-client-14
```

**macOS:**

```bash
brew install postgresql@14
```

### 5. Redis CLI - Opcional

**Windows:**

```powershell
# Redis no tiene soporte oficial para Windows
# Usar WSL2 o contenedor Docker (recomendado para desarrollo)
# O descargar versión no oficial: https://github.com/tporadowski/redis
```

**Linux:**

```bash
sudo apt-get install redis-tools
```

**macOS:**

```bash
brew install redis
```

### 6. Herramientas adicionales

```bash
# Git (control de versiones)
# Windows: https://git-scm.com/download/win
# Linux: sudo apt-get install git
# macOS: brew install git

# curl (para peticiones HTTP)
# Viene preinstalado en la mayoría de sistemas
# Windows: choco install curl

# jq (procesamiento JSON)
# Windows: choco install jq
# Linux: sudo apt-get install jq
# macOS: brew install jq

# openssl (generación de secretos)
# Viene preinstalado en Linux/macOS
# Windows: incluido en Git Bash
```

### 7. Verificar instalación completa

Ejecuta estos comandos para verificar que todas las herramientas estén instaladas:

```bash
docker --version          # Docker version 24.0.0+
docker compose version    # Docker Compose version v2.20.0+
make --version           # GNU Make 4.0+
go version               # go version go1.22.0+
psql --version           # psql (PostgreSQL) 14.0+ (opcional)
redis-cli --version      # redis-cli 6.0+ (opcional)
git --version            # git version 2.30.0+
curl --version           # curl 7.68.0+
jq --version             # jq-1.6+ (opcional)
```

## Variables de entorno

Duplica `.env.example` a `.env` y ajusta según tu entorno.

| Categoría             | Claves                                                | Comentarios                                                                |
| --------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------- |
| Postgres (superuser)  | `PGSUPER`, `PGSUPER_PASS`, `PGHOST`, `PGPORT`         | Usados por `make db-*` para crear la base.                                 |
| Postgres (app)        | `DBNAME`, `DBUSER`, `DBPASS`, `DATABASE_URL`          | `DATABASE_URL` se utiliza tanto por el backend como por scripts de health. |
| Backend/HTTP          | `ENV`, `HTTP_ADDR`                                    | `ENV` admite `dev` o `prod`; el valor controla logging.                    |
| Cookies               | `SECURE_COOKIES`                                      | `false` = HTTP (dev local), `true` = HTTPS requerido (producción).         |
| Auth JWT              | `JWT_SECRET`, `ACCESS_TOKEN_TTL`, `REFRESH_TOKEN_TTL` | El secreto debe tener ≥32 bytes en producción.                             |
| Redis & Rate limiting | `REDIS_URL`, `RATE_LIMIT_RPS`, `RATE_LIMIT_BURST`     | Redis es obligatorio: refresh tokens y rate limiting por IP/endpoint.      |
| Production            | `LOOPBACK_ALLOW_CIDRS`                                | CIDRs permitidos para bypass del middleware (ej: `172.18.0.0/16` para Docker). |

### Comandos útiles para producción

```bash
# Generar JWT secret fuerte (32+ bytes)
openssl rand -base64 32

# Configurar firewall (ejemplo Ubuntu)
sudo ufw allow from <tu-ip> to any port 80,443
sudo ufw enable

# Deploy en producción
make prod-deploy          # Build y deploy completo
make prod-db-reset        # Reset de base de datos
make prod-logs            # Ver logs del backend
make prod-restart         # Reiniciar servicios
```

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
-   **API Pública de Pacientes:** `/api/patient-auth/**` (login, registro, verificación - sin autenticación previa).
-   Rate limiting: ventana rolling de 1 s (`RATE_LIMIT_RPS` + `RATE_LIMIT_BURST`) con encabezados `X-RateLimit-*` y `Retry-After`.
-   Middleware `LoopbackOnly` garantiza que las peticiones provengan de `127.0.0.1` o `::1`; `CSRFMiddleware` soporta formularios `application/x-www-form-urlencoded` y `multipart/form-data`.

### API Pública - Autenticación de Pacientes

| Endpoint                              | Método | Descripción                                      | Auth Requerida |
| ------------------------------------- | ------ | ------------------------------------------------ | -------------- |
| `/api/patient-auth/login`             | POST   | Login de paciente con email/password             | ❌ No          |
| `/api/patient-auth/register`          | POST   | Registro de nuevo paciente                       | ❌ No          |
| `/api/patient-auth/verify-email`      | POST   | Verificar email del paciente                     | ❌ No          |
| `/api/patient-auth/reset-password`    | POST   | Solicitar reset de contraseña                    | ❌ No          |

**Ejemplo de login:**
```bash
curl -X POST http://localhost:8080/api/patient-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maria.delgado@example.com",
    "password": "Test123!"
  }'
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "patient": {
    "id": "8c9436b4-f085-405f-a3d2-87cb1d1cf097",
    "org_id": "uuid-de-org",
    "person_name": "María Delgado",
    "email": "maria.delgado@example.com",
    "email_verified": true,
    "created_at": "2025-11-01T10:30:00Z"
  }
}
```

### Pacientes de Prueba

La base de datos incluye 3 pacientes con credenciales configuradas:

| Email                          | Password  | Email Verificado | Organización |
| ------------------------------ | --------- | ---------------- | ------------ |
| maria.delgado@example.com      | Test123!  | ✅ Sí            | FAM-001      |
| jose.hernandez@example.com     | Test123!  | ✅ Sí            | CLIN-001     |
| valeria.ortiz@example.com      | Test123!  | ❌ No            | FAM-001      |

**Documentación completa:** Ver `docs/patient_auth_api.md` para detalles de todos los endpoints.

### Rutas clave (`/superadmin`)

| Segmento                   | Subruta/acción                                                                  | Descripción                                                                     |
| -------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `dashboard`                | `GET /`, `GET /export`                                                          | Panel principal, exportable a CSV.                                              |
| `organizations`            | `GET /`, `POST /`, `GET /{id}`, `POST /{id}/delete`                             | Listado, alta rápida, detalle y baja lógica de organizaciones.                  |
| `patients`                 | `GET /`, `POST /`, `GET /{id}`, `POST /{id}/update`, `POST /{id}/delete`       | CRUD de pacientes demo con gestión de email/password.                          |
| `patients` (auth)          | `POST /{id}/set-password`, `POST /{id}/verify-email`                            | Establecer contraseña y verificar email de pacientes (superadmin).             |
| `locations/patients`       | `GET /`, `POST /`, `POST /{id}/delete`                                          | Alta manual y administración de ubicaciones de pacientes (sin mapas embebidos). |
| `locations/users`          | `GET /`, `POST /`, `POST /{id}/delete`                                          | Administrador de ubicaciones reportadas por usuarios finales.                   |
| `care-teams`               | `GET /`, `POST /`, `POST /{id}/update`, `POST /{id}/delete`, miembros/pacientes | Gestión de equipos de cuidado, asignaciones y pacientes asociados.              |
| `caregivers`               | `GET /`, endpoints de asignaciones y tipos de relación                          | Administración de cuidadores y su relación con pacientes.                       |
| `ground-truth`             | `GET /`, `POST /`, `POST /{id}/update`, `POST /{id}/delete`                     | Registro de etiquetas ground truth para entrenamiento.                          |
| `devices` / `push-devices` | `GET /`, `POST /`, `POST /{id}/update`, `POST /{id}/delete`                     | Inventario de dispositivos físicos y endpoints push.                            |
| `batch-exports`            | `GET /`, `POST /`, `POST /{id}/status`, `POST /{id}/delete`                     | Solicitudes de exportación con seguimiento de estados.                          |
| `signal-streams`           | `GET /`, `POST /`, actualizaciones/bindings/tags                                | Operaciones completas sobre fuentes de señales y sus bindings.                  |
| `models`                   | `GET /`, `POST /`, `POST /{id}/update`, `POST /{id}/delete`                     | Catálogo de modelos ML demo.                                                    |
| `event-types`              | `GET /`, `POST /`, `POST /{id}/update`, `POST /{id}/delete`                     | Administración de tipos de eventos clínicos.                                    |
| `inferences`               | `GET /`, `POST /`, `POST /{id}/update`, `POST /{id}/delete`                     | Registro de inferencias para auditoría.                                         |
| `alerts`                   | `GET /`, `POST /`, flujos de asignación/ACK/resolución                          | Panel de alertas con workflow completo.                                         |
| `invitations`              | `GET /`, `POST /`, `POST /{id}/cancel`                                          | Invitaciones a la plataforma.                                                   |
| `users`                    | `GET /`, `POST /{id}/status`                                                    | Gestión de usuarios y cambio de estados.                                        |
| `roles`                    | `GET /`, `POST /`, permisos, asignación de usuarios, baja                       | Control RBAC global.                                                            |
| `catalogs`                 | `GET /`, `GET /{catalog}`, `POST /{catalog}`, updates/delete                    | CRUD de catálogos parametrizables.                                              |
| `audit`                    | `GET /`                                                                         | Visor de auditoría con filtros.                                                 |
| `settings/system`          | `GET /`, `POST /`                                                               | Configuración global (branding, contacto, mensajes).                            |

## Base de datos

`db/` contiene todo lo necesario para reconstruir la BD:

-   `init.sql` crea el esquema `heartguard`, catálogos (reemplazando ENUMs) y tablas de RBAC, pacientes, ubicaciones (pacientes/usuarios), invitaciones y auditoría.
-   **Autenticación de pacientes:** Incluye campos `email`, `password_hash`, `email_verified` y `last_login_at` en la tabla `patients`.
-   **Stored procedures para auth:** 5 funciones SQL para registro, login, cambio de contraseña, verificación de email y actualización de último login.
-   `seed.sql` llena catálogos, inserta usuarios demo (incluye superadmin `admin@heartguard.com / Admin#2025`), organizaciones, invitaciones, servicios, ubicaciones de ejemplo, logs y **3 pacientes con credenciales** (password: `Test123!`).
-   `db/README.md` amplía sobre la estructura, roles, funciones SQL y comandos avanzados.

### Stored Procedures de Autenticación

| Función                            | Parámetros                                    | Descripción                                      |
| ---------------------------------- | --------------------------------------------- | ------------------------------------------------ |
| `sp_patient_register`              | org_id, name, email, password_hash, ...       | Registra nuevo paciente con email/password       |
| `sp_patient_find_by_email`         | email                                         | Busca paciente por email (para login)            |
| `sp_patient_set_password`          | patient_id, password_hash                     | Actualiza contraseña del paciente                |
| `sp_patient_verify_email`          | patient_id                                    | Marca email como verificado                      |
| `sp_patient_update_last_login`     | patient_id                                    | Registra fecha de último login                   |

## Testing y validaciones

-   `make lint` corre `go vet`.
-   `go fmt ./...` mantiene el formato antes de subir cambios.
-   Para validar la conexión a la base, usa `make db-health` o `make db-psql`.

## Troubleshooting

### Errores generales

-   **`DATABASE_URL is required` (al correr el backend):** exporta las variables de `.env` en la shell actual.
    ```sh
    export $(grep -v '^#' .env | xargs)
    ```
-   **Dependencias Go faltantes:** `make tidy` regenerará `go.sum`.
-   **Puerto 5432 ocupado:** ajusta el mapeo `5432:5432` en `docker-compose.yml` y las variables `PGPORT`/`DATABASE_URL`.
-   **Redis no responde:** revisa `make logs-redis` y confirma que `REDIS_URL` use el puerto correcto (`6379`).

### Error "CSRF inválido" al iniciar sesión

Este error ocurre cuando las cookies CSRF tienen el atributo `Secure: true` (requiere HTTPS) pero accedes mediante HTTP.

**Solución simple:**

1. **En tu `.env`, agrega o modifica:**

    ```bash
    SECURE_COOKIES=false
    ```

2. **Reinicia el backend:**

    ```bash
    make dev
    ```

3. **Accede normalmente a `http://localhost:8080`**

**Explicación:**

-   `SECURE_COOKIES=false` → Las cookies funcionan con HTTP (desarrollo local)
-   `SECURE_COOKIES=true` → Las cookies requieren HTTPS (producción)
-   El valor por defecto es `false` en `.env.example` para facilitar desarrollo local

**¿Cuándo usar cada valor?**

| Escenario                       | Valor recomendado                                  |
| ------------------------------- | -------------------------------------------------- |
| Desarrollo local (tu PC)        | `SECURE_COOKIES=false`                             |
| Desarrollo en VM con túnel SSH  | `SECURE_COOKIES=false`                             |
| Desarrollo con ngrok/cloudflare | `SECURE_COOKIES=true` (el túnel proporciona HTTPS) |
| Producción con dominio y SSL    | `SECURE_COOKIES=true` (siempre)                    |

**Alternativa: Usar túnel HTTPS (sin modificar .env)**

Si prefieres no cambiar el `.env` y trabajar con HTTPS desde el inicio:

_Con ngrok (Windows/Linux):_

```bash
# Instalar ngrok
# Windows: choco install ngrok
# Linux: https://ngrok.com/download

# Crear túnel HTTPS
ngrok http 8080

# Usar la URL HTTPS que te proporciona (ej: https://abc123.ngrok-free.app)
```

_Con Cloudflare Tunnel:_

```bash
# Instalar cloudflared
# Windows: choco install cloudflared
# Linux: https://github.com/cloudflare/cloudflared/releases

# Crear túnel
cloudflared tunnel --url http://localhost:8080
```

**Verificar que funcione:**

```bash
# 1. Comprobar que Redis está activo
docker exec -it heartguard-redis redis-cli ping
# Debe responder: PONG

# 2. Ver los tokens CSRF en Redis
docker exec -it heartguard-redis redis-cli KEYS "csrf:guest:*"

# 3. Limpiar cache del navegador si persiste el error
# Chrome/Edge: Ctrl+Shift+Delete → Cookies
# Firefox: Ctrl+Shift+Delete → Cookies

# 4. Probar en modo incógnito
```

**⚠️ IMPORTANTE:** En producción, siempre usa `SECURE_COOKIES=true` con un certificado SSL válido (Let's Encrypt, Cloudflare, etc.).

## Próximos pasos sugeridos

-   Revisa `backend/README.md` para flujos de autenticación, arquitectura SSR y rutas del panel.
-   Consulta `db/README.md` si necesitas extender el esquema o ajustar seeds para nuevos catálogos.
-   **Autenticación de pacientes:** Ver `docs/patient_auth_api.md` para documentación completa de la API REST.
-   **Implementación técnica:** Ver `docs/patient_auth_implementation.md` para detalles de la implementación completa.

## Nuevas características implementadas

### 🔐 Autenticación de Pacientes (Nov 2025)

Sistema completo de autenticación para pacientes con:

- ✅ **API REST pública** para login/registro sin autenticación previa
- ✅ **Base de datos actualizada** con campos de email, password_hash, email_verified y last_login_at
- ✅ **5 stored procedures** para gestión completa de autenticación
- ✅ **Panel de administración mejorado** con:
  - Columna de email en listado de pacientes con indicador de verificación (✓/⚠)
  - Formularios de crear/editar con campo email opcional
  - Vista detalle con sección "Gestión de Autenticación"
  - Botones para establecer contraseña y verificar email
- ✅ **Seguridad:** Passwords hasheados con bcrypt, email único, login requiere verificación
- ✅ **3 pacientes de prueba** con credenciales configuradas (password: `Test123!`)
- ✅ **Documentación completa** en `docs/patient_auth_api.md`

**Testing rápido:**
```bash
# Login de paciente
curl -X POST http://localhost:8080/api/patient-auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"maria.delgado@example.com","password":"Test123!"}'

# Registro de paciente
curl -X POST http://localhost:8080/api/patient-auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "org_id":"<uuid-de-org>",
    "person_name":"Test User",
    "email":"test@example.com",
    "password":"Password123!"
  }'
```

### 🚀 Deploy en Producción (Nov 2025)

Infraestructura completa para producción implementada:

- ✅ **Docker Compose** con configuración prod/dev separada
- ✅ **Nginx reverse proxy** con SSL/TLS (Let's Encrypt)
- ✅ **Firewall IP-based** con whitelist configurable
- ✅ **Rate limiting** y seguridad headers
- ✅ **Makefile** con comandos para producción (prod-deploy, prod-logs, etc.)
- ✅ **Health checks** y monitoreo básico
- ✅ **Logs centralizados** con docker compose logs

**Comandos de producción:**
```bash
make prod-deploy       # Deploy completo
make prod-db-reset     # Reset de BD
make prod-logs         # Ver logs
make prod-restart      # Reiniciar servicios
make prod-backup       # Backup de BD (si configurado)
```

````
