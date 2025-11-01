package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Wrapper genérico para las respuestas del gateway que siguen el formato:
 * { "code": 200, "status": "success", "data": {...} }
 * o en caso de error:
 * { "code": 500, "status": "error", "error": { "id": "...", "message": "..." } }
 */
public record GatewayResponse<T>(@JsonProperty("code") int code,
                                  @JsonProperty("status") String status,
                                  @JsonProperty("data") T data,
                                  @JsonProperty("error") GatewayError error) {
}

record GatewayError(@JsonProperty("id") String id,
                    @JsonProperty("message") String message,
                    @JsonProperty("details") Object details) {
}
