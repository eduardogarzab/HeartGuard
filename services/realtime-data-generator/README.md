# HeartGuard Real-time Data Generator Service

Microservicio Flask que genera datos sintéticos de signos vitales en tiempo real para el sistema HeartGuard.

## Descripción

Este servicio genera datos sintéticos realistas de signos vitales para pacientes registrados en el sistema HeartGuard. Los datos se almacenan en InfluxDB y están vinculados con los pacientes en PostgreSQL.

## Características

- **Microservicio Flask** con endpoints REST
- **Worker en background** que genera datos continuamente
- **Conexión con PostgreSQL**: Lee pacientes activos de la base de datos
- **Generación de datos sintéticos realistas**: Basado en rangos del dataset proporcionado
- **Almacenamiento en InfluxDB**: Datos de series temporales para cada paciente
- **Health checks**: Endpoints `/health` y `/status` para monitoreo
- **Parámetros generados**:
  - GPS (Longitud/Latitud) - Área de Monterrey
  - Frecuencia cardíaca (45-92 bpm)
  - Nivel de SpO2 (91-100%)
  - Presión arterial sistólica (102-154 mmHg)
  - Presión arterial diastólica (59-94 mmHg)
  - Temperatura corporal (36.14-37.02°C)

## Instalación

```bash
# Desde el directorio del servicio
make install

# O desde el directorio services/
cd /root/HeartGuard/services
make install-realtime
```

## Configuración

Variables de entorno en `.env`:

```bash
DATABASE_URL=postgres://heartguard_app:dev_change_me@134.199.204.58:5432/heartguard?sslmode=disable
INFLUXDB_URL=http://134.199.204.58:8086
INFLUXDB_TOKEN=heartguard-dev-token-change-me
INFLUXDB_ORG=heartguard
INFLUXDB_BUCKET=timeseries
GENERATION_INTERVAL=5  # Segundos entre generaciones
FLASK_DEBUG=0
```

## Uso

### Desarrollo (modo interactivo):
```bash
make dev
```

### Producción (background):
```bash
cd /root/HeartGuard/services
make start-realtime
```

### Verificar estado:
```bash
# Directo
curl http://localhost:5006/health
curl http://localhost:5006/status

# A través del gateway (recomendado)
curl http://localhost:8080/realtime/health
curl http://localhost:8080/realtime/status
```

## Endpoints

Todos los endpoints son accesibles tanto directamente como a través del gateway:

- **Directo**: `http://localhost:5006`
- **Gateway**: `http://localhost:8080/realtime`

### `GET /health` o `GET /realtime/health`
Health check básico.

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "realtime-data-generator",
  "worker_running": true,
  "iteration": 42
}
```

### `GET /status` o `GET /realtime/status`
Estado detallado del servicio.

**Respuesta:**
```json
{
  "status": "running",
  "service": "realtime-data-generator",
  "worker": {
    "running": true,
    "iteration": 42,
    "interval_seconds": 5
  },
  "database": {
    "connected": true,
    "active_patients": 3
  },
  "influxdb": {
    "connected": true,
    "url": "http://134.199.204.58:8086",
    "bucket": "timeseries"
  }
}
```

### `GET /patients` o `GET /realtime/patients`
Lista de pacientes siendo monitoreados.

**Respuesta:**
```json
{
  "count": 3,
  "patients": [
    {
      "id": "uuid-here",
      "name": "José Hernández",
      "email": "jose@example.com",
      "risk_level": "medium"
    }
  ]
}
```

## Estructura del Proyecto

```
realtime-data-generator/
├── src/
│   └── generator/
│       ├── __init__.py
│       ├── app.py              # Aplicación Flask principal
│       ├── config.py           # Configuración
│       ├── data_generator.py  # Lógica de generación de datos
│       ├── db.py              # Operaciones PostgreSQL
│       ├── influx.py          # Operaciones InfluxDB
│       └── worker.py          # Worker en background
├── Makefile
├── requirements.txt
├── .env
├── .env.example
└── README.md
```

## Integración con el Sistema

El servicio se ejecuta como parte del stack de microservicios:

```bash
# Iniciar todos los servicios (incluido realtime-data-generator)
cd /root/HeartGuard/services
make start

# Ver logs
make logs-realtime
make tail-realtime

# Reiniciar solo este servicio
make restart-realtime

# Detener
make stop-realtime
```

## Estructura de datos en InfluxDB

**Measurement**: `vital_signs`

**Tags**:
- `patient_id`: ID del paciente (UUID)
- `patient_name`: Nombre del paciente
- `org_id`: ID de la organización
- `risk_level`: Nivel de riesgo del paciente

**Fields**:
- `gps_longitude`: Longitud GPS (float)
- `gps_latitude`: Latitud GPS (float)
- `heart_rate`: Frecuencia cardíaca en bpm (int)
- `spo2`: Nivel de oxígeno en sangre en % (int)
- `systolic_bp`: Presión arterial sistólica en mmHg (int)
- `diastolic_bp`: Presión arterial diastólica en mmHg (int)
- `temperature`: Temperatura corporal en °C (float)

## Logs

Los logs se guardan en:
- `generator.log` (archivo)
- Salida estándar (consola)

## Notas importantes

- Los datos generados NO incluyen alertas (Alert columns), ya que estas se generarán mediante modelos de IA
- Cada paciente tiene valores base ligeramente diferentes para simular variabilidad individual
- Los valores generados respetan los rangos del dataset proporcionado
- Las coordenadas GPS simulan movimientos pequeños del paciente en el área de Monterrey

## Troubleshooting

**Error de conexión a PostgreSQL**:
- Verificar que el servidor de base de datos esté accesible
- Verificar credenciales en `.env`

**Error de conexión a InfluxDB**:
- Verificar que InfluxDB esté corriendo
- Verificar el token de autenticación
- Verificar que el bucket exista

**No se encuentran pacientes**:
- Verificar que existan pacientes en la tabla `heartguard.patients`
- Ejecutar el script de seed de la base de datos si es necesario
