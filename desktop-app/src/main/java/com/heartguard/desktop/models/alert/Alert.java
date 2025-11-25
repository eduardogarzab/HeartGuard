package com.heartguard.desktop.models.alert;

import java.time.Instant;
import java.util.Objects;

/**
 * Modelo de alerta generada por IA o manualmente
 * Corresponde a la tabla 'alerts' en PostgreSQL
 */
public class Alert {
    private final String id;
    private final String patientId;
    private final String patientName;
    private final AlertType type;
    private final AlertLevel alertLevel;
    private final AlertStatus status;
    private final String description;
    private final Instant createdAt;
    private final Instant acknowledgedAt;
    private final Instant resolvedAt;
    private final String createdByModelId;
    private final String sourceInferenceId;
    private final Double latitude;
    private final Double longitude;
    private final String acknowledgedByUserId;
    private final String resolvedByUserId;
    
    private Alert(Builder builder) {
        this.id = builder.id;
        this.patientId = builder.patientId;
        this.patientName = builder.patientName;
        this.type = builder.type;
        this.alertLevel = builder.alertLevel;
        this.status = builder.status;
        this.description = builder.description;
        this.createdAt = builder.createdAt;
        this.acknowledgedAt = builder.acknowledgedAt;
        this.resolvedAt = builder.resolvedAt;
        this.createdByModelId = builder.createdByModelId;
        this.sourceInferenceId = builder.sourceInferenceId;
        this.latitude = builder.latitude;
        this.longitude = builder.longitude;
        this.acknowledgedByUserId = builder.acknowledgedByUserId;
        this.resolvedByUserId = builder.resolvedByUserId;
    }
    
    public String getId() {
        return id;
    }
    
    public String getPatientId() {
        return patientId;
    }
    
    public String getPatientName() {
        return patientName;
    }
    
    public AlertType getType() {
        return type;
    }
    
    public AlertLevel getAlertLevel() {
        return alertLevel;
    }
    
    public AlertStatus getStatus() {
        return status;
    }
    
    public String getDescription() {
        return description;
    }
    
    public Instant getCreatedAt() {
        return createdAt;
    }
    
    public Instant getAcknowledgedAt() {
        return acknowledgedAt;
    }
    
    public Instant getResolvedAt() {
        return resolvedAt;
    }
    
    public String getCreatedByModelId() {
        return createdByModelId;
    }
    
    public String getSourceInferenceId() {
        return sourceInferenceId;
    }
    
    public Double getLatitude() {
        return latitude;
    }
    
    public Double getLongitude() {
        return longitude;
    }
    
    public String getAcknowledgedByUserId() {
        return acknowledgedByUserId;
    }
    
    public String getResolvedByUserId() {
        return resolvedByUserId;
    }
    
    public boolean hasLocation() {
        return latitude != null && longitude != null;
    }
    
    public boolean isCreatedByAI() {
        return createdByModelId != null;
    }
    
    public boolean isAcknowledged() {
        return acknowledgedAt != null;
    }
    
    public boolean isResolved() {
        return resolvedAt != null;
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Alert alert = (Alert) o;
        return Objects.equals(id, alert.id);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
    
    @Override
    public String toString() {
        return "Alert{" +
                "id='" + id + '\'' +
                ", patientId='" + patientId + '\'' +
                ", type=" + type +
                ", level=" + alertLevel +
                ", status=" + status +
                ", createdAt=" + createdAt +
                '}';
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private String id;
        private String patientId;
        private String patientName;
        private AlertType type;
        private AlertLevel alertLevel;
        private AlertStatus status;
        private String description;
        private Instant createdAt;
        private Instant acknowledgedAt;
        private Instant resolvedAt;
        private String createdByModelId;
        private String sourceInferenceId;
        private Double latitude;
        private Double longitude;
        private String acknowledgedByUserId;
        private String resolvedByUserId;
        
        public Builder id(String id) {
            this.id = id;
            return this;
        }
        
        public Builder patientId(String patientId) {
            this.patientId = patientId;
            return this;
        }
        
        public Builder patientName(String patientName) {
            this.patientName = patientName;
            return this;
        }
        
        public Builder type(AlertType type) {
            this.type = type;
            return this;
        }
        
        public Builder alertLevel(AlertLevel alertLevel) {
            this.alertLevel = alertLevel;
            return this;
        }
        
        public Builder status(AlertStatus status) {
            this.status = status;
            return this;
        }
        
        public Builder description(String description) {
            this.description = description;
            return this;
        }
        
        public Builder createdAt(Instant createdAt) {
            this.createdAt = createdAt;
            return this;
        }
        
        public Builder acknowledgedAt(Instant acknowledgedAt) {
            this.acknowledgedAt = acknowledgedAt;
            return this;
        }
        
        public Builder resolvedAt(Instant resolvedAt) {
            this.resolvedAt = resolvedAt;
            return this;
        }
        
        public Builder createdByModelId(String createdByModelId) {
            this.createdByModelId = createdByModelId;
            return this;
        }
        
        public Builder sourceInferenceId(String sourceInferenceId) {
            this.sourceInferenceId = sourceInferenceId;
            return this;
        }
        
        public Builder latitude(Double latitude) {
            this.latitude = latitude;
            return this;
        }
        
        public Builder longitude(Double longitude) {
            this.longitude = longitude;
            return this;
        }
        
        public Builder acknowledgedByUserId(String acknowledgedByUserId) {
            this.acknowledgedByUserId = acknowledgedByUserId;
            return this;
        }
        
        public Builder resolvedByUserId(String resolvedByUserId) {
            this.resolvedByUserId = resolvedByUserId;
            return this;
        }
        
        public Alert build() {
            return new Alert(this);
        }
    }
}
