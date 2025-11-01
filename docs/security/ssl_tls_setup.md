# Configuración SSL/TLS en HeartGuard

## 📋 Resumen

HeartGuard implementa **cifrado end-to-end** en producción para todas las comunicaciones:

- ✅ **PostgreSQL con SSL** (puerto 5432)
- ✅ **Redis con TLS** (puerto 6380)
- ✅ **HTTPS en Nginx** (Let's Encrypt)
- ✅ **Verificación de certificados** en todas las conexiones

---

## 🔐 Componentes de Seguridad

### 1. PostgreSQL SSL

**Configuración en `docker-compose.yml`:**
```yaml
postgres:
  command: >
    postgres
    -c ssl=on
    -c ssl_cert_file=/var/lib/postgresql/certs/server.crt
    -c ssl_key_file=/var/lib/postgresql/certs/server.key
    -c ssl_ca_file=/var/lib/postgresql/certs/ca.crt
```

**Configuración en backend:**
- Variable: `DATABASE_URL=postgres://user:pass@host:5432/db?sslmode=require`
- El backend carga `certs/ca.crt` para verificar el servidor
- TLS 1.2+ requerido
- Verificación de certificado habilitada

**Modos SSL disponibles:**
- `disable` - Sin SSL (solo desarrollo)
- `require` - SSL obligatorio, sin verificación
- `verify-ca` - SSL + verificar CA
- `verify-full` - SSL + verificar CA + hostname

**Recomendación:** `require` para desarrollo interno, `verify-full` para producción pública

---

### 2. Redis TLS

**Configuración en `docker-compose.yml`:**
```yaml
redis:
  command: [
    "redis-server",
    "--port", "0",
    "--tls-port", "6380",
    "--tls-cert-file", "/etc/redis/certs/redis.crt",
    "--tls-key-file", "/etc/redis/certs/redis.key",
    "--tls-ca-cert-file", "/etc/redis/certs/ca.crt"
  ]
```

**Configuración en backend:**
- Variable: `REDIS_URL=rediss://redis:6380/0` (nota: doble `s` en `rediss`)
- El backend carga `certs/ca.crt` para verificar el servidor
- TLS 1.2+ requerido

---

### 3. HTTPS en Nginx

**Configuración Let's Encrypt:**
```bash
certbot --nginx -d admin.heartguard.live --email tu@email.com --agree-tos --non-interactive
```

**Headers de seguridad:**
- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options`
- `X-Frame-Options`
- `X-XSS-Protection`

---

## 🚀 Setup Completo

### Paso 1: Generar Certificados

```bash
# Generar certificados auto-firmados para PostgreSQL y Redis
./generate_certs.sh
```

Esto creará:
```
certs/
├── ca.crt                  # Certificate Authority (pública)
├── ca.key                  # CA privada (¡PROTEGER!)
├── client.crt              # Cliente (backend)
├── client.key              # Cliente privada
├── postgres/
│   ├── server.crt
│   ├── server.key
│   └── ca.crt
└── redis/
    ├── redis.crt
    ├── redis.key
    └── ca.crt
```

**⚠️ IMPORTANTE:**
- Los archivos `.key` **NUNCA** deben commitearse a git
- Ya están en `.gitignore`
- En producción, usar certificados de Let's Encrypt o CA confiable

---

### Paso 2: Verificar Variables de Entorno

Archivo `.env.production`:
```bash
# PostgreSQL con SSL
DATABASE_URL=postgres://heartguard_app:PASSWORD@postgres:5432/heartguard?sslmode=require

# Redis con TLS
REDIS_URL=rediss://redis:6380/0
REDIS_TLS_ENABLED=true
```

---

### Paso 3: Iniciar Servicios

```bash
# Generar certificados (primera vez)
./generate_certs.sh

# Deploy en producción
make prod-deploy

# Verificar logs
make prod-logs
```

**Verifica en los logs:**
```
✅ PostgreSQL SSL/TLS habilitado con verificación de certificado
✅ Redis TLS habilitado con verificación de certificado
```

---

## 🔍 Verificación de SSL/TLS

### Verificar PostgreSQL SSL

```bash
# Dentro del contenedor de PostgreSQL
docker exec heartguard-postgres psql -U postgres -c "SHOW ssl;"
# Debe mostrar: ssl | on

# Verificar conexión desde el host
psql "postgres://heartguard_app:PASSWORD@localhost:5432/heartguard?sslmode=require" -c "SELECT version();"
```

### Verificar Redis TLS

```bash
# Dentro del contenedor de Redis
docker exec heartguard-redis redis-cli --tls --cacert /etc/redis/certs/ca.crt -p 6380 PING
# Debe retornar: PONG

# Desde el host (requiere redis-cli con soporte TLS)
redis-cli --tls --cacert certs/ca.crt -h localhost -p 6380 PING
```

### Verificar Conexión Backend

```bash
# Ver logs del backend
docker logs heartguard-backend 2>&1 | grep -E "SSL|TLS"

# Debe mostrar:
# ✅ PostgreSQL SSL/TLS habilitado con verificación de certificado
# ✅ Redis TLS habilitado con verificación de certificado
```

---

## 🔧 Troubleshooting

### Error: "certificate verify failed"

**Problema:** El backend no puede verificar el certificado del servidor.

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

**Problema:** Redis no está escuchando en el puerto TLS.

**Solución:**
```bash
# Verificar puerto TLS
docker exec heartguard-redis netstat -tulpn | grep 6380

# Verificar comando de Redis
docker inspect heartguard-redis | grep -A 10 Cmd

# Debe incluir: --tls-port 6380
```

### Error: "pq: SSL is not enabled on the server"

**Problema:** PostgreSQL no tiene SSL habilitado.

**Solución:**
```bash
# Verificar configuración SSL
docker exec heartguard-postgres psql -U postgres -c "SHOW ssl;"

# Si dice "off", verificar comando de postgres
docker inspect heartguard-postgres | grep -A 10 Cmd

# Debe incluir: -c ssl=on
```

### Warning: "No se pudo cargar CA cert"

**Problema:** El backend no encuentra `certs/ca.crt`.

**Solución:**
```bash
# Verificar que los certificados estén en el contenedor
docker exec heartguard-backend ls -la /app/certs/ca.crt

# Si no existe, agregar volumen en docker-compose.yml:
# volumes:
#   - ./certs:/app/certs:ro
```

---

## 🔒 Seguridad Adicional

### Autenticación Mutua (mTLS)

Para máxima seguridad, habilitar autenticación mutua:

**PostgreSQL:**
```sql
-- En pg_hba.conf
hostssl all all 0.0.0.0/0 cert clientcert=verify-full
```

**Redis:**
```bash
--tls-auth-clients yes
--tls-auth-clients optional
```

**Backend:**
```go
// Cargar certificado de cliente
cert, _ := tls.LoadX509KeyPair("certs/client.crt", "certs/client.key")
tlsConfig.Certificates = []tls.Certificate{cert}
```

---

## 📊 Rendimiento

**Impacto de SSL/TLS:**
- PostgreSQL: ~5-10% overhead
- Redis: ~2-5% overhead
- HTTPS (Nginx): ~1-3% overhead

**Recomendación:** El overhead es **mínimo** comparado con los beneficios de seguridad.

---

## 🔄 Rotación de Certificados

**Para producción con Let's Encrypt:**
```bash
# Auto-renovar cada 60 días
certbot renew --dry-run
```

**Para certificados auto-firmados:**
```bash
# Generar nuevos certificados (validez: 10 años)
./generate_certs.sh

# Reiniciar servicios
make prod-restart
```

**Recomendación:** Rotar certificados cada **90 días** en producción.

---

## 📚 Referencias

- [PostgreSQL SSL Documentation](https://www.postgresql.org/docs/14/ssl-tcp.html)
- [Redis TLS Documentation](https://redis.io/docs/manual/security/encryption/)
- [Let's Encrypt Best Practices](https://letsencrypt.org/docs/)
- [OWASP Transport Layer Protection](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

## ✅ Checklist de Producción

- [ ] Certificados SSL generados con `./generate_certs.sh`
- [ ] `DATABASE_URL` tiene `?sslmode=require`
- [ ] `REDIS_URL` usa `rediss://` (doble s)
- [ ] Logs muestran "✅ PostgreSQL SSL/TLS habilitado"
- [ ] Logs muestran "✅ Redis TLS habilitado"
- [ ] HTTPS configurado en Nginx con Let's Encrypt
- [ ] Firewall permite solo puerto 443 (HTTPS)
- [ ] Certificados `.key` en `.gitignore`
- [ ] Certificados rotados cada 90 días (calendario)
- [ ] Backup de certificados en ubicación segura

---

**Estado:** ✅ Implementado y funcional  
**Última actualización:** Noviembre 2025
