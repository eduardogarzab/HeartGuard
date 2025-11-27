# Patient Service - HeartGuard

Microservicio dedicado a gestionar la información y el portal de pacientes en el sistema HeartGuard.

## 🎯 Propósito

Este servicio proporciona endpoints específicos para pacientes autenticados, permitiéndoles:
- Ver su perfil y datos personales
- Consultar su historial médico
- Ver alertas y eventos relacionados con su salud
- Acceder a sus dispositivos asignados
- Ver su ubicación y datos de telemetría

## 🏗️ Arquitectura

- **Puerto:** 5004
- **Base de datos:** PostgreSQL (compartida con otros servicios)
- **Autenticación:** JWT validado desde auth_service
- **Framework:** Flask

## 📡 Endpoints

### 1. Dashboard del Paciente
```http
GET /patient/dashboard
Authorization: Bearer <patient-token>
```

**Respuesta (200):**
```json
{
  "patient": {
    "id": "uuid",
    "name": "María González",
    "email": "maria@example.com",
    "birthdate": "1990-01-15",
    "sex": "F",
    "risk_level": "medium",
    "org_name": "Hospital Central"
  },
  "stats": {
    "total_alerts": 5,
    "pending_alerts": 2,
    "devices_count": 2,
    "last_reading": "2025-11-03T10:30:00"
  },
  "recent_alerts": [
    {
      "id": "uuid",
      "type": "ARRHYTHMIA",
      "level": "high",
      "description": "Fibrilación auricular detectada",
      "created_at": "2025-11-03T09:15:00",
      "status": "ack"
    }
  ],
  "care_team": [
    {
      "name": "Dr. Juan Pérez",
      "role": "Cardiólogo",
      "email": "juan@hospital.com"
    }
  ]
}
```

### 2. Perfil del Paciente
```http
GET /patient/profile
Authorization: Bearer <patient-token>
```

**Respuesta (200):**
```json
{
  "id": "uuid",
  "name": "María González",
  "email": "maria@example.com",
  "birthdate": "1990-01-15",
  "sex": "Femenino",
  "risk_level": "Medio",
  "organization": {
    "id": "uuid",
    "code": "HOSP-001",
    "name": "Hospital Central"
  },
  "created_at": "2025-01-15T10:00:00"
}
```

### 3. Alertas del Paciente
```http
GET /patient/alerts?status=pending&limit=20
Authorization: Bearer <patient-token>
```

**Respuesta (200):**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "type": "ARRHYTHMIA",
      "type_label": "Arritmia",
      "level": "high",
      "level_label": "Alto",
      "description": "Posible fibrilación detectada",
      "status": "ack",
      "status_label": "Reconocida",
      "created_at": "2025-11-03T09:15:00",
      "location": {
        "lat": 19.4326,
        "lng": -99.1332
      }
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

### 4. Dispositivos del Paciente
```http
GET /patient/devices
Authorization: Bearer <patient-token>
```

**Respuesta (200):**
```json
{
  "devices": [
    {
      "id": "uuid",
      "serial": "HG-ECG-001",
      "brand": "Cardia",
      "model": "Wave Pro",
      "type": "ECG de una derivación",
      "active": true,
      "registered_at": "2024-05-15T08:00:00"
    }
  ]
}
```

### 5. Historial de Lecturas
```http
GET /patient/readings?limit=50&offset=0
Authorization: Bearer <patient-token>
```

**Respuesta (200):**
```json
{
  "readings": [
    {
      "id": "uuid",
      "device_serial": "HG-ECG-001",
      "signal_type": "ECG",
      "started_at": "2025-11-03T08:00:00",
      "ended_at": "2025-11-03T08:30:00",
      "duration_minutes": 30,
      "sample_rate_hz": 256
    }
  ],
  "total": 125,
  "limit": 50,
  "offset": 0
}
```

### 6. Equipo de Cuidado
```http
GET /patient/care-team
Authorization: Bearer <patient-token>
```

**Respuesta (200):**
```json
{
  "teams": [
    {
      "team_name": "Equipo Cardiología Familiar",
      "members": [
        {
          "name": "Dr. Ana Ruiz",
          "role": "Especialista",
          "email": "ana.ruiz@hospital.com"
        },
        {
          "name": "Martín López",
          "role": "Administrador",
          "email": "martin.ops@hospital.com"
        }
      ]
    }
  ]
}
```

### 7. Última Ubicación
```http
GET /patient/location/latest
Authorization: Bearer <patient-token>
```

**Respuesta (200):**
```json
{
  "location": {
    "latitude": 19.4326,
    "longitude": -99.1332,
    "timestamp": "2025-11-03T10:00:00",
    "source": "manual",
    "accuracy_meters": 35.5
  }
}
```

**Respuesta cuando no hay ubicaciones (200):**
```json
{
  "location": null
}
```

### 8. Historial de Ubicaciones (NUEVO)
```http
GET /patient/locations?limit=50&offset=0
Authorization: Bearer <patient-token>
```

**Query Parameters:**
- `limit` (opcional): Cantidad de resultados (default: 50, max: 500)
- `offset` (opcional): Desplazamiento para paginación (default: 0)

**Respuesta (200):**
```json
{
  "locations": [
    {
      "id": "uuid",
      "latitude": 19.4326,
      "longitude": -99.1332,
      "timestamp": "2025-11-03T10:00:00",
      "source": "GPS",
      "accuracy_meters": 15.0
    },
    {
      "id": "uuid",
      "latitude": 19.4305,
      "longitude": -99.1400,
      "timestamp": "2025-11-03T09:30:00",
      "source": "manual",
      "accuracy_meters": 50.0
    }
  ],
  "total": 127,
  "limit": 50,
  "offset": 0
}
```

**Campos de cada ubicación:**
- `id`: UUID de la ubicación
- `latitude`: Latitud (decimal)
- `longitude`: Longitud (decimal)
- `timestamp`: Fecha y hora de la ubicación (ISO 8601)
- `source`: Fuente de la ubicación (GPS, manual, network, etc.)
- `accuracy_meters`: Precisión en metros (puede ser null)

## 🔒 Autenticación

Todos los endpoints requieren un JWT válido de tipo `patient`:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Payload esperado del JWT:**
```json
{
  "patient_id": "uuid",
  "account_type": "patient",
  "email": "maria@example.com",
  "org_id": "uuid",
  "exp": 1234567890
}
```

## 📊 Dashboard del Paciente - Vista Principal

Cuando un paciente inicia sesión, verá:

### Sección 1: Información Personal
- Nombre completo
- Fecha de nacimiento / Edad
- Nivel de riesgo (badge con color)
- Organización asignada

### Sección 2: Resumen de Salud
- Total de alertas (badge)
- Alertas pendientes (destacado)
- Última lectura de dispositivo
- Estado de dispositivos

### Sección 3: Alertas Recientes (Top 5)
- Tipo de alerta con icono
- Nivel de severidad (color)
- Descripción
- Fecha/hora
- Estado actual

### Sección 4: Equipo de Cuidado
- Lista de médicos y staff asignados
- Roles (cardiólogo, enfermero, etc.)
- Información de contacto

### Sección 5: Dispositivos
- Lista de dispositivos asignados
- Estado (activo/inactivo)
- Última sincronización

### Sección 6: Acción Rápida
- Botón: "Ver todas mis alertas"
- Botón: "Ver historial completo"
- Botón: "Configurar dispositivos"

## 🌐 Variables de Entorno

```bash
DATABASE_URL=postgresql://heartguard_app:password@136.115.53.140:5432/heartguard
JWT_SECRET=tu-secreto-compartido
PORT=5004
LOG_LEVEL=INFO
```

## 📦 Dependencias

```txt
Flask>=3.0.0
Flask-CORS>=4.0.0
PyJWT>=2.8.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```

## 🚀 Uso

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servicio
python -m flask --app src.patient.app run --port 5004

# O con Make
make dev
```

## 🔐 Seguridad

- ✅ Validación de JWT en cada request
- ✅ Verificación de `account_type === 'patient'`
- ✅ Acceso solo a datos del paciente autenticado
- ✅ No permite acceso a datos de otros pacientes
- ✅ CORS configurado

## 📄 Licencia

Propiedad de HeartGuard - Todos los derechos reservados
