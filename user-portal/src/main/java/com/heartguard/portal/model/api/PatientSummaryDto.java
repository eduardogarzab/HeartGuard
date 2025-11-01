package com.heartguard.portal.model.api;

public record PatientSummaryDto(
    String id,
    String personName,
    String sexId,
    String riskLevelCode,
    String profilePhotoUrl
) {
}
