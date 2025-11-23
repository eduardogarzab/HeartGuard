# Cambios de Arquitectura - Desktop App

## Fecha: 2025-11-23

## Problema Original
El desktop app se conectaba **directamente** a InfluxDB (puerto 8086), violando la arquitectura de microservicios:
```
Desktop App → InfluxDB (puerto 8086) ❌ INCORRECTO
```

## Solución Implementada
Ahora el desktop app se comunica **solo con el gateway**, que enruta las peticiones al servicio correspondiente:
```
Desktop App → Gateway (puerto 8080) → Realtime Service (puerto 5006) → InfluxDB ✅ CORRECTO
```

## Cambios Realizados

### 1. Backend - Realtime Data Generator Service
**Archivo:** `services/realtime-data-generator/src/generator/influx.py`
- ✅ Agregado método `query_patient_vital_signs()` para consultar datos de InfluxDB
- ✅ Soporta filtros por `patient_id`, `device_id` (opcional), y `limit`
- ✅ Retorna datos en formato JSON compatible con el desktop app

**Archivo:** `services/realtime-data-generator/src/generator/app.py`
- ✅ Agregado endpoint: `GET /patients/{patient_id}/vital-signs`
- ✅ Query parameters: `device_id`, `limit`, `measurement`
- ✅ Respuesta JSON con estructura:
  ```json
  {
    "patient_id": "uuid",
    "device_id": "uuid",
    "count": 10,
    "readings": [
      {
        "timestamp": "2025-11-23T...",
        "heart_rate": 72,
        "spo2": 98,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "temperature": 36.5
      }
    ]
  }
  ```

### 2. Backend - Gateway Service
**Archivo:** `services/gateway/src/gateway/routes/realtime_proxy.py`
- ✅ Agregado proxy endpoint: `GET /realtime/patients/{patient_id}/vital-signs`
- ✅ Reenvía peticiones al servicio realtime-data-generator
- ✅ Soporta todos los query parameters del servicio upstream

### 3. Frontend - Desktop App (Java)

#### 3.1. ApiClient.java
**Archivo:** `desktop-app/src/main/java/com/heartguard/desktop/api/ApiClient.java`
- ✅ Agregado método: `getPatientVitalSigns(patientId, deviceId, limit)`
- ✅ Consume endpoint: `GET /realtime/patients/{patientId}/vital-signs`
- ✅ Retorna `JsonObject` con los datos de signos vitales

#### 3.2. VitalSignsChartPanel.java
**Archivo:** `desktop-app/src/main/java/com/heartguard/desktop/ui/user/VitalSignsChartPanel.java`
- ✅ **ELIMINADO**: Dependency de `InfluxDBService`
- ✅ **AGREGADO**: Dependency de `ApiClient`
- ✅ Constructor ahora recibe `ApiClient` en lugar de `InfluxDBService`
- ✅ Agregado método `parseVitalSignsFromJson()` para parsear respuesta del gateway
- ✅ Agregada clase interna `VitalSignsReading` (antes venía de InfluxDBService)
- ✅ `loadInitialData()` y `startAutoUpdate()` ahora usan `apiClient.getPatientVitalSigns()`

#### 3.3. PatientDetailDialog.java
**Archivo:** `desktop-app/src/main/java/com/heartguard/desktop/ui/user/PatientDetailDialog.java`
- ✅ **ELIMINADO**: Creación de `InfluxDBService` en constructor
- ✅ **ELIMINADO**: Imports relacionados con InfluxDB
- ✅ Constructor de `VitalSignsChartPanel` ahora pasa `apiClient` en lugar de `influxService`

#### 3.4. AppConfig.java
**Archivo:** `desktop-app/src/main/java/com/heartguard/desktop/config/AppConfig.java`
- ✅ **ELIMINADO**: Variables `influxdbUrl`, `influxdbToken`, `influxdbOrg`, `influxdbBucket`
- ✅ **ELIMINADO**: Métodos getters de InfluxDB
- ✅ **ELIMINADO**: Validación de configuración de InfluxDB
- ✅ **SIMPLIFICADO**: Solo mantiene `gatewayBaseUrl`
- ✅ Comentario agregado explicando que todo va a través del gateway

#### 3.5. .env
**Archivo:** `desktop-app/.env`
- ✅ **ELIMINADO**: Variables `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`
- ✅ **MANTENIDO**: `GATEWAY_BASE_URL=http://129.212.181.53:8080`
- ✅ Comentario agregado explicando arquitectura correcta

## Beneficios de los Cambios

### 1. Seguridad
- ❌ Antes: Puerto 8086 de InfluxDB necesitaba estar abierto públicamente
- ✅ Ahora: Solo puerto 8080 del gateway es público
- ✅ InfluxDB solo accesible desde red interna del servidor

### 2. Arquitectura Limpia
- ✅ Desktop app NO conoce detalles de implementación interna (InfluxDB)
- ✅ Toda comunicación pasa por gateway → microservicios
- ✅ Facilita cambios futuros (migración de InfluxDB a otro DB)

### 3. Mantenibilidad
- ✅ Desktop app solo necesita conocer URL del gateway
- ✅ Un solo punto de configuración (.env con GATEWAY_BASE_URL)
- ✅ No necesita tokens de InfluxDB en el cliente

### 4. Escalabilidad
- ✅ Gateway puede implementar rate limiting, caching, load balancing
- ✅ Servicio realtime puede escalar independientemente
- ✅ Posibilidad de agregar autenticación/autorización en gateway

## Testing

### Endpoint Backend
```bash
# Probar endpoint directamente en realtime service
curl http://localhost:5006/patients/8c9436b4-f085-405f-a3d2-87cb1d1cf097/vital-signs?device_id=4e15150a-77dd-4143-9dcf-3357fcd8fc86&limit=10

# Probar a través del gateway
curl http://129.212.181.53:8080/realtime/patients/8c9436b4-f085-405f-a3d2-87cb1d1cf097/vital-signs?device_id=4e15150a-77dd-4143-9dcf-3357fcd8fc86&limit=10
```

### Desktop App
1. Hacer `git pull` en Windows
2. Actualizar `.env` (eliminar variables de InfluxDB)
3. Compilar: `mvn clean package -DskipTests`
4. Ejecutar y abrir detalle de paciente con dispositivos
5. Verificar que las gráficas cargan datos reales (no mock)
6. Verificar que NO aparece mensaje "Datos de demostración (InfluxDB no accesible)"

## Migración para Otros Desarrolladores

### Paso 1: Actualizar código
```bash
git pull origin sync-influx-and-postgresql
```

### Paso 2: Actualizar .env
Eliminar estas líneas de `desktop-app/.env`:
```
INFLUXDB_URL=http://134.199.204.58:8086
INFLUXDB_TOKEN=heartguard-dev-token-change-me
INFLUXDB_ORG=heartguard
INFLUXDB_BUCKET=timeseries
```

Mantener solo:
```
JXBROWSER_LICENSE_KEY=your_license_key_here
GATEWAY_BASE_URL=http://129.212.181.53:8080
```

### Paso 3: Recompilar
```bash
cd desktop-app
mvn clean package -DskipTests
```

### Paso 4: Reiniciar servicios backend (si tienes acceso al servidor)
```bash
# Reiniciar realtime-data-generator
cd /root/HeartGuard/services/realtime-data-generator
make restart

# Reiniciar gateway
cd /root/HeartGuard/services/gateway
make dev  # o el comando que uses para iniciar
```

## Notas Importantes

1. **No abrir puerto 8086**: InfluxDB debe permanecer en red interna
2. **Gateway como único punto de entrada**: Todo tráfico externo → gateway:8080
3. **Tokens de InfluxDB**: Solo necesarios en el backend (realtime service), NO en desktop app
4. **Compatibilidad hacia atrás**: InfluxDBService.java aún existe en el proyecto pero ya NO se usa

## Diagrama de Flujo

### Antes ❌
```
┌─────────────┐
│ Desktop App │
└──────┬──────┘
       │
       │ Direct Connection
       │ Port 8086
       │
       ▼
┌─────────────┐
│  InfluxDB   │
└─────────────┘
```

### Ahora ✅
```
┌─────────────┐
│ Desktop App │
└──────┬──────┘
       │
       │ HTTP Request
       │ Port 8080
       │
       ▼
┌─────────────┐      Internal Network      ┌──────────────────┐
│   Gateway   │──────────────────────────▶│ Realtime Service │
└─────────────┘     Port 5006              └────────┬─────────┘
                                                    │
                                                    │ Query
                                                    │
                                                    ▼
                                           ┌─────────────┐
                                           │  InfluxDB   │
                                           └─────────────┘
```

## Contacto
Para preguntas sobre estos cambios, contactar al equipo de desarrollo.
