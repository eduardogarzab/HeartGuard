package com.heartguard.desktop.models.alert;

/**
 * Fuente de origen de una etiqueta de ground truth
 */
public enum GroundTruthSource {
    AI_MODEL("AI_MODEL", "Modelo de IA", "Validación de predicción del modelo de IA"),
    MANUAL("MANUAL", "Manual", "Anotación manual por personal médico"),
    MEDICAL_RECORD("MEDICAL_RECORD", "Historial Médico", "Extraído del historial médico del paciente");
    
    private final String code;
    private final String displayName;
    private final String description;
    
    GroundTruthSource(String code, String displayName, String description) {
        this.code = code;
        this.displayName = displayName;
        this.description = description;
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
    
    /**
     * Obtiene la fuente a partir del código
     */
    public static GroundTruthSource fromCode(String code) {
        for (GroundTruthSource source : values()) {
            if (source.code.equals(code)) {
                return source;
            }
        }
        return MANUAL; // default
    }
}
