# AI Monitor Service

Servicio worker que monitorea automáticamente los signos vitales de pacientes almacenados en InfluxDB, utiliza el modelo de IA para detectar problemas de salud, crea alertas en PostgreSQL y notifica a los cuidadores.

## 🎯 Funcionalidad

El servicio ejecuta un ciclo continuo que:

1. **Lee datos de InfluxDB**: Obtiene los signos vitales más recientes de pacientes activos
2. **Predice con IA**: Envía los datos al servicio de predicción de IA
3. **Crea alertas**: Si se detectan problemas, crea alertas en PostgreSQL
4. **Notifica**: Envía notificaciones a los cuidadores del paciente (email, SMS, push)

## 📊 Flujo de Trabajo

```
┌─────────────────┐
│   InfluxDB      │ ← Signos vitales en tiempo real
│  (Time Series)  │
└────────┬────────┘
         │
         ↓ Read
┌─────────────────┐
│  AI Monitor     │
│    Worker       │
└────────┬────────┘
         │
         ↓ Predict
┌─────────────────┐
│  AI Service     │ ← Modelo RandomForest
│   (Port 5008)   │
└────────┬────────┘
         │
         ↓ Alerts detected
┌─────────────────┐
│   PostgreSQL    │ ← Alertas persistidas
│   (alerts)      │
└────────┬────────┘
         │
         ↓ Notify
┌─────────────────┐
│   Caregivers    │ ← Email, SMS, Push
│   Team          │
└─────────────────┘
```

## 🚀 Instalación

### Requisitos

- Python 3.10+
- InfluxDB 2.x
- PostgreSQL 13+
- Servicio de IA corriendo

### Configuración

1. Copiar archivo de configuración:
```bash
cp .env.example .env
```

2. Editar `.env` con tus credenciales:
```bash
# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=tu_token_aqui
INFLUXDB_ORG=heartguard
INFLUXDB_BUCKET=heartguard

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=heartguard
POSTGRES_USER=heartguard_app
POSTGRES_PASSWORD=tu_password

# AI Service
AI_SERVICE_URL=http://134.199.204.58:5008

# Configuración de monitoreo
MONITOR_INTERVAL=60     # Cada 60 segundos
LOOKBACK_WINDOW=300     # Buscar datos de últimos 5 minutos
```

3. Instalar dependencias:
```bash
make install
```

## 🏃 Ejecución

### Desarrollo

```bash
make dev
```

### Producción con Docker

```bash
# Build
make docker-build

# Run
docker run -d \
  --name ai-monitor \
  --env-file .env \
  --restart unless-stopped \
  heartguard-ai-monitor:latest
```

### Docker Compose

Agregar al `docker-compose.yml` principal:

```yaml
ai-monitor:
  build:
    context: ./micro-services/ai-monitor
    dockerfile: Dockerfile
  container_name: ai-monitor
  env_file:
    - ./micro-services/ai-monitor/.env
  depends_on:
    - influxdb
    - postgres
    - ai-prediction-service
  restart: unless-stopped
  networks:
    - heartguard-network
```

## 📝 Configuración Detallada

### Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `MONITOR_INTERVAL` | Segundos entre ciclos de monitoreo | 60 |
| `LOOKBACK_WINDOW` | Ventana de búsqueda en InfluxDB (segundos) | 300 |
| `BATCH_SIZE` | Pacientes a procesar en paralelo | 10 |
| `AI_PREDICTION_THRESHOLD` | Umbral de probabilidad para alertas | 0.6 |
| `ENABLE_NOTIFICATIONS` | Habilitar notificaciones | true |
| `LOG_LEVEL` | Nivel de logging (DEBUG, INFO, WARNING, ERROR) | INFO |

### Tipos de Alertas Detectadas

El servicio puede generar los siguientes tipos de alertas basado en el modelo de IA:

- **GENERAL_RISK**: Riesgo general de salud detectado
- **ARRHYTHMIA**: Frecuencia cardíaca anormal (< 60 o > 100 bpm)
- **DESAT**: Desaturación de oxígeno (SpO2 < 95%)
- **HYPERTENSION**: Presión arterial elevada (≥ 140/90 mmHg)
- **HYPOTENSION**: Presión arterial baja (< 90/60 mmHg)
- **FEVER**: Fiebre (≥ 38°C)
- **HYPOTHERMIA**: Hipotermia (< 36°C)

## 🔍 Monitoreo y Logs

### Ver logs en tiempo real

```bash
# Docker
docker logs -f ai-monitor

# Local
tail -f ai-monitor.log
```

### Ejemplo de salida

```
2025-11-24 10:30:00 - INFO - === Monitoring Cycle #1 ===
2025-11-24 10:30:00 - INFO - Found 5 active patients
2025-11-24 10:30:01 - INFO - Health problem detected for patient abc123 (probability: 95.00%)
2025-11-24 10:30:01 - INFO - Alert created: def456 - ARRHYTHMIA for patient abc123
2025-11-24 10:30:01 - INFO - Notifying 3 caregivers for patient abc123
2025-11-24 10:30:02 - INFO - Sent 6 notifications for alert def456
2025-11-24 10:30:05 - INFO - Cycle #1 completed in 5.23s - Patients: 5, Predictions: 5, Alerts: 2, Notifications: 6
```

## 🧪 Testing

### Test manual del flujo completo

```bash
# 1. Verificar que InfluxDB tiene datos
curl -X POST http://localhost:8086/api/v2/query \
  -H "Authorization: Token $INFLUXDB_TOKEN" \
  -H "Content-Type: application/vnd.flux" \
  --data 'from(bucket:"heartguard") |> range(start: -5m) |> limit(n:10)'

# 2. Verificar que AI Service está activo
curl http://134.199.204.58:5008/health

# 3. Ejecutar un ciclo de monitoreo
python src/monitor.py
```

## 📊 Métricas

El worker reporta las siguientes métricas en cada ciclo:

- **Patients Checked**: Número de pacientes procesados
- **Predictions Made**: Número de predicciones realizadas
- **Alerts Created**: Número de alertas generadas
- **Notifications Sent**: Número de notificaciones enviadas

## 🛠️ Troubleshooting

### El worker no encuentra pacientes activos

**Problema**: `Found 0 active patients`

**Solución**:
- Verificar que InfluxDB tiene datos recientes
- Ajustar `LOOKBACK_WINDOW` a un valor mayor
- Verificar credenciales de InfluxDB

### No se pueden crear alertas

**Problema**: `Error creating alert: ...`

**Solución**:
- Verificar conexión a PostgreSQL
- Verificar que existen los tipos de alerta en `alert_types`
- Ejecutar: `psql -d heartguard -f db/seed.sql`

### AI Service no responde

**Problema**: `Cannot connect to AI Service`

**Solución**:
- Verificar que el servicio de IA está corriendo
- Verificar URL: `curl http://134.199.204.58:5008/health`
- Verificar token de autenticación

### Notificaciones no se envían

**Problema**: `Sent 0 notifications`

**Solución**:
- Verificar `ENABLE_NOTIFICATIONS=true`
- Verificar que el servicio de notificaciones está corriendo
- Verificar que el paciente tiene caregivers asignados

## 🔐 Seguridad

- Usa JWT tokens para autenticación con servicios internos
- Almacena credenciales en variables de entorno
- Nunca commitees el archivo `.env`
- Usa conexiones seguras (HTTPS) en producción

## 📚 Documentación Relacionada

- [Flujo IA → Alertas → Ground Truth](../../FLUJO_IA_ALERTAS_GROUND_TRUTH.md)
- [Servicio de IA](../ai-prediction/README.md)
- [Base de datos](../../db/README.md)

## 🤝 Contribuir

Para modificar el comportamiento del worker:

1. Editar `src/monitor.py` para cambiar la lógica de monitoreo
2. Editar `src/ai_client.py` para cambiar la comunicación con IA
3. Editar `src/postgres_client.py` para cambiar la persistencia
4. Editar `src/notification_service.py` para cambiar las notificaciones

## 📄 Licencia

Parte del proyecto HeartGuard - Sistema de Monitoreo Cardiaco

---

**Autor**: AI Assistant  
**Fecha**: 2025-11-24  
**Versión**: 1.0
