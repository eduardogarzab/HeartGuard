# HeartGuard - Suite de Pruebas de Carga con Locust

Suite completa de pruebas de rendimiento para los microservicios de HeartGuard usando Locust.

## 📋 Índice

- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Tipos de Pruebas](#tipos-de-pruebas)
- [Ejecución de Pruebas](#ejecución-de-pruebas)
- [Interpretación de Resultados](#interpretación-de-resultados)
- [Troubleshooting](#troubleshooting)

## 🔧 Requisitos

- Python 3.8 o superior
- Pip (gestor de paquetes de Python)
- Acceso a la red del gateway: `http://129.212.181.53:8080`

## 📦 Instalación

### 1. Instalar Locust

```powershell
pip install locust
```

### 2. Instalar dependencias adicionales

```powershell
pip install requests
```

### 3. Verificar instalación

```powershell
locust --version
```

Deberías ver algo como: `locust 2.x.x`

## ⚙️ Configuración

### Configurar Credenciales

Edita el archivo `config.py` y actualiza las credenciales de prueba:

```python
# Credenciales de usuario staff
STAFF_EMAIL = "tu_usuario_staff@ejemplo.com"
STAFF_PASSWORD = "tu_password"

# Credenciales de paciente
PATIENT_EMAIL = "tu_paciente@ejemplo.com"
PATIENT_PASSWORD = "tu_password"

# IDs de prueba (ajustar según datos disponibles)
TEST_ORG_ID = "tu-org-id"
TEST_PATIENT_ID = "tu-patient-id"
TEST_USER_ID = "tu-user-id"
TEST_DEVICE_ID = "tu-device-id"
TEST_CARE_TEAM_ID = "tu-team-id"
TEST_ALERT_ID = "tu-alert-id"
```

### Estructura de Archivos

```
load-tests/locust/
├── config.py              # Configuración centralizada
├── auth_helper.py         # Helper de autenticación
├── baseline_test.py       # Prueba baseline
├── smoke_test.py          # Prueba smoke
├── read_heavy_test.py     # Prueba read-heavy
├── write_heavy_test.py    # Prueba write-heavy
├── ramp_test.py           # Prueba ramp
├── spike_test.py          # Prueba spike
├── soak_test.py           # Prueba soak
├── breakpoint_test.py     # Prueba breakpoint
└── README.md              # Esta documentación
```

## 🧪 Tipos de Pruebas

### 1. **Baseline Test** 🎯
**Objetivo**: Confirmar latencias estables bajo carga ligera

- **Usuarios**: 10
- **Duración**: 5 minutos
- **Uso**: Establecer métricas de referencia

```powershell
locust -f baseline_test.py --host=http://129.212.181.53:8080 --users=10 --spawn-rate=2 --run-time=5m
```

**Cuándo usar**: Al inicio de cada ciclo de testing para establecer baseline.

---

### 2. **Smoke Test** 💨
**Objetivo**: Verificación rápida de disponibilidad extremo a extremo

- **Usuarios**: 5
- **Duración**: 1 minuto
- **Uso**: Validar que todos los servicios están activos

```powershell
locust -f smoke_test.py --host=http://129.212.181.53:8080 --users=5 --spawn-rate=5 --run-time=1m --headless
```

**Cuándo usar**: Después de cada despliegue o cambio de configuración.

---

### 3. **Read-Heavy Test** 📖
**Objetivo**: Validar comportamiento con predominancia de operaciones de lectura

- **Usuarios**: 50
- **Duración**: 10 minutos
- **Ratio**: 95% lecturas, 5% verificaciones

```powershell
locust -f read_heavy_test.py --host=http://129.212.181.53:8080 --users=50 --spawn-rate=5 --run-time=10m
```

**Cuándo usar**: Para validar cache, dashboards y consultas frecuentes.

---

### 4. **Write-Heavy Test** ✍️
**Objetivo**: Validar operaciones POST idempotentes bajo concurrencia

- **Usuarios**: 30
- **Duración**: 8 minutos
- **Ratio**: 70% escrituras, 30% lecturas de verificación

```powershell
locust -f write_heavy_test.py --host=http://129.212.181.53:8080 --users=30 --spawn-rate=3 --run-time=8m
```

**Cuándo usar**: Para validar actualizaciones, alertas y operaciones de escritura.

---

### 5. **Ramp Test** 📈
**Objetivo**: Observar degradación gradual cuando la carga crece y decrece

- **Usuarios**: 0 → 100 → 0
- **Duración**: 15 minutos
- **Fases**: Ramp up → Plateau → Ramp down

```powershell
locust -f ramp_test.py --host=http://129.212.181.53:8080 --users=100 --spawn-rate=5 --run-time=15m
```

**Cuándo usar**: Para identificar puntos de degradación y observar recuperación.

---

### 6. **Spike Test** ⚡
**Objetivo**: Validar elasticidad ante picos súbitos de tráfico

- **Usuarios**: 20 → 200 → 20
- **Duración**: 8 minutos
- **Fases**: Baseline → Spike → Recovery

```powershell
locust -f spike_test.py --host=http://129.212.181.53:8080
```

**Cuándo usar**: Para validar rate limiting y recuperación ante picos.

---

### 7. **Soak Test** ⏱️
**Objetivo**: Evaluar estabilidad sostenida y detectar fugas de recursos

- **Usuarios**: 20
- **Duración**: 1-4 horas
- **Monitorear**: Memory leaks, degradación acumulativa

```powershell
# 1 hora (recomendado)
locust -f soak_test.py --host=http://129.212.181.53:8080 --users=20 --spawn-rate=2 --run-time=1h

# 2 horas (más exhaustivo)
locust -f soak_test.py --host=http://129.212.181.53:8080 --users=20 --spawn-rate=2 --run-time=2h
```

**Cuándo usar**: Antes de releases importantes para detectar memory leaks.

---

### 8. **Breakpoint Test** 💥
**Objetivo**: Determinar umbral máximo antes de rechazo de solicitudes

- **Usuarios**: 50 → 500 (incremental)
- **Duración**: Variable
- **Objetivo**: Encontrar el punto de quiebre

```powershell
locust -f breakpoint_test.py --host=http://129.212.181.53:8080
```

**Cuándo usar**: Para planificación de capacidad y escalabilidad.

**Detener cuando**:
- Tasa de errores > 50%
- Latencias > 10 segundos
- Timeouts masivos

---

## 🚀 Ejecución de Pruebas

### Modo Headless (Sin UI)

Ideal para CI/CD y ejecuciones automatizadas:

```powershell
locust -f <archivo_test>.py --host=http://129.212.181.53:8080 --users=<num> --spawn-rate=<rate> --run-time=<tiempo> --headless
```

### Modo Web UI (Interactivo)

Ideal para desarrollo y análisis en tiempo real:

```powershell
locust -f <archivo_test>.py --host=http://129.212.181.53:8080
```

Luego abre tu navegador en: `http://localhost:8089`

### Exportar Resultados

```powershell
# Exportar a CSV
locust -f baseline_test.py --host=http://129.212.181.53:8080 --users=10 --spawn-rate=2 --run-time=5m --headless --csv=resultados/baseline

# Exportar a HTML
locust -f baseline_test.py --host=http://129.212.181.53:8080 --users=10 --spawn-rate=2 --run-time=5m --headless --html=resultados/baseline.html
```

## 📊 Interpretación de Resultados

### Métricas Clave

| Métrica | Descripción | Valor Óptimo |
|---------|-------------|--------------|
| **RPS** | Requests por segundo | > 100 |
| **Avg Response Time** | Latencia promedio | < 200ms |
| **95th Percentile** | 95% de requests bajo este tiempo | < 500ms |
| **Failure Rate** | % de requests fallidos | < 1% |
| **Concurrent Users** | Usuarios simultáneos soportados | Depende de capacidad |

### Criterios de Aceptación

#### ✅ Prueba Exitosa
- Failure rate < 1%
- Avg response time < 500ms
- 95th percentile < 1000ms
- Sin errores de servidor (5xx)

#### ⚠️ Advertencia
- Failure rate 1-5%
- Avg response time 500-1000ms
- Algunos errores 429 (rate limiting)

#### ❌ Prueba Fallida
- Failure rate > 5%
- Avg response time > 1000ms
- Múltiples errores 5xx
- Timeouts frecuentes

### Análisis por Tipo de Prueba

#### Baseline
- **Buscar**: Latencias estables y consistentes
- **Umbral**: < 200ms promedio
- **Alertas**: Cualquier error es preocupante

#### Smoke
- **Buscar**: Todos los servicios responden OK
- **Umbral**: 100% de éxito en health checks
- **Alertas**: Cualquier servicio caído

#### Read-Heavy
- **Buscar**: Buen rendimiento de cache
- **Umbral**: < 300ms promedio con 50 usuarios
- **Alertas**: Degradación en dashboards

#### Write-Heavy
- **Buscar**: Consistencia en escrituras concurrentes
- **Umbral**: < 500ms promedio
- **Alertas**: Errores de concurrencia (409, 423)

#### Ramp
- **Buscar**: Punto donde empiezan degradaciones
- **Umbral**: Identificar el "knee point"
- **Alertas**: Degradación abrupta vs gradual

#### Spike
- **Buscar**: Recuperación después del spike
- **Umbral**: Rate limiting efectivo (429)
- **Alertas**: Sistema no se recupera

#### Soak
- **Buscar**: Estabilidad en el tiempo
- **Umbral**: Latencias no deben incrementar > 20%
- **Alertas**: Memory leaks, degradación acumulativa

#### Breakpoint
- **Buscar**: Capacidad máxima del sistema
- **Umbral**: Punto donde errors > 50%
- **Alertas**: Fallo catastrófico vs degradación gradual

## 🔍 Troubleshooting

### Problema: Errores de Autenticación (401)

```
Solución:
1. Verificar credenciales en config.py
2. Crear usuarios de prueba en el sistema
3. Verificar que el servicio de auth esté activo
```

### Problema: Timeouts Frecuentes

```
Solución:
1. Aumentar timeout en config.py: REQUEST_TIMEOUT = 60
2. Reducir número de usuarios concurrentes
3. Verificar conectividad de red al gateway
```

### Problema: Rate Limiting (429)

```
Solución:
1. Es comportamiento esperado en spike/breakpoint tests
2. Reducir spawn rate
3. Incrementar wait_time en los usuarios
```

### Problema: Token Expirado Durante Soak Test

```
Solución:
Ya implementado en soak_test.py:
- Renovación automática de tokens
- Manejo de errores 401
- Re-login automático
```

### Problema: No se puede conectar al gateway

```
Solución:
1. Verificar que el gateway esté corriendo:
   curl http://129.212.181.53:8080/health/

2. Verificar firewall y acceso de red

3. Probar con otro endpoint público
```

## 📈 Mejores Prácticas

### Antes de Ejecutar

1. ✅ Verificar que todos los servicios están activos (smoke test)
2. ✅ Configurar credenciales válidas
3. ✅ Establecer baseline primero
4. ✅ Coordinar con el equipo (evitar pruebas en producción)

### Durante la Ejecución

1. 📊 Monitorear métricas del sistema (CPU, memoria, red)
2. 📝 Documentar anomalías observadas
3. 🔍 Usar Web UI para análisis en tiempo real
4. ⏸️ Detener si hay errores masivos inesperados

### Después de Ejecutar

1. 💾 Exportar y guardar resultados
2. 📊 Comparar con baseline
3. 📝 Documentar hallazgos
4. 🔄 Iterar y mejorar

## 🎯 Plan de Pruebas Recomendado

### Daily (Diario)
```powershell
locust -f smoke_test.py --host=http://129.212.181.53:8080 --users=5 --spawn-rate=5 --run-time=1m --headless
```

### Weekly (Semanal)
```powershell
locust -f baseline_test.py --host=http://129.212.181.53:8080 --users=10 --spawn-rate=2 --run-time=5m --headless
locust -f read_heavy_test.py --host=http://129.212.181.53:8080 --users=50 --spawn-rate=5 --run-time=10m --headless
```

### Pre-Release
```powershell
# Suite completa
locust -f smoke_test.py --host=http://129.212.181.53:8080 --users=5 --spawn-rate=5 --run-time=1m --headless
locust -f baseline_test.py --host=http://129.212.181.53:8080 --users=10 --spawn-rate=2 --run-time=5m --headless
locust -f read_heavy_test.py --host=http://129.212.181.53:8080 --users=50 --spawn-rate=5 --run-time=10m --headless
locust -f write_heavy_test.py --host=http://129.212.181.53:8080 --users=30 --spawn-rate=3 --run-time=8m --headless
locust -f ramp_test.py --host=http://129.212.181.53:8080 --users=100 --spawn-rate=5 --run-time=15m --headless
locust -f spike_test.py --host=http://129.212.181.53:8080 --headless
locust -f soak_test.py --host=http://129.212.181.53:8080 --users=20 --spawn-rate=2 --run-time=1h --headless
```

### Capacity Planning
```powershell
locust -f breakpoint_test.py --host=http://129.212.181.53:8080
```

## 📞 Soporte

Para problemas o preguntas:
1. Revisar logs de Locust
2. Verificar logs del gateway y microservicios
3. Consultar documentación de Locust: https://docs.locust.io/

## 📄 Licencia

Este proyecto es parte de HeartGuard.

---

**Última actualización**: Noviembre 2025
