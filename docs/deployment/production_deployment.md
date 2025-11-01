# 🚀 HeartGuard - Deployment de Producción Completo

## ✅ Estado Actual (2025-11-01)

### Servicios Activos
- **PostgreSQL 14 + PostGIS**: SSL habilitado en puerto 5432
- **Redis 7**: TLS habilitado en puerto 6380 con autenticación
- **Backend Go**: SSL/TLS client verification habilitado
- **Nginx**: HTTPS con certificado Let's Encrypt válido
- **Gateway + Microservicios Python**: Activos

### Dominio y Certificados
- **Dominio**: admin.heartguard.live
- **IP Reservada**: 134.199.133.125 (Digital Ocean)
- **Certificado**: Let's Encrypt (válido hasta 2026-01-30)
- **Renovación**: Automática cada 12 horas vía systemd timer

---

## 🔐 Seguridad Implementada

### SSL/TLS en Todos los Servicios

#### PostgreSQL
```bash
# Verificar SSL activo
docker exec heartguard-postgres-1 psql -U postgres -c "SHOW ssl;"
# Output: on

# Conexión con SSL (desde backend)
DATABASE_URL=postgres://heartguard_app:[PASSWORD]@postgres:5432/heartguard?sslmode=require
```

#### Redis
```bash
# Verificar TLS activo
docker exec heartguard-redis-1 redis-cli --tls \
  --cert /usr/local/etc/redis/certs/redis.crt \
  --key /usr/local/etc/redis/certs/redis.key \
  --cacert /usr/local/etc/redis/certs/ca.crt \
  -a [PASSWORD] PING
# Output: PONG

# Conexión con TLS (desde backend)
REDIS_URL=rediss://:[PASSWORD]@redis:6380
```

#### Nginx + Let's Encrypt
```bash
# Certificado válido en:
/var/lib/docker/volumes/heartguard_certbot-etc/_data/live/admin.heartguard.live/

# Renovación automática configurada:
systemctl status certbot-renew.timer
```

### Firewall (UFW + iptables)

#### Puertos Abiertos
- **22/tcp**: SSH (limitado)
- **80/tcp**: HTTP (redirige a HTTPS)
- **443/tcp**: HTTPS
- **5432/tcp**: PostgreSQL (solo red interna Docker)
- **6380/tcp**: Redis (solo red interna Docker)

#### Reglas iptables Persistentes
```bash
# Script en /etc/iptables-docker-rules.sh
# Servicio systemd: iptables-docker.service

# Verificar reglas:
iptables -L DOCKER-USER -n -v
```

---

## 🔄 Comandos de Gestión

### Iniciar Todo el Sistema
```bash
cd /root/HeartGuard

# Modo producción (con SSL/TLS)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verificar estado
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### Reiniciar Servicios Individuales
```bash
# Backend (Go)
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend

# Nginx
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx

# Base de datos (⚠️ causa downtime)
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart postgres

# Redis (⚠️ pierde cache)
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart redis
```

### Limpieza Completa y Redeploy
```bash
cd /root/HeartGuard

# Detener todo
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Limpiar volúmenes (⚠️ BORRA DATOS)
docker volume rm heartguard_pgdata heartguard_redis-data

# Reconstruir e iniciar
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Nota: Los certificados SSL están en volúmenes separados y NO se borran
```

### Logs y Debugging
```bash
# Logs de todos los servicios
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Logs de un servicio específico
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f nginx

# Últimas 100 líneas
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=100 backend
```

---

## 🔒 Gestión de Certificados SSL

### Renovación Manual
```bash
# Renovar certificado (solo si está próximo a vencer)
docker run --rm \
  -v heartguard_certbot-etc:/etc/letsencrypt \
  -v heartguard_certbot-var:/var/lib/letsencrypt \
  -v heartguard_certbot-www:/var/www/certbot \
  certbot/certbot renew

# Reiniciar Nginx para aplicar
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### Renovación Automática
```bash
# Verificar timer activo
systemctl status certbot-renew.timer

# Próxima ejecución
systemctl list-timers certbot-renew.timer

# Ver historial de renovaciones
journalctl -u certbot-renew.service

# Probar renovación (dry-run)
docker run --rm \
  -v heartguard_certbot-etc:/etc/letsencrypt \
  -v heartguard_certbot-var:/var/lib/letsencrypt \
  -v heartguard_certbot-www:/var/www/certbot \
  certbot/certbot renew --dry-run
```

### Obtener Certificado para Nuevo Dominio
```bash
# Agregar subdominio a Nginx config primero
# Luego ejecutar:
docker run --rm \
  -v heartguard_certbot-etc:/etc/letsencrypt \
  -v heartguard_certbot-var:/var/lib/letsencrypt \
  -v heartguard_certbot-www:/var/www/certbot \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@heartguard.live \
  --agree-tos \
  --no-eff-email \
  -d nuevo.subdominio.heartguard.live
```

---

## 🔑 Credenciales de Producción

**⚠️ VER: `/root/HeartGuard/CREDENTIALS.md` para detalles completos**

### Ubicación de Secretos
- **Archivo principal**: `.env.production` (NO en git)
- **Backup encriptado**: `/root/HeartGuard/backup/.env.production.enc`
- **Certificados SSL**: `/root/HeartGuard/certs/` (NO en git)

### Rotación de Credenciales
```bash
# Generar nueva contraseña PostgreSQL
openssl rand -base64 32

# Actualizar en .env.production
nano .env.production

# Actualizar en base de datos
docker exec -it heartguard-postgres-1 psql -U postgres heartguard
ALTER USER heartguard_app WITH PASSWORD 'nueva_contraseña';
\q

# Reiniciar backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend
```

---

## 📊 Monitoreo y Salud del Sistema

### Verificar Todos los Servicios
```bash
# Estado de contenedores
docker ps --filter "name=heartguard"

# Healthchecks
docker inspect --format='{{.State.Health.Status}}' heartguard-postgres-1
docker inspect --format='{{.State.Health.Status}}' heartguard-redis-1
docker inspect --format='{{.State.Health.Status}}' heartguard-backend-1

# Conectividad HTTPS
curl -I https://admin.heartguard.live

# SSL/TLS interno
docker exec heartguard-postgres-1 psql -U postgres -c "SHOW ssl;"
docker exec heartguard-redis-1 redis-cli --tls \
  --cert /usr/local/etc/redis/certs/redis.crt \
  --key /usr/local/etc/redis/certs/redis.key \
  --cacert /usr/local/etc/redis/certs/ca.crt \
  -a $(grep REDIS_PASSWORD .env.production | cut -d= -f2) PING
```

### Verificar Firewall
```bash
# UFW status
ufw status verbose

# iptables (DOCKER-USER chain)
iptables -L DOCKER-USER -n -v

# Verificar reglas persistentes
systemctl status iptables-docker.service
```

### Verificar IP Reservada
```bash
# Ver IPs activas
ip addr show eth0

# Verificar netplan
cat /etc/netplan/50-cloud-init.yaml | grep 134.199.133.125
```

---

## 🚨 Troubleshooting

### Nginx No Inicia (Error SSL)
```bash
# Ver logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs nginx

# Verificar certificados existen
docker run --rm -v heartguard_certbot-etc:/etc/letsencrypt alpine ls -la /etc/letsencrypt/live/admin.heartguard.live/

# Si no existen, obtener certificados (ver sección anterior)
```

### Backend No Conecta a PostgreSQL/Redis
```bash
# Verificar variables de entorno
docker exec heartguard-backend-1 env | grep -E "DATABASE_URL|REDIS_URL"

# Verificar certificados montados
docker exec heartguard-backend-1 ls -la /srv/app/certs/

# Verificar conectividad desde backend
docker exec heartguard-backend-1 nc -zv postgres 5432
docker exec heartguard-backend-1 nc -zv redis 6380
```

### Let's Encrypt Timeout
```bash
# Verificar iptables (debe permitir 80 y 443)
iptables -L DOCKER-USER -n -v

# Si hay DROP rules, aplicar fix:
/etc/iptables-docker-rules.sh

# Verificar acceso HTTP externo
curl http://admin.heartguard.live/.well-known/acme-challenge/test

# Verificar DNS
dig +short admin.heartguard.live
```

### Sistema Lento / Alto CPU
```bash
# Ver uso de recursos
docker stats

# Si un contenedor consume mucho:
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart [servicio]

# Ver logs de errores
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=100 | grep -i error
```

---

## 🔄 Backup y Disaster Recovery

### Backup de Base de Datos
```bash
# Backup completo
docker exec heartguard-postgres-1 pg_dump -U postgres heartguard > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup con compresión
docker exec heartguard-postgres-1 pg_dump -U postgres heartguard | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Automatizar con cron (cada día a las 2 AM)
0 2 * * * docker exec heartguard-postgres-1 pg_dump -U postgres heartguard | gzip > /root/backups/heartguard_$(date +\%Y\%m\%d).sql.gz
```

### Restaurar Base de Datos
```bash
# Desde backup .sql
docker exec -i heartguard-postgres-1 psql -U postgres heartguard < backup_20251101.sql

# Desde backup .sql.gz
gunzip -c backup_20251101.sql.gz | docker exec -i heartguard-postgres-1 psql -U postgres heartguard
```

### Backup de Certificados
```bash
# Backup de volumen certbot
docker run --rm -v heartguard_certbot-etc:/source -v $(pwd):/backup alpine tar czf /backup/certbot-backup-$(date +%Y%m%d).tar.gz -C /source .

# Restaurar desde backup
docker run --rm -v heartguard_certbot-etc:/target -v $(pwd):/backup alpine sh -c "cd /target && tar xzf /backup/certbot-backup-20251101.tar.gz"
```

---

## 📝 Checklist de Deployment

### Pre-Deployment
- [ ] Código en `main` branch actualizado
- [ ] `.env.production` con credenciales seguras
- [ ] Certificados SSL generados (`certs/`)
- [ ] DNS apuntando a IP correcta
- [ ] Firewall configurado (UFW + iptables)
- [ ] Backup de base de datos actual

### Deployment
- [ ] `docker compose down` (si aplica)
- [ ] `docker compose up -d --build`
- [ ] Verificar healthchecks (`docker ps`)
- [ ] Verificar logs (`docker compose logs`)
- [ ] Verificar SSL/TLS internos
- [ ] Verificar HTTPS externo

### Post-Deployment
- [ ] Probar login en https://admin.heartguard.live
- [ ] Verificar certificado Let's Encrypt válido
- [ ] Verificar timer de renovación activo
- [ ] Verificar servicio iptables-docker activo
- [ ] Crear backup post-deployment
- [ ] Documentar cambios en CHANGELOG.md

---

## 📞 Soporte y Contacto

**Administrador del Sistema**: Ver `/root/HeartGuard/CREDENTIALS.md`

**Logs Importantes**:
- `/var/log/letsencrypt/letsencrypt.log` (dentro del contenedor certbot)
- `journalctl -u certbot-renew.service` (renovación automática)
- `journalctl -u iptables-docker.service` (firewall)

**Documentación Relacionada**:
- `CREDENTIALS.md` - Todas las credenciales
- `SECURITY_SSL_TLS.md` - Detalles de implementación SSL/TLS
- `docs/ssl_tls_setup.md` - Guía de setup SSL/TLS
- `docs/validation_plan.md` - Plan de validación de servicios

---

## 🎯 Estado de Producción

**Última actualización**: 2025-11-01 16:56 UTC

✅ **Sistema completamente operacional en producción**

- PostgreSQL: ✅ SSL ON
- Redis: ✅ TLS ON
- Backend: ✅ SSL/TLS Verification ON
- Nginx: ✅ HTTPS con Let's Encrypt
- Firewall: ✅ Configurado y persistente
- Certificados: ✅ Renovación automática activa
- DNS: ✅ Apuntando a IP Reservada
- Backups: ⚠️ Configurar cron para automatizar

**Próximos pasos sugeridos**:
1. Configurar backups automáticos diarios
2. Implementar monitoreo con Prometheus/Grafana
3. Configurar alertas vía email/Slack
4. Documentar procedimientos de escalado
