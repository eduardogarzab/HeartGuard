# Guía de Despliegue - HeartGuard Backend con HTTPS

## Estado Actual ✅

- **Backend**: Corriendo en Docker (puerto interno 8080)
- **Nginx**: Reverse proxy con HTTPS habilitado (puertos 80/443)
- **Certificado SSL**: Let's Encrypt para `admin.heartguard.live` (expira 2026-01-30)
- **Base de datos**: PostgreSQL + PostGIS inicializada y con datos seed
- **Redis**: Cache y sesiones activos
- **Dominio**: `admin.heartguard.live` → HTTPS activo

## Acceso

🌐 **URL Principal**: https://admin.heartguard.live

### Credenciales por defecto (seed)
- Email: `admin@heartguard.com`
- Password: `admin123`

## Comandos Útiles

### Ver logs
```bash
# Backend
make prod-logs

# Nginx (proxy)
make prod-proxy-logs

# Todos los servicios
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### Reiniciar servicios
```bash
# Reiniciar backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend

# Reiniciar proxy
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx

# Detener todo
make prod-down
```

### Gestión de base de datos
```bash
# Acceder a psql (dentro del contenedor)
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d heartguard

# Re-inicializar DB (⚠️ destruye datos)
make prod-db-reset
```

### Renovación de certificado SSL

El certificado expira el **2026-01-30**. Para renovarlo:

```bash
# 1. Detener nginx (libera puertos 80/443)
make prod-proxy-down

# 2. Renovar certificado
make prod-certbot-renew

# 3. Reactivar nginx
make prod-proxy-up
```

**Recomendación**: Configura un cron job para renovar automáticamente:
```bash
# Editar crontab
crontab -e

# Agregar (ejecuta cada 60 días a las 3 AM)
0 3 */60 * * cd /root/HeartGuard && make prod-proxy-down && make prod-certbot-renew && make prod-proxy-up
```

## Arquitectura de Red

```
Internet (443/80)
    ↓
[Nginx Container]
    ↓ proxy_pass
[Backend Container :8080] ←→ [Postgres] ←→ [Redis]
```

- **Backend**: Solo expuesto internamente (red Docker)
- **Nginx**: Maneja SSL/TLS y proxy reverso
- **Allowlist**: `LOOPBACK_ALLOW_CIDRS=172.16.0.0/12` permite tráfico desde contenedores Docker

## Variables de Entorno Importantes

Editables en `/root/HeartGuard/.env.production`:

| Variable | Valor Actual | Descripción |
|----------|--------------|-------------|
| `ADMIN_HOST` | `admin.heartguard.live` | Dominio del panel |
| `TLS_EMAIL` | `jorge.serangelli@udem.edu` | Email para Let's Encrypt |
| `SECURE_COOKIES` | `true` | Cookies solo via HTTPS (requerido) |
| `LOOPBACK_ALLOW_CIDRS` | `172.16.0.0/12` | IPs permitidas (red Docker) |
| `JWT_SECRET` | *(configurado)* | Clave para tokens de sesión |
| `DATABASE_URL` | `postgres://...` | Conexión a PostgreSQL |
| `REDIS_URL` | `redis://redis:6379/0` | Conexión a Redis |

## Solución de Problemas

### "csrf inválido" en login
- ✅ Ya resuelto: Acceso via HTTPS habilita cookies seguras
- Si persiste: Verificar que `SECURE_COOKIES=true` y accedes via `https://`

### 403 Forbidden (loopback)
- ✅ Ya resuelto: `LOOPBACK_ALLOW_CIDRS` incluye red Docker
- Los logs muestran IPs bloqueadas con `blocked non-loopback request`

### Nginx no arranca
```bash
# Ver errores de configuración
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs nginx

# Probar configuración
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -t
```

### Certificado expirado
```bash
# Ver estado
docker run --rm -v heartguard_certbot-etc:/etc/letsencrypt certbot/certbot:latest certificates

# Renovar manualmente
make prod-proxy-down
make prod-certbot-renew
make prod-proxy-up
```

## Próximos Pasos

1. **Cambiar credenciales por defecto**: Acceder al panel y crear nuevos usuarios superadmin
2. **Backup de base de datos**: Configurar pg_dump periódico
3. **Monitoreo**: Considerar logs centralizados (ej. ELK, Loki)
4. **Firewall**: Verificar que solo puertos 80/443/22 estén expuestos

## Estructura de Archivos

```
/root/HeartGuard/
├── .env.production              # Variables de entorno (producción)
├── docker-compose.yml            # Servicios base (Postgres, Redis)
├── docker-compose.prod.yml       # Overlay producción (Backend, Nginx, Certbot)
├── Makefile                      # Comandos de gestión
├── nginx/
│   └── conf.d/
│       ├── admin.conf            # Config HTTPS activa
│       └── admin-http-only.conf.bak  # Backup config HTTP
└── backend/
    ├── Dockerfile
    ├── cmd/superadmin-api/
    ├── internal/
    └── templates/
```

## Contacto y Soporte

- **Repositorio**: HeartGuard
- **Documentación Backend**: `/root/HeartGuard/backend/README.md`
- **Email certificado**: jorge.serangelli@udem.edu
