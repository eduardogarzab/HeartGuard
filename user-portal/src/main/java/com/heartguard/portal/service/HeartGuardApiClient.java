package com.heartguard.portal.service;

import com.heartguard.portal.config.GatewayProperties;
import com.heartguard.portal.model.api.AlertAckRequest;
import com.heartguard.portal.model.api.AlertDto;
import com.heartguard.portal.model.api.LoginRequest;
import com.heartguard.portal.model.api.LoginResponse;
import com.heartguard.portal.model.api.PatientDetailDto;
import com.heartguard.portal.model.api.PatientSummaryDto;
import com.heartguard.portal.model.api.StreamResponse;
import com.heartguard.portal.model.api.UserProfileDto;
import com.heartguard.portal.session.AuthenticatedUserSession;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import java.net.URI;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Service
public class HeartGuardApiClient {

    private static final Logger log = LoggerFactory.getLogger(HeartGuardApiClient.class);

    private final RestTemplate restTemplate;
    private final GatewayProperties properties;
    private final SessionUserManager sessionUserManager;

    public HeartGuardApiClient(RestTemplate restTemplate, GatewayProperties properties, SessionUserManager sessionUserManager) {
        this.restTemplate = restTemplate;
        this.properties = properties;
        this.sessionUserManager = sessionUserManager;
    }

    public LoginResponse login(LoginRequest request) {
        URI uri = URI.create(properties.getBaseUrl() + "/v1/auth/login");
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<LoginRequest> entity = new HttpEntity<>(request, headers);
        return restTemplate.postForObject(uri, entity, LoginResponse.class);
    }

    public void logout(String accessToken) {
        URI uri = URI.create(properties.getBaseUrl() + "/v1/auth/logout");
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(accessToken);
        headers.setContentType(MediaType.APPLICATION_JSON);
        restTemplate.exchange(uri, HttpMethod.POST, new HttpEntity<>(null, headers), Void.class);
    }

    public UserProfileDto getCurrentUser(HttpSession session) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/users/me");
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<UserProfileDto> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers), UserProfileDto.class);
            return response.getBody();
        });
    }

    public List<PatientSummaryDto> getAssignedPatients(HttpSession session) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/patients/me");
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<List<PatientSummaryDto>> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
                    new ParameterizedTypeReference<>() {});
            return response.getBody() != null ? response.getBody() : Collections.emptyList();
        });
    }

    public PatientDetailDto getPatientDetails(HttpSession session, String patientId) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/patients/" + patientId);
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<PatientDetailDto> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers), PatientDetailDto.class);
            return response.getBody();
        });
    }

    public List<AlertDto> getActiveAlertsForPatient(HttpSession session, String patientId) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/alerts/patient/" + patientId + "?status=active");
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<List<AlertDto>> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
                    new ParameterizedTypeReference<>() {});
            return response.getBody() != null ? response.getBody() : Collections.emptyList();
        });
    }

    public List<AlertDto> getAlertsForPatient(HttpSession session, String patientId) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/alerts/patient/" + patientId);
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<List<AlertDto>> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
                    new ParameterizedTypeReference<>() {});
            return response.getBody() != null ? response.getBody() : Collections.emptyList();
        });
    }

    public int getActiveAlertsCount(HttpSession session) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/alerts/me?status=active");
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<Object> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
                    new ParameterizedTypeReference<>() {});
            Object body = response.getBody();
            if (body instanceof Map<?, ?> mapBody) {
                if (CollectionUtils.isEmpty(mapBody)) {
                    return 0;
                }
                Object count = mapBody.getOrDefault("count", mapBody.get("total"));
                if (count instanceof Number number) {
                    return number.intValue();
                }
                Object data = mapBody.get("data");
                if (data instanceof List<?> list) {
                    return list.size();
                }
            }
            if (body instanceof List<?> listBody) {
                return listBody.size();
            }
            return 0;
        });
    }

    public void acknowledgeAlert(HttpSession session, String alertId, AlertAckRequest request) {
        executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/alerts/" + alertId + "/ack");
            HttpHeaders headers = authorizationHeaders(token);
            headers.setContentType(MediaType.APPLICATION_JSON);
            restTemplate.exchange(uri, HttpMethod.POST, new HttpEntity<>(request, headers), Void.class);
            return null;
        });
    }

    public StreamResponse getStream(HttpSession session, String patientId, String signal, String duration) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/streams/patient/" + patientId + "?signal=" + signal + "&duration=" + duration);
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<StreamResponse> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers), StreamResponse.class);
            return response.getBody();
        });
    }

    private HttpHeaders authorizationHeaders(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));
        return headers;
    }

    private <T> T executeWithRetry(HttpSession session, ApiCall<T> apiCall) {
        AuthenticatedUserSession userSession = sessionUserManager.getCurrentUser(session);
        if (userSession == null) {
            throw HttpClientErrorException.create(HttpStatus.UNAUTHORIZED, "Unauthorized", HttpHeaders.EMPTY, null, null);
        }
        try {
            return apiCall.execute(userSession.getAccessToken());
        } catch (HttpClientErrorException.Unauthorized unauthorized) {
            log.debug("Access token expired, attempting refresh");
            String newToken = refreshAccessToken(userSession);
            if (newToken == null) {
                throw unauthorized;
            }
            sessionUserManager.updateAccessToken(session, newToken);
            return apiCall.execute(newToken);
        }
    }

    private String refreshAccessToken(AuthenticatedUserSession userSession) {
        if (userSession == null || userSession.getRefreshToken() == null) {
            return null;
        }
        try {
            URI uri = URI.create(properties.getBaseUrl() + "/v1/auth/refresh");
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, String> payload = Map.of("refresh_token", userSession.getRefreshToken());
            ResponseEntity<Map<String, String>> response = restTemplate.exchange(uri, HttpMethod.POST, new HttpEntity<>(payload, headers),
                    new ParameterizedTypeReference<>() {});
            Map<String, String> body = response.getBody();
            if (body != null) {
                return body.get("access_token");
            }
        } catch (HttpClientErrorException ex) {
            log.warn("Failed to refresh access token: {}", ex.getMessage());
        }
        return null;
    }

    @FunctionalInterface
    private interface ApiCall<T> {
        T execute(String token);
    }
}
