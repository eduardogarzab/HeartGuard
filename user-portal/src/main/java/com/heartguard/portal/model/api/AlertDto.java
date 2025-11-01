package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.OffsetDateTime;

public record AlertDto(String id,
                       String status,
                       String type,
                       @JsonProperty("severity_level") String severityLevel,
                       String message,
                       @JsonProperty("created_at") OffsetDateTime createdAt,
                       @JsonProperty("updated_at") OffsetDateTime updatedAt) {
}
