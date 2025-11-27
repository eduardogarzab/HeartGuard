package com.heartguard.desktop.models;

import java.util.List;
import java.util.Objects;

/**
 * Resultado de una predicción de IA sobre el estado de salud
 */
public class AIPrediction {
    private final boolean hasProblem;
    private final double probability;
    private final List<AIAlert> alerts;
    private final String processedAt;
    
    public AIPrediction(boolean hasProblem, double probability, 
                       List<AIAlert> alerts, String processedAt) {
        this.hasProblem = hasProblem;
        this.probability = probability;
        this.alerts = alerts;
        this.processedAt = processedAt;
    }
    
    /**
     * @return true si el modelo detectó un problema de salud
     */
    public boolean hasProblem() {
        return hasProblem;
    }
    
    /**
     * @return Probabilidad de problema (0.0 - 1.0)
     */
    public double getProbability() {
        return probability;
    }
    
    /**
     * @return Probabilidad como porcentaje (0-100)
     */
    public double getProbabilityPercent() {
        return probability * 100.0;
    }
    
    /**
     * @return Lista de alertas generadas
     */
    public List<AIAlert> getAlerts() {
        return alerts;
    }
    
    /**
     * @return true si hay alertas
     */
    public boolean hasAlerts() {
        return alerts != null && !alerts.isEmpty();
    }
    
    /**
     * @return Timestamp de procesamiento
     */
    public String getProcessedAt() {
        return processedAt;
    }
    
    /**
     * @return Nivel de riesgo basado en probabilidad (LOW, MEDIUM, HIGH)
     */
    public RiskLevel getRiskLevel() {
        if (probability < 0.3) {
            return RiskLevel.LOW;
        } else if (probability < 0.6) {
            return RiskLevel.MEDIUM;
        } else {
            return RiskLevel.HIGH;
        }
    }
    
    /**
     * @return Número de alertas de alta severidad
     */
    public long getHighSeverityCount() {
        if (alerts == null) return 0;
        return alerts.stream()
                .filter(alert -> "high".equalsIgnoreCase(alert.getSeverity()))
                .count();
    }
    
    /**
     * @return true si hay al menos una alerta de severidad alta
     */
    public boolean hasCriticalAlerts() {
        return getHighSeverityCount() > 0;
    }
    
    @Override
    public String toString() {
        return String.format(
            "AIPrediction{hasProblem=%s, probability=%.2f%%, riskLevel=%s, alerts=%d}",
            hasProblem, getProbabilityPercent(), getRiskLevel(), 
            alerts != null ? alerts.size() : 0
        );
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        AIPrediction that = (AIPrediction) o;
        return hasProblem == that.hasProblem &&
               Double.compare(that.probability, probability) == 0 &&
               Objects.equals(alerts, that.alerts) &&
               Objects.equals(processedAt, that.processedAt);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(hasProblem, probability, alerts, processedAt);
    }
    
    /**
     * Niveles de riesgo
     */
    public enum RiskLevel {
        LOW,     // 0-30%
        MEDIUM,  // 30-60%
        HIGH     // 60-100%
    }
}
