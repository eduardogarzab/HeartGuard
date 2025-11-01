# Configuración SSL/TLS Completa - HeartGuard

## ✅ Implementación Completa

### 📋 Resumen Ejecutivo

Se ha implementado **cifrado end-to-end** en HeartGuard para producción:

1. **PostgreSQL con SSL** (puerto 5432) ✅
2. **Redis con TLS** (puerto 6380) ✅
3. **HTTPS en Nginx** (Let's Encrypt) ✅
4. **Backend con verificación de certificados** ✅

---

## 🔐 Componentes Implementados

### 1. Certificados SSL/TLS

**Script de generación:** `generate_certs.sh`
- Crea CA (Certificate Authority) auto-firmada
- Genera certificados para PostgreSQL server
- Genera certificados para Redis server
- Genera certificados de cliente para el backend
- Establece permisos correctos (600 para .key, 644 para .crt)

**Estructura generada:**
```
certs/
├── ca.crt                  # Certificate Authority pública
├── ca.key                  # CA privada (PROTEGER)
├── client.crt              # Cliente backend
├── client.key              # Cliente privada
├── postgres/
│   ├── server.crt         # Certificado del servidor PostgreSQL
│   ├── server.key         # Clave privada del servidor
│   └── ca.crt             # CA para verificación
└── redis/
    ├── redis.crt          # Certificado del servidor Redis
    ├── redis.key          # Clave privada del servidor
    └── ca.crt             # CA para verificación
```

**Validez:** 10 años (3650 días)
**Algoritmo:** RSA 2048 bits
**Propietarios:** UID 999 (Docker postgres/redis user)

---

### 2. PostgreSQL SSL

#### docker-compose.yml
```yaml
postgres:
  volumes:
    - ./certs/postgres:/var/lib/postgresql/certs:ro
  command: >
    postgres
    -c ssl=on
    -c ssl_cert_file=/var/lib/postgresql/certs/server.crt
    -c ssl_key_file=/var/lib/postgresql/certs/server.key
    -c ssl_ca_file=/var/lib/postgresql/certs/ca.crt
```

#### .env.production
```bash
DATABASE_URL=postgres://heartguard_app:PASSWORD@postgres:5432/heartguard?sslmode=require
```

#### backend/internal/db/db.go
```go
// Carga ca.crt y configura TLS si ENV=prod
if cfg.Env == "prod" {
    caCert, err := os.ReadFile("certs/ca.crt")
    if err == nil {
        pc.ConnConfig.TLSConfig = &tls.Config{
            RootCAs:            caCertPool,
            InsecureSkipVerify: false,
            MinVersion:         tls.VersionTLS12,
        }
    }
}
```

**Verificación:**
```bash
docker exec heartguard-postgres psql -U postgres -c "SHOW ssl;"
# Debe mostrar: ssl | on
```

---

### 3. Redis TLS

#### docker-compose.yml
```yaml
redis:
  ports:
    - "6380:6380"
  command: [
    "redis-server",
    "--port", "0",
    "--tls-port", "6380",
    "--tls-cert-file", "/etc/redis/certs/redis.crt",
    "--tls-key-file", "/etc/redis/certs/redis.key",
    "--tls-ca-cert-file", "/etc/redis/certs/ca.crt"
  ]
  volumes:
    - ./certs/redis:/etc/redis/certs:ro
```

#### .env.production
```bash
REDIS_URL=rediss://redis:6380/0  # Nota: doble 's' en rediss
REDIS_TLS_ENABLED=true
```

#### backend/internal/rediscli/redis.go
```go
// Si URL usa rediss://, configura TLS
if opt.TLSConfig != nil {
    caCert, err := os.ReadFile("certs/ca.crt")
    if err == nil {
        opt.TLSConfig = &tls.Config{
            RootCAs:            caCertPool,
            InsecureSkipVerify: false,
            MinVersion:         tls.VersionTLS12,
        }
    }
}
```

**Verificación:**
```bash
docker exec heartguard-redis redis-cli --tls --cacert /etc/redis/certs/ca.crt -p 6380 PING
# Debe retornar: PONG
```

---

### 4. Backend con Verificación de Certificados

**Modificaciones:**

1. **db.go** - Carga `certs/ca.crt` y configura `TLSConfig` en pool de PostgreSQL
2. **redis.go** - Carga `certs/ca.crt` y configura `TLSConfig` en cliente Redis
3. **Verificación activa** - `InsecureSkipVerify: false`
4. **TLS 1.2+** - Versión mínima obligatoria

**Logs esperados al iniciar:**
```
✅ PostgreSQL SSL/TLS habilitado con verificación de certificado
✅ Redis TLS habilitado con verificación de certificado
```

---

### 5. Makefile con Comandos SSL/TLS

**Nuevos targets:**
```makefile
prod-certs:
    # Genera certificados con generate_certs.sh si no existen

prod-deploy: prod-certs prod-build prod-up prod-db-reset
    # Deploy completo incluyendo generación de certificados

prod-restart:
    # Reinicia servicios de producción
```

**Uso:**
```bash
make prod-certs        # Solo generar certificados
make prod-deploy       # Deploy completo con SSL/TLS
make prod-restart      # Reiniciar servicios
make prod-logs         # Ver logs y verificar SSL/TLS
```

---

### 6. Documentación

**Archivos creados:**
- `docs/ssl_tls_setup.md` - Guía completa de configuración SSL/TLS
- `SECURITY_SSL_TLS.md` - Este resumen técnico

**README actualizado:**
- Sección "SSL/TLS" en variables de entorno
- Comandos `prod-certs` y `prod-deploy` documentados
- Sección "Deploy en Producción" actualizada con SSL/TLS

**`.gitignore` actualizado:**
```
# SSL/TLS Certificates (NUNCA commitear claves privadas)
certs/*.key
certs/**/*.key
certs/ca.key
certs/client.key
```

---

## 🚀 Flujo de Deploy en Producción

### Primera vez (setup completo):

```bash
# 1. Generar certificados SSL/TLS
./generate_certs.sh
# O: make prod-certs

# 2. Configurar variables de entorno
cp .env.production .env
# Editar .env con:
# - DATABASE_URL con ?sslmode=require
# - REDIS_URL con rediss://
# - Passwords seguros

# 3. Deploy completo
make prod-deploy

# 4. Verificar SSL/TLS habilitado
make prod-logs | grep -E 'SSL|TLS'

# Deberías ver:
# ✅ PostgreSQL SSL/TLS habilitado con verificación de certificado
# ✅ Redis TLS habilitado con verificación de certificado
```

### Deploys subsiguientes:

```bash
make prod-build        # Solo rebuild del backend
make prod-up           # Levantar servicios
make prod-restart      # Reiniciar servicios existentes
```

---

## 🔍 Verificación SSL/TLS

### Verificar PostgreSQL SSL

```bash
# Dentro del contenedor
docker exec heartguard-postgres psql -U postgres -c "SHOW ssl;"
# Debe mostrar: ssl | on

# Verificar conexión desde el host
psql "postgres://heartguard_app:PASSWORD@localhost:5432/heartguard?sslmode=require" -c "SELECT version();"
```

### Verificar Redis TLS

```bash
# Dentro del contenedor
docker exec heartguard-redis redis-cli --tls --cacert /etc/redis/certs/ca.crt -p 6380 PING
# Debe retornar: PONG

# Ver configuración TLS
docker exec heartguard-redis redis-cli --tls --cacert /etc/redis/certs/ca.crt -p 6380 INFO server | grep tls
```

### Verificar Backend

```bash
# Ver logs del backend
docker logs heartguard-backend 2>&1 | grep -E "SSL|TLS"

# Debe mostrar:
# ✅ PostgreSQL SSL/TLS habilitado con verificación de certificado
# ✅ Redis TLS habilitado con verificación de certificado
```

### Verificar HTTPS en Nginx

```bash
# Verificar certificado Let's Encrypt
curl -vI https://admin.heartguard.live 2>&1 | grep -E "SSL|TLS|subject"

# Verificar headers de seguridad
curl -I https://admin.heartguard.live | grep -E "Strict-Transport|X-Content-Type|X-Frame"
```

---

## 🔒 Niveles de Seguridad

### Desarrollo (dev):
- ❌ SSL/TLS deshabilitado
- `DATABASE_URL` con `?sslmode=disable`
- `REDIS_URL` con `redis://`
- Cookies sin `Secure` flag

### Producción (prod):
- ✅ SSL/TLS obligatorio
- ✅ `DATABASE_URL` con `?sslmode=require`
- ✅ `REDIS_URL` con `rediss://`
- ✅ Verificación de certificados activa
- ✅ TLS 1.2+ requerido
- ✅ Cookies con `Secure` flag
- ✅ HTTPS en Nginx (Let's Encrypt)
- ✅ Firewall con IP whitelist

---

## 📊 Impacto de SSL/TLS

### Rendimiento:
- PostgreSQL: ~5-10% overhead
- Redis: ~2-5% overhead
- HTTPS (Nginx): ~1-3% overhead
- **Total:** ~8-18% overhead

**Conclusión:** El impacto es **mínimo** comparado con los beneficios de seguridad.

### Latencia:
- Handshake inicial TLS: +50-100ms (una vez por conexión)
- Pool de conexiones minimiza impacto (conexiones reutilizadas)

### Throughput:
- Cifrado AES: ~2GB/s en hardware moderno
- PostgreSQL típicamente limitado por I/O de disco, no por cifrado
- Redis típicamente limitado por red, no por cifrado

---

## 🔧 Troubleshooting

### Error: "certificate verify failed"

**Causa:** El backend no puede verificar el certificado del servidor.

**Solución:**
```bash
# Verificar que existan los certificados
ls -la certs/ca.crt certs/postgres/ca.crt certs/redis/ca.crt

# Regenerar certificados
./generate_certs.sh

# Reiniciar servicios
make prod-restart
```

### Error: "connection refused" en Redis

**Causa:** Redis no está escuchando en el puerto TLS.

**Solución:**
```bash
# Verificar puerto TLS
docker exec heartguard-redis netstat -tulpn | grep 6380

# Verificar logs
docker logs heartguard-redis | grep -i tls

# Debe mostrar: Ready to accept connections (TLS)
```

### Error: "pq: SSL is not enabled on the server"

**Causa:** PostgreSQL no tiene SSL habilitado.

**Solución:**
```bash
# Verificar configuración SSL
docker exec heartguard-postgres psql -U postgres -c "SHOW ssl;"

# Si dice "off", verificar docker-compose.yml
docker inspect heartguard-postgres | grep -A 10 Cmd

# Debe incluir: -c ssl=on
```

### Warning: "No se pudo cargar CA cert"

**Causa:** El backend no encuentra `certs/ca.crt`.

**Solución:**
```bash
# Verificar montaje de volumen en docker-compose.yml
docker inspect heartguard-backend | grep -A 10 Mounts

# Agregar volumen si falta:
# volumes:
#   - ./certs:/app/certs:ro
```

---

## 🔄 Rotación de Certificados

### Certificados Auto-firmados (desarrollo):
```bash
# Validez: 10 años (3650 días)
# Rotar antes de expirar o si se compromete ca.key

# Pasos:
1. Backup de certificados actuales
   cp -r certs certs.backup.$(date +%Y%m%d)

2. Regenerar certificados
   rm -rf certs/
   ./generate_certs.sh

3. Reiniciar servicios
   make prod-restart
```

### Certificados Let's Encrypt (producción):
```bash
# Auto-renovar cada 60 días
certbot renew --dry-run

# Configurar renovación automática (crontab)
0 0 * * 0 certbot renew --quiet && docker compose restart nginx
```

**Recomendación:** Rotar certificados cada **90 días** en producción.

---

## ✅ Checklist de Producción

### Pre-Deploy:
- [ ] Certificados SSL generados con `./generate_certs.sh`
- [ ] `.env.production` configurado con:
  - [ ] `DATABASE_URL` tiene `?sslmode=require`
  - [ ] `REDIS_URL` usa `rediss://`
  - [ ] `JWT_SECRET` con 32+ bytes
  - [ ] `SECURE_COOKIES=true`
  - [ ] Passwords fuertes para DBPASS
- [ ] `docker-compose.yml` tiene volúmenes `certs/` montados
- [ ] `.gitignore` excluye `certs/*.key`

### Post-Deploy:
- [ ] Logs muestran "✅ PostgreSQL SSL/TLS habilitado"
- [ ] Logs muestran "✅ Redis TLS habilitado"
- [ ] `psql` con `?sslmode=require` funciona
- [ ] `redis-cli --tls` funciona
- [ ] HTTPS funciona en Nginx
- [ ] Firewall permite solo puerto 443
- [ ] Health checks pasan
- [ ] Rate limiting funciona

### Seguridad:
- [ ] Certificados `.key` NO commiteados a git
- [ ] `ca.key` protegida (permisos 600)
- [ ] Backup de certificados en ubicación segura
- [ ] Calendario de rotación de certificados (90 días)
- [ ] Firewall configurado con IP whitelist
- [ ] Redis requiere autenticación (si expuesto)
- [ ] PostgreSQL usa usuario con mínimos privilegios

---

## 📚 Referencias

- [PostgreSQL SSL Documentation](https://www.postgresql.org/docs/14/ssl-tcp.html)
- [Redis TLS Documentation](https://redis.io/docs/manual/security/encryption/)
- [Let's Encrypt Best Practices](https://letsencrypt.org/docs/)
- [OWASP Transport Layer Protection](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Go TLS Configuration](https://pkg.go.dev/crypto/tls)
- [Docker Secrets Management](https://docs.docker.com/engine/swarm/secrets/)

---

## 🎯 Próximos Pasos

### Mejoras de Seguridad:

1. **Autenticación Mutua (mTLS):**
   - Backend presenta certificado de cliente
   - PostgreSQL valida certificado del backend
   - Redis valida certificado del backend

2. **Certificados de Producción:**
   - Reemplazar auto-firmados por Let's Encrypt
   - O usar certificados de CA confiable (DigiCert, Sectigo)

3. **Rotación Automática:**
   - Script de renovación automática
   - Reload de servicios sin downtime
   - Notificaciones de expiración

4. **Auditoría:**
   - Logs de conexiones SSL/TLS
   - Alertas de fallos de verificación
   - Métricas de uso de cifrado

5. **Hardening:**
   - Deshabilitar TLS 1.0/1.1 (solo TLS 1.2+)
   - Cipher suites seguros (AEAD)
   - Perfect Forward Secrecy (ECDHE)

---

**Estado:** ✅ Implementado y funcional  
**Última actualización:** Noviembre 1, 2025  
**Versión:** 1.0.0  
**Autor:** HeartGuard Team
