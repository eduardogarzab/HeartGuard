# Ejemplos de Respuestas del Backend - Sistema de Alertas

Este documento muestra ejemplos de las respuestas JSON que el backend debe devolver para que la aplicación desktop funcione correctamente.

## 📋 Endpoints de Alertas

### 1. GET /admin/organizations/{org_id}/alerts

**Request:**
```http
GET /admin/organizations/550e8400-e29b-41d4-a716-446655440000/alerts?status=created,notified&level=high,critical
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** (200 OK)
```json
{
  "alerts": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "patient_name": "Juan Pérez García",
      "type": "ARRHYTHMIA",
      "alert_level": "critical",
      "status": "notified",
      "description": "Frecuencia cardíaca elevada: 135 bpm (normal: 60-100 bpm)",
      "created_at": "2025-11-24T09:30:00Z",
      "acknowledged_at": null,
      "resolved_at": null,
      "created_by_model_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "source_inference_id": "inf_20251124_093000_12345",
      "latitude": 19.4326,
      "longitude": -99.1332,
      "acknowledged_by_user_id": null,
      "resolved_by_user_id": null
    },
    {
      "id": "8d0f7780-8536-51ef-b15c-f18gd2g01bf8",
      "patient_id": "e391g2ff-7d65-5c02-a1f7-e812859g1962",
      "patient_name": "María García López",
      "type": "DESAT",
      "alert_level": "high",
      "status": "created",
      "description": "Saturación de oxígeno baja: 88% (normal: ≥95%)",
      "created_at": "2025-11-24T09:28:15Z",
      "acknowledged_at": null,
      "resolved_at": null,
      "created_by_model_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "source_inference_id": "inf_20251124_092815_12346",
      "latitude": 19.4320,
      "longitude": -99.1340,
      "acknowledged_by_user_id": null,
      "resolved_by_user_id": null
    },
    {
      "id": "9e1g8891-9647-62fg-c26d-g29he3h12cg9",
      "patient_id": "f502h3gg-8e76-6d13-b2g8-f923960h2073",
      "patient_name": "Carlos López Martínez",
      "type": "HYPERTENSION",
      "alert_level": "medium",
      "status": "notified",
      "description": "Presión arterial elevada: 160/100 mmHg (normal: <140/90 mmHg)",
      "created_at": "2025-11-24T09:25:30Z",
      "acknowledged_at": null,
      "resolved_at": null,
      "created_by_model_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "source_inference_id": "inf_20251124_092530_12347",
      "latitude": 19.4315,
      "longitude": -99.1328,
      "acknowledged_by_user_id": null,
      "resolved_by_user_id": null
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 50
}
```

### 2. GET /patient/{patient_id}/alerts

**Request:**
```http
GET /patient/d290f1ee-6c54-4b01-90e6-d701748f0851/alerts
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** (200 OK)
```json
{
  "alerts": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "patient_name": "Juan Pérez García",
      "type": "ARRHYTHMIA",
      "alert_level": "critical",
      "status": "resolved",
      "description": "Frecuencia cardíaca elevada: 135 bpm",
      "created_at": "2025-11-24T09:30:00Z",
      "acknowledged_at": "2025-11-24T09:32:00Z",
      "resolved_at": "2025-11-24T09:45:00Z",
      "created_by_model_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "source_inference_id": "inf_20251124_093000_12345",
      "latitude": 19.4326,
      "longitude": -99.1332,
      "acknowledged_by_user_id": "u123-4567-8901-2345",
      "resolved_by_user_id": "u123-4567-8901-2345"
    }
  ],
  "total": 1
}
```

### 3. GET /alerts/{alert_id}

**Request:**
```http
GET /alerts/7c9e6679-7425-40de-944b-e07fc1f90ae7
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** (200 OK)
```json
{
  "alert": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "patient_name": "Juan Pérez García",
    "type": "ARRHYTHMIA",
    "alert_level": "critical",
    "status": "notified",
    "description": "Frecuencia cardíaca elevada: 135 bpm",
    "created_at": "2025-11-24T09:30:00Z",
    "acknowledged_at": null,
    "resolved_at": null,
    "created_by_model_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "source_inference_id": "inf_20251124_093000_12345",
    "latitude": 19.4326,
    "longitude": -99.1332,
    "acknowledged_by_user_id": null,
    "resolved_by_user_id": null
  }
}
```

### 4. PUT /alerts/{alert_id}/acknowledge

**Request:**
```http
PUT /alerts/7c9e6679-7425-40de-944b-e07fc1f90ae7/acknowledge
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "user_id": "u123-4567-8901-2345"
}
```

**Response:** (200 OK)
```json
{
  "alert": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "patient_name": "Juan Pérez García",
    "type": "ARRHYTHMIA",
    "alert_level": "critical",
    "status": "ack",
    "description": "Frecuencia cardíaca elevada: 135 bpm",
    "created_at": "2025-11-24T09:30:00Z",
    "acknowledged_at": "2025-11-24T09:32:15Z",
    "resolved_at": null,
    "created_by_model_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "source_inference_id": "inf_20251124_093000_12345",
    "latitude": 19.4326,
    "longitude": -99.1332,
    "acknowledged_by_user_id": "u123-4567-8901-2345",
    "resolved_by_user_id": null
  },
  "message": "Alerta reconocida exitosamente"
}
```

### 5. PUT /alerts/{alert_id}/resolve

**Request:**
```http
PUT /alerts/7c9e6679-7425-40de-944b-e07fc1f90ae7/resolve
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "user_id": "u123-4567-8901-2345",
  "notes": "Paciente evaluado. Arritmia confirmada mediante ECG. Iniciado tratamiento."
}
```

**Response:** (200 OK)
```json
{
  "alert": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "patient_name": "Juan Pérez García",
    "type": "ARRHYTHMIA",
    "alert_level": "critical",
    "status": "resolved",
    "description": "Frecuencia cardíaca elevada: 135 bpm",
    "created_at": "2025-11-24T09:30:00Z",
    "acknowledged_at": "2025-11-24T09:32:15Z",
    "resolved_at": "2025-11-24T09:45:30Z",
    "created_by_model_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "source_inference_id": "inf_20251124_093000_12345",
    "latitude": 19.4326,
    "longitude": -99.1332,
    "acknowledged_by_user_id": "u123-4567-8901-2345",
    "resolved_by_user_id": "u123-4567-8901-2345"
  },
  "message": "Alerta resuelta exitosamente"
}
```

### 6. PUT /alerts/{alert_id}/close

**Request:**
```http
PUT /alerts/7c9e6679-7425-40de-944b-e07fc1f90ae7/close
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "user_id": "u123-4567-8901-2345"
}
```

**Response:** (200 OK)
```json
{
  "alert": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "status": "closed"
  },
  "message": "Alerta cerrada exitosamente"
}
```

## 📊 Endpoints de Ground Truth

### 1. POST /ground-truth/validate-true-positive

**Request:**
```http
POST /ground-truth/validate-true-positive
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "alert_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "event_type_code": "ARRHYTHMIA",
  "onset": "2025-11-24T09:30:00Z",
  "offset_at": null,
  "annotated_by_user_id": "u123-4567-8901-2345",
  "source": "AI_MODEL",
  "note": "Arritmia confirmada mediante ECG de 12 derivaciones. Iniciado tratamiento con antiarrítmicos."
}
```

**Response:** (201 Created)
```json
{
  "ground_truth_label": {
    "id": "gt-1234-5678-90ab-cdef",
    "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "event_type_code": "ARRHYTHMIA",
    "onset": "2025-11-24T09:30:00Z",
    "offset_at": null,
    "annotated_by_user_id": "u123-4567-8901-2345",
    "annotated_by_user_name": "Dr. Laura Martínez",
    "source": "AI_MODEL",
    "note": "Arritmia confirmada mediante ECG de 12 derivaciones. Iniciado tratamiento con antiarrítmicos.",
    "created_at": "2025-11-24T09:45:30Z",
    "updated_at": "2025-11-24T09:45:30Z"
  },
  "message": "Ground truth label creada exitosamente"
}
```

### 2. POST /ground-truth/validate-false-positive

**Request:**
```http
POST /ground-truth/validate-false-positive
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "alert_id": "8d0f7780-8536-51ef-b15c-f18gd2g01bf8",
  "validated_by_user_id": "u123-4567-8901-2345",
  "reason": "Sensor de SpO2 mal colocado. Valores reales normales al verificar manualmente."
}
```

**Response:** (200 OK)
```json
{
  "message": "Alerta marcada como falso positivo exitosamente",
  "alert_id": "8d0f7780-8536-51ef-b15c-f18gd2g01bf8",
  "validated_by": "u123-4567-8901-2345",
  "validation_timestamp": "2025-11-24T09:50:00Z"
}
```

### 3. POST /ground-truth/create-manual

**Request:**
```http
POST /ground-truth/create-manual
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "event_type_code": "FEVER",
  "onset": "2025-11-24T08:00:00Z",
  "offset_at": "2025-11-24T12:00:00Z",
  "annotated_by_user_id": "u123-4567-8901-2345",
  "source": "MANUAL",
  "note": "Paciente reportó fiebre durante la mañana. Temperatura máxima: 38.5°C. Administrado antipirético."
}
```

**Response:** (201 Created)
```json
{
  "ground_truth_label": {
    "id": "gt-5678-90ab-cdef-1234",
    "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "event_type_code": "FEVER",
    "onset": "2025-11-24T08:00:00Z",
    "offset_at": "2025-11-24T12:00:00Z",
    "annotated_by_user_id": "u123-4567-8901-2345",
    "annotated_by_user_name": "Enf. Ana González",
    "source": "MANUAL",
    "note": "Paciente reportó fiebre durante la mañana. Temperatura máxima: 38.5°C. Administrado antipirético.",
    "created_at": "2025-11-24T12:15:00Z",
    "updated_at": "2025-11-24T12:15:00Z"
  },
  "message": "Ground truth label manual creada exitosamente"
}
```

### 4. GET /ground-truth/patient/{patient_id}

**Request:**
```http
GET /ground-truth/patient/d290f1ee-6c54-4b01-90e6-d701748f0851
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** (200 OK)
```json
{
  "labels": [
    {
      "id": "gt-1234-5678-90ab-cdef",
      "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "event_type_code": "ARRHYTHMIA",
      "onset": "2025-11-24T09:30:00Z",
      "offset_at": null,
      "annotated_by_user_id": "u123-4567-8901-2345",
      "annotated_by_user_name": "Dr. Laura Martínez",
      "source": "AI_MODEL",
      "note": "Arritmia confirmada mediante ECG",
      "created_at": "2025-11-24T09:45:30Z",
      "updated_at": "2025-11-24T09:45:30Z"
    },
    {
      "id": "gt-5678-90ab-cdef-1234",
      "patient_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "event_type_code": "FEVER",
      "onset": "2025-11-24T08:00:00Z",
      "offset_at": "2025-11-24T12:00:00Z",
      "annotated_by_user_id": "u123-4567-8901-2345",
      "annotated_by_user_name": "Enf. Ana González",
      "source": "MANUAL",
      "note": "Fiebre reportada por paciente",
      "created_at": "2025-11-24T12:15:00Z",
      "updated_at": "2025-11-24T12:15:00Z"
    }
  ],
  "total": 2
}
```

### 5. GET /ground-truth/stats

**Request:**
```http
GET /ground-truth/stats?start_date=2025-11-01T00:00:00Z&end_date=2025-11-30T23:59:59Z
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** (200 OK)
```json
{
  "period": {
    "start": "2025-11-01T00:00:00Z",
    "end": "2025-11-30T23:59:59Z"
  },
  "overall": {
    "total_alerts": 150,
    "total_validated": 120,
    "true_positives": 95,
    "false_positives": 25,
    "precision": 79.17,
    "validation_rate": 80.0
  },
  "by_event_type": [
    {
      "event_type": "ARRHYTHMIA",
      "total_alerts": 45,
      "true_positives": 38,
      "false_positives": 7,
      "precision": 84.44
    },
    {
      "event_type": "DESAT",
      "total_alerts": 30,
      "true_positives": 25,
      "false_positives": 5,
      "precision": 83.33
    },
    {
      "event_type": "HYPERTENSION",
      "total_alerts": 40,
      "true_positives": 28,
      "false_positives": 12,
      "precision": 70.0
    },
    {
      "event_type": "FEVER",
      "total_alerts": 35,
      "true_positives": 30,
      "false_positives": 5,
      "precision": 85.71
    }
  ],
  "trends": {
    "week_1": {"precision": 75.0},
    "week_2": {"precision": 78.5},
    "week_3": {"precision": 80.2},
    "week_4": {"precision": 82.1}
  }
}
```

## 🚨 Errores Comunes

### Error 401 - No autorizado
```json
{
  "error": "Unauthorized",
  "message": "Token inválido o expirado",
  "status": 401
}
```

### Error 404 - Alerta no encontrada
```json
{
  "error": "Not Found",
  "message": "Alerta con ID 7c9e6679-7425-40de-944b-e07fc1f90ae7 no encontrada",
  "status": 404
}
```

### Error 403 - Sin permisos
```json
{
  "error": "Forbidden",
  "message": "No tienes permisos para acceder a las alertas de esta organización",
  "status": 403
}
```

### Error 400 - Datos inválidos
```json
{
  "error": "Bad Request",
  "message": "El campo 'event_type_code' es requerido",
  "status": 400
}
```

---

**Nota**: Todos los timestamps deben estar en formato ISO 8601 UTC (YYYY-MM-DDTHH:mm:ssZ)
