package com.heartguard.desktop.models.alert;

/**
 * Tipos de eventos médicos para Ground Truth
 * Corresponde a la tabla 'event_types' en PostgreSQL
 */
public enum EventType {
    GENERAL_RISK("GENERAL_RISK", "Riesgo General", AlertLevel.MEDIUM),
    ARRHYTHMIA("ARRHYTHMIA", "Arritmia - Frecuencia cardíaca anormal", AlertLevel.HIGH),
    DESAT("DESAT", "Desaturación de oxígeno", AlertLevel.HIGH),
    HYPERTENSION("HYPERTENSION", "Hipertensión arterial", AlertLevel.MEDIUM),
    HYPOTENSION("HYPOTENSION", "Hipotensión arterial", AlertLevel.HIGH),
    FEVER("FEVER", "Fiebre - Temperatura elevada", AlertLevel.MEDIUM),
    HYPOTHERMIA("HYPOTHERMIA", "Hipotermia - Temperatura baja", AlertLevel.HIGH);
    
    private final String code;
    private final String description;
    private final AlertLevel defaultSeverity;
    
    EventType(String code, String description, AlertLevel defaultSeverity) {
        this.code = code;
        this.description = description;
        this.defaultSeverity = defaultSeverity;
    }
    
    public String getCode() {
        return code;
    }
    
    public String getDescription() {
        return description;
    }
    
    public AlertLevel getDefaultSeverity() {
        return defaultSeverity;
    }
    
    /**
     * Obtiene el tipo de evento a partir del código
     */
    public static EventType fromCode(String code) {
        for (EventType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return GENERAL_RISK; // default
    }
    
    /**
     * Convierte un EventType a AlertType correspondiente
     */
    public AlertType toAlertType() {
        return AlertType.fromCode(this.code);
    }
}
