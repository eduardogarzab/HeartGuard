package com.heartguard.desktop.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.heartguard.desktop.models.LoginResponse;
import com.heartguard.desktop.models.Patient;
import com.heartguard.desktop.models.User;
import okhttp3.*;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Cliente HTTP para comunicarse con el Gateway API
 * Todas las peticiones pasan por el Gateway (puerto 8080)
 * El Gateway se encarga de enrutar a los microservicios internos
 */
public class ApiClient {
    private static final String DEFAULT_GATEWAY_URL = "http://136.115.53.140:8080"; // aqui tiene que cambiarse al correspondiente
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    
    private final String gatewayUrl;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private String accessToken;

    public ApiClient() {
        this(DEFAULT_GATEWAY_URL);
    }

    public ApiClient(String gatewayUrl) {
        this.gatewayUrl = gatewayUrl.endsWith("/") ? gatewayUrl.substring(0, gatewayUrl.length() - 1) : gatewayUrl;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .writeTimeout(10, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .build();
        this.gson = new GsonBuilder()
                .setDateFormat("yyyy-MM-dd'T'HH:mm:ss")
                .create();
    }

    /**
     * Establece el token de acceso para peticiones autenticadas
     */
    public void setAccessToken(String accessToken) {
        this.accessToken = accessToken;
    }

    /**
     * Login para usuario (staff)
     * Ruta: POST /auth/login/user
     */
    public LoginResponse loginUser(String email, String password) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("email", email);
        payload.addProperty("password", password);

        String url = gatewayUrl + "/auth/login/user";
        return executeLogin(url, payload);
    }

    /**
     * Login para paciente
     * Ruta: POST /auth/login/patient
     */
    public LoginResponse loginPatient(String email, String password) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("email", email);
        payload.addProperty("password", password);

        String url = gatewayUrl + "/auth/login/patient";
        return executeLogin(url, payload);
    }

    /**
     * Registro de usuario (staff)
     * Ruta: POST /auth/register/user
     * Según el README, solo requiere: name, email, password
     * Se crea sin organización inicial (se agregan por invitaciones)
     */
    public LoginResponse registerUser(String email, String password, String name) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("name", name);
        payload.addProperty("email", email);
        payload.addProperty("password", password);

        String url = gatewayUrl + "/auth/register/user";
        
        // El registro de usuario NO devuelve tokens, solo devuelve user_id y message
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorMessage = errorObj.has("error") ? errorObj.get("error").getAsString() : "Error desconocido";
                throw new ApiException(errorMessage, response.code(), "registration_error", responseBody);
            }

            // Parsear la respuesta de registro
            JsonObject responseObj = gson.fromJson(responseBody, JsonObject.class);
            
            // Crear una respuesta básica (el registro NO devuelve tokens)
            LoginResponse loginResponse = new LoginResponse();
            loginResponse.setAccountType("user");
            
            return loginResponse;
        } catch (IOException e) {
            throw new ApiException("Error de conexión: " + e.getMessage(), e);
        }
    }

    /**
     * Registro de paciente
     * Ruta: POST /auth/register/patient
     * Acepta tanto org_id (UUID) como org_code (código de organización)
     * Detecta automáticamente si es UUID o código
     */
    public LoginResponse registerPatient(String email, String password, String name,
                                        String orgIdOrCode, String birthdate, String sexCode,
                                        String riskLevelCode) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("name", name);
        payload.addProperty("email", email);
        payload.addProperty("password", password);
        
        // Detectar si es UUID o código de organización
        // UUID tiene formato: 8-4-4-4-12 caracteres hexadecimales con guiones
        if (orgIdOrCode.matches("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")) {
            payload.addProperty("org_id", orgIdOrCode); // Es un UUID
        } else {
            payload.addProperty("org_code", orgIdOrCode); // Es un código como CLIN-001
        }
        
        payload.addProperty("birthdate", birthdate); // Formato: YYYY-MM-DD
        payload.addProperty("sex_code", sexCode); // M, F, O
        
        // risk_level_code es opcional, pero lo incluimos si se proporciona
        if (riskLevelCode != null && !riskLevelCode.isEmpty()) {
            payload.addProperty("risk_level_code", riskLevelCode);
        }

        String url = gatewayUrl + "/auth/register/patient";
        
        // El registro de paciente NO devuelve tokens, solo devuelve patient_id y message
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorMessage = errorObj.has("error") ? errorObj.get("error").getAsString() : "Error desconocido";
                throw new ApiException(errorMessage, response.code(), "registration_error", responseBody);
            }

            // Parsear la respuesta de registro
            JsonObject responseObj = gson.fromJson(responseBody, JsonObject.class);
            
            // Crear una respuesta básica (el registro NO devuelve tokens)
            LoginResponse loginResponse = new LoginResponse();
            loginResponse.setAccountType("patient");
            
            return loginResponse;
        } catch (IOException e) {
            throw new ApiException("Error de conexión: " + e.getMessage(), e);
        }
    }

    /**
     * Verifica el token de acceso actual
     * Ruta: GET /auth/verify
     */
    public boolean verifyToken() throws ApiException {
        if (accessToken == null || accessToken.isEmpty()) {
            return false;
        }

        String url = gatewayUrl + "/auth/verify";
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer " + accessToken)
                .get()
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            return response.isSuccessful();
        } catch (IOException e) {
            throw new ApiException("Error de conexión: " + e.getMessage(), e);
        }
    }

    /**
     * Obtiene información del usuario/paciente autenticado
     * Ruta: GET /auth/me
     */
    public LoginResponse getMe() throws ApiException {
        if (accessToken == null || accessToken.isEmpty()) {
            throw new ApiException("No hay token de acceso");
        }

        String url = gatewayUrl + "/auth/me";
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer " + accessToken)
                .get()
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorCode = errorObj.has("error") ? errorObj.get("error").getAsString() : "unknown_error";
                String errorMessage = errorObj.has("message") ? errorObj.get("message").getAsString() : "Error desconocido";
                throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
            }

            return gson.fromJson(responseBody, LoginResponse.class);
        } catch (IOException e) {
            throw new ApiException("Error de conexión: " + e.getMessage(), e);
        }
    }

    /**
     * Ejecuta una petición de login/registro y parsea la respuesta
     */
    private LoginResponse executeLogin(String url, JsonObject payload) throws ApiException {
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorCode = errorObj.has("error") ? errorObj.get("error").getAsString() : "unknown_error";
                String errorMessage = errorObj.has("message") ? errorObj.get("message").getAsString() : "Error desconocido";
                throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
            }

            LoginResponse loginResponse = gson.fromJson(responseBody, LoginResponse.class);
            
            // Establecer el token para futuras peticiones
            if (loginResponse.getAccessToken() != null) {
                setAccessToken(loginResponse.getAccessToken());
            }
            
            return loginResponse;
        } catch (IOException e) {
            throw new ApiException("Error de conexión: " + e.getMessage(), e);
        }
    }

    /**
     * Obtiene el dashboard completo del paciente autenticado
     * Requiere que el token de acceso esté configurado
     * 
     * @param token Token de acceso del paciente
     * @return JsonObject con los datos del dashboard
     * @throws ApiException si hay error en la petición
     */
    public JsonObject getPatientDashboard(String token) throws ApiException {
        return executeGatewayGet("/patient/dashboard", null, token, true, "Error al obtener dashboard");
    }

    /**
     * Obtiene todas las alertas del paciente con paginación
     * 
     * @param token Token de acceso del paciente
     * @param limit Cantidad máxima de alertas a retornar
     * @return JsonObject con las alertas del paciente
     * @throws ApiException si hay error en la petición
     */
    public JsonObject getPatientAlerts(String token, int limit) throws ApiException {
        return getPatientAlerts(token, limit, 0, null);
    }

    public JsonObject getPatientAlerts(String token, int limit, int offset, String status) throws ApiException {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        params.put("offset", String.valueOf(Math.max(0, offset)));
        if (status != null && !status.trim().isEmpty()) {
            params.put("status", status);
        }
        return executeGatewayGet("/patient/alerts", params, token, true, "Error al obtener alertas");
    }

    /**
     * Obtiene todos los dispositivos del paciente
     * 
     * @param token Token de acceso del paciente
     * @return JsonObject con los dispositivos del paciente
     * @throws ApiException si hay error en la petición
     */
    public JsonObject getPatientDevices(String token) throws ApiException {
        return executeGatewayGet("/patient/devices", null, token, true, "Error al obtener dispositivos");
    }

    /**
     * Obtiene la última ubicación del paciente
     */
    public JsonObject getPatientLatestLocation(String token) throws ApiException {
        return executeGatewayGet("/patient/location/latest", null, token, true, "Error al obtener ubicación");
    }
    
    /**
     * Obtiene las últimas N ubicaciones del paciente
     */
    public JsonObject getPatientLocations(String token, int limit) throws ApiException {
        return getPatientLocations(token, limit, 0);
    }

    public JsonObject getPatientLocations(String token, int limit, int offset) throws ApiException {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        params.put("offset", String.valueOf(Math.max(0, offset)));
        return executeGatewayGet("/patient/locations", params, token, true, "Error al obtener ubicaciones");
    }

    public JsonObject getPatientCaregivers(String token) throws ApiException {
        return executeGatewayGet("/patient/caregivers", null, token, true, "Error al obtener cuidadores");
    }

    public JsonObject getPatientCareTeam(String token) throws ApiException {
        return executeGatewayGet("/patient/care-team", null, token, true, "Error al obtener equipo de cuidado");
    }

    public JsonObject getPatientProfile(String token) throws ApiException {
        return executeGatewayGet("/patient/profile", null, token, true, "Error al obtener perfil del paciente");
    }

    public JsonObject getPatientReadings(String token, int limit, int offset) throws ApiException {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        params.put("offset", String.valueOf(Math.max(0, offset)));
        return executeGatewayGet("/patient/readings", params, token, true, "Error al obtener lecturas");
    }

    /**
     * Obtiene la URL del gateway configurada
     */
    public String getGatewayUrl() {
        return gatewayUrl;
    }

    private String resolveToken(String token) {
        if (token != null && !token.isEmpty()) {
            return token;
        }
        return accessToken;
    }

    private JsonObject executeGatewayGet(
            String path,
            Map<String, String> queryParams,
            String token,
            boolean requiresToken,
            String defaultErrorMessage
    ) throws ApiException {
        String authToken = resolveToken(token);
        if (requiresToken && (authToken == null || authToken.isEmpty())) {
            throw new ApiException("Token de acceso no proporcionado");
        }

        HttpUrl baseUrl = HttpUrl.parse(gatewayUrl + path);
        if (baseUrl == null) {
            throw new ApiException("URL inválida del gateway: " + gatewayUrl + path);
        }

        HttpUrl.Builder urlBuilder = baseUrl.newBuilder();
        if (queryParams != null) {
            for (Map.Entry<String, String> entry : queryParams.entrySet()) {
                if (entry.getValue() != null) {
                    urlBuilder.addQueryParameter(entry.getKey(), entry.getValue());
                }
            }
        }

        Request.Builder requestBuilder = new Request.Builder()
                .url(urlBuilder.build())
                .get();

        if (authToken != null && !authToken.isEmpty()) {
            requestBuilder.addHeader("Authorization", "Bearer " + authToken);
        }

        try (Response response = httpClient.newCall(requestBuilder.build()).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            handleErrorIfNeeded(response, responseBody, defaultErrorMessage);

            if (responseBody.isEmpty()) {
                return new JsonObject();
            }

            JsonObject payload = gson.fromJson(responseBody, JsonObject.class);
            return payload != null ? payload : new JsonObject();
        } catch (IOException e) {
            throw new ApiException("Error de conexión con el gateway: " + e.getMessage(), e);
        }
    }

    private JsonObject executeGatewayRequest(
            String method,
            String path,
            JsonObject payload,
            Map<String, String> queryParams,
            String token,
            boolean requiresToken,
            String defaultErrorMessage
    ) throws ApiException {
        String authToken = resolveToken(token);
        if (requiresToken && (authToken == null || authToken.isEmpty())) {
            throw new ApiException("Token de acceso no proporcionado");
        }

        HttpUrl baseUrl = HttpUrl.parse(gatewayUrl + path);
        if (baseUrl == null) {
            throw new ApiException("URL inválida del gateway: " + gatewayUrl + path);
        }

        HttpUrl.Builder urlBuilder = baseUrl.newBuilder();
        if (queryParams != null) {
            for (Map.Entry<String, String> entry : queryParams.entrySet()) {
                if (entry.getValue() != null) {
                    urlBuilder.addQueryParameter(entry.getKey(), entry.getValue());
                }
            }
        }

        RequestBody body = payload != null ? RequestBody.create(gson.toJson(payload), JSON) : RequestBody.create("", JSON);

        Request.Builder requestBuilder = new Request.Builder()
                .url(urlBuilder.build());

        if ("PATCH".equalsIgnoreCase(method)) {
            requestBuilder.patch(body);
        } else if ("POST".equalsIgnoreCase(method)) {
            requestBuilder.post(body);
        } else if ("DELETE".equalsIgnoreCase(method)) {
            requestBuilder.delete(body);
        } else {
            throw new IllegalArgumentException("Método no soportado: " + method);
        }

        if (authToken != null && !authToken.isEmpty()) {
            requestBuilder.addHeader("Authorization", "Bearer " + authToken);
        }

        try (Response response = httpClient.newCall(requestBuilder.build()).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            handleErrorIfNeeded(response, responseBody, defaultErrorMessage);

            if (responseBody.isEmpty()) {
                return new JsonObject();
            }

            JsonObject payloadResponse = gson.fromJson(responseBody, JsonObject.class);
            return payloadResponse != null ? payloadResponse : new JsonObject();
        } catch (IOException e) {
            throw new ApiException("Error de conexión con el gateway: " + e.getMessage(), e);
        }
    }

    private void handleErrorIfNeeded(Response response, String responseBody, String defaultErrorMessage) throws ApiException {
        if (response.isSuccessful()) {
            return;
        }

        JsonObject errorPayload = null;
        if (responseBody != null && !responseBody.isEmpty()) {
            try {
                errorPayload = gson.fromJson(responseBody, JsonObject.class);
            } catch (Exception ignored) {
                errorPayload = null;
            }
        }

        String errorCode = "unknown_error";
        String errorMessage = defaultErrorMessage;

        if (response.code() == 401) {
            errorCode = "unauthorized";
            errorMessage = "Sesión expirada. Por favor, vuelve a iniciar sesión.";
        }

        if (errorPayload != null) {
            if (errorPayload.has("error") && !errorPayload.get("error").isJsonNull()) {
                JsonElement errorElement = errorPayload.get("error");
                // El campo "error" puede ser String o JsonObject
                if (errorElement.isJsonPrimitive()) {
                    errorCode = errorElement.getAsString();
                } else if (errorElement.isJsonObject()) {
                    // Si es objeto, intentar extraer un código o convertir a string
                    JsonObject errorObj = errorElement.getAsJsonObject();
                    if (errorObj.has("code")) {
                        errorCode = errorObj.get("code").getAsString();
                    } else {
                        errorCode = errorObj.toString();
                    }
                }
            }
            if (errorPayload.has("message") && !errorPayload.get("message").isJsonNull()) {
                JsonElement messageElement = errorPayload.get("message");
                // El campo "message" también puede ser String o JsonObject
                if (messageElement.isJsonPrimitive()) {
                    errorMessage = messageElement.getAsString();
                } else if (messageElement.isJsonObject()) {
                    errorMessage = messageElement.toString();
                }
            }
        }

        throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
    }

    // ---------------------------- Usuarios ---------------------------------

    public JsonObject getCurrentUserProfile(String token) throws ApiException {
        return executeGatewayGet("/users/me", null, token, true, "Error al obtener perfil de usuario");
    }

    public JsonArray getCurrentUserMemberships(String token) throws ApiException {
        System.out.println("[DEBUG] ApiClient.getCurrentUserMemberships() - Llamando endpoint /users/me/org-memberships");
        JsonObject response = executeGatewayGet(
                "/users/me/org-memberships",
                null,
                token,
                true,
                "Error al obtener organizaciones"
        );
        System.out.println("[DEBUG] Respuesta completa del endpoint: " + response.toString());
        
        if (response.has("data")) {
            System.out.println("[DEBUG] Campo 'data' encontrado");
            
            // La estructura es: {"data": {"memberships": [...]}}
            if (response.get("data").isJsonObject()) {
                JsonObject dataObj = response.getAsJsonObject("data");
                System.out.println("[DEBUG] 'data' es un JsonObject");
                
                if (dataObj.has("memberships") && dataObj.get("memberships").isJsonArray()) {
                    JsonArray membershipsArray = dataObj.getAsJsonArray("memberships");
                    System.out.println("[DEBUG] Campo 'memberships' encontrado con " + membershipsArray.size() + " elementos");
                    return membershipsArray;
                } else {
                    System.out.println("[DEBUG] ADVERTENCIA: No se encontró campo 'memberships' o no es un array");
                    System.out.println("[DEBUG] Campos disponibles en 'data': " + dataObj.keySet());
                }
            } else if (response.get("data").isJsonArray()) {
                // Por si acaso el formato cambia en el futuro
                JsonArray dataArray = response.getAsJsonArray("data");
                System.out.println("[DEBUG] 'data' es un JsonArray con " + dataArray.size() + " elementos (formato alternativo)");
                return dataArray;
            } else {
                System.out.println("[DEBUG] ADVERTENCIA: 'data' NO es ni JsonObject ni JsonArray, es: " + response.get("data").getClass().getSimpleName());
            }
        } else {
            System.out.println("[DEBUG] ADVERTENCIA: No se encontró campo 'data' en la respuesta");
            System.out.println("[DEBUG] Campos disponibles: " + response.keySet());
        }
        
        return new JsonArray();
    }

    public JsonArray getPendingInvitations(String token) throws ApiException {
        JsonObject response = executeGatewayGet(
                "/users/me/invitations",
                null,
                token,
                true,
                "Error al obtener invitaciones"
        );
        // El backend devuelve: { data: { invitations: [...] } }
        if (response.has("data") && response.get("data").isJsonObject()) {
            JsonObject data = response.getAsJsonObject("data");
            if (data.has("invitations") && data.get("invitations").isJsonArray()) {
                return data.getAsJsonArray("invitations");
            }
        }
        return new JsonArray();
    }

    public JsonObject updateCurrentUserProfile(String token, Map<String, Object> updates) throws ApiException {
        JsonObject payload = new JsonObject();
        if (updates != null) {
            for (Map.Entry<String, Object> entry : updates.entrySet()) {
                if (entry.getValue() == null) {
                    payload.add(entry.getKey(), JsonNull.INSTANCE);
                } else {
                    payload.add(entry.getKey(), gson.toJsonTree(entry.getValue()));
                }
            }
        }
        return executeGatewayRequest(
                "PATCH",
                "/users/me",
                payload,
                null,
                token,
                true,
                "Error al actualizar perfil"
        );
    }

    public JsonObject acceptInvitation(String token, String invitationId) throws ApiException {
        return executeGatewayRequest(
                "POST",
                "/users/me/invitations/" + invitationId + "/accept",
                new JsonObject(),
                null,
                token,
                true,
                "Error al aceptar invitación"
        );
    }

    public JsonObject rejectInvitation(String token, String invitationId) throws ApiException {
        return executeGatewayRequest(
                "POST",
                "/users/me/invitations/" + invitationId + "/reject",
                new JsonObject(),
                null,
                token,
                true,
                "Error al rechazar invitación"
        );
    }

    // ------------------------- Dashboard Organizacional --------------------

    public JsonObject getOrganizationDashboard(String token, String orgId) throws ApiException {
        return executeGatewayGet(
                "/orgs/" + orgId + "/dashboard",
                null,
                token,
                true,
                "Error al obtener dashboard organizacional"
        );
    }

    public JsonObject getOrganizationMetrics(String token, String orgId) throws ApiException {
        return executeGatewayGet(
                "/orgs/" + orgId + "/metrics",
                null,
                token,
                true,
                "Error al obtener métricas de organización"
        );
    }

    public JsonObject getOrganizationCareTeams(String token, String orgId) throws ApiException {
        return executeGatewayGet(
                "/orgs/" + orgId + "/care-teams",
                null,
                token,
                true,
                "Error al obtener equipos de cuidado"
        );
    }

    public JsonObject getOrganizationCareTeamPatients(String token, String orgId) throws ApiException {
        return executeGatewayGet(
                "/orgs/" + orgId + "/care-team-patients",
                null,
                token,
                true,
                "Error al obtener pacientes por equipo"
        );
    }

    public JsonObject getOrganizationPatientDetail(String token, String orgId, String patientId) throws ApiException {
        return executeGatewayGet(
                "/orgs/" + orgId + "/patients/" + patientId,
                null,
                token,
                true,
                "Error al obtener detalle del paciente"
        );
    }

    public JsonObject getOrganizationPatientAlerts(String token, String orgId, String patientId, int limit) throws ApiException {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        return executeGatewayGet(
                "/orgs/" + orgId + "/patients/" + patientId + "/alerts",
                params,
                token,
                true,
                "Error al obtener alertas del paciente"
        );
    }

    public JsonObject getOrganizationPatientNotes(String token, String orgId, String patientId, int limit) throws ApiException {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        return executeGatewayGet(
                "/orgs/" + orgId + "/patients/" + patientId + "/notes",
                params,
                token,
                true,
                "Error al obtener notas del paciente"
        );
    }

    // ------------------------- Pacientes y Cuidadores ----------------------

    public JsonObject getCaregiverPatients(String token) throws ApiException {
        return executeGatewayGet(
                "/caregiver/patients",
                null,
                token,
                true,
                "Error al obtener pacientes asignados"
        );
    }

    public JsonObject getCaregiverPatientAlerts(String token, String patientId, int limit) throws ApiException {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        return executeGatewayGet(
                "/caregiver/patients/" + patientId + "/alerts",
                params,
                token,
                true,
                "Error al obtener alertas del paciente"
        );
    }

    public JsonObject getCaregiverPatientNotes(String token, String patientId) throws ApiException {
        return executeGatewayGet(
                "/caregiver/patients/" + patientId + "/notes",
                null,
                token,
                true,
                "Error al obtener notas del paciente"
        );
    }

    // --------------------------- Mapa y ubicaciones -----------------------

    public JsonObject getCareTeamLocations(String token, Map<String, String> params) throws ApiException {
        return executeGatewayGet(
                "/care-team/locations",
                params,
                token,
                true,
                "Error al obtener ubicaciones de equipos"
        );
    }

    public JsonObject getCaregiverPatientLocations(String token, Map<String, String> params) throws ApiException {
        return executeGatewayGet(
                "/caregiver/patients/locations",
                params,
                token,
                true,
                "Error al obtener ubicaciones de pacientes"
        );
    }

    // --------------------------- Dispositivos ------------------------------

    public JsonObject getCareTeamDevices(String token, String orgId, String teamId) throws ApiException {
        return executeGatewayGet(
                "/orgs/" + orgId + "/care-teams/" + teamId + "/devices",
                null,
                token,
                true,
                "Error al obtener dispositivos del equipo"
        );
    }

    public JsonObject getCareTeamDisconnectedDevices(String token, String orgId, String teamId) throws ApiException {
        return executeGatewayGet(
                "/orgs/" + orgId + "/care-teams/" + teamId + "/devices/disconnected",
                null,
                token,
                true,
                "Error al obtener dispositivos desconectados"
        );
    }

    public JsonObject getCareTeamDeviceStreams(String token, String orgId, String teamId, String deviceId) throws ApiException {
        return executeGatewayGet(
                "/orgs/" + orgId + "/care-teams/" + teamId + "/devices/" + deviceId + "/streams",
                null,
                token,
                true,
                "Error al obtener streams del dispositivo"
        );
    }
}
