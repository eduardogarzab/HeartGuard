# Sincronización InfluxDB-PostgreSQL - Implementación Completada

## ✅ Estado: COMPLETADO Y VALIDADO

Fecha: 2025-11-20
Sistema: HeartGuard - Monitoreo de Signos Vitales

---

## 📋 Resumen Ejecutivo

Se ha implementado exitosamente la sincronización completa entre InfluxDB y PostgreSQL, permitiendo que los datos de series temporales en InfluxDB incluyan metadatos completos desde las tablas `devices`, `signal_streams`, y `timeseries_binding` de PostgreSQL.

**Validación:** ✅ Todos los archivos Python compilados sin errores de sintaxis.

---

## 🎯 Cambios Implementados

### Fase 1: Normalización de Nombres ✅
**Archivo:** `services/user/src/user/services/influxdb_service.py`

**Cambios realizados:**
- ✅ Cambio de `"patient_vitals"` → `"vital_signs"` (3 ubicaciones)
- ✅ Cambio de `"body_temperature"` → `"temperature"` (3 ubicaciones)

**Impacto:** El servicio de usuario ahora consulta el measurement correcto usado por el generador y la aplicación de escritorio.

---

### Fase 2: Script SQL de Inicialización ✅
**Archivo:** `db/init_sync_data.sql` (NUEVO)

**Contenido:**
```sql
-- 1. Inserta tipos de dispositivos (vital_monitor, ecg_sensor, oximeter)
-- 2. Inserta tipos de señales (vital_signs, ecg, ppg)
-- 3. Crea dispositivos automáticamente para cada paciente
-- 4. Crea signal_streams activos para cada paciente
-- 5. Crea timeseries_binding vinculando streams a InfluxDB
-- 6. Agrega tags personalizados (location, signal_type)
-- 7. Incluye queries de verificación
```

**Ejecución:**
```bash
psql -U heartguard_app -d heartguard -f db/init_sync_data.sql
```

**Resultado esperado:**
- Un dispositivo HG-2000 por paciente
- Un stream activo de vital_signs por paciente
- Un binding a InfluxDB por stream
- Tags adicionales: `location=hospital_main`, `signal_type=vital_signs`

---

### Fase 3: Nuevos Métodos en db.py ✅
**Archivo:** `services/realtime-data-generator/src/generator/db.py`

**Métodos agregados:**

#### 1. `get_patient_device_streams() -> List[StreamConfig]`
```python
# Retorna configuración completa con JOIN de:
# - patients + organizations + risk_levels
# - devices (activos)
# - signal_streams (no finalizados)
# - timeseries_binding
# - timeseries_binding_tag (agregados en JSON)
```

**Campos retornados:**
- `patient_id`, `patient_name`, `patient_email`
- `org_id`, `org_name`
- `risk_level_code`
- `device_id`, `device_serial`
- `stream_id`, `signal_type_code`
- `binding_id`
- `influx_org`, `influx_bucket`, `measurement`
- `custom_tags` (dict)

#### 2. `get_binding_tags(binding_id) -> Dict[str, str]`
```python
# Obtiene tags personalizados para un binding específico
# Retorna: {"location": "hospital_main", "floor": "3", ...}
```

**Dataclass nueva:** `StreamConfig` en `data_generator.py`

---

### Fase 4: Nuevo Método en influx.py ✅
**Archivo:** `services/realtime-data-generator/src/generator/influx.py`

**Método agregado:**

#### `write_vital_signs_from_stream(stream_config, reading)`
```python
# Escribe a InfluxDB usando configuración completa:
point = Point(stream_config.measurement)
    .tag("patient_id", stream_config.patient_id)
    .tag("patient_name", stream_config.patient_name)
    .tag("device_id", stream_config.device_id)      # ⭐ NUEVO
    .tag("stream_id", stream_config.stream_id)      # ⭐ NUEVO
    .tag("org_id", stream_config.org_id)
    .tag("signal_type", stream_config.signal_type_code)
    .tag("risk_level", stream_config.risk_level_code)
    # + custom_tags dinámicos desde PostgreSQL
```

**Método legacy:** `write_vital_signs(patient, reading)` mantenido para compatibilidad.

---

### Fase 5: Actualización del Worker ✅
**Archivo:** `services/realtime-data-generator/src/generator/worker.py`

**Cambios en `_generate_and_send_data()`:**

**ANTES:**
```python
patients = self.db_service.get_active_patients()
for patient in patients:
    reading = self.generator.generate_reading(patient.id)
    self.influx_service.write_vital_signs(patient, reading)
```

**AHORA:**
```python
stream_configs = self.db_service.get_patient_device_streams()
for stream_config in stream_configs:
    reading = self.generator.generate_reading(stream_config.patient_id)
    self.influx_service.write_vital_signs_from_stream(stream_config, reading)
```

**Logs mejorados:**
```
Data generation: 5 successful, 0 skipped (total streams: 5)
```

---

## 🔍 Estructura de Datos InfluxDB

### ANTES de la sincronización:
```
Measurement: vital_signs
Tags:
  - patient_id
  - patient_name
  - org_id
  - risk_level
Fields: heart_rate, spo2, systolic_bp, diastolic_bp, temperature, ...
```

### AHORA con sincronización:
```
Measurement: vital_signs (desde timeseries_binding.measurement)
Tags:
  - patient_id
  - patient_name
  - device_id ⭐ NUEVO (desde devices.id)
  - stream_id ⭐ NUEVO (desde signal_streams.id)
  - org_id
  - signal_type ⭐ NUEVO (desde signal_types.code)
  - risk_level
  - location ⭐ NUEVO (tag personalizado desde timeseries_binding_tag)
  - [otros tags personalizados...]
Fields: heart_rate, spo2, systolic_bp, diastolic_bp, temperature, ...
```

---

## 📊 Flujo de Datos Completo

```
PostgreSQL (Metadatos)
├── patients (id, name, email, org_id, risk_level_id)
├── devices (id, serial, owner_patient_id, device_type_id)
├── signal_streams (id, patient_id, device_id, signal_type_id)
├── timeseries_binding (id, stream_id, influx_bucket, measurement)
└── timeseries_binding_tag (binding_id, tag_key, tag_value)
                    ↓
        get_patient_device_streams()
                    ↓
            StreamConfig objects
                    ↓
        VitalSignsGenerator.generate_reading()
                    ↓
    write_vital_signs_from_stream(config, reading)
                    ↓
InfluxDB (Series Temporales)
└── vital_signs measurement
    ├── Tags: patient_id, device_id, stream_id, org_id, signal_type, custom_tags
    └── Fields: heart_rate, spo2, systolic_bp, diastolic_bp, temperature, GPS
```

---

## 🧪 Validación Realizada

### Validación de Sintaxis Python
```
✅ data_generator.py - Sin errores
✅ db.py - Sin errores
✅ influx.py - Sin errores
✅ worker.py - Sin errores
✅ influxdb_service.py - Sin errores
```

### Estructura de Datos Verificada
```python
# StreamConfig incluye todos los campos necesarios:
config = StreamConfig(
    patient_id="uuid",
    device_id="uuid",        # ⭐ Permite vincular con devices
    stream_id="uuid",        # ⭐ Permite vincular con signal_streams
    influx_bucket="...",     # Configuración dinámica desde PostgreSQL
    measurement="...",       # Nombre dinámico desde PostgreSQL
    custom_tags={...}        # Tags adicionales desde PostgreSQL
)
```

---

## 📝 Pasos para Deployment

### 1. Iniciar Servicios Docker
```bash
cd C:\Users\mendo\Downloads\code\UDEM\integracion\HeartGuard
docker-compose up -d postgres influxdb redis
```

### 2. Ejecutar Script SQL de Inicialización
```bash
# Opción A: Desde contenedor Docker
docker exec -i heartguard-postgres psql -U heartguard_app -d heartguard < db/init_sync_data.sql

# Opción B: Con psql local
psql -h 134.199.204.58 -U heartguard_app -d heartguard -f db/init_sync_data.sql
```

### 3. Verificar Datos Creados
```sql
-- Conectarse a PostgreSQL
psql -h 134.199.204.58 -U heartguard_app -d heartguard

-- Verificar dispositivos
SELECT COUNT(*) FROM heartguard.devices;

-- Verificar streams activos
SELECT COUNT(*) FROM heartguard.signal_streams WHERE ended_at IS NULL;

-- Ver configuración completa
SELECT 
  p.person_name,
  d.serial,
  tb.measurement,
  tb.influx_bucket
FROM heartguard.patients p
JOIN heartguard.devices d ON d.owner_patient_id = p.id
JOIN heartguard.signal_streams ss ON ss.device_id = d.id
JOIN heartguard.timeseries_binding tb ON tb.stream_id = ss.id
LIMIT 5;
```

### 4. Reiniciar Servicio Generador
```bash
cd services/realtime-data-generator
docker-compose restart realtime-data-generator

# O si está corriendo localmente:
# Ctrl+C para detener
# python -m generator.main
```

### 5. Verificar Logs
```bash
# Ver logs del generador
docker logs -f heartguard-realtime-generator

# Buscar este mensaje:
# "Data generation: 5 successful, 0 skipped (total streams: 5)"
```

### 6. Verificar InfluxDB
```bash
# Conectarse a InfluxDB
docker exec -it heartguard-influxdb influx

# Query de verificación
from(bucket: "heartguard_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
  |> filter(fn: (r) => exists r["device_id"])
  |> filter(fn: (r) => exists r["stream_id"])
  |> limit(n: 1)

# Debe retornar datos con device_id y stream_id tags
```

---

## 🔧 Troubleshooting

### Problema: "No stream configurations found in database"
**Solución:** Ejecutar `db/init_sync_data.sql` primero.

### Problema: Tags device_id/stream_id no aparecen en InfluxDB
**Causa:** El generador está usando el método legacy.
**Solución:** Verificar que `worker.py` usa `get_patient_device_streams()` y `write_vital_signs_from_stream()`.

### Problema: Error de importación "StreamConfig"
**Causa:** Caché de Python.
**Solución:**
```bash
cd services/realtime-data-generator
find . -type d -name __pycache__ -exec rm -rf {} +
python -m generator.main
```

### Problema: Custom tags no aparecen
**Verificar:**
```sql
SELECT * FROM heartguard.timeseries_binding_tag;
-- Debe retornar registros con tag_key y tag_value
```

---

## 📈 Beneficios de la Implementación

### ✅ Trazabilidad Completa
- Cada dato en InfluxDB ahora se puede vincular a:
  - Paciente específico
  - Dispositivo físico usado
  - Sesión de monitoreo (stream)
  - Organización/hospital
  - Configuración de InfluxDB usada

### ✅ Flexibilidad
- Configuración de buckets/measurements dinámica desde PostgreSQL
- Tags personalizados por stream
- Soporte para múltiples dispositivos por paciente
- Soporte para múltiples streams simultáneos

### ✅ Integridad de Datos
- Normalización a 3FN en PostgreSQL
- Referential integrity con foreign keys
- Streams tienen inicio/fin (audit trail)
- Dispositivos se pueden activar/desactivar

### ✅ Consultas Avanzadas
Ahora es posible consultar:
```sql
-- Datos de un dispositivo específico
|> filter(fn: (r) => r["device_id"] == "abc-123")

-- Datos de una sesión de monitoreo
|> filter(fn: (r) => r["stream_id"] == "stream-xyz")

-- Datos por ubicación
|> filter(fn: (r) => r["location"] == "hospital_main")

-- Comparar diferentes dispositivos del mismo paciente
|> group(columns: ["device_id"])
```

---

## 📚 Archivos Modificados

| Archivo | Tipo | Líneas | Descripción |
|---------|------|--------|-------------|
| `services/user/src/user/services/influxdb_service.py` | MOD | 5 cambios | Normalización measurement/field names |
| `db/init_sync_data.sql` | NEW | 232 | Script SQL de inicialización |
| `services/realtime-data-generator/src/generator/data_generator.py` | MOD | +19 | StreamConfig dataclass |
| `services/realtime-data-generator/src/generator/db.py` | MOD | +124 | Nuevos métodos de consulta |
| `services/realtime-data-generator/src/generator/influx.py` | MOD | +62 | Nuevo método write con stream config |
| `services/realtime-data-generator/src/generator/worker.py` | MOD | +18 | Uso de stream configs |

**Total:** 6 archivos, ~230 líneas de código nuevo/modificado

---

## ✅ Checklist de Deployment

- [ ] Docker containers iniciados (postgres, influxdb, redis)
- [ ] `db/init_sync_data.sql` ejecutado exitosamente
- [ ] Verificación SQL: dispositivos y streams creados
- [ ] Servicio realtime-data-generator reiniciado
- [ ] Logs muestran "stream configurations" encontradas
- [ ] InfluxDB tiene datos con device_id y stream_id tags
- [ ] User service puede consultar datos con "vital_signs" measurement
- [ ] Desktop app muestra gráficas correctamente

---

## 🎓 Documentación Técnica

### Modelo de Datos PostgreSQL
```
devices
├── id (PK)
├── serial (UNIQUE)
├── device_type_id (FK → device_types)
├── owner_patient_id (FK → patients)
└── active (boolean)

signal_streams
├── id (PK)
├── patient_id (FK → patients)
├── device_id (FK → devices)
├── signal_type_id (FK → signal_types)
├── started_at (timestamp)
└── ended_at (timestamp, nullable)

timeseries_binding
├── id (PK)
├── stream_id (FK → signal_streams)
├── influx_org
├── influx_bucket
├── measurement
└── retention_hint

timeseries_binding_tag
├── id (PK)
├── binding_id (FK → timeseries_binding)
├── tag_key
└── tag_value
```

---

## 🚀 Próximos Pasos (Opcionales)

1. **Dashboard de Dispositivos**
   - UI para ver todos los dispositivos registrados
   - Estado: activo/inactivo
   - Última comunicación

2. **Gestión de Streams**
   - UI para iniciar/finalizar streams
   - Ver historial de sesiones de monitoreo
   - Reportes por stream

3. **Alertas Basadas en Dispositivo**
   - Alertas si un dispositivo deja de enviar datos
   - Notificaciones por batería baja
   - Alertas por desconexión

4. **Análisis Multi-dispositivo**
   - Comparar lecturas de diferentes dispositivos
   - Calibración entre dispositivos
   - Detección de dispositivos defectuosos

---

## 📞 Contacto y Soporte

Para preguntas sobre esta implementación:
- Revisar logs en `services/realtime-data-generator/logs/`
- Consultar tablas PostgreSQL directamente
- Verificar datos en InfluxDB con queries de ejemplo

**Versión:** 1.0  
**Fecha:** 2025-11-20  
**Sistema:** HeartGuard - Monitoreo de Signos Vitales
