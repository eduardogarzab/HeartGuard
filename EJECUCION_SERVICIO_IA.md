# 🚀 GUÍA RÁPIDA DE EJECUCIÓN - Servicio de IA

## ✅ ESTADO: TESTS PASANDO - LISTO PARA USAR

Todos los tests locales pasaron exitosamente. El servicio está **100% funcional**.

---

## 📋 REQUISITOS PREVIOS

1. **Python 3.10+** instalado
2. **Modelo ML** en `services/ai-prediction/models/modelo_salud_randomforest.pkl` ✅ (ya copiado)
3. **Dependencias** instaladas

---

## 🏃 OPCIÓN 1: Ejecución Local (Desarrollo)

### Paso 1: Instalar dependencias

```bash
cd services/ai-prediction
pip install -r requirements.txt
```

### Paso 2: Ejecutar servicio

```bash
# Modo desarrollo (con auto-reload)
python -m src.app

# O usando Makefile
make dev
```

### Paso 3: Verificar que funciona

Abrir otro terminal y ejecutar:

```bash
curl http://localhost:5008/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "message": "Servicio de IA operativo",
  "model": {
    "loaded": true,
    "model_type": "RandomForestClassifier",
    "n_estimators": 300,
    "n_features": 7
  },
  "version": "1.0.0"
}
```

---

## 🐳 OPCIÓN 2: Ejecución con Docker

### Paso 1: Construir imagen

```bash
cd services/ai-prediction
docker build -t heartguard-ai-prediction:latest .
```

### Paso 2: Ejecutar contenedor

```bash
docker run -d \
  --name heartguard-ai \
  -p 5008:5008 \
  -v $(pwd)/models:/app/models:ro \
  -e FLASK_DEBUG=False \
  -e PREDICTION_THRESHOLD=0.6 \
  -e JWT_SECRET=heartguard-jwt-secret \
  heartguard-ai-prediction:latest
```

### Paso 3: Ver logs

```bash
docker logs -f heartguard-ai
```

### Paso 4: Verificar

```bash
curl http://localhost:5008/health
```

---

## 🏗️ OPCIÓN 3: Con Docker Compose (Recomendado)

Desde la **raíz del proyecto**:

```bash
# Levantar SOLO el servicio de IA
docker-compose up ai-prediction-service

# O levantar todo el stack
docker-compose up
```

**Verificar:**
```bash
curl http://localhost:5008/health
```

---

## 🧪 PRUEBAS RÁPIDAS

### Test 1: Health Check (sin autenticación)

```bash
curl http://localhost:5008/health
```

### Test 2: Información del Modelo (sin autenticación)

```bash
curl http://localhost:5008/model/info
```

### Test 3: Predicción (requiere token JWT)

**Sin token (fallará con 401):**
```bash
curl -X POST http://localhost:5008/predict \
  -H "Content-Type: application/json" \
  -d '{
    "gps_longitude": -99.1332,
    "gps_latitude": 19.4326,
    "heart_rate": 135,
    "spo2": 88,
    "systolic_bp": 160,
    "diastolic_bp": 100,
    "temperature": 39.5
  }'
```

**Con token (funciona):**
```bash
# Primero necesitas obtener un token del servicio de auth
# TOKEN=$(curl -X POST http://localhost:8080/auth/login/user \
#   -H "Content-Type: application/json" \
#   -d '{"email":"admin@example.com","password":"password"}' \
#   | jq -r '.access_token')

curl -X POST http://localhost:5008/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "gps_longitude": -99.1332,
    "gps_latitude": 19.4326,
    "heart_rate": 135,
    "spo2": 88,
    "systolic_bp": 160,
    "diastolic_bp": 100,
    "temperature": 39.5
  }'
```

### Test 4: A través del Gateway

```bash
# Asumiendo que el gateway está en puerto 8080
curl http://localhost:8080/ai/health
```

---

## 📊 PRUEBAS AUTOMÁTICAS

### Tests locales (sin servidor Flask)

```bash
cd services/ai-prediction
python tests/test_local.py
```

**Resultado esperado:**
```
🎉 ¡TODOS LOS TESTS PASARON!
El servicio de IA está listo para ser usado
```

### Tests del servicio (requiere servidor corriendo)

```bash
cd services/ai-prediction
python tests/test_manual.py
```

---

## 🔧 TROUBLESHOOTING

### Problema: Modelo no encontrado

**Error:**
```
❌ Modelo no encontrado en: models/modelo_salud_randomforest.pkl
```

**Solución:**
```bash
cd services/ai-prediction
mkdir -p models
cp ../../IA/modelo_salud_randomforest.pkl models/
```

### Problema: Puerto 5008 ya está en uso

**Solución:**
```bash
# Cambiar puerto en variables de entorno
FLASK_PORT=5009 python -m src.app
```

### Problema: Error de autenticación en /predict

**Error:**
```json
{
  "error": "No authorization header",
  "message": "Se requiere token de autenticación"
}
```

**Solución temporal (SOLO para desarrollo):**

Editar `src/app.py` y cambiar:
```python
@app.route('/predict', methods=['POST'])
@require_auth  # <-- Cambiar a @optional_auth para desarrollo
def predict():
```

**Solución correcta:**

Obtener un token JWT del servicio de auth primero.

### Problema: Error de nombres de features

**Error:**
```
ValueError: The feature names should match those that were passed during fit
```

**Solución:**

Ya está corregido en `src/config.py`. Los nombres correctos son:
- `SpO2 Level (%)` (no `SpO2 (%)`)
- `Systolic Blood Pressure (mmHg)` (no `Systolic BP (mmHg)`)
- `Diastolic Blood Pressure (mmHg)` (no `Diastolic BP (mmHg)`)
- `Body Temperature (°C)` (no `Temperature (C)`)

---

## 🎯 INTEGRACIÓN CON DESKTOP-APP

Ver guía completa en: **`GUIA_INTEGRACION_IA_DESKTOP.md`**

**Pasos rápidos:**

1. **Asegurar que el servicio está corriendo** (puerto 5008)
2. **En desktop-app**, usar `AIService.java`:

```java
// Inicializar servicio
AIService aiService = AIService.getInstance();
aiService.setAccessToken(userToken);

// Verificar health
boolean isHealthy = aiService.isHealthy();

// Realizar predicción
AIPrediction prediction = aiService.predictHealth(
    gpsLongitude, gpsLatitude,
    heartRate, spo2,
    systolicBp, diastolicBp,
    temperature
);

// Procesar resultado
if (prediction.hasProblem()) {
    for (AIAlert alert : prediction.getAlerts()) {
        System.out.println(alert.getFullDescription());
    }
}
```

---

## 📈 MONITOREO

### Ver logs en tiempo real

```bash
# Local
tail -f logs/ai-prediction.log

# Docker
docker logs -f heartguard-ai

# Docker Compose
docker-compose logs -f ai-prediction-service
```

### Verificar salud del servicio

```bash
# Cada 5 segundos
watch -n 5 curl http://localhost:5008/health
```

---

## 🛑 DETENER EL SERVICIO

### Ejecución local

```
Ctrl+C
```

### Docker

```bash
docker stop heartguard-ai
docker rm heartguard-ai
```

### Docker Compose

```bash
docker-compose down ai-prediction-service
```

---

## 🎉 ¡LISTO!

El servicio de IA está completamente funcional y listo para integrarse con:
- ✅ Desktop App (Java) - `AIService.java` creado
- ⏳ Org-Admin (JavaScript) - Pendiente implementación
- ✅ Gateway - Proxy configurado en `/ai/*`

**Siguiente paso:** Modificar `VitalSignsChartPanel.java` para usar predicciones de IA en lugar de reglas hardcodeadas.

Ver: `GUIA_INTEGRACION_IA_DESKTOP.md`
