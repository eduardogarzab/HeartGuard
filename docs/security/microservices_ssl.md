# 🔐 Configuración SSL/TLS - Microservicios HeartGuard

## 📋 Resumen

Los microservicios de HeartGuard están configurados para comunicarse de manera cifrada con:
- **PostgreSQL** usando SSL (`sslmode=require`)
- **Redis** usando TLS (puerto 6380)
- **Backend** usando autenticación con API Key

---

## 🏗️ Arquitectura de Seguridad

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend Go (SSR)                          │
│                  admin.heartguard.live                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Comunica con Gateway usando:                      │    │
│  │  - Header: X-Internal-API-Key                      │    │
│  │  - Network: heartguard_default (Docker)            │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ API Key: 390013...516f1
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                  Gateway (Puerto 5000)                        │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Middleware: validate_api_key_middleware()          │   │
│  │  - Valida X-Internal-API-Key en cada request        │   │
│  │  - Excepto /health (para health checks)             │   │
│  └─────────────────────────────────────────────────────┘   │
└────────┬──────────┬──────────┬──────────┬───────────────────┘
         │          │          │          │
         │          │          │          │
    ┌────▼────┐ ┌──▼────┐ ┌──▼──────┐ ┌─▼──────┐
    │  Auth   │ │ User  │ │ Patient │ │ Device │ ...
    │ Service │ │Service│ │ Service │ │Service │
    └────┬────┘ └───┬───┘ └────┬────┘ └────┬───┘
         │          │           │           │
         └──────────┴───────────┴───────────┘
                     │
              ┌──────▼──────┐
              │ PostgreSQL  │
              │  SSL Mode   │
              │   require   │
              └─────────────┘
```

---

## 🔑 Configuración de Seguridad

### 1. API Key para Comunicación Interna

**Ubicación**: 
- Backend: `/root/HeartGuard/.env.production`
- Microservicios: `/root/HeartGuard/Microservicios/.env.production`

**Variable**:
```bash
INTERNAL_API_KEY=390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1
```

**Generación**:
```bash
openssl rand -hex 32
```

**Uso en Requests**:
```bash
curl -H "X-Internal-API-Key: 390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1" \
     http://gateway:5000/auth/health
```

---

### 2. PostgreSQL con SSL

**Connection String**:
```
postgresql://heartguard_app:PASSWORD@134.199.133.125:5432/heartguard?sslmode=require
```

**Configuración**:
- `sslmode=require` - Fuerza conexión SSL
- Certificado del servidor verificado automáticamente
- Puerto: 5432 (público, accesible desde microservicios)

---

### 3. Redis con TLS

**Connection String**:
```
rediss://:PASSWORD@134.199.133.125:6380/0
```

**Configuración**:
- Protocolo: `rediss://` (TLS habilitado)
- Puerto: 6380 (TLS)
- Password protegido
- `REDIS_TLS_ENABLED=true`

---

## 🐳 Despliegue con Docker Compose

### Desarrollo
```bash
cd Microservicios
docker compose up -d
```

### Producción
```bash
cd Microservicios
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Nota**: El `docker-compose.prod.yml` configura:
- Variables de entorno desde `.env.production`
- Conexión a la red `heartguard_default` (red del backend)
- SSL habilitado en todas las conexiones de base de datos

---

## 🔒 Middleware de Seguridad

### Gateway - API Key Validation

**Archivo**: `Microservicios/gateway/middleware.py`

**Funcionalidad**:
```python
@app.before_request
def check_api_key():
    # Excepto /health
    if request.path == "/health":
        return None
    
    # Validar X-Internal-API-Key
    if os.getenv("REQUIRE_API_KEY") == "true":
        api_key = request.headers.get("X-Internal-API-Key")
        if api_key != os.getenv("INTERNAL_API_KEY"):
            raise APIError("Invalid API Key", 403)
```

**Activación**:
```bash
# En .env.production
REQUIRE_API_KEY=true
```

---

## 🧪 Pruebas de Conectividad

### 1. Verificar Gateway
```bash
# Sin API Key (debe fallar)
curl http://localhost:5000/auth/health

# Con API Key (debe funcionar)
curl -H "X-Internal-API-Key: 390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1" \
     http://localhost:5000/auth/health
```

### 2. Verificar PostgreSQL SSL
```bash
docker exec gateway psql "$DATABASE_URL" -c "SHOW ssl;"
# Debe retornar: on
```

### 3. Verificar Redis TLS
```bash
docker exec gateway python -c "
import redis
import os
r = redis.from_url(os.getenv('REDIS_URL'), ssl_cert_reqs='required')
print(r.ping())
"
# Debe retornar: True
```

---

## 📝 Variables de Entorno Clave

### Backend (.env.production)
```bash
MICROSERVICES_API_KEY=390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1
MICROSERVICES_GATEWAY_URL=http://gateway:5000
```

### Microservicios (.env.production)
```bash
# Seguridad
INTERNAL_API_KEY=390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1
REQUIRE_API_KEY=true
SSL_VERIFY=true

# Base de datos con SSL
DATABASE_URL=postgresql://heartguard_app:PASSWORD@134.199.133.125:5432/heartguard?sslmode=require

# Redis con TLS
REDIS_URL=rediss://:PASSWORD@134.199.133.125:6380/0
REDIS_TLS_ENABLED=true

# Backend
BACKEND_INSTANCE_HOST=134.199.133.125
BACKEND_HTTPS_URL=https://admin.heartguard.live
```

---

## ⚠️ Consideraciones de Seguridad

### ✅ Implementado:
- ✅ API Key para autenticación entre servicios
- ✅ PostgreSQL con SSL obligatorio
- ✅ Redis con TLS habilitado
- ✅ Variables de entorno protegidas (gitignore)
- ✅ Middleware de validación en Gateway

### 🔄 Pendiente/Recomendaciones:
- [ ] Rotar API Key periódicamente (cada 90 días)
- [ ] Implementar rate limiting por API Key
- [ ] Logs de auditoría para accesos con API Key
- [ ] Monitoreo de intentos de acceso fallidos
- [ ] Certificados SSL propios para comunicación interna (opcional)

---

## 🚨 Troubleshooting

### Error: "Missing API Key"
**Solución**: Agregar header `X-Internal-API-Key` con el valor correcto

### Error: "Invalid API Key"
**Solución**: Verificar que el API Key en backend y microservicios sea el mismo

### Error: "SSL connection error"
**Solución**: Verificar que PostgreSQL tenga SSL habilitado y `sslmode=require` en DATABASE_URL

### Error: "Redis TLS error"
**Solución**: Verificar que Redis esté corriendo en puerto 6380 con TLS habilitado

---

## 📞 Contacto

Para más información o soporte:
- Documentación completa: `docs/README.md`
- Credenciales: `docs/security/CREDENTIALS.md`

---

**Última actualización**: 2025-11-01  
**Versión**: 1.0.0
