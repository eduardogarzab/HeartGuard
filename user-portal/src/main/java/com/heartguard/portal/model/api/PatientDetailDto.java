package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.LocalDate;

public record PatientDetailDto(String id,
                               @JsonProperty("person_name") String personName,
                               String gender,
                               Integer age,
                               @JsonProperty("risk_level_code") String riskLevelCode,
                               @JsonProperty("profile_photo_url") String profilePhotoUrl,
                               @JsonProperty("date_of_birth") LocalDate dateOfBirth) {
}
