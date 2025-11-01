package com.heartguard.portal.model.api;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Estructura de datos devuelta por el gateway en el login
 */
public record LoginData(@JsonProperty("tokens") TokensPair tokens,
                        @JsonProperty("user") UserData user) {
    
    public record TokensPair(@JsonProperty("access_token") String accessToken,
                            @JsonProperty("refresh_token") String refreshToken,
                            @JsonProperty("expires_in") Integer expiresIn,
                            @JsonProperty("roles") List<String> roles,
                            @JsonProperty("token_type") String tokenType) {
    }
    
    public record UserData(@JsonProperty("id") String id,
                          @JsonProperty("name") String name,
                          @JsonProperty("email") String email,
                          @JsonProperty("user_status_id") String userStatusId,
                          @JsonProperty("profile_photo_url") String profilePhotoUrl,
                          @JsonProperty("created_at") String createdAt) {
    }
}
