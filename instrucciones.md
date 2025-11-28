# 🚀 Instrucciones Completas de Despliegue HeartGuard

Guía paso a paso para desplegar HeartGuard en dos VMs usando Docker desde cero.

## 📋 Arquitectura del Sistema

```
┌────────────────────────────────────────────┐
│  VM 1: Backend (134.199.204.58)            │
│  ┌──────────────────────────────────────┐  │
│  │ PostgreSQL + PostGIS      :5432      │  │
│  │ Redis                     :6379      │  │
│  │ InfluxDB 2.7             :8086       │  │
│  │ Backend SSR (Go)         :8080       │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
              ↕ Conexión TCP/IP
┌────────────────────────────────────────────┐
│  VM 2: Microservicios (129.212.181.53)     │
│  ┌──────────────────────────────────────┐  │
│  │ auth-service             :5001       │  │
│  │ admin-service            :5002       │  │
│  │ user-service             :5003       │  │
│  │ patient-service          :5004       │  │
│  │ media-service            :5005       │  │
│  │ realtime-service         :5006       │  │
│  │ ai-prediction            :5007       │  │
│  │ ai-monitor               :5008       │  │
│  │ gateway (Flask)          :8080       │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

# VMs Requeridas:

-   **VM 1: Backend**
    - Puertos abiertos (entrantes): 5432, 6379, 8086, 8080 (desde la VM de microservicios)
-   **VM 2: Microservicios**
    - Puertos abiertos (entrantes): 8080 (público para el gateway)

# Bucket de DigitalOcean Spaces

- Crear un bucket en DigitalOcean Spaces para almacenamiento de medios.

### Configuración Inicial

Habilitar CORS en el bucket para permitir acceso desde el frontend para el público. Con todos los orígenes (`*`) y métodos `GET`, `PUT`, `POST`, `DELETE`, `HEAD`.

Crear una clave de acceso (Access Key) y una clave secreta (Secret Key) para el bucket.

---

# 🖥️ PARTE 1: Preparación VM del Backend

## Paso 1.1: Instalar Dependencias Básicas

Conectarse a la VM del backend:

```bash
ssh root@IP_BACKEND
```

### Actualizar el sistema (CentOS 9)

```bash
# Actualizar paquetes
dnf update -y

# Instalar herramientas básicas
dnf install -y git curl wget vim net-tools nc
```

## Paso 1.2: Instalar Docker

```bash
# Instalar Docker
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io

# Iniciar y habilitar Docker
systemctl start docker
systemctl enable docker

# Verificar instalación
docker --version
```

Deberías ver algo como: `Docker version 24.0.x`

## Paso 1.3: Instalar Docker Compose

```bash
# Descargar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permisos de ejecución
chmod +x /usr/local/bin/docker-compose

# Crear symlink
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verificar instalación
docker-compose --version
```

Deberías ver: `Docker Compose version v2.23.0`

## Paso 1.4: Instalar Make

```bash
dnf install -y make

# Verificar
make --version
```

## Paso 1.5: Clonar el Repositorio

```bash
cd /root
git clone https://github.com/eduardogarzab/HeartGuard.git
cd HeartGuard
```

## Paso 1.6: Configurar Firewall (IMPORTANTE)

Abrir puertos para que los microservicios puedan conectarse:

```bash
# PostgreSQL
firewall-cmd --permanent --add-port=5432/tcp

# Redis
firewall-cmd --permanent --add-port=6379/tcp

# InfluxDB
firewall-cmd --permanent --add-port=8086/tcp

# Backend Go (opcional, si quieres acceso externo)
firewall-cmd --permanent --add-port=8080/tcp

# Recargar firewall
firewall-cmd --reload

# Verificar
firewall-cmd --list-ports
```

## Paso 1.7: Generar Archivos de Configuración

```bash
cd /root/HeartGuard
make bootstrap-envs
```

El script te pedirá la siguiente información:

### Configuración General

```
IP/hostname del backend [134.199.204.58]: IP_BACKEND
IP/hostname de microservicios [129.212.181.53]: IP_MICROSERVICIOS
```

### PostgreSQL

```
Usuario superadmin [postgres]: postgres
Password superadmin [oculto]: postgres123
Puerto expuesto [5432]: 5432
Nombre de la base [heartguard]: heartguard
Usuario app [heartguard_app]: heartguard_app
Password app [oculto]: MySecurePass123
```

### Redis / Influx

```
Puerto Redis [6379]: 6379
Puerto Influx [8086]: 8086
Usuario Influx [admin]: admin
Password Influx [oculto]: influxdb123
Bucket [timeseries]: timeseries
Organización [heartguard]: heartguard
Token [oculto]: heartguard-token-change-me-in-prod
```

### Claves Compartidas (IMPORTANTES - Guárdalas)

```
JWT_SECRET [oculto]: <genera uno con: openssl rand -base64 32>
INTERNAL_SERVICE_KEY [oculto]: <genera otro: openssl rand -base64 32>
AI_MODEL_ID [988e1fee-e18e-4eb9-9b9d-72ae7d48d8bc]: [Enter para usar default]
```

Para generar claves seguras:

```bash
# Generar JWT_SECRET
openssl rand -base64 32

# Generar INTERNAL_SERVICE_KEY
openssl rand -base64 32
```

**⚠️ IMPORTANTE**: Guarda estas claves, las necesitarás para configurar los microservicios.

### DigitalOcean Spaces

```
Spaces Access Key [DO00EXAMPLEID]: TU_ACCESS_KEY_REAL
Spaces Secret Key [oculto]: TU_SECRET_KEY_REAL
Origin endpoint [https://...]: https://tu-bucket.region.digitaloceanspaces.com/
```

### Gateway

```
FLASK_SECRET_KEY [oculto]: <genera otro: openssl rand -base64 32>
```

## Paso 1.8: Configurar ENV del Backend para Acceso Remoto

Editar el archivo de configuración del backend:

```bash
vi /root/HeartGuard/backend/.env
```

Cambiar `ENV=prod` a `ENV=dev` para permitir acceso remoto y desactivar las Secure Cookies:

```env
ENV=dev
HTTP_ADDR=:8080
DATABASE_URL=postgres://heartguard_app:MySecurePass123@postgres:5432/heartguard?sslmode=disable
JWT_SECRET=<el_que_generaste>
ACCESS_TOKEN_TTL=15m
REFRESH_TOKEN_TTL=720h
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_RPS=10
RATE_LIMIT_BURST=20
SECURE_COOKIES=false
```

**Nota**: `ENV=dev` desactiva el middleware `LoopbackOnly` para permitir acceso remoto. En producción, usa un reverse proxy y vuelve a `ENV=prod`.

## Paso 1.9: Levantar el Stack del Backend

```bash
cd /root/HeartGuard

# Levantar todos los servicios
docker compose up -d

# Ver el estado
docker compose ps
```

Deberías ver algo como:

```
NAME                  IMAGE                    STATUS
heartguard-backend    heartguard-backend       Up (healthy)
heartguard-influxdb   influxdb:2.7-alpine      Up (healthy)
heartguard-postgres   postgis/postgis:14-3.2   Up (healthy)
heartguard-redis      redis:7-alpine           Up (healthy)
```

## Paso 1.10: Verificar que Todo Funciona

### Verificar PostgreSQL

```bash
docker compose exec -T postgres pg_isready -U postgres
```

Debe responder: `accepting connections`

### Verificar Redis

```bash
docker compose exec -T redis redis-cli PING
```

Debe responder: `PONG`

### Verificar InfluxDB

```bash
docker compose exec -T influxdb influx ping
```

Debe responder: `OK`

### Verificar Backend Go

```bash
curl http://localhost:8080/healthz
```

Debe responder con un `200 OK`

### Ver logs del backend

```bash
docker compose logs -f backend
```

Presiona `Ctrl+C` para salir.

---

# 🖥️ PARTE 2: Preparación VM de Microservicios

## Paso 2.1: Instalar Dependencias Básicas

Conectarse a la VM de microservicios (en otra terminal o desconectarse de la anterior):

```bash
ssh root@IP_MICROSERVICIOS
```

### Actualizar el sistema (CentOS 9)

```bash
# Actualizar paquetes
dnf update -y

# Instalar herramientas básicas
dnf install -y git curl wget vim net-tools nc
```

## Paso 2.2: Instalar Docker

```bash
# Instalar Docker
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce docker-ce-cli containerd.io

# Iniciar y habilitar Docker
systemctl start docker
systemctl enable docker

# Verificar instalación
docker --version
```

## Paso 2.3: Instalar Docker Compose

```bash
# Descargar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permisos de ejecución
chmod +x /usr/local/bin/docker-compose

# Crear symlink
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verificar instalación
docker-compose --version
```

## Paso 2.4: Instalar Make

```bash
dnf install -y make

# Verificar
make --version
```

## Paso 2.5: Clonar el Repositorio

```bash
cd /root
git clone https://github.com/eduardogarzab/HeartGuard.git
cd HeartGuard
```

## Paso 2.6: Verificar Conectividad con el Backend

**MUY IMPORTANTE**: Antes de continuar, verifica que puedes conectarte al backend:

```bash
# PostgreSQL
nc -zv IP_BACKEND 5432

# Redis
nc -zv IP_BACKEND 6379

# InfluxDB
nc -zv IP_BACKEND 8086
```

Si alguno falla:

1. Verifica el firewall en la VM del backend (Paso 1.6)
2. Verifica las reglas de seguridad del cloud provider
3. Verifica que los servicios estén corriendo en el backend

## Paso 2.7: Generar Archivos de Configuración

```bash
cd /root/HeartGuard
make bootstrap-envs
```

**⚠️ CRÍTICO**: Usa las **MISMAS** credenciales y claves que usaste en el backend.

### Configuración General

```
IP/hostname del backend [134.199.204.58]: IP_BACKEND
IP/hostname de microservicios [129.212.181.53]: IP_MICROSERVICIOS
```

### PostgreSQL (USAR LOS MISMOS VALORES DEL BACKEND)

```
Usuario superadmin [postgres]: postgres
Password superadmin [oculto]: postgres123
Puerto expuesto [5432]: 5432
Nombre de la base [heartguard]: heartguard
Usuario app [heartguard_app]: heartguard_app
Password app [oculto]: MySecurePass123  <-- MISMO que en backend
```

### Redis / Influx (USAR LOS MISMOS VALORES DEL BACKEND)

```
Puerto Redis [6379]: 6379
Puerto Influx [8086]: 8086
Usuario Influx [admin]: admin
Password Influx [oculto]: influxdb123
Bucket [timeseries]: timeseries
Organización [heartguard]: heartguard
Token [oculto]: heartguard-token-change-me-in-prod  <-- MISMO que en backend
```

### Claves Compartidas (USAR LAS MISMAS DEL BACKEND)

```
JWT_SECRET [oculto]: <EXACTAMENTE EL MISMO que en backend>
INTERNAL_SERVICE_KEY [oculto]: <EXACTAMENTE EL MISMO que en backend>
AI_MODEL_ID: [Enter para usar default]
```

### DigitalOcean Spaces (USAR LOS MISMOS)

```
Spaces Access Key: TU_ACCESS_KEY_REAL
Spaces Secret Key: TU_SECRET_KEY_REAL
Origin endpoint: https://tu-bucket.region.digitaloceanspaces.com/
```

### Gateway

```
FLASK_SECRET_KEY [oculto]: <genera uno nuevo: openssl rand -base64 32>
```

## Paso 2.8: Verificar Archivos .env Generados

```bash
ls -la micro-services/*/.env
```

Deberías ver 9 archivos `.env`:

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

### Verificar que las claves coincidan

```bash
# Ver JWT_SECRET en auth
grep JWT_SECRET micro-services/auth/.env

# Compara con el del backend (conéctate al backend en otra terminal)
ssh root@IP_BACKEND 'grep JWT_SECRET /root/HeartGuard/backend/.env'
```

**DEBEN SER IDÉNTICOS**. Si no coinciden, edítalos manualmente.

## Paso 2.9: Levantar los Microservicios

```bash
cd /root/HeartGuard/docker/microservices

# Levantar todos los microservicios
docker compose up -d

# Ver el progreso
docker compose logs -f
```

Este proceso puede tomar 2-5 minutos en la primera ejecución porque debe:

-   Descargar imágenes base de Python
-   Construir las imágenes de cada servicio
-   Instalar dependencias de Python

Presiona `Ctrl+C` cuando veas que todos están iniciando.

## Paso 2.10: Verificar Estado de los Contenedores

```bash
docker compose ps
```

Espera hasta que todos aparezcan como `healthy` (puede tomar 1-2 minutos):

```
NAME                     STATUS
heartguard-admin         Up (healthy)
heartguard-ai            Up (healthy)
heartguard-ai-monitor    Up (healthy)
heartguard-auth          Up (healthy)
heartguard-gateway       Up (healthy)
heartguard-media         Up (healthy)
heartguard-patient       Up (healthy)
heartguard-realtime      Up (healthy)
heartguard-user          Up (healthy)
```

Si alguno está `unhealthy`, revisa los logs:

```bash
docker compose logs <nombre-servicio>
```

---

# 🧪 PARTE 3: Pruebas End-to-End

## Paso 3.1: Acceder al Panel de Superadmin

Abre tu navegador en: `http://IP_BACKEND:8080/login`

**Credenciales por defecto**:

-   Email: `admin@heartguard.com`
-   Password: `Admin#2025`

## Paso 3.2: Probar el Gateway de Microservicios

En tu navegador: `http://IP_MICROSERVICIOS:8080/health`

## Paso 3.3: Acceder al Panel del Org Admin

**Se requiere python instalado localmente**

En tu computadora local, clona el repositorio:

```bash
git clone https://github.com/eduardogarzab/HeartGuard.git
cd HeartGuard
```

Navega a la carpeta del panel web:

```bash
cd clients/org-admin
```

Crea un servidor http local:

```bash
python3 -m http.server 4000
```

Abre tu navegador en: `http://localhost:4000`

**Credenciales por defecto**:

-   Email: `ana.ruiz@heartguard.com`
-   Password: `Demo#2025`

## Paso 3.4: Acceder a la aplicación de escritorio de Usuario/Paciente

---

# 🔧 PARTE 4: Comandos Útiles

## En la VM del Backend

### Ver logs

```bash
cd /root/HeartGuard
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f influxdb
```

### Reiniciar servicios

```bash
docker compose restart backend
docker compose restart postgres
```

### Acceder a PostgreSQL

```bash
docker compose exec postgres psql -U heartguard_app -d heartguard
```

### Backup de la base de datos

```bash
docker compose exec postgres pg_dump -U postgres heartguard > backup_$(date +%Y%m%d).sql
```

### Detener todo

```bash
docker compose down
```

### Limpiar todo y empezar de nuevo

```bash
docker compose down -v
docker compose up -d
```

## En la VM de Microservicios

### Ver logs de todos los servicios

```bash
cd /root/HeartGuard/docker/microservices
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

### Reconstruir un servicio

```bash
docker compose up -d --build auth-service
```

### Ver uso de recursos

```bash
docker stats
```

### Detener todo

```bash
docker compose down
```

### Limpiar y reconstruir

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

# 🐛 PARTE 5: Troubleshooting

## Problema: "Connection refused" al conectar a PostgreSQL

**Síntoma**: Los microservicios no pueden conectarse a PostgreSQL en el backend.

**Solución**:

1. Verifica que PostgreSQL esté escuchando en todas las interfaces:

```bash
# En VM del backend
docker compose exec postgres grep "listen_addresses" /var/lib/postgresql/data/postgresql.conf
```

2. Verifica el firewall:

```bash
# En VM del backend
firewall-cmd --list-ports | grep 5432
```

3. Verifica que el mapeo de puertos sea correcto:

```bash
docker port heartguard-postgres
```

4. Prueba conexión manual desde la VM de microservicios:

```bash
# En VM de microservicios
nc -zv IP_BACKEND 5432
```

## Problema: "JWT verification failed"

**Síntoma**: Los servicios rechazan tokens con error de firma inválida.

**Causa**: El `JWT_SECRET` no coincide entre el backend y los microservicios.

**Solución**:

1. Verifica el secret en el backend:

```bash
ssh root@IP_BACKEND 'cat /root/HeartGuard/backend/.env | grep JWT_SECRET'
```

2. Verifica en microservicios:

```bash
ssh root@IP_MICROSERVICIOS 'cat /root/HeartGuard/micro-services/auth/.env | grep JWT_SECRET'
```

3. Si no coinciden, edítalos y reinicia:

```bash
# Editar
nano /root/HeartGuard/micro-services/auth/.env

# Reiniciar
cd /root/HeartGuard/docker/microservices
docker compose restart
```

## Problema: Contenedor en estado "unhealthy"

**Solución**:

1. Ver logs detallados:

```bash
docker compose logs --tail=200 <nombre-servicio>
```

2. Ver el healthcheck:

```bash
docker inspect <nombre-contenedor> --format='{{json .State.Health}}' | python3 -m json.tool
```

3. Entrar al contenedor para debugging:

```bash
docker compose exec <nombre-servicio> sh
```

4. Probar el healthcheck manualmente:

```bash
docker compose exec <nombre-servicio> curl -f http://localhost:5001/health
```

## Problema: Puerto ya en uso

**Síntoma**: `Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use`

**Solución**:

1. Ver qué proceso está usando el puerto:

```bash
lsof -i :5432
```

2. Detener el proceso o cambiar el puerto en docker-compose.yml:

```yaml
ports:
    - "5433:5432" # Mapear al puerto 5433 del host
```

3. Actualizar los `.env` con el nuevo puerto.

## Problema: "Cannot connect to Docker daemon"

**Solución**:

```bash
# Verificar que Docker esté corriendo
systemctl status docker

# Si no está corriendo, iniciarlo
systemctl start docker

# Verificar permisos
ls -la /var/run/docker.sock
```

## Problema: Microservicio no puede resolver nombres (auth-service, etc.)

**Síntoma**: `Could not resolve host: auth-service`

**Causa**: Los servicios no están en la misma red Docker.

**Solución**:

1. Verificar las redes:

```bash
docker network ls
docker network inspect microservices_micro_net
```

2. Verificar que todos los servicios estén en la red:

```bash
docker compose ps --format "{{.Name}}\t{{.Networks}}"
```

3. Recrear la red:

```bash
docker compose down
docker network rm microservices_micro_net
docker compose up -d
```

---

# 🔒 PARTE 6: Seguridad en Producción

## Antes de ir a producción, realiza estos pasos:

### 1. Cambiar todas las contraseñas por defecto

```bash
# Generar passwords seguros
openssl rand -base64 32  # Para cada servicio
```

Editar todos los `.env` y cambiar:

-   `PGSUPER_PASS`
-   `DBPASS`
-   `INFLUXDB_PASSWORD`
-   `JWT_SECRET`
-   `INTERNAL_SERVICE_KEY`
-   `GATEWAY_SECRET`

### 2. Habilitar HTTPS

Instalar nginx como reverse proxy en ambas VMs:

```bash
dnf install -y nginx certbot python3-certbot-nginx

# Configurar nginx para el backend
nano /etc/nginx/conf.d/backend.conf
```

Ejemplo de configuración:

```nginx
server {
    listen 80;
    server_name backend.heartguard.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Obtener certificado SSL
certbot --nginx -d backend.heartguard.com
```

### 3. Cambiar ENV del backend a producción

```bash
nano /root/HeartGuard/backend/.env
```

Cambiar:

```env
ENV=prod
SECURE_COOKIES=true
```

Reiniciar:

```bash
docker compose restart backend
```

### 4. Restringir acceso a puertos

```bash
# Cerrar puertos públicos, permitir solo entre VMs
firewall-cmd --permanent --remove-port=5432/tcp
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="IP_MICROSERVICIOS" port protocol="tcp" port="5432" accept'
firewall-cmd --reload
```

### 5. Configurar backups automáticos

```bash
# Crear script de backup
nano /root/backup-heartguard.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker compose exec -T postgres pg_dump -U postgres heartguard > $BACKUP_DIR/heartguard_$DATE.sql

# Mantener solo los últimos 7 días
find $BACKUP_DIR -name "heartguard_*.sql" -mtime +7 -delete
```

```bash
chmod +x /root/backup-heartguard.sh

# Agregar a crontab (diario a las 2am)
crontab -e
```

Agregar:

```
0 2 * * * /root/backup-heartguard.sh
```

### 6. Configurar logging centralizado

Agregar a `/root/HeartGuard/docker-compose.yml`:

```yaml
services:
    backend:
        logging:
            driver: "json-file"
            options:
                max-size: "10m"
                max-file: "3"
```

### 7. Monitoreo de salud

Instalar un monitor externo (ej: UptimeRobot) o crear un script:

```bash
nano /root/health-check.sh
```

```bash
#!/bin/bash
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Verificar backend
if ! curl -sf http://localhost:8080/healthz > /dev/null; then
    curl -X POST $WEBHOOK_URL -d '{"text":"⚠️ Backend está caído!"}'
fi

# Verificar microservicios
if ! ssh root@IP_MICROSERVICIOS 'curl -sf http://localhost:8080/health' > /dev/null; then
    curl -X POST $WEBHOOK_URL -d '{"text":"⚠️ Gateway está caído!"}'
fi
```

```bash
chmod +x /root/health-check.sh

# Ejecutar cada 5 minutos
crontab -e
```

Agregar:

```
*/5 * * * * /root/health-check.sh
```

---

# 📊 PARTE 7: Monitoreo de Recursos

## Ver uso de CPU y memoria

```bash
# En tiempo real
docker stats

# Recursos por contenedor
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## Ver logs del sistema

```bash
# Logs de Docker
journalctl -u docker -f

# Logs del kernel
dmesg -T
```

## Espacio en disco

```bash
# Ver uso general
df -h

# Uso de Docker
docker system df

# Limpiar imágenes sin usar
docker system prune -a
```

---

# Comandos útiles de referencia rápida

```bash
# Ver todos los contenedores
docker ps -a

# Ver redes
docker network ls

# Ver volúmenes
docker volume ls

# Ver imágenes
docker images

# Limpiar todo
docker system prune -a --volumes

# Ver versión de todo
docker --version
docker compose version
make --version
```