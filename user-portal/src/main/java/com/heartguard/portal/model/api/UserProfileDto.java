package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;

public record UserProfileDto(String id,
                             String name,
                             String email,
                             @JsonProperty("phone_number") String phoneNumber,
                             String role) {
}
