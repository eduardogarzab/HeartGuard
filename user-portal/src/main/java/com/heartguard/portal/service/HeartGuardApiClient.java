package com.heartguard.portal.service;

import com.heartguard.portal.config.GatewayProperties;
import com.heartguard.portal.model.api.AlertAckRequest;
import com.heartguard.portal.model.api.AlertDto;
import com.heartguard.portal.model.api.DeviceDto;
import com.heartguard.portal.model.api.GatewayResponse;
import com.heartguard.portal.model.api.LoginData;
import com.heartguard.portal.model.api.LoginRequest;
import com.heartguard.portal.model.api.LoginResponse;
import com.heartguard.portal.model.api.PatientDetailDto;
import com.heartguard.portal.model.api.PatientSummaryDto;
import com.heartguard.portal.model.api.StreamResponse;
import com.heartguard.portal.model.api.UserProfileDto;
import com.heartguard.portal.model.api.UserSummary;
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
import org.springframework.web.client.HttpServerErrorException;
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
        URI uri = URI.create(properties.getBaseUrl() + "/auth/login");
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<LoginRequest> entity = new HttpEntity<>(request, headers);
        
        // El gateway devuelve: { "code": 200, "status": "success", "data": { "tokens": {...}, "user": {...} } }
        ResponseEntity<GatewayResponse<LoginData>> response = restTemplate.exchange(uri, HttpMethod.POST, entity,
            new ParameterizedTypeReference<GatewayResponse<LoginData>>() {});
        
        GatewayResponse<LoginData> gatewayResponse = response.getBody();
        if (gatewayResponse == null || gatewayResponse.data() == null) {
            throw new IllegalStateException("Respuesta inválida del gateway");
        }
        
        LoginData data = gatewayResponse.data();
        
        // Extraer el primer rol de la lista de roles en tokens, o usar "USER" por defecto
        String role = (data.tokens().roles() != null && !data.tokens().roles().isEmpty()) 
            ? data.tokens().roles().get(0).toUpperCase() 
            : "USER";
        
        // Construir UserSummary con los datos del usuario y el rol de los tokens
        UserSummary userSummary = new UserSummary(
            data.user().id(),
            data.user().name(),
            data.user().email(),
            role
        );
        
        return new LoginResponse(
            data.tokens().accessToken(),
            data.tokens().refreshToken(),
            userSummary
        );
    }

    public void logout(String accessToken) {
        URI uri = URI.create(properties.getBaseUrl() + "/auth/logout");
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(accessToken);
        headers.setContentType(MediaType.APPLICATION_JSON);
        restTemplate.exchange(uri, HttpMethod.POST, new HttpEntity<>(null, headers), Void.class);
    }

    public UserProfileDto getCurrentUser(HttpSession session) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/users/me");
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<UserProfileDto> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers), UserProfileDto.class);
            return response.getBody();
        });
    }

    public List<PatientSummaryDto> getAssignedPatients(HttpSession session) {
        log.info("Iniciando getAssignedPatients...");
        return executeWithRetry(session, token -> {
            try {
                URI uri = URI.create(properties.getBaseUrl() + "/patients");
                log.info("URL del endpoint: {}", uri);
                
                HttpHeaders headers = authorizationHeaders(token);
                log.info("Headers configurados: Authorization=Bearer ***");
                
                ResponseEntity<GatewayResponse<Map<String, Object>>> response = restTemplate.exchange(
                    uri, HttpMethod.GET, new HttpEntity<>(headers),
                    new ParameterizedTypeReference<GatewayResponse<Map<String, Object>>>() {});
                
                log.info("Respuesta recibida: status={}", response.getStatusCode());
                
                GatewayResponse<Map<String, Object>> body = response.getBody();
                if (body != null && body.data() != null) {
                    log.info("Body data presente: {}", body.data().keySet());
                    Object patientsData = body.data().get("patients");
                    if (patientsData instanceof List<?> patientsList) {
                        log.info("Lista de pacientes encontrada: {} elementos", patientsList.size());
                        List<PatientSummaryDto> result = patientsList.stream()
                            .filter(item -> item instanceof Map)
                            .map(item -> {
                                @SuppressWarnings("unchecked")
                                Map<String, Object> patientMap = (Map<String, Object>) item;
                                return new PatientSummaryDto(
                                    (String) patientMap.get("id"),
                                    (String) patientMap.get("person_name"),
                                    (String) patientMap.get("sex_id"),
                                    (String) patientMap.get("risk_level_id"),
                                    (String) patientMap.get("profile_photo_url")
                                );
                            })
                            .toList();
                        log.info("Pacientes parseados exitosamente: {}", result.size());
                        return result;
                    } else {
                        log.warn("patientsData no es una lista: {}", patientsData != null ? patientsData.getClass() : "null");
                    }
                } else {
                    log.warn("Body o data es null: body={}, data={}", body, body != null ? body.data() : "n/a");
                }
                return Collections.emptyList();
            } catch (HttpServerErrorException e) {
                // Handle 5xx errors from gateway
                log.error("Gateway returned 5xx error: status={}, body={}", e.getStatusCode(), e.getResponseBodyAsString());
                
                // Try to parse the error response
                try {
                    String errorBody = e.getResponseBodyAsString();
                    log.error("Error details: {}", errorBody);
                    
                    // Check if it's a GatewayResponse error format
                    if (errorBody.contains("\"error\"")) {
                        log.error("Gateway error detected. This might be due to authentication or permission issues.");
                        log.error("Please verify:");
                        log.error("  1. User has correct roles assigned in database (user_role table)");
                        log.error("  2. Auth service is loading roles from database");
                        log.error("  3. JWT token contains required roles");
                    }
                } catch (Exception parseEx) {
                    log.error("Could not parse error response", parseEx);
                }
                
                // Return empty list instead of throwing exception
                return Collections.emptyList();
            } catch (Exception e) {
                log.error("Error en getAssignedPatients", e);
                return Collections.emptyList();
            }
        });
    }

    public PatientDetailDto getPatientDetails(HttpSession session, String patientId) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/patients/" + patientId);
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<PatientDetailDto> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers), PatientDetailDto.class);
            return response.getBody();
        });
    }

    public List<AlertDto> getActiveAlertsForPatient(HttpSession session, String patientId) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/alerts/patient/" + patientId + "?status=active");
            HttpHeaders headers = authorizationHeaders(token);
        ResponseEntity<List<AlertDto>> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
            new ParameterizedTypeReference<List<AlertDto>>() {});
            return response.getBody() != null ? response.getBody() : Collections.emptyList();
        });
    }

    public List<AlertDto> getAlertsForPatient(HttpSession session, String patientId) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/alerts/patient/" + patientId);
            HttpHeaders headers = authorizationHeaders(token);
        ResponseEntity<List<AlertDto>> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
            new ParameterizedTypeReference<List<AlertDto>>() {});
            return response.getBody() != null ? response.getBody() : Collections.emptyList();
        });
    }

    public int getActiveAlertsCount(HttpSession session) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/alerts/me?status=active");
            HttpHeaders headers = authorizationHeaders(token);
        ResponseEntity<Object> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers), Object.class);
            Object body = response.getBody();
            if (body instanceof Map<?, ?> mapBody) {
                if (CollectionUtils.isEmpty(mapBody)) {
                    return 0;
                }
                Object count = mapBody.containsKey("count") ? mapBody.get("count") : mapBody.get("total");
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
            URI uri = URI.create(properties.getBaseUrl() + "/alerts/" + alertId + "/ack");
            HttpHeaders headers = authorizationHeaders(token);
            headers.setContentType(MediaType.APPLICATION_JSON);
            restTemplate.exchange(uri, HttpMethod.POST, new HttpEntity<>(request, headers), Void.class);
            return null;
        });
    }

    public StreamResponse getStream(HttpSession session, String patientId, String signal, String duration) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/streams/patient/" + patientId + "?signal=" + signal + "&duration=" + duration);
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<StreamResponse> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers), StreamResponse.class);
            return response.getBody();
        });
    }

    public List<AlertDto> getAllAlerts(HttpSession session) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/alerts");
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<GatewayResponse<Map<String, Object>>> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
                new ParameterizedTypeReference<GatewayResponse<Map<String, Object>>>() {});
            
            GatewayResponse<Map<String, Object>> body = response.getBody();
            if (body != null && body.data() != null) {
                Object alertsData = body.data().get("alerts");
                if (alertsData instanceof List<?> alertsList) {
                    List<AlertDto> result = alertsList.stream()
                        .filter(item -> item instanceof Map)
                        .map(item -> {
                            @SuppressWarnings("unchecked")
                            Map<String, Object> alertMap = (Map<String, Object>) item;
                            return new AlertDto(
                                (String) alertMap.get("id"),
                                (String) alertMap.get("patient_id"),
                                (String) alertMap.get("type_id"),
                                (String) alertMap.get("alert_level_id"),
                                (String) alertMap.get("status_id"),
                                (String) alertMap.get("description"),
                                alertMap.get("created_at") != null ? String.valueOf(alertMap.get("created_at")) : null
                            );
                        })
                        .toList();
                    return result;
                }
            }
            return Collections.emptyList();
        });
    }

    public List<DeviceDto> getAllDevices(HttpSession session) {
        return executeWithRetry(session, token -> {
            URI uri = URI.create(properties.getBaseUrl() + "/devices");
            HttpHeaders headers = authorizationHeaders(token);
            ResponseEntity<GatewayResponse<Map<String, Object>>> response = restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
                new ParameterizedTypeReference<GatewayResponse<Map<String, Object>>>() {});
            
            GatewayResponse<Map<String, Object>> body = response.getBody();
            if (body != null && body.data() != null) {
                Object devicesData = body.data().get("devices");
                if (devicesData instanceof List<?> devicesList) {
                    List<DeviceDto> result = devicesList.stream()
                        .filter(item -> item instanceof Map)
                        .map(item -> {
                            @SuppressWarnings("unchecked")
                            Map<String, Object> deviceMap = (Map<String, Object>) item;
                            return new DeviceDto(
                                (String) deviceMap.get("id"),
                                (String) deviceMap.get("serial"),
                                (String) deviceMap.get("brand"),
                                (String) deviceMap.get("model"),
                                (String) deviceMap.get("device_type_code"),
                                (String) deviceMap.get("device_type_label"),
                                (String) deviceMap.get("owner_patient_id"),
                                (String) deviceMap.get("owner_patient_name"),
                                (Boolean) deviceMap.get("active")
                            );
                        })
                        .toList();
                    return result;
                }
            }
            return Collections.emptyList();
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
            URI uri = URI.create(properties.getBaseUrl() + "/auth/refresh");
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, String> payload = Map.of("refresh_token", userSession.getRefreshToken());
        ResponseEntity<Map<String, String>> response = restTemplate.exchange(uri, HttpMethod.POST, new HttpEntity<>(payload, headers),
            new ParameterizedTypeReference<Map<String, String>>() {});
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
