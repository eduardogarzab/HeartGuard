package com.heartguard.portal.model.api;

public record AlertDto(
    String id,
    String patientId,
    String typeId,
    String alertLevelId,
    String statusId,
    String description,
    String createdAt
) {
}
