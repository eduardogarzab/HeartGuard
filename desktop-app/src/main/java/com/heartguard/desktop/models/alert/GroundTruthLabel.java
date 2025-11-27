package com.heartguard.desktop.models.alert;

import java.time.Instant;
import java.util.Objects;

/**
 * Etiqueta de ground truth para validación de predicciones de IA
 * Corresponde a la tabla 'ground_truth_labels' en PostgreSQL
 */
public class GroundTruthLabel {
    private final String id;
    private final String patientId;
    private final EventType eventType;
    private final Instant onset;
    private final Instant offsetAt;
    private final String annotatedByUserId;
    private final String annotatedByUserName;
    private final GroundTruthSource source;
    private final String note;
    private final Instant createdAt;
    private final Instant updatedAt;
    
    private GroundTruthLabel(Builder builder) {
        this.id = builder.id;
        this.patientId = builder.patientId;
        this.eventType = builder.eventType;
        this.onset = builder.onset;
        this.offsetAt = builder.offsetAt;
        this.annotatedByUserId = builder.annotatedByUserId;
        this.annotatedByUserName = builder.annotatedByUserName;
        this.source = builder.source;
        this.note = builder.note;
        this.createdAt = builder.createdAt;
        this.updatedAt = builder.updatedAt;
    }
    
    public String getId() {
        return id;
    }
    
    public String getPatientId() {
        return patientId;
    }
    
    public EventType getEventType() {
        return eventType;
    }
    
    public Instant getOnset() {
        return onset;
    }
    
    public Instant getOffsetAt() {
        return offsetAt;
    }
    
    public String getAnnotatedByUserId() {
        return annotatedByUserId;
    }
    
    public String getAnnotatedByUserName() {
        return annotatedByUserName;
    }
    
    public GroundTruthSource getSource() {
        return source;
    }
    
    public String getNote() {
        return note;
    }
    
    public Instant getCreatedAt() {
        return createdAt;
    }
    
    public Instant getUpdatedAt() {
        return updatedAt;
    }
    
    public boolean hasEndTime() {
        return offsetAt != null;
    }
    
    public boolean isFromAI() {
        return source == GroundTruthSource.AI_MODEL;
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GroundTruthLabel that = (GroundTruthLabel) o;
        return Objects.equals(id, that.id);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
    
    @Override
    public String toString() {
        return "GroundTruthLabel{" +
                "id='" + id + '\'' +
                ", patientId='" + patientId + '\'' +
                ", eventType=" + eventType +
                ", onset=" + onset +
                ", source=" + source +
                '}';
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private String id;
        private String patientId;
        private EventType eventType;
        private Instant onset;
        private Instant offsetAt;
        private String annotatedByUserId;
        private String annotatedByUserName;
        private GroundTruthSource source;
        private String note;
        private Instant createdAt;
        private Instant updatedAt;
        
        public Builder id(String id) {
            this.id = id;
            return this;
        }
        
        public Builder patientId(String patientId) {
            this.patientId = patientId;
            return this;
        }
        
        public Builder eventType(EventType eventType) {
            this.eventType = eventType;
            return this;
        }
        
        public Builder onset(Instant onset) {
            this.onset = onset;
            return this;
        }
        
        public Builder offsetAt(Instant offsetAt) {
            this.offsetAt = offsetAt;
            return this;
        }
        
        public Builder annotatedByUserId(String annotatedByUserId) {
            this.annotatedByUserId = annotatedByUserId;
            return this;
        }
        
        public Builder annotatedByUserName(String annotatedByUserName) {
            this.annotatedByUserName = annotatedByUserName;
            return this;
        }
        
        public Builder source(GroundTruthSource source) {
            this.source = source;
            return this;
        }
        
        public Builder note(String note) {
            this.note = note;
            return this;
        }
        
        public Builder createdAt(Instant createdAt) {
            this.createdAt = createdAt;
            return this;
        }
        
        public Builder updatedAt(Instant updatedAt) {
            this.updatedAt = updatedAt;
            return this;
        }
        
        public GroundTruthLabel build() {
            return new GroundTruthLabel(this);
        }
    }
}
