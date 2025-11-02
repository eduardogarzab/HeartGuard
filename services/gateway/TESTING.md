# Guía de Prueba - Gateway HeartGuard

## ✅ Revisión de la Implementación

La implementación del gateway sigue **buenas prácticas** de Flask:

### Arquitectura
- ✅ **Application Factory Pattern**: `create_app()` permite múltiples instancias y facilita testing
- ✅ **Blueprints modulares**: Rutas organizadas por dominio (health, futuro: patients, organizations)
- ✅ **Separación de configuración**: Variables de entorno con valores por defecto seguros
- ✅ **Type hints**: Código tipado para mejor mantenibilidad
- ✅ **Estructura escalable**: Preparado para agregar middleware, extensiones y nuevos servicios

### Estructura de Carpetas
```
services/gateway/
├── src/gateway/          # Código fuente principal
│   ├── app.py           # Factory de aplicación
│   ├── config.py        # Configuración centralizada
│   ├── extensions.py    # Placeholder para extensiones
│   ├── routes/          # Blueprints por dominio
│   └── services/        # Clientes de microservicios
└── tests/               # Tests con pytest
```

---

## 🧪 Cómo Probar el Gateway

### Opción 1: Pruebas Automatizadas (Recomendado primero)

```bash
cd /home/azureuser/HeartGuard/services/gateway

# Instalar dependencias y ejecutar tests
make test
```

**Resultado esperado:**
```
✓ test_health_endpoint_returns_ok PASSED
1 passed in 0.XX s
```

---

### Opción 2: Servidor de Desarrollo

```bash
cd /home/azureuser/HeartGuard/services/gateway

# Levantar servidor en modo desarrollo
make dev
```

**Resultado esperado:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

#### Probar endpoints con curl:

**1. Health Check:**
```bash
curl http://localhost:5000/health/
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "service": "heartguard-gateway",
  "timestamp": "2025-11-02T...",
  "debug": true
}
```

**2. Verificar con navegador:**
Abrir en tu navegador: http://localhost:5000/health/

---

### Opción 3: Prueba Manual con Python

```bash
cd /home/azureuser/HeartGuard/services/gateway

# Activar entorno virtual
source .venv/bin/activate

# Ejecutar Flask manualmente
export FLASK_APP=gateway.app:create_app
export FLASK_DEBUG=1
flask run
```

---

## 🔧 Comandos Útiles del Makefile

| Comando | Descripción |
|---------|-------------|
| `make install` | Crea virtualenv e instala dependencias |
| `make dev` | Levanta servidor con hot-reload |
| `make test` | Ejecuta suite de tests con pytest |
| `make lint` | Verifica sintaxis Python |
| `make clean` | Elimina virtualenv y cache |

---

## 🐛 Solución de Problemas

### Error: "No module named 'gateway'"
**Solución:** El Makefile ya configura `PYTHONPATH=src`, pero si ejecutas Flask manualmente:
```bash
export PYTHONPATH=src
flask run
```

### Puerto 5000 ocupado
**Solución:** Cambia el puerto en `.flaskenv`:
```
FLASK_RUN_PORT=8080
```

### Dependencias faltantes
**Solución:**
```bash
make clean
make install
```

---

## 📝 Próximos Pasos Sugeridos

1. **Agregar autenticación JWT**:
   - Crear middleware en `src/gateway/middleware/auth.py`
   - Integrar con el sistema de auth existente en `backend/internal/auth/`

2. **Blueprints para dominios**:
   - `routes/organizations.py` → Panel de administración de organizaciones
   - `routes/patients.py` → API para pacientes
   - `routes/users.py` → Gestión de usuarios finales

3. **Clientes de microservicios**:
   - `services/organization_client.py`
   - `services/patient_client.py`
   - Usar `requests` con timeouts configurables

4. **Middleware común**:
   - Rate limiting
   - CORS
   - Request logging
   - Error handling centralizado

5. **Integración Docker**:
   - Crear `Dockerfile` para el gateway
   - Agregar servicio al `docker-compose.yml` raíz
