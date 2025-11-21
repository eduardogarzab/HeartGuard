# 🔗 Análisis: Sincronización InfluxDB ↔ PostgreSQL

## 📊 Estado Actual de la Arquitectura

### ✅ Lo que YA EXISTE en PostgreSQL

#### 1. **Tabla `devices`** (línea 840)
```sql
CREATE TABLE devices (
  id               UUID PRIMARY KEY,
  org_id           UUID REFERENCES organizations(id),
  serial           VARCHAR(80) NOT NULL UNIQUE,
  brand            VARCHAR(80),
  model            VARCHAR(80),
  device_type_id   UUID NOT NULL REFERENCES device_types(id),
  owner_patient_id UUID REFERENCES patients(id),
  registered_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  active           BOOLEAN NOT NULL DEFAULT TRUE
);
```
**Propósito**: Registra dispositivos IoT (monitores cardíacos, oxímetros, etc.)

#### 2. **Tabla `signal_streams`** (línea 855)
```sql
CREATE TABLE signal_streams (
  id             UUID PRIMARY KEY,
  patient_id     UUID NOT NULL REFERENCES patients(id),
  device_id      UUID NOT NULL REFERENCES devices(id),
  signal_type_id UUID NOT NULL REFERENCES signal_types(id),
  sample_rate_hz NUMERIC(10,3),
  started_at     TIMESTAMP NOT NULL,
  ended_at       TIMESTAMP
);
```
**Propósito**: Define streams de datos (sesiones de monitoreo)
- Vincula: **paciente → dispositivo → tipo de señal**
- Ejemplo: "Stream de ECG del paciente Juan usando dispositivo ABC123"

#### 3. **Tabla `timeseries_binding`** (línea 869) ⭐ **CLAVE**
```sql
CREATE TABLE timeseries_binding (
  id             UUID PRIMARY KEY,
  stream_id      UUID NOT NULL REFERENCES signal_streams(id),
  influx_org     VARCHAR(120),
  influx_bucket  VARCHAR(120) NOT NULL,
  measurement    VARCHAR(120) NOT NULL,
  retention_hint VARCHAR(60),
  created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE (stream_id, influx_bucket, measurement)
);
```
**Propósito**: **VINCULA PostgreSQL con InfluxDB**
- Mapea cada `signal_stream` a una ubicación en InfluxDB
- Define dónde se almacenan los datos de series temporales

#### 4. **Tabla `timeseries_binding_tag`** (línea 881)
```sql
CREATE TABLE timeseries_binding_tag (
  id         UUID PRIMARY KEY,
  binding_id UUID NOT NULL REFERENCES timeseries_binding(id),
  tag_key    VARCHAR(120) NOT NULL,
  tag_value  VARCHAR(240) NOT NULL,
  UNIQUE (binding_id, tag_key)
);
```
**Propósito**: Tags adicionales para filtrar datos en InfluxDB
- Ejemplo: `patient_id=uuid`, `device_serial=ABC123`, `location=hospital_norte`

---

## ❌ PROBLEMA DETECTADO: Inconsistencia de Measurements

### Configuración Actual:

| Servicio | Measurement Name | Fields |
|----------|-----------------|--------|
| **realtime-data-generator** | `vital_signs` | heart_rate, spo2, systolic_bp, diastolic_bp, temperature, gps_* |
| **user service** | `patient_vitals` | heart_rate, spo2, systolic_bp, diastolic_bp, body_temperature, gps_* |
| **desktop-app** | `vital_signs` | heart_rate, spo2, systolic_bp, diastolic_bp, temperature, gps_* |

### ⚠️ Inconsistencias:
1. **Nombres diferentes**: `vital_signs` vs `patient_vitals`
2. **Campo temperatura**: `temperature` vs `body_temperature`
3. **Falta de vinculación con `timeseries_binding`**

---

## 🎯 Solución: Sistema de Sincronización Completo

### Arquitectura Propuesta:

```
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL                              │
│  ┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   devices    │──│ signal_streams  │──│timeseries_binding││
│  │ (IoT HW)     │  │ (sesiones mon.) │  │ (config InfluxDB)││
│  └──────────────┘  └─────────────────┘  └─────────────────┘│
│         │                   │                      │         │
│         │                   │                      │         │
│         └───────────────────┴──────────────────────┘         │
│                             ↓                                │
│              Metadata de sincronización                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    SERVICIO DE SYNC
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       InfluxDB                               │
│  Bucket: heartguard_vitals                                  │
│  Measurement: vital_signs                                   │
│  Tags:                                                       │
│    - patient_id (UUID)                                       │
│    - device_id (UUID)                                        │
│    - stream_id (UUID) ← NUEVO                                │
│    - org_id (UUID)                                           │
│    - signal_type (string)                                    │
│  Fields:                                                     │
│    - heart_rate (int)                                        │
│    - spo2 (int)                                              │
│    - systolic_bp (int)                                       │
│    - diastolic_bp (int)                                      │
│    - temperature (float)                                     │
│    - gps_longitude (float)                                   │
│    - gps_latitude (float)                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Pasos de Implementación

### **PASO 1: Normalizar Measurements en InfluxDB**

Todos los servicios deben usar:
- **Measurement**: `vital_signs` (no `patient_vitals`)
- **Campo temperatura**: `temperature` (no `body_temperature`)

### **PASO 2: Agregar Tags de Vinculación**

Cada punto escrito en InfluxDB debe incluir:
```python
point = Point("vital_signs") \
    .tag("patient_id", patient_id) \
    .tag("device_id", device_id) \
    .tag("stream_id", stream_id)  # ← NUEVO
    .tag("org_id", org_id) \
    .tag("signal_type", "vital_signs")  # ← NUEVO
    .field("heart_rate", 72) \
    # ... más fields
```

### **PASO 3: Crear Servicio de Sincronización**

Crear `services/sync/` con:
1. **Sync Writer**: Escribe en InfluxDB con metadata de PostgreSQL
2. **Metadata Resolver**: Consulta `timeseries_binding` para saber dónde escribir
3. **Tag Enrichment**: Agrega tags desde `timeseries_binding_tag`

---

## 🔧 Modificaciones Necesarias

### Archivo 1: `services/realtime-data-generator/src/generator/influx.py`

**CAMBIAR DE:**
```python
point = Point("vital_signs") \
    .tag("patient_id", patient.id) \
    .tag("patient_name", patient.name) \
    .tag("org_id", patient.org_id or "none") \
    .tag("risk_level", patient.risk_level_code or "unknown")
```

**CAMBIAR A:**
```python
point = Point("vital_signs") \
    .tag("patient_id", patient.id) \
    .tag("device_id", device.id) \  # ← NUEVO
    .tag("stream_id", stream.id) \   # ← NUEVO
    .tag("org_id", patient.org_id) \
    .tag("signal_type", "vital_signs") \  # ← NUEVO
    # Agregar tags dinámicos desde timeseries_binding_tag
    .tag("patient_name", patient.name) \
    .tag("risk_level", patient.risk_level_code)
```

### Archivo 2: `services/user/src/user/services/influxdb_service.py`

**CAMBIAR:**
- `r["_measurement"] == "patient_vitals"` → `r["_measurement"] == "vital_signs"`
- `body_temperature` → `temperature`

**AGREGAR filtros por tags:**
```python
query = f'''
from(bucket: "{self.bucket}")
    |> range(start: -{hours}h)
    |> filter(fn: (r) => r["_measurement"] == "vital_signs")
    |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
    |> filter(fn: (r) => r["signal_type"] == "vital_signs")  # ← NUEVO
'''
```

---

## 🗄️ Flujo de Datos Completo

### 1. **Inicio de Sesión de Monitoreo**

```sql
-- Crear stream en PostgreSQL
INSERT INTO signal_streams (id, patient_id, device_id, signal_type_id, started_at)
VALUES (gen_random_uuid(), 'patient-uuid', 'device-uuid', 'signal-type-uuid', NOW());

-- Crear binding con InfluxDB
INSERT INTO timeseries_binding (stream_id, influx_bucket, measurement)
VALUES ('stream-uuid', 'heartguard_vitals', 'vital_signs');

-- Agregar tags personalizados
INSERT INTO timeseries_binding_tag (binding_id, tag_key, tag_value)
VALUES 
  ('binding-uuid', 'location', 'ICU-Room-5'),
  ('binding-uuid', 'monitor_brand', 'Philips');
```

### 2. **Escritura de Datos en InfluxDB**

```python
# Consultar binding desde PostgreSQL
binding = db.query("""
    SELECT tb.*, ss.patient_id, ss.device_id, ss.signal_type_id
    FROM timeseries_binding tb
    JOIN signal_streams ss ON ss.id = tb.stream_id
    WHERE tb.stream_id = %s
""", (stream_id,))

# Obtener tags adicionales
tags = db.query("""
    SELECT tag_key, tag_value
    FROM timeseries_binding_tag
    WHERE binding_id = %s
""", (binding.id,))

# Escribir en InfluxDB
point = Point(binding.measurement) \
    .tag("patient_id", binding.patient_id) \
    .tag("device_id", binding.device_id) \
    .tag("stream_id", stream_id) \
    .tag("signal_type", get_signal_type_code(binding.signal_type_id))

# Agregar tags dinámicos
for tag in tags:
    point = point.tag(tag.tag_key, tag.tag_value)

# Agregar fields
point = point \
    .field("heart_rate", 72) \
    .field("spo2", 98) \
    # ... etc

influx.write(bucket=binding.influx_bucket, record=point)
```

### 3. **Lectura de Datos desde InfluxDB**

```python
# Consultar binding
binding = get_binding_for_stream(stream_id)

# Query con tags correctos
query = f'''
from(bucket: "{binding.influx_bucket}")
    |> range(start: -1h)
    |> filter(fn: (r) => r._measurement == "{binding.measurement}")
    |> filter(fn: (r) => r.stream_id == "{stream_id}")
    |> filter(fn: (r) => r.patient_id == "{patient_id}")
'''
```

---

## 📋 Checklist de Sincronización

### PostgreSQL → InfluxDB (Metadata)
- [ ] `devices.id` → Tag `device_id`
- [ ] `signal_streams.id` → Tag `stream_id`
- [ ] `signal_streams.patient_id` → Tag `patient_id`
- [ ] `patients.org_id` → Tag `org_id`
- [ ] `signal_types.code` → Tag `signal_type`
- [ ] `timeseries_binding.measurement` → Measurement name
- [ ] `timeseries_binding.influx_bucket` → Bucket name
- [ ] `timeseries_binding_tag.*` → Tags dinámicos

### InfluxDB → PostgreSQL (Agregados)
- [ ] Último timestamp por stream → `signal_streams.ended_at`
- [ ] Conteo de puntos escritos → Tabla de métricas (opcional)
- [ ] Detección de gaps → Tabla de alertas (opcional)

---

## 🚀 Ventajas de Esta Arquitectura

1. **Trazabilidad Completa**: Cada punto en InfluxDB está vinculado a un stream en PostgreSQL
2. **Flexibilidad**: Tags dinámicos desde `timeseries_binding_tag`
3. **Multi-tenant**: Filtrado por `org_id`
4. **Auditoría**: Stream IDs permiten rastrear origen de datos
5. **Escalabilidad**: InfluxDB maneja millones de puntos, PostgreSQL maneja metadata
6. **Consultas Rápidas**: Tags indexados en InfluxDB + JOINs en PostgreSQL

---

## 📊 Ejemplo Completo

### PostgreSQL:
```sql
-- Device
devices.id = 'dev-123'
devices.serial = 'ABC-001'
devices.owner_patient_id = 'pat-456'

-- Stream
signal_streams.id = 'stream-789'
signal_streams.patient_id = 'pat-456'
signal_streams.device_id = 'dev-123'

-- Binding
timeseries_binding.stream_id = 'stream-789'
timeseries_binding.influx_bucket = 'heartguard_vitals'
timeseries_binding.measurement = 'vital_signs'

-- Tags
timeseries_binding_tag: location = "ICU-5"
timeseries_binding_tag: priority = "high"
```

### InfluxDB:
```
vital_signs,
  patient_id=pat-456,
  device_id=dev-123,
  stream_id=stream-789,
  org_id=org-999,
  signal_type=vital_signs,
  location=ICU-5,
  priority=high
heart_rate=72,
spo2=98,
systolic_bp=120,
diastolic_bp=80,
temperature=36.5
1700000000000000000
```

---

## ⚡ Próximos Pasos Recomendados

1. **Crear servicio de sincronización** en `services/sync/`
2. **Normalizar measurements** a `vital_signs` en todos los servicios
3. **Agregar `stream_id` tag** en realtime-data-generator
4. **Actualizar queries** en user service y desktop app
5. **Implementar metadata resolver** que consulte `timeseries_binding`
6. **Agregar validación** de que el stream existe antes de escribir

¿Necesitas que implemente alguno de estos pasos?
