# Guía de Despliegue - Microservicios HeartGuard

Esta guía te ayudará a levantar el stack de microservicios en la VM `129.212.181.53`.

## 📋 Requisitos Previos

- VM con Docker y Docker Compose instalados
- Acceso SSH a la VM
- El stack del backend ya debe estar corriendo en `134.199.204.58`
- Puerto de red abierto para comunicación entre ambas VMs

## 🚀 Paso 1: Clonar el Repositorio

```bash
# Conectarse a la VM de microservicios
ssh root@129.212.181.53

# Clonar el repositorio
cd /root
git clone https://github.com/eduardogarzab/HeartGuard.git
cd HeartGuard
```

## 🔧 Paso 2: Generar Archivos de Configuración

Ejecuta el script interactivo para generar todos los archivos `.env`:

```bash
make bootstrap-envs
```

El script te pedirá la siguiente información:

### Configuración General
- **IP del backend**: `134.199.204.58`
- **IP de microservicios**: `129.212.181.53`

### PostgreSQL (en VM del backend)
- **Usuario superadmin**: `postgres` (default)
- **Password superadmin**: `postgres123` (o el que hayas configurado)
- **Puerto**: `5432` (default)
- **Nombre de la base**: `heartguard` (default)
- **Usuario app**: `heartguard_app` (default)
- **Password app**: (el que configuraste en el backend)

### Redis / InfluxDB (en VM del backend)
- **Puerto Redis**: `6379` (default)
- **Puerto Influx**: `8086` (default)
- **Usuario Influx**: `admin` (default)
- **Password Influx**: `influxdb123` (o el que configuraste)
- **Bucket**: `timeseries` (default)
- **Organización**: `heartguard` (default)
- **Token**: (el que configuraste en el backend)

### Claves Compartidas (IMPORTANTE: usar las mismas del backend)
- **JWT_SECRET**: (el mismo que usas en el backend)
- **INTERNAL_SERVICE_KEY**: (llave para comunicación interna entre servicios)
- **AI_MODEL_ID**: `988e1fee-e18e-4eb9-9b9d-72ae7d48d8bc` (default)

### DigitalOcean Spaces
- **Spaces Access Key**: Tu access key de DO
- **Spaces Secret Key**: Tu secret key de DO
- **Origin endpoint**: `https://heartguard-bucket.atl1.digitaloceanspaces.com/` (o tu endpoint)

### Gateway
- **FLASK_SECRET_KEY**: (genera uno seguro o usa uno de prueba)

## 📦 Paso 3: Verificar Archivos .env Generados

El script habrá creado los siguientes archivos:

```bash
ls -la micro-services/*/.env
```

Deberías ver:
```
micro-services/admin/.env
micro-services/ai-monitor/.env
micro-services/ai-prediction/.env
micro-services/auth/.env
micro-services/gateway/.env
micro-services/influxdb-service/.env
micro-services/media/.env
micro-services/patient/.env
micro-services/user/.env
```

## 🔍 Paso 4: Verificar Conectividad con el Backend

Antes de levantar los microservicios, verifica que puedas conectarte al backend:

```bash
# Probar PostgreSQL
nc -zv 134.199.204.58 5432

# Probar Redis
nc -zv 134.199.204.58 6379

# Probar InfluxDB
nc -zv 134.199.204.58 8086
```

Si alguno falla, verifica:
- Firewall de la VM del backend
- Reglas de seguridad del cloud provider
- Que el backend esté corriendo: `ssh root@134.199.204.58 'docker compose ps'`

## 🐳 Paso 5: Levantar los Microservicios

```bash
cd docker/microservices
docker compose up -d
```

Esto levantará los siguientes servicios:
- `auth-service` (puerto 5001)
- `admin-service` (puerto 5002)
- `user-service` (puerto 5003)
- `patient-service` (puerto 5004)
- `media-service` (puerto 5005)
- `realtime-service` (puerto 5006)
- `ai-prediction` (puerto 5007)
- `ai-monitor` (puerto 5008)
- `gateway` (puerto 8080)

## ✅ Paso 6: Verificar que los Contenedores Estén Saludables

```bash
docker compose ps
```

Todos los contenedores deben aparecer como `healthy`. Si alguno está `unhealthy`, revisa los logs:

```bash
docker compose logs <nombre-servicio>
```

## 🧪 Paso 7: Probar los Servicios

### Probar Auth Service
```bash
curl http://localhost:5001/health
```

Deberías ver:
```json
{"status": "healthy"}
```

### Probar Gateway
```bash
curl http://localhost:8080/health
```

### Probar AI Prediction
```bash
curl http://localhost:5007/health
```

### Probar todos los servicios a través del Gateway

```bash
# Auth
curl http://localhost:8080/auth/health

# Admin
curl http://localhost:8080/admin/health

# User
curl http://localhost:8080/user/health

# Patient
curl http://localhost:8080/patient/health

# Media
curl http://localhost:8080/media/health

# Realtime (InfluxDB service)
curl http://localhost:8080/realtime/health

# AI
curl http://localhost:8080/ai/health
```

## 🔧 Comandos Útiles

### Ver logs de todos los servicios
```bash
docker compose logs -f
```

### Ver logs de un servicio específico
```bash
docker compose logs -f auth-service
docker compose logs -f gateway
docker compose logs -f ai-monitor
```

### Reiniciar un servicio
```bash
docker compose restart auth-service
```

### Detener todos los servicios
```bash
docker compose down
```

### Reconstruir e iniciar un servicio
```bash
docker compose up -d --build auth-service
```

### Ver el estado de los healthchecks
```bash
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

## 🐛 Troubleshooting

### Error: "could not connect to postgres"

**Problema**: Los microservicios no pueden conectarse a PostgreSQL en el backend.

**Solución**:
1. Verifica que PostgreSQL esté escuchando en `0.0.0.0:5432` en el backend:
   ```bash
   ssh root@134.199.204.58 'docker compose logs postgres | grep "listening"'
   ```

2. Verifica el firewall:
   ```bash
   ssh root@134.199.204.58 'iptables -L | grep 5432'
   ```

3. Prueba la conexión manual:
   ```bash
   psql -h 134.199.204.58 -U heartguard_app -d heartguard
   ```

### Error: "connection refused" en Redis o InfluxDB

**Solución**: Igual que PostgreSQL, verifica:
- Que los servicios estén expuestos en `0.0.0.0` (no solo `127.0.0.1`)
- Firewall y reglas de seguridad
- Que los puertos estén correctos en los `.env`

### Error: "JWT signature verification failed"

**Problema**: El `JWT_SECRET` no coincide entre el backend y los microservicios.

**Solución**:
1. Verifica el secret en el backend:
   ```bash
   ssh root@134.199.204.58 'grep JWT_SECRET /root/HeartGuard/backend/.env'
   ```

2. Verifica en microservicios:
   ```bash
   grep JWT_SECRET micro-services/auth/.env
   ```

3. Deben ser **exactamente iguales**. Si no coinciden, edita los archivos y reinicia:
   ```bash
   docker compose restart
   ```

### Servicio en estado "unhealthy"

**Solución**:
1. Ver logs detallados:
   ```bash
   docker compose logs --tail=100 <nombre-servicio>
   ```

2. Ver el healthcheck específico:
   ```bash
   docker inspect <nombre-contenedor> --format='{{json .State.Health}}' | jq
   ```

3. Entrar al contenedor para debugging:
   ```bash
   docker compose exec <nombre-servicio> sh
   ```

### Gateway no puede conectarse a otros servicios

**Problema**: El gateway usa nombres de servicio (ej: `http://auth-service:5001`) pero no resuelve.

**Solución**: Todos los servicios deben estar en la misma red Docker. Verifica:
```bash
docker network ls
docker network inspect microservices_micro_net
```

## 📊 Monitoreo Continuo

Para producción, considera agregar monitoreo:

```bash
# Ver uso de recursos
docker stats

# Ver logs en tiempo real de todos los servicios
docker compose logs -f --tail=50
```

## 🔒 Seguridad en Producción

Antes de ir a producción:

1. ✅ Cambia todos los passwords por defecto
2. ✅ Genera JWT_SECRET y INTERNAL_SERVICE_KEY con `openssl rand -base64 32`
3. ✅ Configura `SECURE_COOKIES=true` en el backend
4. ✅ Habilita HTTPS con un reverse proxy (nginx/traefik)
5. ✅ Restringe acceso a puertos solo entre las VMs necesarias
6. ✅ Habilita logging centralizado
7. ✅ Configura backups automáticos de PostgreSQL

## 📚 Arquitectura de Red

```
┌─────────────────────────────────────────┐
│  VM Backend (134.199.204.58)            │
│                                         │
│  ┌──────────┐  ┌───────┐  ┌──────────┐ │
│  │PostgreSQL│  │ Redis │  │ InfluxDB │ │
│  │  :5432   │  │ :6379 │  │  :8086   │ │
│  └──────────┘  └───────┘  └──────────┘ │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Backend SSR (Go)              │   │
│  │   :8080 (solo loopback)         │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
              ▲
              │ Red TCP/IP
              │ 5432, 6379, 8086
              ▼
┌─────────────────────────────────────────┐
│  VM Microservicios (129.212.181.53)     │
│                                         │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │
│  │ Auth │ │Admin │ │ User │ │Patient│  │
│  │:5001 │ │:5002 │ │:5003 │ │:5004  │  │
│  └──────┘ └──────┘ └──────┘ └──────┘  │
│                                         │
│  ┌──────┐ ┌─────────┐ ┌──────┐        │
│  │Media │ │Realtime │ │  AI  │        │
│  │:5005 │ │ :5006   │ │:5007 │        │
│  └──────┘ └─────────┘ └──────┘        │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Gateway (Flask)               │   │
│  │   :8080 (público)               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 📞 Soporte

Si encuentras problemas, revisa:
1. Los logs de Docker Compose
2. La documentación en `/root/HeartGuard/readme.md`
3. La documentación de cada microservicio en `micro-services/<servicio>/README.md`

---

**Última actualización**: Noviembre 2025
