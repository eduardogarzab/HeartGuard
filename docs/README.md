# 📚 HeartGuard - Documentación Completa

## 📖 Índice General

### 🚀 Deployment y Producción
- **[PRODUCTION_STATUS.md](./deployment/PRODUCTION_STATUS.md)** - Estado actual del sistema en producción
- **[production_deployment.md](./deployment/production_deployment.md)** - Guía completa de deployment
- **[DEPLOYMENT.md](./deployment/DEPLOYMENT.md)** - Documentación de deployment anterior
- **[SETUP-COMPLETE.md](./deployment/SETUP-COMPLETE.md)** - Setup inicial completado

### 🔐 Seguridad y SSL/TLS
- **[CREDENTIALS.md](./security/CREDENTIALS.md)** - Todas las credenciales del sistema (NO en git)
- **[SECURITY_SSL_TLS.md](./security/SECURITY_SSL_TLS.md)** - Implementación de SSL/TLS
- **[ssl_tls_setup.md](./security/ssl_tls_setup.md)** - Guía de setup SSL/TLS

### 🛠️ Scripts y Utilidades
- **[generate_certs.sh](./scripts/generate_certs.sh)** - Generación de certificados SSL/TLS
- **[verify_production.sh](./scripts/verify_production.sh)** - Verificación del sistema
- **[reset_and_deploy_prod.sh](./scripts/reset_and_deploy_prod.sh)** - Reset y deploy completo
- **[redis-entrypoint.sh](./scripts/redis-entrypoint.sh)** - Entrypoint de Redis con TLS
- **[docker-ufw-fix.sh](./scripts/docker-ufw-fix.sh)** - Fix de UFW con Docker

---

## 🎯 Guías Rápidas

### Para Deployment
1. Revisa el [estado de producción](./deployment/PRODUCTION_STATUS.md)
2. Sigue la [guía de deployment](./deployment/production_deployment.md)
3. Verifica con el [script de verificación](./scripts/verify_production.sh)

### Para Seguridad
1. Consulta las [credenciales](./security/CREDENTIALS.md)
2. Revisa la [implementación SSL/TLS](./security/SECURITY_SSL_TLS.md)
3. Regenera certificados con [generate_certs.sh](./scripts/generate_certs.sh)

### Para Desarrollo
1. Revisa el README principal en la raíz
2. Consulta el Makefile para comandos disponibles
3. Revisa la configuración en backend/

---

## 📂 Estructura de la Documentación

```
docs/
├── README.md (este archivo)
├── deployment/
│   ├── PRODUCTION_STATUS.md      # Estado actual del sistema
│   ├── production_deployment.md  # Guía completa de deployment
│   ├── DEPLOYMENT.md             # Documentación de deployment
│   └── SETUP-COMPLETE.md         # Setup inicial
├── security/
│   ├── CREDENTIALS.md            # Credenciales (NO en git)
│   ├── SECURITY_SSL_TLS.md       # Implementación SSL/TLS
│   └── ssl_tls_setup.md          # Guía de setup SSL/TLS
├── scripts/
│   ├── generate_certs.sh         # Generación de certificados
│   ├── verify_production.sh      # Verificación del sistema
│   ├── reset_and_deploy_prod.sh  # Reset y deploy
│   ├── redis-entrypoint.sh       # Entrypoint Redis
│   └── docker-ufw-fix.sh         # Fix UFW
└── README.md                     # Este archivo
```

---

## 🔗 Enlaces Importantes

- [README Principal](../readme.md) - Documentación principal del proyecto
- [CHANGELOG](../CHANGELOG.md) - Historial de cambios
- [Makefile](../Makefile) - Comandos disponibles

---

## 📞 Soporte

Para información de contacto y soporte, consulta el archivo de credenciales:
```bash
cat docs/security/CREDENTIALS.md
```

---

**Última actualización**: 2025-11-01  
**Sistema**: Completamente operacional en producción con HTTPS
