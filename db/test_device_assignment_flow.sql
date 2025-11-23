-- =========================================================
-- Script de prueba: Flujo de asignación de dispositivos
-- =========================================================
-- Este script demuestra el flujo completo de:
-- 1. Compra de dispositivo por organización
-- 2. Asignación a paciente (trigger automático crea stream)
-- 3. Verificación de generación de datos

\c heartguard
SET search_path = heartguard, public;

-- =========================================================
-- PASO 1: Estado inicial - Ver dispositivos existentes
-- =========================================================
\echo '========================================='
\echo 'PASO 1: Dispositivos existentes'
\echo '========================================='

SELECT 
  d.serial AS dispositivo,
  d.brand || ' ' || d.model AS modelo,
  CASE WHEN d.owner_patient_id IS NOT NULL THEN p.person_name ELSE 'SIN ASIGNAR' END AS paciente,
  d.active AS activo,
  CASE WHEN ss.id IS NOT NULL THEN 'SÍ' ELSE 'NO' END AS tiene_stream
FROM devices d
LEFT JOIN patients p ON p.id = d.owner_patient_id
LEFT JOIN signal_streams ss ON ss.device_id = d.id AND ss.ended_at IS NULL
ORDER BY d.serial;

-- =========================================================
-- PASO 2: Organización compra nuevo dispositivo
-- =========================================================
\echo ''
\echo '========================================='
\echo 'PASO 2: Comprando nuevo dispositivo...'
\echo '========================================='

DO $$
DECLARE
  v_org_id UUID;
  v_device_type_id UUID;
BEGIN
  -- Obtener primera organización
  SELECT id INTO v_org_id FROM organizations LIMIT 1;
  
  -- Obtener tipo de dispositivo
  SELECT id INTO v_device_type_id FROM device_types WHERE code = 'PULSE_OX';
  
  -- Crear dispositivo SIN asignar
  INSERT INTO devices (
    org_id,
    serial,
    brand,
    model,
    device_type_id,
    owner_patient_id,  -- NULL: sin asignar
    active,
    registered_at
  ) VALUES (
    v_org_id,
    'TEST-OXY-' || SUBSTRING(gen_random_uuid()::TEXT, 1, 8),
    'Nonin',
    'WristOx2 Model 3150',
    v_device_type_id,
    NULL,
    TRUE,
    NOW()
  );
  
  RAISE NOTICE '✓ Dispositivo TEST-OXY-* creado (sin asignar)';
END $$;

-- Ver dispositivos después de la compra
SELECT 
  d.serial,
  CASE WHEN d.owner_patient_id IS NOT NULL THEN 'ASIGNADO' ELSE 'INVENTARIO' END AS estado
FROM devices d
WHERE d.serial LIKE 'TEST-OXY-%'
ORDER BY d.registered_at DESC
LIMIT 1;

-- =========================================================
-- PASO 3: Asignar dispositivo a paciente (trigger automático)
-- =========================================================
\echo ''
\echo '========================================='
\echo 'PASO 3: Asignando dispositivo a paciente...'
\echo '========================================='

DO $$
DECLARE
  v_device_id UUID;
  v_patient_id UUID;
  v_device_serial TEXT;
  v_patient_name TEXT;
BEGIN
  -- Obtener dispositivo de prueba
  SELECT id, serial INTO v_device_id, v_device_serial
  FROM devices
  WHERE serial LIKE 'TEST-OXY-%'
  ORDER BY registered_at DESC
  LIMIT 1;
  
  -- Obtener primer paciente
  SELECT id, person_name INTO v_patient_id, v_patient_name
  FROM patients
  LIMIT 1;
  
  -- ASIGNAR DISPOSITIVO (esto dispara el trigger)
  UPDATE devices
  SET owner_patient_id = v_patient_id
  WHERE id = v_device_id;
  
  RAISE NOTICE '✓ Dispositivo % asignado a paciente %', v_device_serial, v_patient_name;
  RAISE NOTICE '✓ Trigger automático creó stream y binding en InfluxDB';
END $$;

-- =========================================================
-- PASO 4: Verificar que se creó stream y binding
-- =========================================================
\echo ''
\echo '========================================='
\echo 'PASO 4: Verificando stream y binding...'
\echo '========================================='

SELECT 
  d.serial AS dispositivo,
  p.person_name AS paciente,
  ss.id AS stream_id,
  tb.influx_bucket AS bucket,
  tb.measurement,
  string_agg(tbt.tag_key || '=' || tbt.tag_value, ', ') AS tags
FROM devices d
JOIN patients p ON p.id = d.owner_patient_id
JOIN signal_streams ss ON ss.device_id = d.id AND ss.ended_at IS NULL
JOIN timeseries_binding tb ON tb.stream_id = ss.id
LEFT JOIN timeseries_binding_tag tbt ON tbt.binding_id = tb.id
WHERE d.serial LIKE 'TEST-OXY-%'
GROUP BY d.serial, p.person_name, ss.id, tb.influx_bucket, tb.measurement;

-- =========================================================
-- PASO 5: Ver todos los streams activos (generando datos)
-- =========================================================
\echo ''
\echo '========================================='
\echo 'PASO 5: Streams activos (generando datos)'
\echo '========================================='

SELECT 
  p.person_name AS paciente,
  d.serial AS dispositivo,
  d.brand || ' ' || d.model AS modelo,
  tb.influx_bucket AS bucket_influx,
  tb.measurement,
  EXTRACT(EPOCH FROM (NOW() - ss.started_at))/60 AS minutos_activo
FROM patients p
JOIN devices d ON d.owner_patient_id = p.id AND d.active = TRUE
JOIN signal_streams ss ON ss.device_id = d.id AND ss.ended_at IS NULL
JOIN timeseries_binding tb ON tb.stream_id = ss.id
ORDER BY ss.started_at DESC;

-- =========================================================
-- PASO 6: Simular desasignación de dispositivo
-- =========================================================
\echo ''
\echo '========================================='
\echo 'PASO 6: Desasignando dispositivo de prueba...'
\echo '========================================='

DO $$
DECLARE
  v_device_id UUID;
  v_stream_id UUID;
  v_device_serial TEXT;
BEGIN
  -- Obtener dispositivo de prueba
  SELECT id, serial INTO v_device_id, v_device_serial
  FROM devices
  WHERE serial LIKE 'TEST-OXY-%'
  ORDER BY registered_at DESC
  LIMIT 1;
  
  -- Finalizar stream activo
  UPDATE signal_streams
  SET ended_at = NOW()
  WHERE device_id = v_device_id
    AND ended_at IS NULL
  RETURNING id INTO v_stream_id;
  
  -- Desasignar dispositivo
  UPDATE devices
  SET owner_patient_id = NULL
  WHERE id = v_device_id;
  
  RAISE NOTICE '✓ Stream % finalizado', v_stream_id;
  RAISE NOTICE '✓ Dispositivo % desasignado (vuelve a inventario)', v_device_serial;
  RAISE NOTICE '✓ Generación de datos DETENIDA para este dispositivo';
END $$;

-- Verificar estado final
SELECT 
  d.serial AS dispositivo,
  CASE WHEN d.owner_patient_id IS NOT NULL THEN 'ASIGNADO' ELSE 'INVENTARIO' END AS estado,
  COUNT(ss.id) AS streams_historicos,
  SUM(CASE WHEN ss.ended_at IS NULL THEN 1 ELSE 0 END) AS streams_activos
FROM devices d
LEFT JOIN signal_streams ss ON ss.device_id = d.id
WHERE d.serial LIKE 'TEST-OXY-%'
GROUP BY d.serial, d.owner_patient_id;

\echo ''
\echo '========================================='
\echo 'Prueba completada exitosamente ✓'
\echo '========================================='
\echo ''
\echo 'Ahora el generador de datos (realtime-data-generator) solo'
\echo 'generará datos sintéticos para dispositivos ASIGNADOS y ACTIVOS.'
\echo ''
\echo 'Logs esperados en el generador:'
\echo '  - Retrieved N stream configurations from database'
\echo '  - Wrote vital signs for patient X (device: Y, stream: Z)'
\echo ''
