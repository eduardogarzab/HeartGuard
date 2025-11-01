# 🎯 HeartGuard - Guía de Inicio Rápido

## ✅ Estado Actual

**Sistema**: ✅ Completamente operacional en producción  
**URL**: https://admin.heartguard.live  
**SSL**: ✅ Let's Encrypt válido hasta 2026-01-30  
**Última verificación**: 2025-11-01 17:00 UTC

---

## 🚀 Comandos Esenciales

### Verificar Sistema
```bash
./verify_production.sh
```

### Ver Logs
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### Reiniciar Servicios
```bash
# Reiniciar todo
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Reiniciar servicio específico
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend
```

### Regenerar Certificados SSL/TLS Internos
```bash
./generate_certs.sh
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart postgres redis backend
```

---

## 🔑 Credenciales de Acceso

### Panel de Administración
- **URL**: https://admin.heartguard.live/login
- **Email**: admin@heartguard.com
- **Password**: Configurada vía variable de entorno `ADMIN_PASSWORD`

**🔐 Seguridad**: La contraseña del superadmin NO está hardcodeada en el código. Se configura mediante variable de entorno en `.env.production`.

**⚠️ IMPORTANTE**: 
1. Cambia `ADMIN_PASSWORD` en `.env.production` antes del primer despliegue
2. Después del primer login, cambia la contraseña desde el panel
3. Ver `docs/security/CREDENTIALS.md` para más detalles

### Pacientes de Prueba (API)
- **María Delgado**: maria.delgado@example.com / Test123!
- **José Hernández**: jose.hernandez@example.com / Test123!
- **Valeria Ortiz**: valeria.ortiz@example.com / Test123!

**⚠️ IMPORTANTE**: Ver `docs/security/CREDENTIALS.md` para todas las credenciales del sistema.

---

## 📚 Documentación Completa

### Guías Principales
1. **[Estado de Producción](docs/deployment/PRODUCTION_STATUS.md)** - Checklist completo
2. **[Guía de Deployment](docs/deployment/production_deployment.md)** - Comandos y troubleshooting
3. **[Seguridad SSL/TLS](docs/security/SECURITY_SSL_TLS.md)** - Implementación detallada
4. **[Índice de Documentación](docs/README.md)** - Todas las guías disponibles

### Estructura del Proyecto
```
HeartGuard/
├── backend/           # Backend Go SSR
├── microservicios/    # Servicios Python
├── db/                # Scripts de base de datos
├── nginx/             # Configuración Nginx
├── certs/             # Certificados SSL/TLS
├── docs/              # 📚 Documentación completa
│   ├── deployment/    # Guías de deployment
│   ├── security/      # Docs de seguridad
│   └── scripts/       # Scripts de utilidad
├── docker-compose.yml
└── docker-compose.prod.yml
```

---

## 🔧 Troubleshooting Rápido

### El sitio no carga
```bash
# 1. Verificar que los servicios están corriendo
docker compose ps

# 2. Verificar logs de Nginx
docker compose logs nginx

# 3. Verificar certificado SSL
curl -I https://admin.heartguard.live
```

### Login no funciona
```bash
# 1. Verificar backend
docker compose logs backend | tail -20

# 2. Verificar PostgreSQL
docker exec heartguard-postgres psql -U postgres heartguard -c "SELECT email FROM users WHERE email='admin@heartguard.com';"

# 3. Verificar Redis
docker exec heartguard-redis redis-cli --tls --cert /usr/local/etc/redis/certs/redis.crt --key /usr/local/etc/redis/certs/redis.key --cacert /usr/local/etc/redis/certs/ca.crt -a $(grep REDIS_PASSWORD .env.production | cut -d= -f2) PING
```

### Certificado SSL expirado
```bash
# La renovación es automática, pero si falla:
docker run --rm \
  -v heartguard_certbot-etc:/etc/letsencrypt \
  -v heartguard_certbot-var:/var/lib/letsencrypt \
  -v heartguard_certbot-www:/var/www/certbot \
  certbot/certbot renew

# Reiniciar Nginx
docker compose restart nginx
```

---

## 📞 Contacto y Soporte

Ver `docs/security/CREDENTIALS.md` sección "📞 Contacto y Soporte"

---

## ⚡ Desarrollo Local

### Iniciar Desarrollo
```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Iniciar servicios
make dev-up

# 3. Inicializar base de datos
make db-reset

# 4. Iniciar backend
make dev
```

### Acceder en Desarrollo
- Panel admin: http://localhost:8080/login
- API: http://localhost:8080/api/

---

**Última actualización**: 2025-11-01  
**Versión**: 2.0.0  
**Estado**: ✅ Producción estable
