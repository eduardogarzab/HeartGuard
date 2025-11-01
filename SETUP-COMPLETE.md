# 🎉 HeartGuard Backend - Configuración Completa

## ✅ Estado del Sistema

### Servicios Activos
- **Backend Go**: `heartguard/superadmin-api:latest` (puerto interno 8080)
- **Nginx**: Reverse proxy con HTTPS (puertos 80/443, solo localhost)
- **PostgreSQL**: Base de datos PostGIS (puerto 5432)
- **Redis**: Cache y sesiones (puerto 6379)

### Seguridad
- ✅ Firewall UFW activo
- ✅ Puertos 80/443 bloqueados para acceso externo (solo localhost)
- ✅ Puerto 22 (SSH) abierto
- ✅ Certificado SSL Let's Encrypt válido hasta 2026-01-30
- ✅ Cookies seguras (HTTPS only, SameSite Strict)
- ✅ CSRF protection activa

### Base de Datos
- ✅ PostgreSQL 14 + PostGIS
- ✅ Usuario: `heartguard_app` / Password: `dev_change_me`
- ✅ Schema `heartguard` con datos seed
- ✅ Usuario admin: `admin@heartguard.com` / `admin123`

---

## 🔐 Acceso

### Acceso Directo con Whitelist (CONFIGURADO)
```bash
# Conéctate por SSH (el firewall se actualiza automáticamente)
ssh root@134.199.133.125
```

Luego accede en tu navegador:
- **URL**: https://admin.heartguard.live
- **Email**: admin@heartguard.com
- **Password**: admin123

> ✅ El firewall permite SOLO tu IP actual
> 🔄 Se actualiza automáticamente al conectarte via SSH
> ❌ Resto del mundo: BLOQUEADO

### Acceso via Túnel SSH (Alternativa)
```bash
ssh -L 8443:127.0.0.1:443 root@134.199.133.125
```
Luego: https://localhost:8443

---

## 🛠️ Comandos Útiles

### Gestión de Servicios
```bash
# Ver logs
make prod-logs              # Backend
make prod-proxy-logs        # Nginx
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Reiniciar servicios
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx

# Detener todo
make prod-down
```

### Base de Datos
```bash
# Acceder a psql
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec postgres \
  psql -U heartguard_app -d heartguard

# Re-inicializar DB (⚠️ destruye datos)
make prod-db-reset
```

### Firewall
```bash
# Ver reglas UFW
sudo ufw status verbose

# Ver reglas Docker
sudo iptables -L DOCKER-USER -n --line-numbers

# Re-aplicar reglas Docker (tras reinicio)
sudo systemctl restart docker-ufw-fix.service
```

### Certificado SSL
```bash
# Ver estado
docker run --rm -v heartguard_certbot-etc:/etc/letsencrypt \
  certbot/certbot:latest certificates

# Renovar (antes del 2026-01-30)
make prod-proxy-down
make prod-certbot-renew
make prod-proxy-up
```

---

## 📁 Estructura

```
/root/HeartGuard/
├── .env.production              # Variables de entorno (producción)
├── docker-compose.yml            # Servicios base (Postgres, Redis)
├── docker-compose.prod.yml       # Overlay producción (Backend, Nginx)
├── docker-ufw-fix.sh            # Script firewall Docker
├── Makefile                      # Comandos de gestión
├── DEPLOYMENT.md                 # Guía de despliegue
├── backend/                      # Código fuente Go
│   ├── Dockerfile
│   ├── cmd/superadmin-api/
│   └── internal/
├── nginx/
│   └── conf.d/
│       └── admin.conf            # Config HTTPS activa
└── db/
    ├── init.sql
    └── seed.sql
```

---

## 🔄 Persistencia tras Reinicios

El servicio `docker-ufw-fix.service` se ejecuta automáticamente al iniciar el sistema para re-aplicar las reglas de firewall Docker.

```bash
# Verificar estado
sudo systemctl status docker-ufw-fix.service
```

---

## 🆘 Solución de Problemas

### "csrf inválido" en login
- ✅ Ya resuelto: Acceso via HTTPS con cookies seguras
- Limpia cookies del navegador si persiste

### 403 Forbidden
- ✅ Ya resuelto: Middleware acepta tráfico del proxy nginx
- Variable `LOOPBACK_ALLOW_CIDRS=172.16.0.0/12` en `.env.production`

### No puedo acceder desde internet
- ✅ **Correcto**: El sitio está bloqueado para acceso externo
- Usa túnel SSH: `ssh -L 8443:127.0.0.1:443 root@134.199.133.125`

### Certificado expirado
```bash
make prod-proxy-down
make prod-certbot-renew
make prod-proxy-up
```

---

## 📊 Información del Sistema

- **IP Pública**: 134.199.133.125
- **Dominio**: admin.heartguard.live (solo para certificado)
- **Email TLS**: jorge.serangelli@udem.edu
- **Certificado expira**: 2026-01-30

---

## 🎯 Próximos Pasos Recomendados

1. **Cambiar credenciales por defecto**
   - Crear nuevos usuarios superadmin
   - Deshabilitar/eliminar admin@heartguard.com

2. **Backup de base de datos**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml exec postgres \
     pg_dump -U heartguard_app heartguard > backup_$(date +%Y%m%d).sql
   ```

3. **Monitoreo**
   - Configurar alertas para certificado SSL
   - Logs centralizados (opcional)

4. **Documentación**
   - Documentar usuarios y roles específicos del proyecto
   - Guía de onboarding para nuevos administradores

---

**Configuración completada el**: 2025-11-01  
**Por**: GitHub Copilot
