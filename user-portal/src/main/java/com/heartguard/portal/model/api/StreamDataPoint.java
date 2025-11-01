package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;

public record StreamDataPoint(@JsonProperty("timestamp") String timestamp,
                              @JsonProperty("value") Double value) {
}
