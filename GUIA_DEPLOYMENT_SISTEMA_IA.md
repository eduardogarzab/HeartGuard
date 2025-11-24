# 🚀 Guía de Deployment: Sistema Completo con IA

Esta guía cubre el deployment completo del sistema HeartGuard con integración de IA, incluyendo el nuevo servicio de monitoreo automático.

## 📋 Componentes del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    HEARTGUARD SYSTEM                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   InfluxDB   │  │  PostgreSQL  │  │    Redis     │      │
│  │ (Time Series)│  │  (Relational)│  │   (Cache)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                          │                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MICROSERVICES LAYER                      │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                       │  │
│  │  • Auth Service       (Port 8081)                    │  │
│  │  • User Service       (Port 8082)                    │  │
│  │  • Patient Service    (Port 8083)                    │  │
│  │  • Admin Service      (Port 8084)                    │  │
│  │  • Media Service      (Port 8085)                    │  │
│  │  • Gateway            (Port 8080)                    │  │
│  │  • AI Prediction      (Port 5008) ← NUEVO           │  │
│  │  • AI Monitor Worker           ← NUEVO              │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                CLIENT APPLICATIONS                    │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                       │  │
│  │  • Org Admin (Web)                                   │  │
│  │  • Desktop App (Java)                                │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Pre-requisitos

### Servidor Backend (134.199.204.58)

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Mínimo 4GB RAM
- Puerto 5008 abierto (AI Service)

### Servidor Gateway (129.212.181.53)

- Gateway proxy configurado
- Ruta `/ai/*` apuntando a `http://134.199.204.58:5008`

## 📦 Paso 1: Preparar Base de Datos

### 1.1 Actualizar Schema con Tipos de Eventos

```bash
cd /path/to/HeartGuard

# Conectar a PostgreSQL
psql -U heartguard_app -d heartguard

# O si usas Docker:
docker exec -it heartguard-postgres psql -U postgres -d heartguard
```

Ejecutar el seed actualizado:

```bash
\i db/seed.sql
```

Verificar que los tipos de eventos están creados:

```sql
SELECT code, description, 
       (SELECT code FROM alert_levels WHERE id = severity_default_id) as severity
FROM event_types;
```

Deberías ver:

```
      code      |              description               | severity
----------------+----------------------------------------+----------
 GENERAL_RISK   | Riesgo general de salud detectado...  | medium
 ARRHYTHMIA     | Arritmia - Frecuencia cardiaca...     | high
 DESAT          | Desaturación de oxígeno                | high
 HYPERTENSION   | Hipertensión arterial                  | medium
 HYPOTENSION    | Hipotensión arterial                   | high
 FEVER          | Fiebre - Temperatura elevada           | medium
 HYPOTHERMIA    | Hipotermia - Temperatura baja          | high
```

## 📦 Paso 2: Deployment del Servicio de IA

### 2.1 Verificar Modelo

```bash
# En servidor backend
cd /path/to/HeartGuard/services/ai-prediction

# Verificar que el modelo existe
ls -lh models/modelo_salud_randomforest.pkl
```

### 2.2 Construir y Ejecutar

```bash
# Desde la raíz del proyecto
cd /path/to/HeartGuard

# Build y start con Docker Compose
docker-compose up -d ai-prediction-service

# Verificar logs
docker logs -f heartguard-ai-prediction

# Verificar health
curl http://localhost:5008/health
```

Respuesta esperada:

```json
{
  "status": "healthy",
  "model": {
    "loaded": true,
    "n_estimators": 300,
    "n_features": 7
  }
}
```

## 📦 Paso 3: Deployment del AI Monitor Worker

### 3.1 Configurar Variables de Entorno

```bash
cd services/ai-monitor

# Copiar template
cp .env.example .env

# Editar configuración
nano .env
```

Variables críticas:

```bash
# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=heartguard-dev-token-change-me
INFLUXDB_ORG=heartguard
INFLUXDB_BUCKET=timeseries

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=heartguard
POSTGRES_USER=heartguard_app
POSTGRES_PASSWORD=<tu_password>

# AI Service
AI_SERVICE_URL=http://ai-prediction-service:5008

# Monitoring
MONITOR_INTERVAL=60        # Cada 60 segundos
LOOKBACK_WINDOW=300        # Buscar datos de últimos 5 minutos
```

### 3.2 Construir y Ejecutar

```bash
# Desde la raíz del proyecto
docker-compose up -d ai-monitor

# Verificar logs
docker logs -f heartguard-ai-monitor
```

Deberías ver:

```
2025-11-24 10:00:00 - INFO - AI Monitor Service - HeartGuard
2025-11-24 10:00:00 - INFO - Initializing AI Monitor Worker...
2025-11-24 10:00:01 - INFO - InfluxDB client initialized
2025-11-24 10:00:01 - INFO - AI Service is healthy and model is loaded
2025-11-24 10:00:01 - INFO - PostgreSQL connection established
2025-11-24 10:00:01 - INFO - Worker started. Monitoring every 60 seconds...
2025-11-24 10:00:01 - INFO - === Monitoring Cycle #1 ===
```

## ✅ Sistema Completo Implementado

El monitoreo automático ahora:
1. ✅ Lee datos de InfluxDB cada 60 segundos
2. ✅ Predice problemas de salud con IA
3. ✅ Crea alertas automáticamente en PostgreSQL
4. ✅ Notifica a caregivers
5. ✅ Permite validación en ground truth

Ver documentación completa en:
- [Flujo IA → Alertas → Ground Truth](./FLUJO_IA_ALERTAS_GROUND_TRUTH.md)
- [AI Monitor Service](./services/ai-monitor/README.md)
