package com.heartguard.desktop.models.alert;

import java.awt.Color;

/**
 * Tipos de alerta del sistema HeartGuard
 * Corresponde a la tabla 'alert_types' en PostgreSQL
 */
public enum AlertType {
    GENERAL_RISK("GENERAL_RISK", "Riesgo General", "Riesgo general de salud detectado por IA", new Color(255, 193, 7)),
    ARRHYTHMIA("ARRHYTHMIA", "Arritmia", "Frecuencia cardíaca anormal", new Color(220, 53, 69)),
    DESAT("DESAT", "Desaturación", "Saturación de oxígeno baja", new Color(220, 53, 69)),
    HYPERTENSION("HYPERTENSION", "Hipertensión", "Presión arterial elevada", new Color(255, 152, 0)),
    HYPOTENSION("HYPOTENSION", "Hipotensión", "Presión arterial baja", new Color(220, 53, 69)),
    FEVER("FEVER", "Fiebre", "Temperatura corporal elevada", new Color(255, 152, 0)),
    HYPOTHERMIA("HYPOTHERMIA", "Hipotermia", "Temperatura corporal baja", new Color(220, 53, 69));
    
    private final String code;
    private final String displayName;
    private final String description;
    private final Color color;
    
    AlertType(String code, String displayName, String description, Color color) {
        this.code = code;
        this.displayName = displayName;
        this.description = description;
        this.color = color;
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
    
    /**
     * Obtiene el emoji correspondiente al tipo de alerta
     */
    public String getEmoji() {
        switch (this) {
            case GENERAL_RISK:
                return "⚠️";
            case ARRHYTHMIA:
                return "💓";
            case DESAT:
                return "🫁";
            case HYPERTENSION:
            case HYPOTENSION:
                return "🩸";
            case FEVER:
            case HYPOTHERMIA:
                return "🌡️";
            default:
                return "⚕️";
        }
    }
    
    /**
     * Obtiene el tipo de alerta a partir del código
     */
    public static AlertType fromCode(String code) {
        for (AlertType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return GENERAL_RISK; // default
    }
}
