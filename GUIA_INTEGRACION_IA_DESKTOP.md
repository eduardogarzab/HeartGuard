# 🎉 Guía de Integración del Modelo de IA en Desktop-App

Esta guía muestra cómo modificar `VitalSignsChartPanel.java` para usar predicciones de IA en lugar de reglas hardcodeadas.

## 📋 Paso 1: Importar las clases necesarias

Agregar al inicio de `VitalSignsChartPanel.java`:

```java
import com.heartguard.desktop.api.AIService;
import com.heartguard.desktop.api.AIService.AIServiceException;
import com.heartguard.desktop.models.AIPrediction;
import com.heartguard.desktop.models.AIAlert;
import java.awt.Color;
import java.awt.Font;
```

## 📋 Paso 2: Agregar campo de instancia

Dentro de la clase `VitalSignsChartPanel`, agregar:

```java
private final AIService aiService;
private boolean useAIPredictions = true; // Flag para activar/desactivar IA
```

## 📋 Paso 3: Inicializar el servicio en el constructor

```java
public VitalSignsChartPanel(String patientId, String deviceId) {
    this.patientId = patientId;
    this.deviceId = deviceId;
    this.apiClient = ApiClient.getInstance();
    this.aiService = AIService.getInstance(); // <-- NUEVO
    
    // Compartir el token con AIService
    this.aiService.setAccessToken(apiClient.getAccessToken());
    
    initializeUI();
    loadVitalSignsData();
    startAutoRefresh();
}
```

## 📋 Paso 4: Reemplazar lógica de alertas hardcodeadas

### ANTES (Líneas 500-540):

```java
// ❌ ANTIGUO: Reglas hardcodeadas
private void setupTemperatureChart(XYPlot plot) {
    // Zona de hipotermia (< 36°C)
    IntervalMarker hypothermia = new IntervalMarker(
        35.0, 36.0,
        new Color(135, 206, 250, 100),
        new BasicStroke(1.0f),
        Color.BLUE,
        new BasicStroke(1.0f),
        0.5f
    );
    hypothermia.setLabel("Hipotermia");
    plot.addRangeMarker(hypothermia, Layer.BACKGROUND);
    
    // Zona normal (36.1 - 37.2°C)
    IntervalMarker normalTemp = new IntervalMarker(
        36.1, 37.2, ZONE_NORMAL
    );
    normalTemp.setLabel("Normal");
    plot.addRangeMarker(normalTemp, Layer.BACKGROUND);
    
    // Línea de fiebre (38°C)
    ValueMarker feverLine = new ValueMarker(38.0);
    feverLine.setPaint(Color.RED);
    feverLine.setStroke(new BasicStroke(2.0f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND,
        1.0f, new float[]{6.0f, 6.0f}, 0.0f));
    feverLine.setLabel("Fiebre");
    feverLine.setLabelFont(new Font("SansSerif", Font.BOLD, 12));
    feverLine.setLabelPaint(Color.RED);
    plot.addRangeMarker(feverLine, Layer.FOREGROUND);
}
```

### DESPUÉS:

```java
// ✅ NUEVO: Alertas dinámicas de IA
private void checkAlertsWithIA(TimeSeries tempSeries, TimeSeries hrSeries, 
                               TimeSeries spo2Series, TimeSeries bpSystolicSeries,
                               TimeSeries bpDiastolicSeries) {
    if (!useAIPredictions) {
        // Fallback a reglas hardcodeadas si IA está desactivada
        setupHardcodedAlerts();
        return;
    }
    
    try {
        // Obtener valores más recientes
        if (tempSeries.getItemCount() == 0) return;
        
        int lastIndex = tempSeries.getItemCount() - 1;
        double temperature = tempSeries.getValue(lastIndex).doubleValue();
        double heartRate = hrSeries.getItemCount() > 0 ? 
                          hrSeries.getValue(lastIndex).doubleValue() : 75.0;
        double spo2 = spo2Series.getItemCount() > 0 ? 
                     spo2Series.getValue(lastIndex).doubleValue() : 98.0;
        double systolicBp = bpSystolicSeries.getItemCount() > 0 ? 
                           bpSystolicSeries.getValue(lastIndex).doubleValue() : 120.0;
        double diastolicBp = bpDiastolicSeries.getItemCount() > 0 ? 
                            bpDiastolicSeries.getValue(lastIndex).doubleValue() : 80.0;
        
        // GPS (puedes obtenerlo de los datos del paciente o usar valores por defecto)
        double gpsLongitude = -99.1332; // Default CDMX
        double gpsLatitude = 19.4326;
        
        // Llamar al servicio de IA
        AIPrediction prediction = aiService.predictHealth(
            gpsLongitude, gpsLatitude,
            heartRate, spo2,
            systolicBp, diastolicBp,
            temperature,
            0.6 // threshold
        );
        
        // Mostrar predicción en la UI
        displayAIPrediction(prediction);
        
        // Si hay problema, mostrar alertas específicas
        if (prediction.hasProblem()) {
            highlightAlertsInCharts(prediction);
        }
        
    } catch (AIServiceException e) {
        System.err.println("Error en predicción de IA: " + e.getMessage());
        // Fallback a reglas hardcodeadas
        setupHardcodedAlerts();
    }
}

private void displayAIPrediction(AIPrediction prediction) {
    // Crear panel de información de IA
    JPanel aiPanel = new JPanel();
    aiPanel.setLayout(new BoxLayout(aiPanel, BoxLayout.Y_AXIS));
    aiPanel.setBorder(BorderFactory.createTitledBorder("🧠 Análisis de IA"));
    
    // Mostrar probabilidad
    JLabel probLabel = new JLabel(String.format(
        "Probabilidad de problema: %.1f%% - Nivel: %s",
        prediction.getProbabilityPercent(),
        prediction.getRiskLevel()
    ));
    
    // Color según severidad
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
    probLabel.setForeground(labelColor);
    probLabel.setFont(new Font("SansSerif", Font.BOLD, 14));
    aiPanel.add(probLabel);
    
    // Mostrar alertas
    if (prediction.hasAlerts()) {
        JLabel alertsLabel = new JLabel("Alertas detectadas:");
        alertsLabel.setFont(new Font("SansSerif", Font.BOLD, 12));
        aiPanel.add(alertsLabel);
        
        for (AIAlert alert : prediction.getAlerts()) {
            JLabel alertLabel = new JLabel("  • " + alert.getFullDescription());
            alertLabel.setForeground(alert.isHighSeverity() ? Color.RED : Color.ORANGE);
            aiPanel.add(alertLabel);
        }
    } else {
        JLabel noAlertsLabel = new JLabel("✓ Sin alertas - Valores normales");
        noAlertsLabel.setForeground(new Color(0, 128, 0));
        aiPanel.add(noAlertsLabel);
    }
    
    // Agregar panel a la UI (ajusta según tu layout)
    // Por ejemplo, en el panel superior o lateral
    add(aiPanel, BorderLayout.NORTH);
}

private void highlightAlertsInCharts(AIPrediction prediction) {
    // Recorrer alertas y marcar en gráficas según tipo
    for (AIAlert alert : prediction.getAlerts()) {
        switch (alert.getType()) {
            case "FEVER":
            case "HYPOTHERMIA":
                highlightTemperatureAlert(alert);
                break;
            case "ARRHYTHMIA":
                highlightHeartRateAlert(alert);
                break;
            case "DESAT":
                highlightSpO2Alert(alert);
                break;
            case "HYPERTENSION":
            case "HYPOTENSION":
                highlightBloodPressureAlert(alert);
                break;
        }
    }
}

private void highlightTemperatureAlert(AIAlert alert) {
    // En lugar de línea fija en 38°C, marcar el valor actual
    if (alert.hasValue()) {
        ValueMarker marker = new ValueMarker(alert.getValue());
        marker.setPaint(alert.isHighSeverity() ? Color.RED : Color.ORANGE);
        marker.setStroke(new BasicStroke(2.0f));
        marker.setLabel(alert.getMessage());
        marker.setLabelFont(new Font("SansSerif", Font.BOLD, 11));
        
        // Agregar a la gráfica de temperatura
        // (necesitas tener referencia al plot)
        temperaturePlot.addRangeMarker(marker, Layer.FOREGROUND);
    }
}
```

## 📋 Paso 5: Toggle entre IA y reglas hardcodeadas

Agregar un botón para activar/desactivar IA:

```java
private JToggleButton createAIToggleButton() {
    JToggleButton toggleButton = new JToggleButton("🧠 IA Activada", true);
    toggleButton.addActionListener(e -> {
        useAIPredictions = toggleButton.isSelected();
        toggleButton.setText(useAIPredictions ? "🧠 IA Activada" : "📋 Reglas Manuales");
        refreshCharts(); // Recargar gráficas
    });
    return toggleButton;
}
```

## 📋 Paso 6: Mantener fallback a reglas hardcodeadas

```java
private void setupHardcodedAlerts() {
    // Código original de líneas 500-540
    // Mantener como fallback si el servicio de IA falla
    ValueMarker feverLine = new ValueMarker(38.0);
    feverLine.setLabel("Fiebre (regla manual)");
    // ... resto del código original
}
```

## 🎯 Ventajas de esta Integración

1. ✅ **Predicciones inteligentes**: El modelo ML detecta patrones que reglas simples no pueden
2. ✅ **Alertas contextuales**: Considera múltiples signos vitales simultáneamente
3. ✅ **Probabilidad cuantificada**: Muestra la confianza del modelo (no solo sí/no)
4. ✅ **Fallback robusto**: Si el servicio falla, usa reglas hardcodeadas
5. ✅ **Actualizable**: Puedes mejorar el modelo sin recompilar la app

## 🚀 Próximos Pasos

1. Ejecutar el servicio de IA: `cd services/ai-prediction && make run`
2. Actualizar token en `AIService` cuando el usuario hace login
3. Probar la integración con datos reales
4. Ajustar threshold según necesidades clínicas
5. Agregar logs para auditoría de predicciones

## 📝 Notas

- El servicio de IA debe estar corriendo (puerto 5008)
- Requiere autenticación JWT (mismo token que otras APIs)
- Considera hacer cache de predicciones para reducir llamadas
- Implementa retry logic para mayor robustez
