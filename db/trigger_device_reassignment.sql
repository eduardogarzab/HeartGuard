-- =========================================================
-- Trigger: Reasignación Automática de Dispositivos
-- =========================================================
-- Ejecutar con: PGPASSWORD='postgres123' psql -h 134.199.204.58 -U postgres -d heartguard -f trigger_device_reassignment.sql

-- Función que se ejecuta cuando cambia owner_patient_id
CREATE OR REPLACE FUNCTION heartguard.reassign_device_stream()
RETURNS TRIGGER AS $$
DECLARE
    v_signal_type_id UUID;
    v_new_stream_id UUID;
    v_old_measurement TEXT;
    v_old_bucket TEXT;
    v_old_org TEXT;
BEGIN
    -- Solo actuar si cambió el owner_patient_id y no es NULL
    IF NEW.owner_patient_id IS DISTINCT FROM OLD.owner_patient_id 
       AND NEW.owner_patient_id IS NOT NULL THEN
        
        -- Obtener el measurement del stream anterior para replicarlo
        SELECT tb.measurement, tb.influx_bucket, tb.influx_org
        INTO v_old_measurement, v_old_bucket, v_old_org
        FROM heartguard.signal_streams ss
        JOIN heartguard.timeseries_binding tb ON tb.stream_id = ss.id
        WHERE ss.device_id = NEW.id 
          AND ss.ended_at IS NULL
        LIMIT 1;
        
        -- Si no hay stream anterior, usar valores por defecto
        IF v_old_measurement IS NULL THEN
            v_old_measurement := 'vital_signs';
            v_old_bucket := 'timeseries';
            v_old_org := 'heartguard';
        END IF;
        
        -- Terminar todos los streams activos del dispositivo
        UPDATE heartguard.signal_streams 
        SET ended_at = NOW()
        WHERE device_id = NEW.id 
          AND ended_at IS NULL;
        
        -- Obtener el signal_type_id del stream anterior o usar el primero disponible
        SELECT ss.signal_type_id INTO v_signal_type_id
        FROM heartguard.signal_streams ss
        WHERE ss.device_id = NEW.id
        ORDER BY ss.started_at DESC
        LIMIT 1;
        
        -- Si no hay signal_type previo, buscar uno por defecto (HR o el primero)
        IF v_signal_type_id IS NULL THEN
            SELECT id INTO v_signal_type_id
            FROM heartguard.signal_types
            WHERE code = 'HR'
            LIMIT 1;
            
            IF v_signal_type_id IS NULL THEN
                SELECT id INTO v_signal_type_id
                FROM heartguard.signal_types
                LIMIT 1;
            END IF;
        END IF;
        
        -- Crear nuevo stream para el nuevo owner
        INSERT INTO heartguard.signal_streams (device_id, patient_id, signal_type_id, started_at)
        VALUES (NEW.id, NEW.owner_patient_id, v_signal_type_id, NOW())
        RETURNING id INTO v_new_stream_id;
        
        -- Crear timeseries_binding para el nuevo stream
        INSERT INTO heartguard.timeseries_binding (stream_id, influx_bucket, influx_org, measurement)
        VALUES (v_new_stream_id, v_old_bucket, v_old_org, v_old_measurement);
        
        RAISE NOTICE 'Device % reassigned: stream % created for patient %', 
            NEW.serial, v_new_stream_id, NEW.owner_patient_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger (elimina el anterior si existe)
DROP TRIGGER IF EXISTS device_reassignment_trigger ON heartguard.devices;
CREATE TRIGGER device_reassignment_trigger
    AFTER UPDATE OF owner_patient_id ON heartguard.devices
    FOR EACH ROW
    EXECUTE FUNCTION heartguard.reassign_device_stream();

-- Confirmar creación
SELECT 'Trigger device_reassignment_trigger creado correctamente' as status;
