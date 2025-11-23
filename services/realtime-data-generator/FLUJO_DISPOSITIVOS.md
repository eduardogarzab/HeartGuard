# Flujo de Dispositivos y Generación de Datos en Tiempo Real

## 📋 Concepto General

El sistema HeartGuard simula dispositivos médicos reales que capturan signos vitales de pacientes. Los datos sintéticos se generan automáticamente para dispositivos **asignados y activos**, reflejando el flujo de trabajo real de una organización de salud.

## 🔄 Flujo Completo

### 1️⃣ Compra de Dispositivo por Organización

La organización adquiere un dispositivo médico (oxímetro, monitor ECG, etc.):

```sql
INSERT INTO devices (
    org_id, 
    serial, 
    brand, 
    model, 
    device_type_id, 
    owner_patient_id,  -- NULL (sin asignar)
    active              -- TRUE (operativo)
) VALUES (
    'org-uuid',
    'HG-ECG-001',
    'Cardia',
    'Wave Pro',
    (SELECT id FROM device_types WHERE code='ECG_1LEAD'),
    NULL,   -- Sin paciente asignado todavía
    TRUE
);
```

**Estado**: Dispositivo en inventario, sin generar datos.

---

### 2️⃣ Asignación de Dispositivo a Paciente

Un administrador asigna el dispositivo a un paciente específico:

```sql
UPDATE devices 
SET owner_patient_id = 'patient-uuid'
WHERE serial = 'HG-ECG-001';
```

**⚡ Trigger Automático**: Al asignar el dispositivo, PostgreSQL ejecuta automáticamente:

1. **Crea `signal_stream`**: Vincula dispositivo → paciente
2. **Crea `timeseries_binding`**: Configura conexión con InfluxDB
   - `influx_bucket`: `timeseries`
   - `measurement`: `vital_signs`
   - `retention`: 30 días
3. **Crea `timeseries_binding_tag`**: Agrega metadatos
   - GPS desde `patient_locations`
   - Tags custom: `location`, `floor`

**Estado**: Dispositivo asignado, stream activo, **generación de datos INICIA**.

---

### 3️⃣ Generación de Datos Sintéticos

El servicio `realtime-data-generator` consulta cada 5 segundos:

```sql
SELECT 
    p.person_name AS patient_name,
    d.serial AS device_serial,
    d.brand, d.model,
    ss.id AS stream_id,
    tb.influx_bucket, tb.measurement
FROM patients p
JOIN devices d ON d.owner_patient_id = p.id 
    AND d.active = TRUE          -- Solo activos
    AND d.owner_patient_id IS NOT NULL  -- Solo asignados
JOIN signal_streams ss ON ss.device_id = d.id 
    AND ss.ended_at IS NULL      -- Solo streams activos
JOIN timeseries_binding tb ON tb.stream_id = ss.id
```

**Generación**: Por cada dispositivo asignado y activo:
- Genera signos vitales sintéticos (HR, SpO2, BP, Temp, GPS)
- Escribe a InfluxDB con metadatos completos (device_id, stream_id, org_id, tags)

**Escritura en InfluxDB**:
```
measurement: vital_signs
├── tags:
│   ├── patient_id: UUID del paciente
│   ├── patient_name: Nombre completo
│   ├── device_id: UUID del dispositivo ✅
│   ├── stream_id: UUID del stream ✅
│   ├── org_id: UUID de la organización
│   ├── signal_type: HR (Heart Rate)
│   ├── risk_level: high/medium/low
│   ├── location: hospital_main ✅
│   └── floor: 3 ✅
└── fields:
    ├── heart_rate: 60-92 bpm
    ├── spo2: 91-100%
    ├── systolic_bp: 102-154 mmHg
    ├── diastolic_bp: 59-94 mmHg
    ├── temperature: 36.14-37.02°C
    ├── gps_longitude: (desde patient_locations)
    └── gps_latitude: (desde patient_locations)
```

---

### 4️⃣ Desasignación de Dispositivo

Si el paciente es dado de alta o el dispositivo necesita mantenimiento:

```sql
-- Opción 1: Desasignar completamente
UPDATE devices 
SET owner_patient_id = NULL
WHERE serial = 'HG-ECG-001';

-- Opción 2: Desactivar temporalmente
UPDATE devices 
SET active = FALSE
WHERE serial = 'HG-ECG-001';

-- Opción 3: Finalizar stream (mantener historial)
UPDATE signal_streams 
SET ended_at = NOW()
WHERE device_id = (SELECT id FROM devices WHERE serial = 'HG-ECG-001')
  AND ended_at IS NULL;
```

**Estado**: **Generación de datos SE DETIENE** para ese dispositivo.

---

## 🎯 Visualización en Desktop App

Cuando un usuario abre el detalle de un paciente (`PatientDetailDialog.java`):

1. **Consulta InfluxDB** filtrando por `patient_id`
2. **Obtiene datos de los últimos 5 minutos**
3. **Grafica en tiempo real**:
   - 4 Value Cards (último valor de HR, SpO2, BP, Temp)
   - 4 Gráficas de línea (histórico de 5 min, auto-actualización cada 10s)

**Query InfluxDB desde Desktop App**:
```flux
from(bucket: "timeseries")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "vital_signs")
  |> filter(fn: (r) => r.patient_id == "patient-uuid")
  |> filter(fn: (r) => r.device_id == "device-uuid")
```

---

## 🔧 Archivos Clave

| Archivo | Función |
|---------|---------|
| `db/seed.sql` | Trigger automático para crear streams al asignar dispositivos |
| `services/realtime-data-generator/src/generator/db.py` | Query que filtra solo dispositivos asignados y activos |
| `services/realtime-data-generator/src/generator/influx.py` | Escribe datos a InfluxDB con metadatos completos |
| `services/realtime-data-generator/src/generator/worker.py` | Loop cada 5 segundos generando datos |
| `desktop-app/src/.../InfluxDBService.java` | Consulta InfluxDB desde la app de escritorio |
| `desktop-app/src/.../VitalSignsChartPanel.java` | Gráficas en tiempo real (auto-actualización 10s) |

---

## 🚀 Comandos Útiles

### Ver dispositivos asignados
```sql
SELECT 
  d.serial,
  d.brand,
  d.model,
  p.person_name AS paciente,
  d.active,
  CASE WHEN ss.id IS NOT NULL THEN 'SÍ' ELSE 'NO' END AS tiene_stream
FROM devices d
LEFT JOIN patients p ON p.id = d.owner_patient_id
LEFT JOIN signal_streams ss ON ss.device_id = d.id AND ss.ended_at IS NULL
WHERE d.owner_patient_id IS NOT NULL
ORDER BY d.serial;
```

### Ver datos en InfluxDB (últimos 1 minuto)
```bash
curl -s "http://134.199.204.58:8086/api/v2/query?org=heartguard" \
  -H "Authorization: Token heartguard-dev-token-change-me" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket: "timeseries")
  |> range(start: -1m)
  |> filter(fn: (r) => r._measurement == "vital_signs")
  |> limit(n: 5)'
```

### Reiniciar generador de datos
```bash
cd /root/HeartGuard/services/realtime-data-generator
pkill -f "flask.*generator"
export PYTHONPATH=/root/HeartGuard/services/realtime-data-generator/src
source .venv/bin/activate
FLASK_APP=generator.app:app flask run --host=0.0.0.0 --port=5006
```

---

## ✅ Ventajas del Nuevo Diseño

1. **Automatización**: Trigger crea streams automáticamente al asignar dispositivos
2. **Sincronización**: Solo genera datos para dispositivos realmente asignados
3. **Escalabilidad**: Fácil agregar más dispositivos sin modificar código
4. **Trazabilidad**: Cada dato incluye device_id, stream_id, org_id
5. **Realismo**: Simula el flujo de trabajo real de compra → asignación → monitoreo
6. **Flexibilidad**: Desactivar dispositivos detiene generación sin perder historial

---

## 📊 Ejemplo Completo

```sql
-- 1. Organización compra 2 dispositivos
INSERT INTO devices (org_id, serial, brand, model, device_type_id, active) VALUES
  ('org-123', 'OXY-2024-001', 'Nonin', '3150', (SELECT id FROM device_types WHERE code='PULSE_OX'), TRUE),
  ('org-123', 'ECG-2024-002', 'Cardia', 'Mobile', (SELECT id FROM device_types WHERE code='ECG_1LEAD'), TRUE);
-- Estado: 2 dispositivos en inventario, 0 pacientes monitoreados

-- 2. Administrador asigna dispositivos a 2 pacientes
UPDATE devices SET owner_patient_id = 'patient-maria' WHERE serial = 'OXY-2024-001';
UPDATE devices SET owner_patient_id = 'patient-jose' WHERE serial = 'ECG-2024-002';
-- Estado: 2 dispositivos asignados, 2 streams creados automáticamente ✅

-- 3. Generador produce datos cada 5 segundos
-- María (OXY): HR=78, SpO2=97%, ...
-- José (ECG):  HR=65, SpO2=98%, ...

-- 4. Desktop app muestra gráficas en tiempo real
-- PatientDetailDialog.java consulta InfluxDB cada 10 segundos
-- Gráficas se actualizan automáticamente
```

---

**Fecha**: 2025-11-22  
**Autor**: Sistema HeartGuard  
**Versión**: 2.0 (Sincronización Automática)
