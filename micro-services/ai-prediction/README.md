# 🧠 HeartGuard AI Prediction Service

Microservicio para predicciones de salud usando modelo RandomForest.

## 📋 Descripción

Este servicio proporciona predicciones de problemas de salud basadas en signos vitales utilizando un modelo de Machine Learning entrenado (RandomForest Classifier).

## 🚀 Características

- **Predicción individual**: Analiza signos vitales en tiempo real
- **Predicción en lote**: Procesa múltiples lecturas simultáneamente
- **Alertas inteligentes**: Genera alertas específicas basadas en rangos clínicos
- **Autenticación JWT**: Endpoints protegidos
- **Health checks**: Monitoreo del estado del servicio
- **Recarga de modelo**: Actualiza el modelo sin reiniciar el servicio

## 🛠️ Tecnologías

- Python 3.10+
- Flask 3.0
- scikit-learn 1.3
- pandas, numpy
- JWT para autenticación

## 📦 Instalación

```bash
cd micro-services/ai-prediction
pip install -r requirements.txt
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5008
FLASK_DEBUG=False

# Modelo
PREDICTION_THRESHOLD=0.6

# JWT
JWT_SECRET=your-secret-key-change-in-production
```

### Modelo

El servicio requiere el archivo `modelo_salud_randomforest.pkl` en la carpeta `models/`:

```bash
mkdir -p models
cp ../../IA/modelo_salud_randomforest.pkl models/
```

## 🏃 Ejecución

### Modo Desarrollo

```bash
make dev
```

### Modo Producción

```bash
make run
```

### Con Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5008 src.app:app
```

## 📡 API Endpoints

### 1. Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Servicio de IA operativo",
  "model": {
    "loaded": true,
    "n_estimators": 300,
    "n_features": 7
  }
}
```

### 2. Predicción Individual

```bash
POST /predict
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "gps_longitude": -99.1332,
  "gps_latitude": 19.4326,
  "heart_rate": 75,
  "spo2": 98,
  "systolic_bp": 120,
  "diastolic_bp": 80,
  "temperature": 36.7,
  "threshold": 0.6
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
      "type": "GENERAL_RISK",
      "severity": "high",
      "message": "Riesgo general detectado por el modelo",
      "probability": 0.87
    },
    {
      "type": "ARRHYTHMIA",
      "severity": "high",
      "message": "Posible arritmia cardíaca",
      "value": 135,
      "unit": "bpm"
    }
  ],
  "processed_at": "2025-11-23T22:00:00Z"
}
```

### 3. Predicción en Lote

```bash
POST /batch-predict
Authorization: Bearer <token>
Content-Type: application/json
```

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
    }
  ],
  "threshold": 0.6
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
      "alerts": [],
      "processed_at": "2025-11-23T22:00:00Z"
    }
  ],
  "summary": {
    "total": 1,
    "problems_detected": 0,
    "avg_probability": 0.15
  }
}
```

### 4. Información del Modelo

```bash
GET /model/info
```

### 5. Recargar Modelo

```bash
POST /model/reload
Authorization: Bearer <token>
```

## 🧪 Pruebas

```bash
make test
```

## 🐳 Docker

```bash
# Construir imagen
make docker-build

# Ejecutar contenedor
make docker-run
```

## 📊 Tipos de Alertas

- **GENERAL_RISK**: Riesgo general detectado por el modelo
- **ARRHYTHMIA**: Frecuencia cardíaca anormal (< 60 o > 100 bpm)
- **DESAT**: Desaturación de oxígeno (< 95%)
- **HYPERTENSION**: Presión arterial alta (≥ 140/90 mmHg)
- **HYPOTENSION**: Presión arterial baja (< 90/60 mmHg)
- **FEVER**: Fiebre (≥ 38°C)
- **HYPOTHERMIA**: Hipotermia (< 36°C)

## 🔒 Seguridad

- Todos los endpoints (excepto `/health` y `/model/info`) requieren autenticación JWT
- El token debe incluirse en el header: `Authorization: Bearer <token>`
- Configura `JWT_SECRET` en producción

## 📝 Logs

El servicio registra:
- Todas las requests recibidas
- Predicciones realizadas
- Errores y excepciones
- Carga/recarga del modelo

## 🚨 Troubleshooting

### Modelo no encontrado
```
❌ Modelo no encontrado en: models/modelo_salud_randomforest.pkl
```
**Solución**: Copia el archivo del modelo a `models/`

### Error de autenticación
```
{
  "error": "Invalid token",
  "message": "Token de autenticación inválido"
}
```
**Solución**: Verifica que el token JWT sea válido y no haya expirado

### Error de features
```
{
  "error": "Validation error",
  "message": "Falta el campo requerido: heart_rate"
}
```
**Solución**: Asegúrate de incluir todos los campos requeridos en el request

## 📄 Licencia

HeartGuard © 2025
