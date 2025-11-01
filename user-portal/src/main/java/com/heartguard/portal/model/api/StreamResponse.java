package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record StreamResponse(String signal,
                             @JsonProperty("patient_id") String patientId,
                             List<StreamDataPoint> data) {
}
