# Guía Rápida de Deployment - Sincronización InfluxDB-PostgreSQL

## ⚡ Inicio Rápido (5 minutos)

### Paso 1: Iniciar Docker (30 segundos)
```powershell
cd C:\Users\mendo\Downloads\code\UDEM\integracion\HeartGuard
docker-compose up -d postgres influxdb redis
docker ps  # Verificar que estén corriendo
```

### Paso 2: Ejecutar SQL (1 minuto)
```powershell
# Opción A: Desde Docker (recomendado)
Get-Content .\db\init_sync_data.sql | docker exec -i heartguard-postgres psql -U heartguard_app -d heartguard

# Opción B: Con psql local
psql -h localhost -U heartguard_app -d heartguard -f db\init_sync_data.sql
```

### Paso 3: Verificar Datos (30 segundos)
```sql
-- Conectar
docker exec -it heartguard-postgres psql -U heartguard_app -d heartguard

-- Verificar
SELECT COUNT(*) FROM heartguard.devices;
SELECT COUNT(*) FROM heartguard.signal_streams WHERE ended_at IS NULL;
```

### Paso 4: Reiniciar Generador (1 minuto)
```powershell
cd services\realtime-data-generator
docker-compose restart realtime-data-generator

# Ver logs
docker logs -f heartguard-realtime-generator
```

### Paso 5: Verificar InfluxDB (2 minutos)
```powershell
docker exec -it heartguard-influxdb influx
```
```flux
from(bucket: "heartguard_bucket")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
  |> limit(n: 1)
  |> yield(name: "check")
```

**Buscar en resultado:**
- ✅ `device_id` tag presente
- ✅ `stream_id` tag presente
- ✅ `location` tag presente

---

## 🔍 Comandos de Verificación Rápida

### PostgreSQL - Ver Configuración Completa
```sql
SELECT 
  p.person_name AS paciente,
  d.serial AS dispositivo,
  ss.id::text AS stream_id,
  tb.measurement,
  tb.influx_bucket
FROM heartguard.patients p
JOIN heartguard.devices d ON d.owner_patient_id = p.id
JOIN heartguard.signal_streams ss ON ss.device_id = d.id AND ss.ended_at IS NULL
JOIN heartguard.timeseries_binding tb ON tb.stream_id = ss.id
LIMIT 5;
```

### InfluxDB - Verificar Tags
```flux
from(bucket: "heartguard_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
  |> keep(columns: ["_time", "patient_id", "device_id", "stream_id", "heart_rate"])
  |> limit(n: 5)
```

### Docker - Ver Logs del Generador
```powershell
docker logs --tail 50 -f heartguard-realtime-generator
```

**Mensaje esperado:**
```
Data generation: 5 successful, 0 skipped (total streams: 5)
```

---

## ❌ Troubleshooting Rápido

### Error: "No stream configurations found"
```sql
-- Verificar si existen streams
SELECT COUNT(*) FROM heartguard.signal_streams WHERE ended_at IS NULL;
-- Si es 0: Ejecutar init_sync_data.sql de nuevo
```

### Error: device_id/stream_id no en InfluxDB
```powershell
# Reiniciar el generador
docker restart heartguard-realtime-generator
docker logs --tail 20 heartguard-realtime-generator
```

### Error: "Connection refused" a PostgreSQL
```powershell
docker ps | Select-String postgres
# Si no está corriendo:
docker-compose up -d postgres
```

### Error: "Connection refused" a InfluxDB
```powershell
docker ps | Select-String influx
# Si no está corriendo:
docker-compose up -d influxdb
```

---

## 📊 Monitoreo en Tiempo Real

### Terminal 1 - Logs del Generador
```powershell
docker logs -f heartguard-realtime-generator
```

### Terminal 2 - Consulta PostgreSQL
```powershell
docker exec -it heartguard-postgres psql -U heartguard_app -d heartguard
```
```sql
-- Ver última actividad
SELECT 
  p.person_name,
  d.serial,
  ss.started_at,
  EXTRACT(EPOCH FROM (NOW() - ss.started_at)) AS segundos_activo
FROM heartguard.patients p
JOIN heartguard.devices d ON d.owner_patient_id = p.id
JOIN heartguard.signal_streams ss ON ss.device_id = d.id AND ss.ended_at IS NULL
ORDER BY ss.started_at DESC;
```

### Terminal 3 - Consulta InfluxDB
```powershell
docker exec -it heartguard-influxdb influx
```
```flux
from(bucket: "heartguard_bucket")
  |> range(start: -1m)
  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
  |> group(columns: ["patient_name"])
  |> count()
```

---

## 🎯 Validación Exitosa

✅ **PostgreSQL tiene:**
- Dispositivos creados (tabla `devices`)
- Streams activos (tabla `signal_streams` con `ended_at IS NULL`)
- Bindings configurados (tabla `timeseries_binding`)

✅ **Generador muestra:**
```
Retrieved X stream configurations from database
Data generation: X successful, 0 skipped
```

✅ **InfluxDB contiene:**
- Tags: `device_id`, `stream_id`, `patient_id`, `org_id`, `signal_type`, `location`
- Fields: `heart_rate`, `spo2`, `systolic_bp`, `diastolic_bp`, `temperature`
- Measurement: `vital_signs`

---

## 📁 Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `db/init_sync_data.sql` | Script SQL de inicialización |
| `services/realtime-data-generator/src/generator/db.py` | Nuevos métodos de consulta |
| `services/realtime-data-generator/src/generator/influx.py` | Escritura con stream config |
| `services/realtime-data-generator/src/generator/worker.py` | Loop principal actualizado |
| `IMPLEMENTACION_SYNC_COMPLETADA.md` | Documentación completa |

---

## 🆘 Ayuda Rápida

**Base de datos no inicia:**
```powershell
docker-compose down
docker-compose up -d postgres influxdb redis
```

**Quiero empezar de cero:**
```powershell
docker-compose down -v  # CUIDADO: Borra todos los datos
docker-compose up -d
# Ejecutar init.sql y init_sync_data.sql de nuevo
```

**Ver todos los contenedores:**
```powershell
docker ps -a
```

**Ver uso de recursos:**
```powershell
docker stats
```

---

## ✨ Resultado Final

Cada punto de datos en InfluxDB ahora incluye:

```json
{
  "measurement": "vital_signs",
  "tags": {
    "patient_id": "abc-123",
    "patient_name": "Juan Pérez",
    "device_id": "device-456",        // ⭐ NUEVO
    "stream_id": "stream-789",        // ⭐ NUEVO
    "org_id": "org-xyz",
    "signal_type": "vital_signs",     // ⭐ NUEVO
    "risk_level": "medium",
    "location": "hospital_main"       // ⭐ NUEVO (tag personalizado)
  },
  "fields": {
    "heart_rate": 72,
    "spo2": 98,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "temperature": 36.5,
    "gps_latitude": 25.6866,
    "gps_longitude": -100.3161
  },
  "timestamp": "2025-11-20T10:30:00Z"
}
```

**¡Listo para producción! 🚀**
