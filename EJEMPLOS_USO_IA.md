# 💡 EJEMPLOS PRÁCTICOS DE USO DEL SERVICIO DE IA

Este documento contiene ejemplos de código completos y funcionales para integrar el servicio de IA.

---

## 📱 EJEMPLO 1: Desktop App - Predicción Simple

### Código Java Completo

```java
package com.heartguard.desktop.ui;

import com.heartguard.desktop.api.AIService;
import com.heartguard.desktop.api.AIService.AIServiceException;
import com.heartguard.desktop.models.AIPrediction;
import com.heartguard.desktop.models.AIAlert;

import javax.swing.*;
import java.awt.*;

public class VitalSignsMonitor extends JPanel {
    private final AIService aiService;
    private JLabel predictionLabel;
    private JTextArea alertsArea;
    
    public VitalSignsMonitor() {
        this.aiService = AIService.getInstance();
        initUI();
    }
    
    private void initUI() {
        setLayout(new BorderLayout(10, 10));
        setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Panel de predicción
        JPanel predictionPanel = new JPanel(new GridLayout(2, 1));
        predictionPanel.setBorder(
            BorderFactory.createTitledBorder("🧠 Análisis de IA")
        );
        
        predictionLabel = new JLabel("Sin datos");
        predictionLabel.setFont(new Font("SansSerif", Font.BOLD, 16));
        
        alertsArea = new JTextArea(5, 40);
        alertsArea.setEditable(false);
        alertsArea.setLineWrap(true);
        alertsArea.setWrapStyleWord(true);
        
        predictionPanel.add(predictionLabel);
        predictionPanel.add(new JScrollPane(alertsArea));
        
        add(predictionPanel, BorderLayout.CENTER);
        
        // Botón de test
        JButton testButton = new JButton("🧪 Probar IA");
        testButton.addActionListener(e -> testPrediction());
        add(testButton, BorderLayout.SOUTH);
    }
    
    private void testPrediction() {
        try {
            // Verificar salud del servicio primero
            if (!aiService.isHealthy()) {
                JOptionPane.showMessageDialog(
                    this,
                    "Servicio de IA no disponible",
                    "Error",
                    JOptionPane.ERROR_MESSAGE
                );
                return;
            }
            
            // Valores de ejemplo (obtener de los datos reales)
            double gpsLong = -99.1332;
            double gpsLat = 19.4326;
            double heartRate = 135.0;  // Taquicardia
            double spo2 = 88.0;        // Hipoxemia
            double systolicBp = 160.0; // Hipertensión
            double diastolicBp = 100.0;
            double temperature = 39.5; // Fiebre
            
            // Realizar predicción
            AIPrediction prediction = aiService.predictHealth(
                gpsLong, gpsLat,
                heartRate, spo2,
                systolicBp, diastolicBp,
                temperature,
                0.6  // threshold
            );
            
            // Actualizar UI
            displayPrediction(prediction);
            
        } catch (AIServiceException ex) {
            JOptionPane.showMessageDialog(
                this,
                "Error en predicción: " + ex.getMessage(),
                "Error",
                JOptionPane.ERROR_MESSAGE
            );
        }
    }
    
    private void displayPrediction(AIPrediction prediction) {
        // Actualizar etiqueta de probabilidad
        String probText = String.format(
            "Probabilidad de problema: %.1f%% - Riesgo: %s",
            prediction.getProbabilityPercent(),
            prediction.getRiskLevel()
        );
        predictionLabel.setText(probText);
        
        // Color según nivel de riesgo
        Color labelColor;
        switch (prediction.getRiskLevel()) {
            case HIGH:
                labelColor = Color.RED;
                break;
            case MEDIUM:
                labelColor = new Color(255, 165, 0); // Orange
                break;
            default:
                labelColor = new Color(0, 128, 0); // Green
        }
        predictionLabel.setForeground(labelColor);
        
        // Mostrar alertas
        StringBuilder alertsText = new StringBuilder();
        
        if (prediction.hasAlerts()) {
            alertsText.append("⚠️ ALERTAS DETECTADAS:\n\n");
            
            for (AIAlert alert : prediction.getAlerts()) {
                String severity = alert.isHighSeverity() ? "🔴 ALTA" : "🟡 MEDIA";
                alertsText.append(severity).append(" - ");
                alertsText.append(alert.getFullDescription());
                alertsText.append("\n");
            }
        } else {
            alertsText.append("✓ Sin alertas - Valores normales");
        }
        
        alertsArea.setText(alertsText.toString());
        alertsArea.setForeground(
            prediction.hasCriticalAlerts() ? Color.RED : Color.BLACK
        );
    }
    
    public void updateWithVitalSigns(
        double heartRate, 
        double spo2,
        double systolicBp,
        double diastolicBp,
        double temperature
    ) {
        // Método para actualizar con datos reales
        try {
            AIPrediction prediction = aiService.predictHealth(
                -99.1332, 19.4326,  // GPS default
                heartRate, spo2,
                systolicBp, diastolicBp,
                temperature
            );
            
            displayPrediction(prediction);
            
        } catch (AIServiceException ex) {
            predictionLabel.setText("Error en predicción");
            predictionLabel.setForeground(Color.RED);
        }
    }
}
```

---

## 📊 EJEMPLO 2: Integración en VitalSignsChartPanel

### Modificación de VitalSignsChartPanel.java

```java
// Al inicio de la clase
private final AIService aiService;
private Timer aiPredictionTimer;
private boolean enableAIPredictions = true;

// En el constructor
public VitalSignsChartPanel(String patientId, String deviceId) {
    this.patientId = patientId;
    this.deviceId = deviceId;
    this.apiClient = ApiClient.getInstance();
    this.aiService = AIService.getInstance(); // NUEVO
    
    // Compartir token
    this.aiService.setAccessToken(apiClient.getAccessToken());
    
    initializeUI();
    loadVitalSignsData();
    startAutoRefresh();
    startAIPredictions(); // NUEVO
}

// Nuevo método para iniciar predicciones periódicas
private void startAIPredictions() {
    aiPredictionTimer = new Timer(5000, e -> {  // Cada 5 segundos
        if (enableAIPredictions) {
            performAIPrediction();
        }
    });
    aiPredictionTimer.start();
}

// Método para realizar predicción
private void performAIPrediction() {
    SwingUtilities.invokeLater(() -> {
        try {
            // Obtener últimos valores de las series
            if (temperatureSeries.getItemCount() == 0) return;
            
            int lastIndex = temperatureSeries.getItemCount() - 1;
            
            double temp = temperatureSeries.getValue(lastIndex).doubleValue();
            double hr = heartRateSeries.getItemCount() > 0 ? 
                       heartRateSeries.getValue(lastIndex).doubleValue() : 75.0;
            double spo2 = spo2Series.getItemCount() > 0 ? 
                         spo2Series.getValue(lastIndex).doubleValue() : 98.0;
            double systolic = bpSystolicSeries.getItemCount() > 0 ? 
                             bpSystolicSeries.getValue(lastIndex).doubleValue() : 120.0;
            double diastolic = bpDiastolicSeries.getItemCount() > 0 ? 
                              bpDiastolicSeries.getValue(lastIndex).doubleValue() : 80.0;
            
            // Llamar al servicio de IA
            AIPrediction prediction = aiService.predictHealth(
                -99.1332, 19.4326,  // GPS - obtener del paciente
                hr, spo2,
                systolic, diastolic,
                temp,
                0.6
            );
            
            // Actualizar UI con predicción
            updateUIWithPrediction(prediction);
            
            // Si hay problema crítico, mostrar alerta
            if (prediction.hasCriticalAlerts()) {
                showCriticalAlert(prediction);
            }
            
        } catch (AIService.AIServiceException ex) {
            System.err.println("Error en predicción de IA: " + ex.getMessage());
            // Continuar sin IA (fallback a reglas hardcodeadas)
        }
    });
}

// Actualizar UI con predicción
private void updateUIWithPrediction(AIPrediction prediction) {
    // Actualizar panel de información
    if (aiInfoPanel != null) {
        remove(aiInfoPanel);
    }
    
    aiInfoPanel = createAIInfoPanel(prediction);
    add(aiInfoPanel, BorderLayout.NORTH);
    revalidate();
    repaint();
    
    // Marcar en gráficas si hay alertas
    if (prediction.hasAlerts()) {
        highlightAlertsInCharts(prediction);
    }
}

// Crear panel de información de IA
private JPanel createAIInfoPanel(AIPrediction prediction) {
    JPanel panel = new JPanel();
    panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
    panel.setBorder(
        BorderFactory.createTitledBorder("🧠 Análisis de IA (Tiempo Real)")
    );
    
    // Label de probabilidad
    JLabel probLabel = new JLabel(String.format(
        "Riesgo: %.1f%% (%s) - %s",
        prediction.getProbabilityPercent(),
        prediction.getRiskLevel(),
        prediction.hasProblem() ? "⚠️ ATENCIÓN" : "✓ Normal"
    ));
    
    probLabel.setFont(new Font("SansSerif", Font.BOLD, 14));
    probLabel.setForeground(
        prediction.getRiskLevel() == AIPrediction.RiskLevel.HIGH ? Color.RED :
        prediction.getRiskLevel() == AIPrediction.RiskLevel.MEDIUM ? new Color(255, 165, 0) :
        new Color(0, 128, 0)
    );
    
    panel.add(probLabel);
    
    // Mostrar alertas
    if (prediction.hasAlerts()) {
        JTextArea alertsArea = new JTextArea(3, 50);
        alertsArea.setEditable(false);
        alertsArea.setLineWrap(true);
        
        StringBuilder alerts = new StringBuilder();
        for (AIAlert alert : prediction.getAlerts()) {
            alerts.append("• ").append(alert.getMessage());
            if (alert.hasValue()) {
                alerts.append(String.format(" (%.1f %s)", 
                    alert.getValue(), alert.getUnit()));
            }
            alerts.append("\n");
        }
        
        alertsArea.setText(alerts.toString());
        alertsArea.setForeground(
            prediction.hasCriticalAlerts() ? Color.RED : Color.ORANGE
        );
        
        panel.add(new JScrollPane(alertsArea));
    }
    
    return panel;
}

// Resaltar alertas en gráficas
private void highlightAlertsInCharts(AIPrediction prediction) {
    for (AIAlert alert : prediction.getAlerts()) {
        switch (alert.getType()) {
            case "FEVER":
            case "HYPOTHERMIA":
                if (alert.hasValue()) {
                    addValueMarker(temperaturePlot, alert.getValue(), 
                                 alert.getMessage(), Color.RED);
                }
                break;
                
            case "ARRHYTHMIA":
                if (alert.hasValue()) {
                    addValueMarker(heartRatePlot, alert.getValue(), 
                                 alert.getMessage(), Color.ORANGE);
                }
                break;
                
            case "DESAT":
                if (alert.hasValue()) {
                    addValueMarker(spo2Plot, alert.getValue(), 
                                 alert.getMessage(), Color.RED);
                }
                break;
        }
    }
}

// Helper para agregar marcador en gráfica
private void addValueMarker(XYPlot plot, double value, String label, Color color) {
    ValueMarker marker = new ValueMarker(value);
    marker.setPaint(color);
    marker.setStroke(new BasicStroke(2.0f));
    marker.setLabel(label);
    marker.setLabelFont(new Font("SansSerif", Font.BOLD, 10));
    marker.setLabelPaint(color);
    plot.addRangeMarker(marker, org.jfree.ui.Layer.FOREGROUND);
}

// Mostrar alerta crítica
private void showCriticalAlert(AIPrediction prediction) {
    StringBuilder message = new StringBuilder();
    message.append("🚨 ALERTA CRÍTICA - Modelo de IA\n\n");
    message.append(String.format("Probabilidad de problema: %.1f%%\n\n", 
                                prediction.getProbabilityPercent()));
    message.append("Alertas detectadas:\n");
    
    for (AIAlert alert : prediction.getAlerts()) {
        if (alert.isHighSeverity()) {
            message.append("• ").append(alert.getFullDescription()).append("\n");
        }
    }
    
    JOptionPane.showMessageDialog(
        this,
        message.toString(),
        "Alerta de IA - Acción Requerida",
        JOptionPane.WARNING_MESSAGE
    );
}

// Cleanup
@Override
public void dispose() {
    if (aiPredictionTimer != null) {
        aiPredictionTimer.stop();
    }
    super.dispose();
}
```

---

## 🌐 EJEMPLO 3: Org-Admin (JavaScript) - Pendiente

### api.js - Cliente API

```javascript
// Agregar en assets/js/api.js

const Api = {
    // ... código existente ...
    
    ai: {
        /**
         * Predice problemas de salud basado en signos vitales
         */
        async predict(token, vitalSigns) {
            const response = await requestJson('/ai/predict', {
                method: 'POST',
                token,
                body: vitalSigns
            });
            return response;
        },
        
        /**
         * Predicción en lote
         */
        async batchPredict(token, readings) {
            const response = await requestJson('/ai/batch-predict', {
                method: 'POST',
                token,
                body: { readings }
            });
            return response;
        },
        
        /**
         * Health check del servicio de IA
         */
        async health() {
            const response = await requestJson('/ai/health', {
                method: 'GET'
            });
            return response;
        },
        
        /**
         * Información del modelo
         */
        async modelInfo() {
            const response = await requestJson('/ai/model/info', {
                method: 'GET'
            });
            return response;
        }
    }
};
```

### app.js - Integración en gráficas

```javascript
// Agregar en loadVitalSignsData()

const loadVitalSignsData = async (patientId, deviceId, containerId, isUpdate = false) => {
    // ... código existente para obtener datos ...
    
    // NUEVO: Obtener predicción de IA
    if (data.readings && data.readings.length > 0) {
        const latestReading = data.readings[data.readings.length - 1];
        
        try {
            const prediction = await Api.ai.predict(state.token, {
                gps_longitude: -99.1332,
                gps_latitude: 19.4326,
                heart_rate: latestReading.heart_rate || 75,
                spo2: latestReading.spo2 || 98,
                systolic_bp: latestReading.systolic_bp || 120,
                diastolic_bp: latestReading.diastolic_bp || 80,
                temperature: latestReading.temperature || 36.7
            });
            
            // Mostrar predicción en UI
            displayAIPrediction(containerId, prediction);
            
        } catch (error) {
            console.error('Error en predicción de IA:', error);
        }
    }
    
    // ... resto del código ...
};

// Nueva función para mostrar predicción
function displayAIPrediction(containerId, prediction) {
    const container = document.getElementById(containerId);
    
    // Buscar o crear panel de IA
    let aiPanel = container.querySelector('.ai-prediction-panel');
    if (!aiPanel) {
        aiPanel = document.createElement('div');
        aiPanel.className = 'ai-prediction-panel';
        container.insertBefore(aiPanel, container.firstChild);
    }
    
    // Color según riesgo
    const riskColor = 
        prediction.probability >= 0.6 ? '#dc3545' :  // Rojo
        prediction.probability >= 0.3 ? '#ffc107' :  // Amarillo
        '#28a745';  // Verde
    
    // HTML
    aiPanel.innerHTML = `
        <div class="ai-prediction" style="
            background: linear-gradient(135deg, ${riskColor}22 0%, ${riskColor}11 100%);
            border-left: 4px solid ${riskColor};
            padding: 12px;
            margin-bottom: 15px;
            border-radius: 4px;
        ">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 24px;">🧠</span>
                <div>
                    <strong>Análisis de IA</strong>
                    <div style="font-size: 12px; color: #666;">
                        Actualizado en tiempo real
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 10px;">
                <div style="
                    font-size: 18px;
                    font-weight: bold;
                    color: ${riskColor};
                    margin-bottom: 5px;
                ">
                    Probabilidad: ${(prediction.probability * 100).toFixed(1)}%
                    ${prediction.has_problem ? '⚠️' : '✓'}
                </div>
                
                ${prediction.alerts && prediction.alerts.length > 0 ? `
                    <div style="margin-top: 10px;">
                        <strong style="color: #333;">Alertas:</strong>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            ${prediction.alerts.map(alert => `
                                <li style="color: ${alert.severity === 'high' ? '#dc3545' : '#ffc107'};">
                                    ${alert.message}
                                    ${alert.value ? `(${alert.value} ${alert.unit || ''})` : ''}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : `
                    <div style="color: #28a745; margin-top: 5px;">
                        ✓ Sin alertas - Valores normales
                    </div>
                `}
            </div>
        </div>
    `;
}
```

---

## 🧪 EJEMPLO 4: Tests con cURL

### Test 1: Health Check

```bash
curl -X GET http://localhost:5008/health | jq
```

### Test 2: Predicción (con token)

```bash
# Primero obtener token
TOKEN=$(curl -X POST http://localhost:8080/auth/login/user \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}' \
  | jq -r '.access_token')

# Luego hacer predicción
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
  }' | jq
```

### Test 3: Batch Prediction

```bash
curl -X POST http://localhost:5008/batch-predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
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
      {
        "gps_longitude": -99.1332,
        "gps_latitude": 19.4326,
        "heart_rate": 135,
        "spo2": 88,
        "systolic_bp": 160,
        "diastolic_bp": 100,
        "temperature": 39.5,
        "timestamp": "2025-11-23T22:00:00Z"
      }
    ],
    "threshold": 0.6
  }' | jq
```

---

## 💻 EJEMPLO 5: Python Test Script

```python
import requests
import json

BASE_URL = "http://localhost:5008"

# 1. Health Check
def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health: {response.json()}")

# 2. Predicción con valores normales
def test_normal_values():
    data = {
        "gps_longitude": -99.1332,
        "gps_latitude": 19.4326,
        "heart_rate": 75,
        "spo2": 98,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "temperature": 36.7
    }
    
    # Nota: Agregar token en headers['Authorization']
    response = requests.post(
        f"{BASE_URL}/predict",
        json=data
        # headers={"Authorization": f"Bearer {token}"}
    )
    
    result = response.json()
    print(f"\nValores normales:")
    print(f"  Has Problem: {result['has_problem']}")
    print(f"  Probability: {result['probability']:.2%}")
    print(f"  Alerts: {len(result['alerts'])}")

# 3. Predicción con valores anormales
def test_abnormal_values():
    data = {
        "gps_longitude": -99.1332,
        "gps_latitude": 19.4326,
        "heart_rate": 135,
        "spo2": 88,
        "systolic_bp": 160,
        "diastolic_bp": 100,
        "temperature": 39.5
    }
    
    response = requests.post(f"{BASE_URL}/predict", json=data)
    result = response.json()
    
    print(f"\nValores anormales:")
    print(f"  Has Problem: {result['has_problem']}")
    print(f"  Probability: {result['probability']:.2%}")
    print(f"  Alerts:")
    for alert in result['alerts']:
        print(f"    - {alert['type']}: {alert['message']}")

if __name__ == "__main__":
    test_health()
    # test_normal_values()  # Descomentar con token
    # test_abnormal_values()
```

---

## 📚 REFERENCIAS

- **Arquitectura:** `ARQUITECTURA_INTEGRACION_IA.md`
- **Guía Desktop:** `GUIA_INTEGRACION_IA_DESKTOP.md`
- **Ejecución:** `EJECUCION_SERVICIO_IA.md`
- **Resumen:** `IMPLEMENTACION_IA_COMPLETADA.md`

---

**¡Estos ejemplos están listos para copiar y pegar!** 🚀
