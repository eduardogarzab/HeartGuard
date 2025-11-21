-- =========================================================
-- HeartGuard - Inicialización de datos para sincronización
-- InfluxDB-PostgreSQL
-- =========================================================
-- Este script crea los registros necesarios en PostgreSQL para
-- vincular los datos de InfluxDB con las tablas de metadatos.
--
-- Ejecutar con:
--   psql -U heartguard_app -d heartguard -f init_sync_data.sql

\connect heartguard
SET search_path = heartguard, public;

-- =========================================================
-- 1) Insertar tipos de dispositivos
-- =========================================================
INSERT INTO device_types (code, label) VALUES
  ('vital_monitor', 'Monitor de Signos Vitales'),
  ('ecg_sensor', 'Sensor ECG'),
  ('oximeter', 'Oxímetro de Pulso')
ON CONFLICT (code) DO NOTHING;

-- =========================================================
-- 2) Insertar tipos de señales
-- =========================================================
INSERT INTO signal_types (code, label) VALUES
  ('vital_signs', 'Signos Vitales'),
  ('ecg', 'Electrocardiograma'),
  ('ppg', 'Fotopletismografía')
ON CONFLICT (code) DO NOTHING;

-- =========================================================
-- 3) Crear dispositivos para cada paciente
-- =========================================================
-- Obtener el ID del tipo de dispositivo vital_monitor
DO $$
DECLARE
  v_device_type_id UUID;
  v_signal_type_id UUID;
  v_patient RECORD;
  v_device_id UUID;
  v_stream_id UUID;
  v_binding_id UUID;
  v_serial TEXT;
BEGIN
  -- Obtener IDs de catálogos
  SELECT id INTO v_device_type_id FROM device_types WHERE code = 'vital_monitor';
  SELECT id INTO v_signal_type_id FROM signal_types WHERE code = 'vital_signs';

  -- Para cada paciente existente
  FOR v_patient IN SELECT id, org_id, person_name FROM patients
  LOOP
    -- Generar serial único basado en el ID del paciente
    v_serial := 'HG-' || SUBSTRING(v_patient.id::TEXT, 1, 8);

    -- Verificar si ya existe un dispositivo para este paciente
    SELECT id INTO v_device_id 
    FROM devices 
    WHERE owner_patient_id = v_patient.id 
      AND device_type_id = v_device_type_id
    LIMIT 1;

    -- Si no existe, crear el dispositivo
    IF v_device_id IS NULL THEN
      INSERT INTO devices (
        org_id,
        serial,
        brand,
        model,
        device_type_id,
        owner_patient_id,
        active
      ) VALUES (
        v_patient.org_id,
        v_serial,
        'HeartGuard',
        'HG-2000',
        v_device_type_id,
        v_patient.id,
        TRUE
      ) RETURNING id INTO v_device_id;

      RAISE NOTICE 'Dispositivo creado: % para paciente %', v_serial, v_patient.person_name;
    ELSE
      RAISE NOTICE 'Dispositivo ya existe para paciente %', v_patient.person_name;
    END IF;

    -- Verificar si ya existe un stream activo
    SELECT id INTO v_stream_id
    FROM signal_streams
    WHERE patient_id = v_patient.id
      AND device_id = v_device_id
      AND signal_type_id = v_signal_type_id
      AND ended_at IS NULL
    LIMIT 1;

    -- Si no existe, crear el stream
    IF v_stream_id IS NULL THEN
      INSERT INTO signal_streams (
        patient_id,
        device_id,
        signal_type_id,
        sample_rate_hz,
        started_at,
        ended_at
      ) VALUES (
        v_patient.id,
        v_device_id,
        v_signal_type_id,
        1.0, -- 1 Hz (una lectura por segundo)
        NOW(),
        NULL -- Stream activo, sin fecha de finalización
      ) RETURNING id INTO v_stream_id;

      RAISE NOTICE 'Stream creado para paciente %', v_patient.person_name;
    ELSE
      RAISE NOTICE 'Stream ya existe para paciente %', v_patient.person_name;
    END IF;

    -- Verificar si ya existe el binding
    SELECT id INTO v_binding_id
    FROM timeseries_binding
    WHERE stream_id = v_stream_id
    LIMIT 1;

    -- Si no existe, crear el binding
    IF v_binding_id IS NULL THEN
      INSERT INTO timeseries_binding (
        stream_id,
        influx_org,
        influx_bucket,
        measurement,
        retention_hint
      ) VALUES (
        v_stream_id,
        'heartguard', -- Organización de InfluxDB
        'heartguard_bucket', -- Bucket de InfluxDB
        'vital_signs', -- Measurement normalizado
        '30d' -- Retención de 30 días
      ) RETURNING id INTO v_binding_id;

      RAISE NOTICE 'Binding creado para paciente %', v_patient.person_name;

      -- Agregar tags adicionales al binding
      INSERT INTO timeseries_binding_tag (binding_id, tag_key, tag_value) VALUES
        (v_binding_id, 'location', 'hospital_main'),
        (v_binding_id, 'signal_type', 'vital_signs');

      RAISE NOTICE 'Tags agregados para paciente %', v_patient.person_name;
    ELSE
      RAISE NOTICE 'Binding ya existe para paciente %', v_patient.person_name;
    END IF;

  END LOOP;

  RAISE NOTICE '✓ Sincronización completada exitosamente';
END $$;

-- =========================================================
-- 4) Verificar los resultados
-- =========================================================
-- Contar dispositivos creados
SELECT COUNT(*) AS total_devices FROM devices;

-- Contar streams activos
SELECT COUNT(*) AS total_active_streams 
FROM signal_streams 
WHERE ended_at IS NULL;

-- Contar bindings
SELECT COUNT(*) AS total_bindings FROM timeseries_binding;

-- Mostrar configuración completa de sincronización
SELECT 
  p.person_name AS paciente,
  p.email,
  d.serial AS dispositivo,
  d.model,
  st.label AS tipo_señal,
  ss.sample_rate_hz AS frecuencia_hz,
  tb.influx_bucket AS bucket,
  tb.measurement,
  ss.started_at AS stream_inicio,
  CASE WHEN ss.ended_at IS NULL THEN 'ACTIVO' ELSE 'FINALIZADO' END AS estado
FROM patients p
JOIN devices d ON d.owner_patient_id = p.id
JOIN signal_streams ss ON ss.patient_id = p.id AND ss.device_id = d.id
JOIN signal_types st ON st.id = ss.signal_type_id
JOIN timeseries_binding tb ON tb.stream_id = ss.id
ORDER BY p.person_name;

-- =========================================================
-- 5) Query de validación para el generador
-- =========================================================
-- Esta query muestra todos los datos que el generador necesita
SELECT 
  p.id AS patient_id,
  p.person_name AS patient_name,
  p.email AS patient_email,
  p.org_id,
  o.name AS org_name,
  rl.code AS risk_level_code,
  d.id AS device_id,
  d.serial AS device_serial,
  ss.id AS stream_id,
  st.code AS signal_type_code,
  tb.id AS binding_id,
  tb.influx_org,
  tb.influx_bucket,
  tb.measurement,
  tb.retention_hint,
  COALESCE(
    json_object_agg(tbt.tag_key, tbt.tag_value) 
    FILTER (WHERE tbt.tag_key IS NOT NULL),
    '{}'::json
  ) AS custom_tags
FROM patients p
LEFT JOIN organizations o ON o.id = p.org_id
LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
JOIN devices d ON d.owner_patient_id = p.id AND d.active = TRUE
JOIN signal_streams ss ON ss.patient_id = p.id AND ss.device_id = d.id AND ss.ended_at IS NULL
JOIN signal_types st ON st.id = ss.signal_type_id
JOIN timeseries_binding tb ON tb.stream_id = ss.id
LEFT JOIN timeseries_binding_tag tbt ON tbt.binding_id = tb.id
GROUP BY 
  p.id, p.person_name, p.email, p.org_id, o.name, rl.code,
  d.id, d.serial, ss.id, st.code,
  tb.id, tb.influx_org, tb.influx_bucket, tb.measurement, tb.retention_hint
ORDER BY p.person_name;
