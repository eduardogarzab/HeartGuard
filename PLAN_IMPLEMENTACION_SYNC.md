# 🔧 Plan de Implementación: Sincronización Completa InfluxDB ↔ PostgreSQL

## 📋 Resumen Ejecutivo

### Situación Actual
- ✅ **PostgreSQL tiene las tablas necesarias**: `devices`, `signal_streams`, `timeseries_binding`, `timeseries_binding_tag`
- ❌ **El servicio realtime-data-generator NO las está usando**: Solo consulta `patients` y escribe directamente a InfluxDB
- ❌ **Inconsistencia de nombres**: `vital_signs` vs `patient_vitals`
- ❌ **Falta vinculación**: No se registran `stream_id` ni `device_id` en InfluxDB

### Objetivo
Crear un flujo completo donde:
1. Los dispositivos se registren en PostgreSQL
2. Los streams se creen y vinculen con InfluxDB
3. Los datos escritos en InfluxDB incluyan toda la metadata de PostgreSQL
4. Los servicios lean usando la configuración de `timeseries_binding`

---

## 🎯 Modificaciones Requeridas

### 📁 **1. Normalizar Measurement Name**

#### Archivo: `services/user/src/user/services/influxdb_service.py`

**LÍNEA 72, 125, 176 - CAMBIAR:**
```python
|> filter(fn: (r) => r["_measurement"] == "patient_vitals")
```

**A:**
```python
|> filter(fn: (r) => r["_measurement"] == "vital_signs")
```

**LÍNEAS con `body_temperature` - CAMBIAR:**
```python
'body_temperature': record.values.get('body_temperature')
```

**A:**
```python
'temperature': record.values.get('temperature')
```

---

### 📁 **2. Actualizar Generador de Datos en Tiempo Real**

#### Archivo: `services/realtime-data-generator/src/generator/db.py`

**AGREGAR nuevo método después de `get_active_patients()` (línea ~100):**

```python
    def get_patient_device_streams(self) -> List[dict]:
        """
        Obtiene pacientes con sus dispositivos y streams activos.
        Incluye la configuración de timeseries_binding para saber dónde escribir.
        """
        try:
            self.ensure_connection()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        p.id::text as patient_id,
                        p.person_name as patient_name,
                        p.email as patient_email,
                        p.org_id::text as org_id,
                        rl.code as risk_level_code,
                        d.id::text as device_id,
                        d.serial as device_serial,
                        d.brand as device_brand,
                        d.model as device_model,
                        dt.code as device_type_code,
                        ss.id::text as stream_id,
                        st.code as signal_type_code,
                        ss.sample_rate_hz,
                        ss.started_at,
                        tb.id::text as binding_id,
                        tb.influx_org,
                        tb.influx_bucket,
                        tb.measurement,
                        tb.retention_hint
                    FROM heartguard.patients p
                    LEFT JOIN heartguard.risk_levels rl ON p.risk_level_id = rl.id
                    -- Unir con dispositivos del paciente
                    LEFT JOIN heartguard.devices d ON d.owner_patient_id = p.id AND d.active = TRUE
                    LEFT JOIN heartguard.device_types dt ON d.device_type_id = dt.id
                    -- Unir con streams activos (sin ended_at)
                    LEFT JOIN heartguard.signal_streams ss ON ss.patient_id = p.id 
                        AND ss.device_id = d.id 
                        AND ss.ended_at IS NULL
                    LEFT JOIN heartguard.signal_types st ON ss.signal_type_id = st.id
                    -- Unir con binding de InfluxDB
                    LEFT JOIN heartguard.timeseries_binding tb ON tb.stream_id = ss.id
                    WHERE p.id IS NOT NULL
                    ORDER BY p.created_at DESC
                    LIMIT 100
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                logger.info(f"Fetched {len(results)} patient-device-stream bindings")
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error fetching patient device streams: {e}")
            return []
    
    def get_binding_tags(self, binding_id: str) -> List[dict]:
        """
        Obtiene los tags personalizados de un binding.
        """
        try:
            self.ensure_connection()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT tag_key, tag_value
                    FROM heartguard.timeseries_binding_tag
                    WHERE binding_id = %s
                """
                cursor.execute(query, (binding_id,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error fetching binding tags: {e}")
            return []
```

---

#### Archivo: `services/realtime-data-generator/src/generator/influx.py`

**REEMPLAZAR método `write_vital_signs` completo (líneas ~50-80):**

```python
    def write_vital_signs(self, stream_config: Dict, reading: Dict):
        """
        Write vital signs to InfluxDB using stream configuration from PostgreSQL.
        
        Args:
            stream_config: Diccionario con patient_id, device_id, stream_id, 
                          binding info, etc.
            reading: Diccionario con los valores de signos vitales
        """
        try:
            # Validar que tengamos la configuración necesaria
            if not stream_config.get('stream_id'):
                logger.warning(f"No active stream for patient {stream_config.get('patient_id')}, skipping")
                return
            
            if not stream_config.get('binding_id'):
                logger.warning(f"No InfluxDB binding for stream {stream_config.get('stream_id')}, skipping")
                return
            
            timestamp = reading['timestamp']
            
            # Usar configuración de binding
            measurement = stream_config.get('measurement', 'vital_signs')
            bucket = stream_config.get('influx_bucket', self.bucket)
            
            # Crear point con tags de metadata de PostgreSQL
            point = Point(measurement) \
                .tag("patient_id", stream_config['patient_id']) \
                .tag("device_id", stream_config['device_id']) \
                .tag("stream_id", stream_config['stream_id']) \
                .tag("org_id", stream_config.get('org_id') or "none") \
                .tag("signal_type", stream_config.get('signal_type_code', 'vital_signs'))
            
            # Agregar tags opcionales si existen
            if stream_config.get('patient_name'):
                point = point.tag("patient_name", stream_config['patient_name'])
            if stream_config.get('risk_level_code'):
                point = point.tag("risk_level", stream_config['risk_level_code'])
            if stream_config.get('device_serial'):
                point = point.tag("device_serial", stream_config['device_serial'])
            if stream_config.get('device_brand'):
                point = point.tag("device_brand", stream_config['device_brand'])
            
            # Agregar fields de signos vitales
            point = point \
                .field("gps_longitude", reading['gps_longitude']) \
                .field("gps_latitude", reading['gps_latitude']) \
                .field("heart_rate", reading['heart_rate']) \
                .field("spo2", reading['spo2']) \
                .field("systolic_bp", reading['systolic_bp']) \
                .field("diastolic_bp", reading['diastolic_bp']) \
                .field("temperature", reading['temperature']) \
                .time(timestamp, WritePrecision.NS)
            
            # Escribir en el bucket configurado
            self.write_api.write(
                bucket=bucket,
                org=stream_config.get('influx_org') or self.org,
                record=point
            )
            
            logger.debug(
                f"Wrote to {bucket}/{measurement}: patient={stream_config['patient_name']}, "
                f"stream={stream_config['stream_id'][:8]}..., "
                f"HR={reading['heart_rate']}, SpO2={reading['spo2']}"
            )
        except Exception as e:
            logger.error(f"Error writing to InfluxDB for stream {stream_config.get('stream_id')}: {e}")
    
    def write_vital_signs_with_custom_tags(self, stream_config: Dict, reading: Dict, custom_tags: List[Dict]):
        """
        Write vital signs with additional custom tags from timeseries_binding_tag.
        """
        try:
            # Usar método base
            timestamp = reading['timestamp']
            measurement = stream_config.get('measurement', 'vital_signs')
            bucket = stream_config.get('influx_bucket', self.bucket)
            
            # Crear point base
            point = Point(measurement) \
                .tag("patient_id", stream_config['patient_id']) \
                .tag("device_id", stream_config['device_id']) \
                .tag("stream_id", stream_config['stream_id']) \
                .tag("org_id", stream_config.get('org_id') or "none") \
                .tag("signal_type", stream_config.get('signal_type_code', 'vital_signs'))
            
            # Agregar tags personalizados
            for tag in custom_tags:
                point = point.tag(tag['tag_key'], tag['tag_value'])
            
            # Agregar tags opcionales
            if stream_config.get('patient_name'):
                point = point.tag("patient_name", stream_config['patient_name'])
            if stream_config.get('risk_level_code'):
                point = point.tag("risk_level", stream_config['risk_level_code'])
            
            # Agregar fields
            point = point \
                .field("gps_longitude", reading['gps_longitude']) \
                .field("gps_latitude", reading['gps_latitude']) \
                .field("heart_rate", reading['heart_rate']) \
                .field("spo2", reading['spo2']) \
                .field("systolic_bp", reading['systolic_bp']) \
                .field("diastolic_bp", reading['diastolic_bp']) \
                .field("temperature", reading['temperature']) \
                .time(timestamp, WritePrecision.NS)
            
            self.write_api.write(bucket=bucket, org=stream_config.get('influx_org') or self.org, record=point)
            
        except Exception as e:
            logger.error(f"Error writing with custom tags: {e}")
```

---

#### Archivo: `services/realtime-data-generator/src/generator/worker.py`

**REEMPLAZAR método `_generate_and_send_data` (líneas ~55-70):**

```python
    def _generate_and_send_data(self):
        """Generate and send data for all active patient-device-stream configurations."""
        # Obtener configuraciones de streams desde PostgreSQL
        stream_configs = self.db_service.get_patient_device_streams()
        
        if not stream_configs:
            logger.warning("No active patient-device-stream configurations found")
            return
        
        count_success = 0
        count_skipped = 0
        
        for config in stream_configs:
            try:
                # Validar que tenga stream activo
                if not config.get('stream_id'):
                    count_skipped += 1
                    continue
                
                # Generar lectura de signos vitales
                patient_id = config['patient_id']
                reading = self.generator.generate_reading(patient_id)
                
                # Obtener tags personalizados si existen
                if config.get('binding_id'):
                    custom_tags = self.db_service.get_binding_tags(config['binding_id'])
                    if custom_tags:
                        self.influx_service.write_vital_signs_with_custom_tags(
                            config, reading, custom_tags
                        )
                    else:
                        self.influx_service.write_vital_signs(config, reading)
                else:
                    # Sin binding, no escribir
                    logger.debug(f"Skipping patient {patient_id} - no InfluxDB binding")
                    count_skipped += 1
                    continue
                
                count_success += 1
                
            except Exception as e:
                logger.error(f"Error processing stream {config.get('stream_id')}: {e}")
        
        logger.info(
            f"Data generation: {count_success} successful, {count_skipped} skipped, "
            f"{len(stream_configs)} total configurations"
        )
```

---

### 📁 **3. Actualizar Desktop App**

#### Archivo: `desktop-app/src/main/java/com/heartguard/desktop/api/InfluxDBService.java`

**AGREGAR en los Flux queries (líneas ~100, ~175):**

**CAMBIAR:**
```java
|> filter(fn: (r) => r["_measurement"] == "vital_signs")
|> filter(fn: (r) => r["patient_id"] == "%s")
```

**A:**
```java
|> filter(fn: (r) => r["_measurement"] == "vital_signs")
|> filter(fn: (r) => r["patient_id"] == "%s")
|> filter(fn: (r) => r["signal_type"] == "vital_signs")
```

Esto asegura que solo se lean signos vitales, no otros tipos de señales (ECG, EEG, etc.)

---

## 🗄️ Scripts SQL para Inicializar Datos de Prueba

### Script 1: Crear Dispositivos y Streams

```sql
-- 1. Insertar tipos de dispositivo si no existen
INSERT INTO heartguard.device_types (code, label) 
VALUES 
    ('vital_monitor', 'Monitor de Signos Vitales'),
    ('ecg_sensor', 'Sensor ECG'),
    ('oximeter', 'Oxímetro de Pulso')
ON CONFLICT (code) DO NOTHING;

-- 2. Insertar tipos de señal si no existen
INSERT INTO heartguard.signal_types (code, label)
VALUES
    ('vital_signs', 'Signos Vitales'),
    ('ecg', 'Electrocardiograma'),
    ('ppg', 'Fotopletismografía')
ON CONFLICT (code) DO NOTHING;

-- 3. Crear dispositivos de ejemplo para cada paciente activo
INSERT INTO heartguard.devices (org_id, serial, brand, model, device_type_id, owner_patient_id)
SELECT 
    p.org_id,
    'HG-' || UPPER(SUBSTRING(p.id::text, 1, 8)),
    'HeartGuard',
    'HG-2000',
    (SELECT id FROM heartguard.device_types WHERE code = 'vital_monitor' LIMIT 1),
    p.id
FROM heartguard.patients p
WHERE NOT EXISTS (
    SELECT 1 FROM heartguard.devices d WHERE d.owner_patient_id = p.id
)
LIMIT 10;

-- 4. Crear streams activos (sin ended_at) para cada paciente con dispositivo
INSERT INTO heartguard.signal_streams (patient_id, device_id, signal_type_id, sample_rate_hz, started_at)
SELECT 
    d.owner_patient_id,
    d.id,
    (SELECT id FROM heartguard.signal_types WHERE code = 'vital_signs' LIMIT 1),
    0.2,  -- 1 lectura cada 5 segundos
    NOW() - INTERVAL '1 hour'
FROM heartguard.devices d
WHERE d.owner_patient_id IS NOT NULL
  AND d.active = TRUE
  AND NOT EXISTS (
      SELECT 1 FROM heartguard.signal_streams ss 
      WHERE ss.device_id = d.id AND ss.ended_at IS NULL
  );

-- 5. Crear bindings de InfluxDB para cada stream
INSERT INTO heartguard.timeseries_binding (stream_id, influx_org, influx_bucket, measurement)
SELECT 
    ss.id,
    'heartguard',
    'timeseries',
    'vital_signs'
FROM heartguard.signal_streams ss
WHERE ss.ended_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM heartguard.timeseries_binding tb WHERE tb.stream_id = ss.id
  );

-- 6. Agregar tags personalizados de ejemplo
INSERT INTO heartguard.timeseries_binding_tag (binding_id, tag_key, tag_value)
SELECT 
    tb.id,
    'location',
    'hospital_main'
FROM heartguard.timeseries_binding tb
WHERE NOT EXISTS (
    SELECT 1 FROM heartguard.timeseries_binding_tag tbt 
    WHERE tbt.binding_id = tb.id AND tbt.tag_key = 'location'
)
LIMIT 5;
```

### Script 2: Verificar Configuración

```sql
-- Ver pacientes con sus dispositivos, streams y bindings
SELECT 
    p.person_name as patient,
    d.serial as device,
    dt.label as device_type,
    st.label as signal_type,
    ss.started_at,
    tb.measurement,
    tb.influx_bucket,
    COUNT(tbt.id) as custom_tags_count
FROM heartguard.patients p
JOIN heartguard.devices d ON d.owner_patient_id = p.id
JOIN heartguard.device_types dt ON d.device_type_id = dt.id
JOIN heartguard.signal_streams ss ON ss.patient_id = p.id AND ss.device_id = d.id
JOIN heartguard.signal_types st ON ss.signal_type_id = st.id
LEFT JOIN heartguard.timeseries_binding tb ON tb.stream_id = ss.id
LEFT JOIN heartguard.timeseries_binding_tag tbt ON tbt.binding_id = tb.id
WHERE ss.ended_at IS NULL
GROUP BY p.person_name, d.serial, dt.label, st.label, ss.started_at, tb.measurement, tb.influx_bucket
ORDER BY p.person_name;
```

---

## ✅ Checklist de Implementación

### Fase 1: Normalización
- [ ] Cambiar `patient_vitals` → `vital_signs` en user service
- [ ] Cambiar `body_temperature` → `temperature` en user service
- [ ] Agregar filtro `signal_type` en desktop app queries

### Fase 2: Base de Datos
- [ ] Ejecutar Script SQL 1 para crear dispositivos y streams
- [ ] Verificar con Script SQL 2 que todo está configurado
- [ ] Confirmar que hay al menos 5 pacientes con streams activos

### Fase 3: Actualizar Generador
- [ ] Agregar métodos `get_patient_device_streams()` y `get_binding_tags()` en `db.py`
- [ ] Reemplazar método `write_vital_signs()` en `influx.py`
- [ ] Agregar método `write_vital_signs_with_custom_tags()` en `influx.py`
- [ ] Actualizar `_generate_and_send_data()` en `worker.py`

### Fase 4: Pruebas
- [ ] Reiniciar servicio realtime-data-generator
- [ ] Verificar logs que digan "Data generation: X successful, Y skipped"
- [ ] Consultar InfluxDB con tags `stream_id` y `device_id`
- [ ] Verificar en desktop app que se muestran datos con nueva estructura

### Fase 5: Validación Final
- [ ] Confirmar que cada punto en InfluxDB tiene `stream_id`
- [ ] Confirmar que cada punto tiene `device_id`
- [ ] Confirmar que tags personalizados aparecen (ej: `location`)
- [ ] Verificar que desktop app puede leer y graficar datos

---

## 📊 Flujo de Datos Completo (Post-Implementación)

```
1. POSTGRESQL (Metadata)
   ↓
   patients (Juan Pérez) → ID: abc-123
   ↓
   devices (Monitor HG-2000) → ID: dev-456, serial: HG-ABC123
   ↓
   signal_streams (Stream activo) → ID: stream-789
   ↓
   timeseries_binding → bucket: timeseries, measurement: vital_signs
   ↓
   timeseries_binding_tag → location: "ICU-5", priority: "high"

2. REALTIME-DATA-GENERATOR
   ↓
   Consulta PostgreSQL → Obtiene config completa
   ↓
   Genera lectura → HR=72, SpO2=98, etc.
   ↓
   Escribe a InfluxDB con TODOS los tags

3. INFLUXDB (Datos)
   ↓
   vital_signs,
     patient_id=abc-123,
     device_id=dev-456,
     stream_id=stream-789,
     signal_type=vital_signs,
     location=ICU-5,
     priority=high
   heart_rate=72,spo2=98,temperature=36.5
   [timestamp]

4. DESKTOP APP / USER SERVICE
   ↓
   Query con filtros por patient_id + stream_id
   ↓
   Obtiene solo datos del stream correcto
   ↓
   Muestra gráficas actualizadas
```

---

## 🎯 Beneficios de la Implementación

1. ✅ **Trazabilidad**: Cada dato apunta a stream, dispositivo y paciente específico
2. ✅ **Flexibilidad**: Tags dinámicos desde PostgreSQL
3. ✅ **Multi-tenant**: Aislamiento por org_id
4. ✅ **Escalabilidad**: Múltiples dispositivos por paciente
5. ✅ **Auditoría**: Historial completo en signal_streams
6. ✅ **Normalización**: Measurement único (`vital_signs`)

---

## 🚨 Notas Importantes

- **No elimines datos existentes en InfluxDB**: Los nuevos datos tendrán más tags, pero los viejos seguirán funcionando
- **Reinicia el servicio realtime-data-generator** después de hacer cambios
- **Verifica logs** para confirmar que está escribiendo con stream_id
- **Los scripts SQL son idempotentes**: Puedes ejecutarlos múltiples veces

