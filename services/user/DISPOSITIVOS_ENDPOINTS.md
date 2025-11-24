# Endpoints de Dispositivos - Correcciones

## Problema Original

El tab de dispositivos en la organización tenía varios problemas:

1. **Filtrado incorrecto por care_team**: Los dispositivos pertenecen a la **organización**, no a equipos de cuidado
2. **Estado "desconectado" incorrecto**: Todos los dispositivos aparecían como desconectados cuando en realidad estaban activos
3. **Paciente asignado único**: Un dispositivo puede tener múltiples `signal_streams` con diferentes pacientes a lo largo del tiempo

## Solución Implementada

### Nuevos Endpoints (Nivel Organización)

#### 1. Listar Dispositivos de Organización
```
GET /orgs/{org_id}/devices
```

**Query Parameters:**
- `active` (boolean): Filtrar por dispositivos activos/inactivos
- `connected` (boolean): Filtrar por dispositivos con stream activo
- `patient_id` (UUID): Filtrar por paciente propietario
- `limit` (int): Máximo de resultados (default: 200, max: 500)
- `offset` (int): Offset para paginación

**Ejemplo:**
```bash
GET /orgs/d3fc1b0c-f94b-416c-8dca-4cd1a6d4a4c7/devices?active=true&connected=true
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "organization": {
      "id": "d3fc1b0c-f94b-416c-8dca-4cd1a6d4a4c7",
      "name": "Familia García",
      "role": "admin"
    },
    "devices": [
      {
        "id": "1ec46655-ba0c-4e2a-b315-dc6bbcbeda7d",
        "serial": "HG-ECG-001",
        "brand": "HeartGuard",
        "model": "ECG-Portable-V1",
        "active": true,
        "connected": true,
        "registered_at": "2025-11-20T10:30:00Z",
        "type": {
          "code": "ECG_PORTABLE",
          "label": "ECG portátil de una derivación"
        },
        "owner": {
          "id": "8c9436b4-f085-405f-a3d2-87cb1d1cf097",
          "name": "María Delgado",
          "email": "maria@example.com"
        },
        "current_connection": {
          "patient_id": "8c9436b4-f085-405f-a3d2-87cb1d1cf097",
          "patient_name": "María Delgado",
          "started_at": "2025-11-23T08:15:00Z"
        },
        "streams": {
          "total": 1,
          "last_started_at": "2025-11-23T08:15:00Z"
        }
      }
    ],
    "pagination": {
      "limit": 200,
      "offset": 0,
      "returned": 1
    }
  }
}
```

#### 2. Detalle de Dispositivo
```
GET /orgs/{org_id}/devices/{device_id}
```

**Ejemplo:**
```bash
GET /orgs/d3fc1b0c-f94b-416c-8dca-4cd1a6d4a4c7/devices/1ec46655-ba0c-4e2a-b315-dc6bbcbeda7d
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "organization": {...},
    "device": {
      "id": "1ec46655-ba0c-4e2a-b315-dc6bbcbeda7d",
      "serial": "HG-ECG-001",
      "connected": true,
      "owner": {...},
      "current_connection": {...},
      "streams": {...}
    }
  }
}
```

#### 3. Historial de Streams de un Dispositivo
```
GET /orgs/{org_id}/devices/{device_id}/streams
```

Muestra **todos los signal_streams** del dispositivo (pacientes con los que se ha conectado).

**Query Parameters:**
- `limit` (int): Máximo de resultados (default: 50, max: 200)
- `offset` (int): Offset para paginación

**Ejemplo:**
```bash
GET /orgs/d3fc1b0c-f94b-416c-8dca-4cd1a6d4a4c7/devices/e085ff18-d8bd-46f6-b34c-26bb0b797a14/streams
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "organization": {...},
    "device": {...},
    "streams": [
      {
        "id": "stream-uuid-1",
        "device_id": "e085ff18-d8bd-46f6-b34c-26bb0b797a14",
        "status": "active",
        "patient": {
          "id": "fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21",
          "name": "José Hernández",
          "email": "jose@example.com"
        },
        "started_at": "2025-11-23T10:00:00Z",
        "ended_at": null
      },
      {
        "id": "stream-uuid-2",
        "device_id": "e085ff18-d8bd-46f6-b34c-26bb0b797a14",
        "status": "ended",
        "patient": {
          "id": "8c9436b4-f085-405f-a3d2-87cb1d1cf097",
          "name": "María Delgado",
          "email": "maria@example.com"
        },
        "started_at": "2025-11-20T08:00:00Z",
        "ended_at": "2025-11-22T18:30:00Z"
      }
    ],
    "pagination": {
      "limit": 50,
      "offset": 0,
      "returned": 2
    }
  }
}
```

## Cambios en la Lógica

### Estado de Conexión
**Antes:**
```sql
-- Lógica incorrecta (todos aparecían desconectados)
WHERE d.active = TRUE
  AND (ls.last_ended_at IS NULL OR ls.last_ended_at < NOW() - INTERVAL '24 hours')
```

**Ahora:**
```sql
-- Lógica correcta: conectado = tiene stream activo
WITH active_stream AS (
    SELECT ss.id, ss.device_id, ss.patient_id
    FROM signal_streams ss
    WHERE ss.ended_at IS NULL  -- Stream activo
)
```

El campo `connected` es un **boolean** basado en:
- `connected = true`: El dispositivo tiene al menos un `signal_stream` con `ended_at IS NULL`
- `connected = false`: Todos los streams del dispositivo tienen `ended_at IS NOT NULL`

### Múltiples Pacientes

Un dispositivo puede conectarse con **diferentes pacientes** a lo largo del tiempo:

- **Owner** (`owner_patient_id`): Paciente propietario del dispositivo (no cambia)
- **Current Connection** (`current_patient_id`): Paciente con el stream activo actual (puede ser diferente al owner)
- **Streams**: Historial completo de todos los pacientes con los que se ha conectado

**Ejemplo Real (HG-PUL-201):**
```json
{
  "serial": "HG-PUL-201",
  "owner": {
    "name": "José Hernández"  // Propietario
  },
  "current_connection": {
    "patient_name": "José Hernández"  // Conectado actualmente
  },
  "streams": {
    "total": 2  // Se ha conectado con 2 pacientes diferentes en el pasado
  }
}
```

## Endpoints Anteriores (Deprecated)

Los endpoints de `care_team` siguen existiendo pero **NO son apropiados** para el tab de dispositivos:

```
❌ /orgs/{org_id}/care-teams/{team_id}/devices
✅ /orgs/{org_id}/devices
```

**Razón**: Los dispositivos pertenecen a la **organización**, no al equipo de cuidado. Un dispositivo puede servir a pacientes de múltiples equipos.

## Testing

### Base de Datos Real (134.199.204.58)

Dispositivos existentes:
```
serial        | active | connected | owner           | org
--------------+--------+-----------+-----------------+------------------
addadad       | t      | t         | José Hernández  | Clínica Central
HG-ECG-001    | t      | t         | María Delgado   | Familia García
HG-ECG-OLD-01 | t      | t         | Valeria Ortiz   | Servicios Ops
HG-PUL-201    | t      | t         | José Hernández  | Clínica Central
SDADAD        | t      | t         | María Delgado   | Familia García
SDADADAD      | t      | t         | María Delgado   | Familia García
```

### Test con curl

```bash
# 1. Login (obtener token)
TOKEN=$(curl -s http://localhost:5002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.data.access_token')

# 2. Listar todos los dispositivos de "Familia García"
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5003/orgs/d3fc1b0c-f94b-416c-8dca-4cd1a6d4a4c7/devices"

# 3. Solo dispositivos conectados
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5003/orgs/d3fc1b0c-f94b-416c-8dca-4cd1a6d4a4c7/devices?connected=true"

# 4. Detalle de un dispositivo específico
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5003/orgs/d3fc1b0c-f94b-416c-8dca-4cd1a6d4a4c7/devices/1ec46655-ba0c-4e2a-b315-dc6bbcbeda7d"

# 5. Historial de streams
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5003/orgs/d3fc1b0c-f94b-416c-8dca-4cd1a6d4a4c7/devices/e085ff18-d8bd-46f6-b34c-26bb0b797a14/streams"
```

## Migración en Frontend

### Antes (Incorrecto)
```javascript
// ❌ Endpoint incorrecto con care_team_id
fetch(`/orgs/${orgId}/care-teams/${teamId}/devices`)
```

### Ahora (Correcto)
```javascript
// ✅ Endpoint correcto a nivel de organización
fetch(`/orgs/${orgId}/devices?active=true&connected=true`)
  .then(res => res.json())
  .then(data => {
    data.devices.forEach(device => {
      console.log(`${device.serial}: ${device.connected ? 'Conectado' : 'Desconectado'}`);
      console.log(`  Owner: ${device.owner.name}`);
      if (device.current_connection) {
        console.log(`  Conectado con: ${device.current_connection.patient_name}`);
      }
    });
  });
```

## Resumen de Correcciones

| Problema | Antes | Ahora |
|----------|-------|-------|
| **Endpoint** | `/care-teams/{id}/devices` | `/orgs/{id}/devices` |
| **Filtro** | Por care_team | Por organización |
| **Estado conectado** | Lógica invertida | `ended_at IS NULL` |
| **Paciente** | Solo owner | Owner + current_connection + historial |
| **Streams** | No visible | Endpoint dedicado con historial completo |

## Archivos Modificados

1. `services/user/src/user/repositories/user_repo.py`
   - `list_org_devices()` - Nueva query sin care_team
   - `get_org_device()` - Detalle de dispositivo
   - `list_device_streams()` - Historial completo

2. `services/user/src/user/services/user_service.py`
   - `list_org_devices()` - Lógica de negocio
   - `get_org_device_detail()` - Validaciones
   - `list_device_streams()` - Paginación
   - `_format_org_device()` - Formateo con connected, owner, current_connection

3. `services/user/src/user/blueprints/user.py`
   - `GET /orgs/{org_id}/devices` - Listar
   - `GET /orgs/{org_id}/devices/{device_id}` - Detalle
   - `GET /orgs/{org_id}/devices/{device_id}/streams` - Historial
