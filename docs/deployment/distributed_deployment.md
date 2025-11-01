# 🌐 Guía de Despliegue Distribuido - HeartGuard

## 📋 Arquitectura Distribuida

```
┌─────────────────────────────────────────────────────────┐
│           MÁQUINA 1: 134.199.133.125                    │
│           (Backend + Base de Datos)                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Nginx (443)                                   │    │
│  │  └─> Backend Go (8080)                         │    │
│  │      - Panel de administración                 │    │
│  │      - APIs internas                           │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  PostgreSQL (5432) - SSL habilitado            │    │
│  │  └─> Público, accesible desde microservicios   │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Redis (6380) - TLS habilitado                 │    │
│  │  └─> Público, accesible desde microservicios   │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS + API Key
                           │
┌──────────────────────────▼──────────────────────────────┐
│           MÁQUINA 2: [IP_MICROSERVICIOS]                │
│           (Microservicios)                               │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Gateway (5000) - Expuesto públicamente        │    │
│  │  └─> Middleware: X-Internal-API-Key            │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Auth Service (5001)                           │    │
│  │  Organization Service (5002)                   │    │
│  │  User Service (5003)                           │    │
│  │  Patient Service (5004)                        │    │
│  │  Device Service (5005)                         │    │
│  │  ... (otros servicios)                         │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  RabbitMQ (5672, 15672)                        │    │
│  │  └─> Cola de mensajes interna                  │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuración Requerida

### MÁQUINA 1 (Backend - 134.199.133.125)

#### 1. Firewall - Abrir Puertos
```bash
# PostgreSQL (acceso desde microservicios)
sudo ufw allow from [IP_MICROSERVICIOS] to any port 5432 proto tcp comment "PostgreSQL from microservices"

# Redis TLS (acceso desde microservicios)
sudo ufw allow from [IP_MICROSERVICIOS] to any port 6380 proto tcp comment "Redis from microservices"

# Verificar reglas
sudo ufw status numbered
```

#### 2. Configurar .env.production
```bash
# En /root/HeartGuard/.env.production
# Agregar configuración de microservicios

# URL del Gateway en la máquina de microservicios
MICROSERVICES_GATEWAY_URL=http://[IP_MICROSERVICIOS]:5000

# API Key (debe coincidir con microservicios)
MICROSERVICES_API_KEY=390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1
```

#### 3. PostgreSQL - Permitir Conexiones Remotas
```bash
# Editar postgresql.conf
docker exec -it heartguard-postgres bash
vi /var/lib/postgresql/data/postgresql.conf

# Cambiar:
listen_addresses = '*'  # o 'localhost,134.199.133.125'

# Editar pg_hba.conf para permitir conexión desde microservicios
echo "hostssl heartguard heartguard_app [IP_MICROSERVICIOS]/32 md5" >> /var/lib/postgresql/data/pg_hba.conf

# Reiniciar PostgreSQL
docker compose restart postgres
```

#### 4. Redis - Ya está configurado
✅ Redis ya escucha en `0.0.0.0:6380` con TLS

---

### MÁQUINA 2 (Microservicios)

#### 1. Instalar Dependencias
```bash
# Docker & Docker Compose
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker

# Git
sudo apt install -y git
```

#### 2. Clonar Repositorio
```bash
git clone https://github.com/eduardogarzab/HeartGuard.git
cd HeartGuard/Microservicios
```

#### 3. Configurar .env.production
```bash
# Copiar el archivo .env.production que ya creamos
# O crear uno nuevo con estos valores:

# PostgreSQL (apunta a MÁQUINA 1)
DATABASE_URL=postgresql://heartguard_app:PASSWORD@134.199.133.125:5432/heartguard?sslmode=require

# Redis (apunta a MÁQUINA 1)
REDIS_URL=rediss://:PASSWORD@134.199.133.125:6380/0

# API Key (debe coincidir con backend)
INTERNAL_API_KEY=390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1

# Backend URL
BACKEND_INSTANCE_HOST=134.199.133.125
BACKEND_HTTPS_URL=https://admin.heartguard.live

# Seguridad
REQUIRE_API_KEY=true
```

#### 4. Firewall - Abrir Puerto Gateway
```bash
# Permitir conexiones al Gateway desde el Backend
sudo ufw allow from 134.199.133.125 to any port 5000 proto tcp comment "Gateway from backend"

# Si necesitas acceder al panel de RabbitMQ
sudo ufw allow from [TU_IP] to any port 15672 proto tcp comment "RabbitMQ management"

sudo ufw enable
```

#### 5. Desplegar Microservicios
```bash
cd /root/HeartGuard/Microservicios

# Usar docker-compose con overlay de producción
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Ver logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

---

## 🧪 Verificación de Conectividad

### Desde MÁQUINA 2 (Microservicios) → MÁQUINA 1 (Backend)

#### 1. Probar PostgreSQL
```bash
docker exec gateway python3 -c "
import psycopg2
import os
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT version();')
print(cur.fetchone())
conn.close()
print('✅ PostgreSQL SSL OK')
"
```

#### 2. Probar Redis
```bash
docker exec gateway python3 -c "
import redis
import os
r = redis.from_url(os.getenv('REDIS_URL'), ssl_cert_reqs=None)
print(r.ping())
print('✅ Redis TLS OK')
"
```

#### 3. Health Check Gateway
```bash
curl http://localhost:5000/health
# Debe retornar: {"service": "gateway", "status": "healthy"}
```

---

### Desde MÁQUINA 1 (Backend) → MÁQUINA 2 (Microservicios)

#### 1. Probar Gateway con API Key
```bash
# Reemplazar [IP_MICROSERVICIOS] con la IP real
curl -H "X-Internal-API-Key: 390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1" \
     http://[IP_MICROSERVICIOS]:5000/auth/health
```

#### 2. Sin API Key (debe fallar)
```bash
curl http://[IP_MICROSERVICIOS]:5000/auth/health
# Debe retornar: 401 o 403
```

---

## 🔐 Seguridad en Producción

### Checklist de Seguridad

- [ ] **Firewall en MÁQUINA 1**:
  - ✅ Puerto 443 abierto públicamente (HTTPS)
  - ✅ Puerto 5432 abierto solo para IP de microservicios
  - ✅ Puerto 6380 abierto solo para IP de microservicios

- [ ] **Firewall en MÁQUINA 2**:
  - ✅ Puerto 5000 abierto solo para IP del backend
  - ❌ Puertos 5001-5011 cerrados (internos Docker)

- [ ] **Autenticación**:
  - ✅ API Key en todas las requests al Gateway
  - ✅ PostgreSQL requiere SSL (`sslmode=require`)
  - ✅ Redis requiere TLS y password

- [ ] **Monitoreo**:
  - [ ] Logs centralizados
  - [ ] Alertas de intentos de acceso sin API Key
  - [ ] Health checks periódicos

---

## 📝 Scripts de Despliegue

### deploy-backend.sh (MÁQUINA 1)
```bash
#!/bin/bash
cd /root/HeartGuard
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend
```

### deploy-microservices.sh (MÁQUINA 2)
```bash
#!/bin/bash
cd /root/HeartGuard/Microservicios
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 🚨 Troubleshooting

### Error: "Connection refused" desde microservicios → PostgreSQL
**Solución**:
1. Verificar firewall en MÁQUINA 1: `sudo ufw status`
2. Verificar PostgreSQL escucha en `0.0.0.0`: `docker exec heartguard-postgres cat /var/lib/postgresql/data/postgresql.conf | grep listen_addresses`
3. Verificar `pg_hba.conf` permite la IP de microservicios

### Error: "Invalid API Key" desde backend → microservicios
**Solución**:
1. Verificar que `INTERNAL_API_KEY` sea idéntico en ambas máquinas
2. Verificar que `REQUIRE_API_KEY=true` en microservicios
3. Verificar header `X-Internal-API-Key` en el request

### Error: "SSL connection error" PostgreSQL
**Solución**:
1. Verificar que PostgreSQL tenga SSL habilitado: `SHOW ssl;`
2. Verificar certificados en `/root/HeartGuard/certs/postgres/`
3. Usar `sslmode=require` en `DATABASE_URL`

---

## 📞 Checklist de Deployment

### Pre-Deployment
- [ ] IP de MÁQUINA 2 conocida y documentada
- [ ] Firewall configurado en ambas máquinas
- [ ] `.env.production` actualizado en ambas máquinas
- [ ] API Key sincronizada
- [ ] Passwords de PostgreSQL y Redis actualizadas

### Deployment
- [ ] MÁQUINA 1: Backend desplegado y funcionando
- [ ] MÁQUINA 1: PostgreSQL y Redis accesibles remotamente
- [ ] MÁQUINA 2: Microservicios desplegados
- [ ] MÁQUINA 2: Health checks pasando

### Post-Deployment
- [ ] Pruebas de conectividad exitosas
- [ ] Logs sin errores
- [ ] Monitoreo configurado
- [ ] Backups configurados

---

**Última actualización**: 2025-11-01  
**Versión**: 1.0.0 - Despliegue Distribuido
