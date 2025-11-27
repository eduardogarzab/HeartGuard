# HeartGuard Micro-Services

> **Docker Compose (recomendado):** `make bootstrap-envs && cd docker/microservices && docker compose up -d` levanta todos los servicios con las mismas imágenes utilizadas en las VMs. Los microservicios se conectan al stack de bases de datos expuesto por la VM del backend.

Gestión centralizada de microservicios HeartGuard (auth, admin, gateway, patient, user, media, realtime, AI, etc.).

## 🚀 Inicio Rápido

### Docker Compose (recomendado)

```bash
make bootstrap-envs                  # genera todos los .env necesarios
cd docker/microservices
docker compose up -d                 # levanta auth/admin/user/.../gateway
```

### Makefile legacy (hot reload local)

```bash
# Instalar todas las dependencias
make install

# Iniciar todos los servicios
make start

# Ver estado
make status

# Ver logs
make logs
```

## 📋 Servicios Disponibles

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **auth-service** | 5001 | Autenticación y autorización JWT |
| **admin-service** | 5002 | API de administración (organizaciones, pacientes, equipos) |
| **user-service** | 5003 | API de perfil y membresías del usuario autenticado |
| **patient-service** | 5004 | Portal de pacientes y datos asociados |
| **media-service** | 5005 | Gestión de fotos de perfil en DigitalOcean Spaces |
| **gateway** | 8080 | API Gateway que enruta a los servicios |

## 🎯 Comandos Principales

### Instalación

```bash
make install              # Instalar todas las dependencias
make install-auth         # Solo auth-service
make install-admin        # Solo admin-service
make install-gateway      # Solo gateway
```

### Iniciar Servicios

```bash
make start                # Iniciar todos los servicios
make start-auth           # Solo auth-service
make start-admin          # Solo admin-service
make start-gateway        # Solo gateway
```

Los servicios se inician en segundo plano y esperan a estar listos antes de continuar.

### Detener Servicios

```bash
make stop                 # Detener todos los servicios
make stop-auth            # Solo auth-service
make stop-admin           # Solo admin-service
make stop-gateway         # Solo gateway
```

### Reiniciar Servicios

```bash
make restart              # Reiniciar todos los servicios
make restart-auth         # Solo auth-service
make restart-admin        # Solo admin-service
make restart-gateway      # Solo gateway
```

### Monitoreo

```bash
# Ver estado de servicios (PID, puerto, estado)
make status

# Ver últimas líneas de logs
make logs                 # Todos los servicios
make logs-auth            # Solo auth-service
make logs-admin           # Solo admin-service
make logs-gateway         # Solo gateway

# Seguir logs en tiempo real
make tail                 # Todos los servicios
make tail-auth            # Solo auth-service
make tail-admin           # Solo admin-service
make tail-gateway         # Solo gateway
```

### Testing

```bash
make test                 # Ejecutar tests de todos los servicios
make test-auth            # Tests de auth-service
make test-admin           # Tests de admin-service
make test-gateway         # Tests de gateway
```

### Limpieza

```bash
make clean                # Limpiar caches y archivos temporales
make clean-venv           # Eliminar entornos virtuales
make clean-all            # Limpieza completa (stop + clean + clean-venv)
```

## 📁 Estructura de Archivos

```
micro-services/
├── Makefile              # Makefile maestro (gestión centralizada)
├── README.md             # Esta documentación
├── auth/
│   ├── Makefile          # Comandos específicos de auth
│   ├── test_auth_service.sh
│   └── src/auth/...
├── admin/
│   ├── Makefile          # Comandos específicos de admin
│   ├── test_admin_service.sh
│   └── src/admin/...
├── user/
│   ├── Makefile          # Comandos específicos de user
│   └── src/user/...
├── patient/
│   ├── Makefile          # Comandos específicos de patient
│   └── src/patient/...
├── media/
│   ├── Makefile          # Comandos específicos de media
│   └── src/media/...
├── influxdb-service/
│   └── src/generator/...
├── ai-prediction/
│   └── src/
├── ai-monitor/
│   └── src/
└── gateway/
  ├── Makefile          # Comandos específicos de gateway
  ├── test_gateway.sh
  └── src/gateway/...
```

## 🔍 Logs y PIDs

- **Logs**: `/tmp/heartguard-logs/`
  - `auth.log`
  - `admin.log`
  - `gateway.log`

- **PIDs**: `/tmp/heartguard-pids/`
  - `auth.pid`
  - `admin.pid`
  - `gateway.pid`

## 💡 Ejemplos de Uso

### Iniciar todo el sistema

```bash
cd micro-services
make install    # Primera vez
make start      # Iniciar servicios
make status     # Verificar estado
```

### Desarrollo individual

```bash
# Trabajar solo con auth-service
cd micro-services/auth
make dev        # Modo desarrollo con hot-reload
```

### Reiniciar un servicio específico

```bash
# Hiciste cambios en admin-service
make restart-admin

# Ver logs para verificar
make logs-admin
```

### Debugging

```bash
# Ver logs en tiempo real mientras pruebas
make tail-gateway

# En otra terminal
curl http://localhost:8080/health
```

### Testing completo

```bash
# Asegurarse de que servicios estén corriendo
make start

# Ejecutar todos los tests
make test

# Ver resultados en logs
make logs
```

## 🛠️ Desarrollo

### Modo Desarrollo con Hot-Reload

Para trabajar en un servicio individual con recarga automática:

```bash
cd micro-services/auth    # o admin, o gateway
make dev
```

Esto inicia el servicio en modo desarrollo con Flask Debug y hot-reload activado.

### Comandos por Servicio

Cada servicio tiene su propio `Makefile` con comandos consistentes:

```bash
cd micro-services/auth    # o admin, o gateway
make help           # Ver comandos disponibles
make install        # Instalar dependencias
make dev            # Modo desarrollo
make test           # Ejecutar tests
make clean          # Limpiar
```

## 🔐 Autenticación y Testing

Los scripts de prueba (`test_*.sh`) están ubicados en cada servicio:

- `micro-services/auth/test_auth_service.sh` - Pruebas de autenticación
- `micro-services/admin/test_admin_service.sh` - Pruebas de admin API
- `micro-services/gateway/test_gateway.sh` - Pruebas de gateway

Ejecutar con: `make test` o `make test-[servicio]`

## 📊 Flujo de Trabajo Típico

```bash
# 1. Instalación inicial
make install

# 2. Iniciar servicios
make start

# 3. Ver que todo esté corriendo
make status

# 4. Ejecutar tests
make test

# 5. Durante desarrollo - ver logs
make tail-admin

# 6. Reiniciar después de cambios
make restart-admin

# 7. Al terminar
make stop
```

## 🆘 Troubleshooting

### Servicio no inicia

```bash
# Ver logs
make logs-[servicio]

# Revisar que el puerto no esté ocupado
lsof -i :5001    # auth
lsof -i :5002    # admin
lsof -i :8080    # gateway
```

### Limpiar todo y empezar de nuevo

```bash
make clean-all
make install
make start
```

### Ver procesos activos

```bash
make status

# O manualmente
ps aux | grep flask
```

## 📝 Notas

- Los servicios se inician en el orden correcto: auth → admin → gateway
- Cada servicio espera a estar listo antes de iniciar el siguiente
- Los logs se guardan automáticamente en `/tmp/heartguard-logs/`
- Los PIDs se gestionan automáticamente en `/tmp/heartguard-pids/`
- Use `make help` en cualquier momento para ver comandos disponibles
