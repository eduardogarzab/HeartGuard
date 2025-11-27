package com.heartguard.desktop.models.alert;

import java.awt.Color;

/**
 * Estados de una alerta en su ciclo de vida
 * Corresponde a la tabla 'alert_status' en PostgreSQL
 */
public enum AlertStatus {
    CREATED("created", "Creada", "Alerta creada, pendiente de notificación", new Color(158, 158, 158)),
    NOTIFIED("notified", "Notificada", "Equipo médico ha sido notificado", new Color(33, 150, 243)),
    ACKNOWLEDGED("ack", "Reconocida", "Caregiver ha reconocido la alerta", new Color(255, 193, 7)),
    RESOLVED("resolved", "Resuelta", "Alerta resuelta por el equipo médico", new Color(76, 175, 80)),
    CLOSED("closed", "Cerrada", "Caso cerrado", new Color(96, 125, 139));
    
    private final String code;
    private final String displayName;
    private final String description;
    private final Color color;
    
    AlertStatus(String code, String displayName, String description, Color color) {
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
     * Obtiene el estado de alerta a partir del código
     */
    public static AlertStatus fromCode(String code) {
        for (AlertStatus status : values()) {
            if (status.code.equals(code)) {
                return status;
            }
        }
        return CREATED; // default
    }
    
    /**
     * @return true si la alerta está en estado activo (no resuelta/cerrada)
     */
    public boolean isActive() {
        return this != RESOLVED && this != CLOSED;
    }
    
    /**
     * @return true si la alerta requiere atención inmediata
     */
    public boolean requiresAttention() {
        return this == CREATED || this == NOTIFIED;
    }
}
