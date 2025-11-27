package com.heartguard.desktop.models;

import java.util.Objects;

/**
 * Alerta generada por el modelo de IA
 */
public class AIAlert {
    private final String type;
    private final String severity;
    private final String message;
    private final Double value;
    private final String unit;
    private final Double probability;
    
    public AIAlert(String type, String severity, String message, 
                  Double value, String unit, Double probability) {
        this.type = type;
        this.severity = severity;
        this.message = message;
        this.value = value;
        this.unit = unit;
        this.probability = probability;
    }
    
    /**
     * Tipos de alerta conocidos
     */
    public enum AlertType {
        GENERAL_RISK,
        ARRHYTHMIA,
        DESAT,
        HYPERTENSION,
        HYPOTENSION,
        FEVER,
        HYPOTHERMIA
    }
    
    /**
     * @return Tipo de alerta (GENERAL_RISK, ARRHYTHMIA, etc.)
     */
    public String getType() {
        return type;
    }
    
    /**
     * @return Severidad (low, medium, high)
     */
    public String getSeverity() {
        return severity;
    }
    
    /**
     * @return Mensaje descriptivo de la alerta
     */
    public String getMessage() {
        return message;
    }
    
    /**
     * @return Valor asociado a la alerta (opcional)
     */
    public Double getValue() {
        return value;
    }
    
    /**
     * @return Unidad del valor (opcional)
     */
    public String getUnit() {
        return unit;
    }
    
    /**
     * @return Probabilidad asociada (opcional)
     */
    public Double getProbability() {
        return probability;
    }
    
    /**
     * @return true si tiene valor asociado
     */
    public boolean hasValue() {
        return value != null;
    }
    
    /**
     * @return true si la severidad es alta
     */
    public boolean isHighSeverity() {
        return "high".equalsIgnoreCase(severity);
    }
    
    /**
     * @return Descripción completa de la alerta para mostrar en UI
     */
    public String getFullDescription() {
        StringBuilder sb = new StringBuilder();
        sb.append(message);
        
        if (hasValue() && unit != null) {
            sb.append(String.format(" (Valor: %.1f %s)", value, unit));
        }
        
        if (probability != null) {
            sb.append(String.format(" [Probabilidad: %.0f%%]", probability * 100));
        }
        
        return sb.toString();
    }
    
    @Override
    public String toString() {
        return String.format(
            "AIAlert{type=%s, severity=%s, message=%s, value=%s %s}",
            type, severity, message, 
            value != null ? value : "N/A",
            unit != null ? unit : ""
        );
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        AIAlert aiAlert = (AIAlert) o;
        return Objects.equals(type, aiAlert.type) &&
               Objects.equals(severity, aiAlert.severity) &&
               Objects.equals(message, aiAlert.message) &&
               Objects.equals(value, aiAlert.value) &&
               Objects.equals(unit, aiAlert.unit);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(type, severity, message, value, unit);
    }
}
