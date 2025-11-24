# Trigger: Reasignación Automática de Dispositivos

## Descripción

Trigger automático que se ejecuta cuando se cambia el `owner_patient_id` de un dispositivo. Automatiza el proceso de reasignación para que el dispositivo deje de generar datos para el paciente anterior y empiece a generar para el nuevo.

## Funcionamiento

Cuando se ejecuta un `UPDATE` en `devices.owner_patient_id`:

1. **Termina streams activos**: Todos los `signal_streams` activos del dispositivo reciben `ended_at = NOW()`
2. **Replica configuración**: Copia `measurement`, `influx_bucket`, `influx_org` del stream anterior
3. **Crea nuevo stream**: Inserta en `signal_streams` con el nuevo `patient_id`
4. **Crea binding**: Inserta en `timeseries_binding` con la configuración replicada
5. **Log**: Emite `NOTICE` con detalles de la reasignación

## Valores por Defecto

Si no existe stream anterior:
- `measurement`: `vital_signs`
- `influx_bucket`: `timeseries`
- `influx_org`: `heartguard`
- `signal_type_id`: Busca `HR`, si no existe usa el primero disponible

## Uso

```sql
-- Reasignar dispositivo a otro paciente
UPDATE devices 
SET owner_patient_id = '8c9436b4-f085-405f-a3d2-87cb1d1cf097'
WHERE serial = 'HG-ECG-001';

-- El trigger se ejecuta automáticamente y emite:
-- NOTICE: Device HG-ECG-001 reassigned: stream <uuid> created for patient <uuid>
```

## Verificación

```sql
-- Ver historial de streams del dispositivo
SELECT 
    ss.id as stream_id,
    p.person_name as patient,
    st.code as signal,
    tb.measurement,
    ss.started_at,
    ss.ended_at,
    CASE WHEN ss.ended_at IS NULL THEN 'ACTIVO' ELSE 'TERMINADO' END as status
FROM signal_streams ss
JOIN patients p ON p.id = ss.patient_id
JOIN signal_types st ON st.id = ss.signal_type_id
LEFT JOIN timeseries_binding tb ON tb.stream_id = ss.id
WHERE ss.device_id = (SELECT id FROM devices WHERE serial = 'HG-ECG-001')
ORDER BY ss.started_at DESC;
```

## Reinicio del Generador

El `realtime-data-generator` detecta automáticamente los nuevos streams cada 5 segundos. Si quieres que tome efecto inmediatamente:

```bash
cd /root/HeartGuard/services
make restart-realtime
```

## Archivos Relacionados

- **Función trigger**: `heartguard.reassign_device_stream()`
- **Trigger**: `device_reassignment_trigger` ON `heartguard.devices`
- **Generador**: `services/realtime-data-generator/src/generator/db.py`

## Ejemplo Completo

```sql
-- Estado inicial: HG-ECG-001 asignado a Valeria
SELECT serial, 
       (SELECT person_name FROM patients WHERE id = owner_patient_id) as owner,
       (SELECT COUNT(*) FROM signal_streams WHERE device_id = devices.id AND ended_at IS NULL) as active_streams
FROM devices WHERE serial = 'HG-ECG-001';
-- Resultado: HG-ECG-001 | Valeria Ortiz | 1

-- Reasignar a María
UPDATE devices 
SET owner_patient_id = '8c9436b4-f085-405f-a3d2-87cb1d1cf097'
WHERE serial = 'HG-ECG-001';
-- NOTICE: Device HG-ECG-001 reassigned: stream ab0eef70-... created for patient 8c9436b4-...

-- Verificar cambio
SELECT serial, 
       (SELECT person_name FROM patients WHERE id = owner_patient_id) as owner,
       (SELECT COUNT(*) FROM signal_streams WHERE device_id = devices.id AND ended_at IS NULL) as active_streams
FROM devices WHERE serial = 'HG-ECG-001';
-- Resultado: HG-ECG-001 | María Delgado | 1

-- El generador ahora envía datos a InfluxDB con patient_id de María
```

## Notas Importantes

1. **Solo se activa con `owner_patient_id`**: El trigger solo se ejecuta si cambia `owner_patient_id`, no otros campos
2. **NULL no dispara**: Si se asigna `NULL` a `owner_patient_id`, el trigger no crea un nuevo stream (solo termina el anterior si existe)
3. **Idempotente**: Si se ejecuta el mismo UPDATE múltiples veces, no crea streams duplicados
4. **Transaccional**: Si falla alguna operación, se hace rollback completo
5. **Sin reinicio necesario**: El generador detecta automáticamente los cambios en 5 segundos

## Instalación

Si necesitas reinstalar el trigger:

```bash
PGPASSWORD='postgres123' psql -h 134.199.204.58 -U postgres -d heartguard -f /root/HeartGuard/db/trigger_device_reassignment.sql
```

## Desinstalación

```sql
DROP TRIGGER IF EXISTS device_reassignment_trigger ON heartguard.devices;
DROP FUNCTION IF EXISTS heartguard.reassign_device_stream();
```
