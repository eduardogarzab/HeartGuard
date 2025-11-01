package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;

public record PatientSummaryDto(String id,
                                @JsonProperty("person_name") String personName,
                                @JsonProperty("risk_level_code") String riskLevelCode,
                                @JsonProperty("profile_photo_url") String profilePhotoUrl) {
}
