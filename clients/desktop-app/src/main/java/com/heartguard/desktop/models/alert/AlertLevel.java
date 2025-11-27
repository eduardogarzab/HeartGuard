package com.heartguard.desktop.models.alert;

import java.awt.Color;

/**
 * Niveles de severidad de alertas
 * Corresponde a la tabla 'alert_levels' en PostgreSQL
 */
public enum AlertLevel {
    LOW("low", "Bajo", "Riesgo bajo - Monitoreo de rutina", new Color(76, 175, 80), 1),
    MEDIUM("medium", "Medio", "Riesgo medio - Atención recomendada", new Color(255, 193, 7), 2),
    HIGH("high", "Alto", "Riesgo alto - Atención prioritaria", new Color(255, 152, 0), 3),
    CRITICAL("critical", "Crítico", "Riesgo crítico - Atención inmediata", new Color(220, 53, 69), 4);
    
    private final String code;
    private final String displayName;
    private final String description;
    private final Color color;
    private final int priority;
    
    AlertLevel(String code, String displayName, String description, Color color, int priority) {
        this.code = code;
        this.displayName = displayName;
        this.description = description;
        this.color = color;
        this.priority = priority;
    }
    
    public String getCode() {
        return code;
    }
    
    public String getDisplayName() {
        return displayName;
    }
    
    public String getDescription() {
        return description;
    }
    
    public Color getColor() {
        return color;
    }
    
    public int getPriority() {
        return priority;
    }
    
    /**
     * Obtiene el nivel de alerta a partir del código
     */
    public static AlertLevel fromCode(String code) {
        for (AlertLevel level : values()) {
            if (level.code.equals(code)) {
                return level;
            }
        }
        return MEDIUM; // default
    }
    
    /**
     * Compara la prioridad de dos niveles
     * @return true si este nivel tiene mayor o igual prioridad que el otro
     */
    public boolean isHigherOrEqualPriority(AlertLevel other) {
        return this.priority >= other.priority;
    }
}
