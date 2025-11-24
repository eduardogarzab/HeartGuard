# Flujo de IA → Alertas → Ground Truth

## 📋 Resumen

Este documento describe cómo funciona el flujo completo desde que el modelo de IA analiza datos de InfluxDB hasta que se genera una alerta validable en PostgreSQL.

## 🔄 Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DATOS EN INFLUXDB (Time Series)                                 │
│    - Timestamp: 2025-11-24T09:30:00Z                               │
│    - Heart Rate: 135 bpm                                           │
│    - SpO2: 88%                                                     │
│    - Blood Pressure: 160/100 mmHg                                  │
│    - Temperature: 39.5°C                                           │
│    - GPS: 19.4326, -99.1332                                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. SERVICIO DE IA (http://134.199.204.58:5008)                     │
│    POST /predict                                                    │
│    {                                                                │
│      "gps_longitude": -99.1332,                                    │
│      "gps_latitude": 19.4326,                                      │
│      "heart_rate": 135,                                            │
│      "spo2": 88,                                                   │
│      "systolic_bp": 160,                                           │
│      "diastolic_bp": 100,                                          │
│      "temperature": 39.5                                           │
│    }                                                                │
│                                                                     │
│    RESPUESTA:                                                       │
│    {                                                                │
│      "prediction": 1,                    // Problema detectado     │
│      "probability": 0.95,                // 95% confianza          │
│      "risk_level": "HIGH",                                         │
│      "alerts": [                                                   │
│        {                                                           │
│          "type": "ARRHYTHMIA",           // HR: 135 > 100          │
│          "severity": "high",                                       │
│          "message": "Frecuencia cardíaca elevada",                 │
│          "value": 135,                                             │
│          "unit": "bpm"                                             │
│        },                                                          │
│        {                                                           │
│          "type": "DESAT",                // SpO2: 88 < 95          │
│          "severity": "critical",                                   │
│          "message": "Saturación de oxígeno baja",                  │
│          "value": 88,                                              │
│          "unit": "%"                                               │
│        },                                                          │
│        {                                                           │
│          "type": "HYPERTENSION",         // BP: 160/100 >= 140/90  │
│          "severity": "high",                                       │
│          "message": "Presión arterial elevada",                    │
│          "value": "160/100",                                       │
│          "unit": "mmHg"                                            │
│        },                                                          │
│        {                                                           │
│          "type": "FEVER",                // Temp: 39.5 >= 38       │
│          "severity": "medium",                                     │
│          "message": "Temperatura corporal elevada",                │
│          "value": 39.5,                                            │
│          "unit": "°C"                                              │
│        }                                                           │
│      ],                                                            │
│      "timestamp": "2025-11-24T09:30:00Z"                           │
│    }                                                                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. CREACIÓN DE ALERTAS EN POSTGRESQL                               │
│    Para cada alerta en la respuesta del modelo:                    │
│                                                                     │
│    INSERT INTO alerts (                                            │
│      patient_id,                  -- UUID del paciente             │
│      type_id,                     -- ARRHYTHMIA, DESAT, etc.       │
│      created_by_model_id,         -- UUID del modelo de IA         │
│      source_inference_id,         -- UUID de la inferencia         │
│      alert_level_id,              -- high, critical, medium        │
│      status_id,                   -- 'created'                     │
│      created_at,                  -- Timestamp de InfluxDB         │
│      description,                 -- Mensaje del modelo            │
│      location                     -- GPS del paciente              │
│    )                                                                │
│                                                                     │
│    Ejemplo para ARRHYTHMIA:                                        │
│    - patient_id: 'd290f1ee-6c54-4b01-90e6-d701748f0851'            │
│    - type_id: (SELECT id FROM alert_types WHERE code='ARRHYTHMIA') │
│    - created_by_model_id: (modelo RandomForest)                    │
│    - alert_level_id: (SELECT id FROM alert_levels WHERE code='high')│
│    - status_id: (SELECT id FROM alert_status WHERE code='created') │
│    - description: 'Frecuencia cardíaca elevada: 135 bpm'           │
│    - location: POINT(-99.1332 19.4326)                             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. NOTIFICACIÓN AL CAREGIVER TEAM                                  │
│    - Se buscan todos los caregivers del paciente                   │
│    - Se envían notificaciones según sus preferencias:              │
│      * SMS                                                         │
│      * Email                                                       │
│      * Push notification                                           │
│    - El equipo médico ve las alertas en org-admin                  │
│    - Estado cambia a 'notified'                                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. RECONOCIMIENTO Y RESOLUCIÓN                                     │
│    - Caregiver reconoce la alerta (status → 'ack')                │
│    - Evalúa si es verdadero positivo o falso positivo              │
│    - Toma acción médica si es necesario                            │
│    - Resuelve la alerta (status → 'resolved')                      │
│    - Cierra el caso (status → 'closed')                            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 6. GROUND TRUTH (Validación del Modelo)                            │
│    El caregiver anota si el evento fue REAL o FALSO:               │
│                                                                     │
│    INSERT INTO ground_truth_labels (                               │
│      patient_id,                  -- UUID del paciente             │
│      event_type_id,               -- ARRHYTHMIA confirmado         │
│      onset,                       -- Inicio del evento             │
│      offset_at,                   -- Fin del evento (si aplica)    │
│      annotated_by_user_id,        -- Caregiver que validó          │
│      source,                      -- 'AI_MODEL' o 'MANUAL'         │
│      note                         -- 'Arritmia confirmada por ECG' │
│    )                                                                │
│                                                                     │
│    Esto sirve para:                                                │
│    ✅ Medir precisión del modelo (true positives vs false positives)│
│    ✅ Reentrenar el modelo con datos validados                     │
│    ✅ Auditoría médica y legal                                     │
│    ✅ Estadísticas de calidad del servicio                         │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Tipos de Eventos Soportados

### En `event_types` (PostgreSQL)

Todos los eventos que el modelo de IA puede detectar están registrados en la base de datos:

```sql
-- SEED DATA actualizado
INSERT INTO event_types(code, description, severity_default_id)
SELECT x.code, x.description, (SELECT id FROM alert_levels WHERE code = x.def_level)
FROM (VALUES
  ('GENERAL_RISK','Riesgo general de salud detectado por IA','medium'),
  ('ARRHYTHMIA','Arritmia - Frecuencia cardiaca anormal','high'),
  ('DESAT','Desaturación de oxígeno','high'),
  ('HYPERTENSION','Hipertensión arterial','medium'),
  ('HYPOTENSION','Hipotensión arterial','high'),
  ('FEVER','Fiebre - Temperatura elevada','medium'),
  ('HYPOTHERMIA','Hipotermia - Temperatura baja','high')
) AS x(code,description,def_level)
ON CONFLICT (code) DO NOTHING;
```

### Criterios del Modelo de IA

| Tipo          | Condición                       | Severidad      |
|---------------|---------------------------------|----------------|
| GENERAL_RISK  | probability ≥ 0.6               | medium-high    |
| ARRHYTHMIA    | HR < 60 o HR > 100 bpm          | high-critical  |
| DESAT         | SpO2 < 95%                      | high-critical  |
| HYPERTENSION  | ≥ 140/90 mmHg                   | medium-high    |
| HYPOTENSION   | < 90/60 mmHg                    | high-critical  |
| FEVER         | ≥ 38°C                          | medium-high    |
| HYPOTHERMIA   | < 36°C                          | high-critical  |

## 🔗 Relación entre Tablas

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  event_types │      │ alert_types  │      │    alerts    │
│──────────────│      │──────────────│      │──────────────│
│ id (UUID)    │      │ id (UUID)    │      │ id (UUID)    │
│ code         │◄─────│ code         │◄─────│ type_id      │
│ description  │      │ severity_min │      │ patient_id   │
│ severity_def │      │ severity_max │      │ alert_level  │
└──────────────┘      └──────────────┘      │ status_id    │
                                              │ description  │
       ▲                                      │ location     │
       │                                      │ created_at   │
       │ REFERENCES                           └──────────────┘
       │                                              │
┌──────────────────┐                                 │
│ ground_truth_    │                                 │
│     labels       │                                 │
│──────────────────│                                 │
│ id (UUID)        │                                 │
│ patient_id       │◄────────────────────────────────┘
│ event_type_id    │  (Mismo paciente)
│ onset            │
│ offset_at        │
│ annotated_by     │
│ source           │
│ note             │
└──────────────────┘
```

## 💻 Ejemplo de Código (Backend Service)

### Flujo completo en Python:

```python
import requests
from datetime import datetime
import psycopg2

# 1. Obtener datos de InfluxDB
def get_vital_signs_from_influx(patient_id, timestamp):
    # Query a InfluxDB para obtener signos vitales en ese timestamp
    query = f'''
    from(bucket: "heartguard")
      |> range(start: {timestamp}, stop: {timestamp + 1s})
      |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    # Retorna: {"hr": 135, "spo2": 88, "bp_sys": 160, "bp_dia": 100, "temp": 39.5, "gps": {...}}
    return influx_client.query(query)

# 2. Llamar al modelo de IA
def predict_health_risk(vital_signs, jwt_token):
    ai_service_url = "http://134.199.204.58:5008/predict"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "gps_longitude": vital_signs["gps"]["longitude"],
        "gps_latitude": vital_signs["gps"]["latitude"],
        "heart_rate": vital_signs["hr"],
        "spo2": vital_signs["spo2"],
        "systolic_bp": vital_signs["bp_sys"],
        "diastolic_bp": vital_signs["bp_dia"],
        "temperature": vital_signs["temp"]
    }
    response = requests.post(ai_service_url, json=payload, headers=headers)
    return response.json()

# 3. Crear alertas en PostgreSQL
def create_alerts(patient_id, prediction, timestamp, location):
    conn = psycopg2.connect("dbname=heartguard user=heartguard_app")
    cur = conn.cursor()
    
    # Solo crear alertas si hay problema detectado
    if prediction["prediction"] == 1:
        for alert in prediction["alerts"]:
            cur.execute("""
                INSERT INTO alerts (
                    patient_id, 
                    type_id, 
                    alert_level_id, 
                    status_id, 
                    created_at, 
                    description, 
                    location
                )
                VALUES (
                    %s,
                    (SELECT id FROM alert_types WHERE code = %s),
                    (SELECT id FROM alert_levels WHERE code = %s),
                    (SELECT id FROM alert_status WHERE code = 'created'),
                    %s,
                    %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                )
                RETURNING id
            """, (
                patient_id,
                alert["type"],                    # 'ARRHYTHMIA', 'DESAT', etc.
                alert["severity"],                # 'high', 'critical', etc.
                timestamp,
                alert["message"],
                location["longitude"],
                location["latitude"]
            ))
            alert_id = cur.fetchone()[0]
            print(f"✅ Alerta creada: {alert_id} - {alert['type']}")
    
    conn.commit()
    cur.close()
    conn.close()

# 4. Notificar al equipo de cuidadores
def notify_caregivers(patient_id, alerts):
    # Obtener caregivers del paciente
    caregivers = get_patient_caregivers(patient_id)
    
    for caregiver in caregivers:
        # Enviar notificaciones según preferencias
        if caregiver["notify_email"]:
            send_email(caregiver["email"], alerts)
        if caregiver["notify_sms"]:
            send_sms(caregiver["phone"], alerts)
        if caregiver["notify_push"]:
            send_push_notification(caregiver["device_token"], alerts)

# 5. FLUJO COMPLETO
def monitor_patient_health(patient_id, timestamp):
    # Paso 1: Obtener datos
    vital_signs = get_vital_signs_from_influx(patient_id, timestamp)
    
    # Paso 2: Predecir con IA
    jwt_token = get_auth_token()
    prediction = predict_health_risk(vital_signs, jwt_token)
    
    # Paso 3: Crear alertas si hay problema
    if prediction["prediction"] == 1:
        create_alerts(
            patient_id, 
            prediction, 
            timestamp, 
            vital_signs["gps"]
        )
        
        # Paso 4: Notificar
        notify_caregivers(patient_id, prediction["alerts"])
        
        print(f"⚠️  {len(prediction['alerts'])} alertas generadas para paciente {patient_id}")
    else:
        print(f"✅ Paciente {patient_id} - Sin problemas detectados")
```

## 🎯 Ground Truth Validation

Cuando un caregiver valida una alerta:

```python
def validate_alert(alert_id, is_true_positive, caregiver_id, notes):
    conn = psycopg2.connect("dbname=heartguard user=heartguard_app")
    cur = conn.cursor()
    
    # Obtener detalles de la alerta
    cur.execute("""
        SELECT patient_id, type_id, created_at, location
        FROM alerts
        WHERE id = %s
    """, (alert_id,))
    
    patient_id, event_type_id, onset, location = cur.fetchone()
    
    if is_true_positive:
        # Crear registro de ground truth
        cur.execute("""
            INSERT INTO ground_truth_labels (
                patient_id,
                event_type_id,
                onset,
                annotated_by_user_id,
                source,
                note
            )
            VALUES (%s, %s, %s, %s, 'AI_MODEL', %s)
        """, (patient_id, event_type_id, onset, caregiver_id, notes))
        
        print(f"✅ Evento confirmado como VERDADERO POSITIVO")
    else:
        print(f"❌ Evento marcado como FALSO POSITIVO")
    
    # Actualizar estado de la alerta
    cur.execute("""
        UPDATE alerts
        SET status_id = (SELECT id FROM alert_status WHERE code = 'resolved')
        WHERE id = %s
    """, (alert_id,))
    
    conn.commit()
    cur.close()
    conn.close()
```

## 📈 Métricas del Modelo

Con los datos de ground truth se pueden calcular métricas:

```sql
-- Precisión del modelo por tipo de evento
SELECT 
    et.code AS event_type,
    COUNT(*) FILTER (WHERE gt.id IS NOT NULL) AS true_positives,
    COUNT(*) FILTER (WHERE gt.id IS NULL) AS false_positives,
    ROUND(
        COUNT(*) FILTER (WHERE gt.id IS NOT NULL)::numeric / 
        COUNT(*)::numeric * 100, 
        2
    ) AS precision_percentage
FROM alerts a
JOIN alert_types at ON at.id = a.type_id
JOIN event_types et ON et.code = at.code
LEFT JOIN ground_truth_labels gt ON 
    gt.patient_id = a.patient_id AND
    gt.event_type_id = et.id AND
    gt.onset = a.created_at
WHERE a.created_by_model_id IS NOT NULL  -- Solo alertas generadas por IA
GROUP BY et.code
ORDER BY precision_percentage DESC;
```

## 🚀 Siguientes Pasos

1. ✅ **COMPLETADO**: Event types actualizados en seed.sql
2. ✅ **COMPLETADO**: Alert types actualizados en seed.sql
3. 🔄 **PENDIENTE**: Implementar servicio que lea InfluxDB y llame al modelo
4. 🔄 **PENDIENTE**: Implementar creación automática de alertas
5. 🔄 **PENDIENTE**: Implementar sistema de notificaciones
6. 🔄 **PENDIENTE**: UI para validación de ground truth en org-admin

## 📝 Notas Importantes

- **SIEMPRE** guardar el timestamp original de InfluxDB en `alerts.created_at`
- **SIEMPRE** incluir la ubicación GPS del paciente en `alerts.location`
- **SIEMPRE** referenciar el modelo que generó la alerta en `created_by_model_id`
- El campo `source_inference_id` puede usarse para rastrear la inferencia específica
- Ground truth es CRÍTICO para mejorar el modelo y medir su efectividad

---

**Autor**: AI Assistant  
**Fecha**: 2025-11-24  
**Versión**: 1.0
