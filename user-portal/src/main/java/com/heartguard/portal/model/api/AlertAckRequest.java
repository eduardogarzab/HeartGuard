package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AlertAckRequest(@JsonProperty("note") String note) {
}
