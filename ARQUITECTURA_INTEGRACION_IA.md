# 🧠 Arquitectura de Integración del Modelo de IA en HeartGuard

## 📊 Análisis del Estado Actual

### Desktop App (Java Swing)
- **Ubicación**: `desktop-app/src/main/java/`
- **Problema**: Reglas hardcodeadas en `VitalSignsChartPanel.java`:
  - Fiebre: `>= 38°C`
  - Hipotermia: `< 36°C`
  - Temperatura normal: `36.1-37.2°C`
  - Otros thresholds similares para HR, SpO2, BP

### Org-Admin Client (Web - JavaScript)
- **Ubicación**: `clients/org-admin/`
- **Funcionalidad**: Visualización de gráficas en tiempo real desde InfluxDB
- **Estado**: Las alertas se obtienen desde el backend (no se calculan en el frontend)

### Modelo de IA
- **Ubicación**: `IA/modelo_salud_randomforest.pkl`
- **Tipo**: RandomForest Classifier (scikit-learn)
- **Input**: 7 features (GPS_longitude, GPS_latitude, HeartRate, SpO2, SystolicBP, DiastolicBP, Temperature)
- **Output**: Probabilidad de problema (0-1) + clasificación binaria

---

## 🎯 Estrategia Recomendada: MICROSERVICIO DE IA

### ¿Por qué un Microservicio?

1. **Separación de responsabilidades**: El modelo de IA está en Python, la desktop-app en Java
2. **Escalabilidad**: Múltiples clientes pueden consultar el modelo
3. **Actualización independiente**: Puedes actualizar el modelo sin recompilar la desktop-app
4. **Reutilización**: Mismo servicio para org-admin, desktop-app y futuros clientes
5. **Integración con pipeline existente**: Se alinea con tu arquitectura de microservicios

---

## 🏗️ Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                         │
├──────────────────────┬──────────────────────┬───────────────────┤
│   Desktop App        │   Org-Admin Client   │  Mobile App       │
│   (Java Swing)       │   (JavaScript)       │  (Futuro)         │
└──────────┬───────────┴──────────┬───────────┴───────────────────┘
           │                      │
           │  HTTP/JSON           │  HTTP/JSON
           │                      │
           ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                                │
│                   (Puerto 8080)                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │  Rutas:
                            │  /ai/predict
                            │  /ai/batch-predict
                            │  /ai/health
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              🧠 SERVICIO DE IA (NUEVO)                          │
│                   (Python/Flask)                                │
│                   Puerto: 5008                                  │
│                                                                 │
│  • Carga modelo: modelo_salud_randomforest.pkl                 │
│  • Endpoint: POST /predict                                     │
│  • Input: {gps_long, gps_lat, hr, spo2, sbp, dbp, temp}       │
│  • Output: {has_problem, probability, alerts[]}               │
│  • Autenticación: JWT token                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Nuevo Microservicio

```
services/
└── ai-prediction/
    ├── Makefile
    ├── requirements.txt
    ├── README.md
    ├── modelo_salud_randomforest.pkl  (copiado desde IA/)
    ├── src/
    │   ├── __init__.py
    │   ├── app.py                     # Flask app principal
    │   ├── config.py                  # Configuración
    │   ├── middleware.py              # Auth JWT
    │   └── ml/
    │       ├── __init__.py
    │       ├── model_loader.py        # Carga del modelo
    │       ├── predictor.py           # Lógica de predicción
    │       └── alert_mapper.py        # Mapeo de alerts
    └── tests/
        ├── test_predict.py
        └── test_integration.py
```

---

## 🔌 API del Servicio de IA

### 1. POST `/predict` - Predicción Individual

**Request:**
```json
{
  "gps_longitude": -99.1332,
  "gps_latitude": 19.4326,
  "heart_rate": 75,
  "spo2": 98,
  "systolic_bp": 120,
  "diastolic_bp": 80,
  "temperature": 36.7
}
```

**Response:**
```json
{
  "has_problem": false,
  "probability": 0.15,
  "alerts": [],
  "processed_at": "2025-11-23T22:00:00Z"
}
```

**Con Problema:**
```json
{
  "has_problem": true,
  "probability": 0.87,
  "alerts": [
    {
      "type": "ARRHYTHMIA",
      "severity": "high",
      "message": "Frecuencia cardíaca anómala detectada"
    },
    {
      "type": "DESAT",
      "severity": "medium",
      "message": "Desaturación de oxígeno potencial"
    }
  ],
  "processed_at": "2025-11-23T22:00:00Z"
}
```

### 2. POST `/batch-predict` - Predicción por Lotes

Para procesar múltiples lecturas (útil para org-admin):

**Request:**
```json
{
  "readings": [
    {
      "gps_longitude": -99.1332,
      "gps_latitude": 19.4326,
      "heart_rate": 75,
      "spo2": 98,
      "systolic_bp": 120,
      "diastolic_bp": 80,
      "temperature": 36.7,
      "timestamp": "2025-11-23T21:59:00Z"
    },
    { ... }
  ]
}
```

**Response:**
```json
{
  "predictions": [
    {
      "timestamp": "2025-11-23T21:59:00Z",
      "has_problem": false,
      "probability": 0.15,
      "alerts": []
    },
    { ... }
  ],
  "summary": {
    "total": 100,
    "problems_detected": 3,
    "avg_probability": 0.23
  }
}
```

---

## 🔗 Integración con Desktop App

### Opción 1: Llamada Directa al Servicio de IA (Recomendada)

Crear una clase `AIService.java` que llame al servicio de IA:

```java
// desktop-app/src/main/java/com/heartguard/desktop/api/AIService.java
public class AIService {
    private final String AI_SERVICE_URL = "http://localhost:8080/ai";
    
    public AIPrediction predictHealth(VitalSignsReading reading) {
        JsonObject request = new JsonObject();
        request.addProperty("gps_longitude", reading.gpsLongitude);
        request.addProperty("gps_latitude", reading.gpsLatitude);
        request.addProperty("heart_rate", reading.heartRate);
        request.addProperty("spo2", reading.spo2);
        request.addProperty("systolic_bp", reading.systolicBp);
        request.addProperty("diastolic_bp", reading.diastolicBp);
        request.addProperty("temperature", reading.temperature);
        
        // HTTP POST to AI service
        JsonObject response = httpPost(AI_SERVICE_URL + "/predict", request);
        
        return new AIPrediction(
            response.get("has_problem").getAsBoolean(),
            response.get("probability").getAsDouble(),
            parseAlerts(response.getAsJsonArray("alerts"))
        );
    }
}
```

### Modificar `VitalSignsChartPanel.java`:

```java
// En lugar de thresholds hardcodeados:
private void checkForAlerts(VitalSignsReading reading) {
    try {
        AIPrediction prediction = aiService.predictHealth(reading);
        
        if (prediction.hasProblem()) {
            // Mostrar alertas del modelo IA
            showAIAlerts(prediction.getAlerts(), prediction.getProbability());
        }
    } catch (Exception e) {
        // Fallback a reglas hardcodeadas si el servicio falla
        checkWithHardcodedRules(reading);
    }
}
```

### Opción 2: Procesamiento en Backend (Alternativa)

El realtime-service procesa cada lectura de InfluxDB y crea alertas automáticamente:

```python
# services/realtime-data-generator/src/generator/worker.py

def process_vital_signs_stream(reading):
    # Llamar al servicio de IA
    prediction = ai_service.predict(reading)
    
    if prediction['has_problem']:
        # Crear alertas en PostgreSQL
        for alert in prediction['alerts']:
            create_alert(
                patient_id=reading.patient_id,
                type=alert['type'],
                level=alert['severity'],
                created_by_model='ai-rf-v1.0'
            )
```

---

## 🔗 Integración con Org-Admin Client

### Mostrar Probabilidad de IA en Gráficas

Modificar `app.js` para incluir predicción de IA:

```javascript
// clients/org-admin/assets/js/app.js

const loadVitalSignsData = async (patientId, deviceId, containerId, isUpdate = false) => {
    const response = await Api.admin.getPatientVitalSigns(state.token, patientId, deviceId, 100);
    const readings = response.readings;
    
    // NUEVO: Obtener predicciones de IA para las lecturas
    const predictions = await Api.ai.batchPredict(state.token, readings);
    
    // Combinar lecturas con predicciones
    const enrichedReadings = readings.map((reading, idx) => ({
        ...reading,
        ai_prediction: predictions[idx]
    }));
    
    // Renderizar gráficas con indicador de probabilidad
    renderVitalSignsWithAI(enrichedReadings);
};
```

---

## 🚀 Plan de Implementación

### Fase 1: Crear Servicio de IA (1-2 días)
1. Crear estructura del servicio `services/ai-prediction/`
2. Implementar Flask app con endpoints `/predict` y `/batch-predict`
3. Cargar modelo `modelo_salud_randomforest.pkl`
4. Implementar autenticación JWT
5. Pruebas unitarias

### Fase 2: Configurar Gateway (30 min)
1. Agregar ruta `/ai/*` → `ai-prediction:5008`
2. Actualizar `docker-compose.yml`

### Fase 3: Integración Desktop App (2-3 días)
1. Crear `AIService.java`
2. Modificar `VitalSignsChartPanel.java` para usar IA
3. Implementar fallback a reglas hardcodeadas
4. Agregar indicador visual de "Evaluado por IA"

### Fase 4: Integración Org-Admin (1-2 días)
1. Crear `Api.ai.predict()` y `Api.ai.batchPredict()`
2. Modificar `loadVitalSignsData()` para incluir predicciones
3. Agregar indicador visual de probabilidad en gráficas

### Fase 5: Testing End-to-End (1 día)
1. Pruebas de integración completa
2. Pruebas de rendimiento (batch predictions)
3. Pruebas de fallback

---

## 📊 Ventajas de esta Arquitectura

### ✅ Ventajas Técnicas
- **Desacoplamiento**: Desktop-app y org-admin no dependen del modelo directamente
- **Escalabilidad**: El servicio de IA puede escalar independientemente
- **Versionado**: Puedes actualizar el modelo sin recompilar clientes
- **Monitoreo**: Logs centralizados de todas las predicciones
- **Fallback**: Si el servicio falla, usa reglas hardcodeadas

### ✅ Ventajas de Negocio
- **Consistencia**: Mismas predicciones en todos los clientes
- **Auditoría**: Todas las predicciones quedan registradas
- **Mejora continua**: Puedes reentrenar el modelo y desplegarlo sin afectar clientes
- **Multi-modelo**: Puedes tener múltiples modelos (RF, XGBoost, NN) y elegir el mejor

---

## 🎓 Recomendación Final

**Implementa el Microservicio de IA** porque:

1. ✅ Se alinea con tu arquitectura existente
2. ✅ Permite reutilizar el modelo en desktop-app Y org-admin
3. ✅ Facilita actualizaciones del modelo
4. ✅ Mantiene la lógica de negocio en el backend
5. ✅ Es escalable y mantenible

**Alternativa rápida (no recomendada a largo plazo)**:
- Exportar el modelo a PMML/ONNX y usarlo directamente en Java
- **Problema**: Tienes que mantener 2 implementaciones (Java + Python)

---

## 📝 Próximos Pasos

¿Quieres que te ayude a:
1. **Crear el microservicio de IA completo** (código Python + Flask)?
2. **Modificar la desktop-app** para integrar el servicio?
3. **Actualizar org-admin** para mostrar predicciones?
4. **Todo lo anterior** paso a paso?

Dime por dónde quieres empezar y te genero el código completo. 🚀
