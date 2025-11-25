package com.heartguard.desktop.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.heartguard.desktop.config.AppConfig;
import com.heartguard.desktop.models.LoginResponse;
import com.heartguard.desktop.models.Patient;
import com.heartguard.desktop.models.User;
import okhttp3.*;

import java.io.IOException;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * Cliente HTTP para comunicarse con el Gateway API
 * Todas las peticiones pasan por el Gateway (puerto 8080)
 * El Gateway se encarga de enrutar a los microservicios internos
 */
public class ApiClient {
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");

    private final String gatewayUrl;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private String accessToken;

    public ApiClient() {
        this(AppConfig.getInstance().getGatewayBaseUrl());
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
                .get()
                .header("Cache-Control", "no-cache");

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

    private CompletableFuture<JsonObject> executeGatewayGetAsync(
            String path,
            Map<String, String> queryParams,
            String token,
            boolean requiresToken,
            String defaultErrorMessage
    ) {
        CompletableFuture<JsonObject> future = new CompletableFuture<>();

        String authToken = resolveToken(token);
        if (requiresToken && (authToken == null || authToken.isEmpty())) {
            future.completeExceptionally(new ApiException("Token de acceso no proporcionado"));
            return future;
        }

        HttpUrl baseUrl = HttpUrl.parse(gatewayUrl + path);
        if (baseUrl == null) {
            future.completeExceptionally(new ApiException("URL inválida del gateway: " + gatewayUrl + path));
            return future;
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
                .get()
                .header("Cache-Control", "no-cache");

        if (authToken != null && !authToken.isEmpty()) {
            requestBuilder.addHeader("Authorization", "Bearer " + authToken);
        }

        httpClient.newCall(requestBuilder.build()).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                future.completeExceptionally(new ApiException("Error de conexión con el gateway: " + e.getMessage(), e));
            }

            @Override
            public void onResponse(Call call, Response response) {
                try (response) {
                    String responseBody = response.body() != null ? response.body().string() : "";
                    handleErrorIfNeeded(response, responseBody, defaultErrorMessage);
                    if (responseBody.isEmpty()) {
                        future.complete(new JsonObject());
                        return;
                    }
                    JsonObject payload = gson.fromJson(responseBody, JsonObject.class);
                    future.complete(payload != null ? payload : new JsonObject());
                } catch (ApiException e) {
                    future.completeExceptionally(e);
                } catch (Exception e) {
                    future.completeExceptionally(new ApiException("Error procesando respuesta: " + e.getMessage(), e));
                }
            }
        });

        return future;
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
        return executeGatewayGet("/user/users/me", null, token, true, "Error al obtener perfil de usuario");
    }

    public JsonArray getCurrentUserMemberships(String token) throws ApiException {
        JsonObject response = executeGatewayGet(
                "/user/users/me/org-memberships",
                null,
                token,
                true,
                "Error al obtener organizaciones"
        );

        if (response.has("data")) {
            // La estructura es: {"data": {"memberships": [...]}}
            if (response.get("data").isJsonObject()) {
                JsonObject dataObj = response.getAsJsonObject("data");

                if (dataObj.has("memberships") && dataObj.get("memberships").isJsonArray()) {
                    JsonArray membershipsArray = dataObj.getAsJsonArray("memberships");
                    return membershipsArray;
                }
            } else if (response.get("data").isJsonArray()) {
                // Por si acaso el formato cambia en el futuro
                JsonArray dataArray = response.getAsJsonArray("data");
                return dataArray;
            }
        }

        return new JsonArray();
    }

    public JsonArray getPendingInvitations(String token) throws ApiException {
        JsonObject response = executeGatewayGet(
                "/user/users/me/invitations",
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
                "/user/users/me",
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
                "/user/users/me/invitations/" + invitationId + "/accept",
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
                "/user/users/me/invitations/" + invitationId + "/reject",
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
                "/user/orgs/" + orgId + "/dashboard",
                null,
                token,
                true,
                "Error al obtener dashboard organizacional"
        );
    }

    public JsonObject getOrganizationMetrics(String token, String orgId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/metrics",
                null,
                token,
                true,
                "Error al obtener métricas de organización"
        );
    }

    public JsonObject getOrganizationCareTeams(String token, String orgId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/care-teams",
                null,
                token,
                true,
                "Error al obtener equipos de cuidado"
        );
    }

    public JsonObject getOrganizationCareTeamDevices(String token, String orgId, String careTeamId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/care-teams/" + careTeamId + "/devices",
                null,
                token,
                true,
                "Error al obtener dispositivos del equipo"
        );
    }

    public JsonObject getOrganizationCareTeamPatients(String token, String orgId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/care-team-patients",
                null,
                token,
                true,
                "Error al obtener pacientes por equipo"
        );
    }

    public JsonObject getOrganizationPatientDetail(String token, String orgId, String patientId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/patients/" + patientId,
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
                "/user/orgs/" + orgId + "/patients/" + patientId + "/alerts",
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
                "/user/orgs/" + orgId + "/patients/" + patientId + "/notes",
                params,
                token,
                true,
                "Error al obtener notas del paciente"
        );
    }

    // ------------------------- Pacientes y Cuidadores ----------------------

    public JsonObject getCaregiverPatients(String token) throws ApiException {
        return executeGatewayGet(
                "/user/caregiver/patients",
                null,
                token,
                true,
                "Error al obtener pacientes asignados"
        );
    }

    public JsonObject getEventTypes() throws ApiException {
        return executeGatewayGet(
                "/user/event-types",
                null,
                null,
                false,
                "Error al obtener tipos de evento"
        );
    }

    public JsonObject getCaregiverPatientDetail(String token, String patientId) throws ApiException {
        return executeGatewayGet(
                "/user/caregiver/patients/" + patientId,
                null,
                token,
                true,
                "Error al obtener detalle del paciente"
        );
    }

    public JsonObject getCaregiverPatientAlerts(String token, String patientId, int limit) throws ApiException {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        return executeGatewayGet(
                "/user/caregiver/patients/" + patientId + "/alerts",
                params,
                token,
                true,
                "Error al obtener alertas del paciente"
        );
    }

    public JsonObject getCaregiverPatientNotes(String token, String patientId, int limit) throws ApiException {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        return executeGatewayGet(
                "/user/caregiver/patients/" + patientId + "/notes",
                params,
                token,
                true,
                "Error al obtener notas del paciente"
        );
    }

    public JsonObject getCaregiverPatientDevices(String token, String patientId) throws ApiException {
        return executeGatewayGet(
                "/user/caregiver/patients/" + patientId + "/devices",
                null,
                token,
                true,
                "Error al obtener dispositivos del paciente"
        );
    }

    public JsonObject getOrganizationPatientDevices(String token, String orgId, String patientId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/patients/" + patientId + "/devices",
                null,
                token,
                true,
                "Error al obtener dispositivos del paciente"
        );
    }

    public JsonObject createCaregiverPatientNote(String token, String patientId, JsonObject noteData) throws ApiException {
        return executeGatewayRequest(
                "POST",
                "/user/caregiver/patients/" + patientId + "/notes",
                noteData,
                null,
                token,
                true,
                "Error al crear nota del paciente"
        );
    }

    // --------------------------- Mapa y ubicaciones -----------------------

    public JsonObject getCareTeamLocations(String token, Map<String, String> params) throws ApiException {
        return executeGatewayGet(
                "/user/care-team/locations",
                params,
                token,
                true,
                "Error al obtener ubicaciones de equipos"
        );
    }

    public JsonObject getCaregiverPatientLocations(String token, Map<String, String> params) throws ApiException {
        return executeGatewayGet(
                "/user/caregiver/patients/locations",
                params,
                token,
                true,
                "Error al obtener ubicaciones de pacientes"
        );
    }

    public JsonObject getOrganizationCareTeamPatientsLocations(String token, String orgId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/care-team-patients/locations",
                null,
                token,
                true,
                "Error al obtener ubicaciones de pacientes de care teams"
        );
    }

    // --------------------------- Dispositivos ------------------------------

    /**
     * Obtiene TODOS los dispositivos de una organización (sin filtro de care_team)
     * @param token Token de autenticación
     * @param orgId ID de la organización
     * @param active Filtro opcional: true=activos, false=inactivos, null=todos
     * @param connected Filtro opcional: true=conectados, false=desconectados, null=todos
     * @return JsonObject con lista de dispositivos
     */
    public JsonObject getOrganizationDevices(String token, String orgId, Boolean active, Boolean connected) throws ApiException {
        Map<String, String> queryParams = new HashMap<>();
        if (active != null) {
            queryParams.put("active", active.toString());
        }
        if (connected != null) {
            queryParams.put("connected", connected.toString());
        }
        
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/devices",
                queryParams.isEmpty() ? null : queryParams,
                token,
                true,
                "Error al obtener dispositivos de la organización"
        );
    }

    /**
     * Obtiene detalle de un dispositivo específico
     */
    public JsonObject getOrganizationDevice(String token, String orgId, String deviceId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/devices/" + deviceId,
                null,
                token,
                true,
                "Error al obtener detalle del dispositivo"
        );
    }

    /**
     * Obtiene historial de streams (conexiones) de un dispositivo
     */
    public JsonObject getOrganizationDeviceStreams(String token, String orgId, String deviceId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/devices/" + deviceId + "/streams",
                null,
                token,
                true,
                "Error al obtener historial de streams del dispositivo"
        );
    }

    // Métodos legacy (deprecated - mantener para compatibilidad)
    @Deprecated
    public JsonObject getCareTeamDevices(String token, String orgId, String teamId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/care-teams/" + teamId + "/devices",
                null,
                token,
                true,
                "Error al obtener dispositivos del equipo"
        );
    }

    @Deprecated
    public JsonObject getCareTeamDisconnectedDevices(String token, String orgId, String teamId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/care-teams/" + teamId + "/devices/disconnected",
                null,
                token,
                true,
                "Error al obtener dispositivos desconectados"
        );
    }

    @Deprecated
    public JsonObject getCareTeamDeviceStreams(String token, String orgId, String teamId, String deviceId) throws ApiException {
        return executeGatewayGet(
                "/user/orgs/" + orgId + "/care-teams/" + teamId + "/devices/" + deviceId + "/streams",
                null,
                token,
                true,
                "Error al obtener streams del dispositivo"
        );
    }

    // --------------------------- Variantes asíncronas ------------------------------

    public CompletableFuture<JsonObject> getOrganizationDashboardAsync(String token, String orgId) {
        return executeGatewayGetAsync(
                "/user/orgs/" + orgId + "/dashboard",
                null,
                token,
                true,
                "Error al obtener dashboard organizacional"
        );
    }

    public CompletableFuture<JsonObject> getOrganizationMetricsAsync(String token, String orgId) {
        return executeGatewayGetAsync(
                "/user/orgs/" + orgId + "/metrics",
                null,
                token,
                true,
                "Error al obtener métricas de organización"
        );
    }

    public CompletableFuture<JsonObject> getOrganizationCareTeamsAsync(String token, String orgId) {
        return executeGatewayGetAsync(
                "/user/orgs/" + orgId + "/care-teams",
                null,
                token,
                true,
                "Error al obtener equipos de cuidado"
        );
    }

    public CompletableFuture<JsonObject> getOrganizationCareTeamPatientsAsync(String token, String orgId) {
        return executeGatewayGetAsync(
                "/user/orgs/" + orgId + "/care-team-patients",
                null,
                token,
                true,
                "Error al obtener pacientes por equipo"
        );
    }

    public CompletableFuture<JsonObject> getCaregiverPatientsAsync(String token) {
        return executeGatewayGetAsync(
                "/user/caregiver/patients",
                null,
                token,
                true,
                "Error al obtener pacientes asignados"
        );
    }

    public CompletableFuture<JsonObject> getCareTeamLocationsAsync(String token, Map<String, String> params) {
        return executeGatewayGetAsync(
                "/user/care-team/locations",
                params,
                token,
                true,
                "Error al obtener ubicaciones de equipos"
        );
    }

    public CompletableFuture<JsonObject> getCaregiverPatientLocationsAsync(String token, Map<String, String> params) {
        return executeGatewayGetAsync(
                "/user/caregiver/patients/locations",
                params,
                token,
                true,
                "Error al obtener ubicaciones de pacientes"
        );
    }

    public CompletableFuture<JsonObject> getOrganizationCareTeamPatientsLocationsAsync(String token, String orgId) {
        return executeGatewayGetAsync(
                "/user/orgs/" + orgId + "/care-team-patients/locations",
                null,
                token,
                true,
                "Error al obtener ubicaciones de pacientes de care teams"
        );
    }

    public CompletableFuture<JsonObject> getCareTeamDevicesAsync(String token, String orgId, String teamId) {
        return executeGatewayGetAsync(
                "/user/orgs/" + orgId + "/care-teams/" + teamId + "/devices",
                null,
                token,
                true,
                "Error al obtener dispositivos del equipo"
        );
    }

    public CompletableFuture<JsonObject> getCareTeamDisconnectedDevicesAsync(String token, String orgId, String teamId) {
        return executeGatewayGetAsync(
                "/user/orgs/" + orgId + "/care-teams/" + teamId + "/devices/disconnected",
                null,
                token,
                true,
                "Error al obtener dispositivos desconectados"
        );
    }

    public CompletableFuture<JsonObject> getCareTeamDeviceStreamsAsync(String token, String orgId, String teamId, String deviceId) {
        return executeGatewayGetAsync(
                "/user/orgs/" + orgId + "/care-teams/" + teamId + "/devices/" + deviceId + "/streams",
                null,
                token,
                true,
                "Error al obtener streams del dispositivo"
        );
    }

    public CompletableFuture<JsonObject> getPatientDashboardAsync(String token) {
        return executeGatewayGetAsync(
                "/patient/dashboard",
                null,
                token,
                true,
                "Error al obtener dashboard"
        );
    }

    public CompletableFuture<JsonObject> getPatientAlertsAsync(String token, int limit) {
        return getPatientAlertsAsync(token, limit, 0, null);
    }

    public CompletableFuture<JsonObject> getPatientAlertsAsync(String token, int limit, int offset, String status) {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        params.put("offset", String.valueOf(Math.max(0, offset)));
        if (status != null && !status.trim().isEmpty()) {
            params.put("status", status);
        }
        return executeGatewayGetAsync(
                "/patient/alerts",
                params,
                token,
                true,
                "Error al obtener alertas"
        );
    }

    public CompletableFuture<JsonObject> getPatientDevicesAsync(String token) {
        return executeGatewayGetAsync(
                "/patient/devices",
                null,
                token,
                true,
                "Error al obtener dispositivos"
        );
    }

    public CompletableFuture<JsonObject> getPatientLocationsAsync(String token, int limit) {
        return getPatientLocationsAsync(token, limit, 0);
    }

    public CompletableFuture<JsonObject> getPatientLocationsAsync(String token, int limit, int offset) {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("limit", String.valueOf(Math.max(1, limit)));
        params.put("offset", String.valueOf(Math.max(0, offset)));
        return executeGatewayGetAsync(
                "/patient/locations",
                params,
                token,
                true,
                "Error al obtener ubicaciones"
        );
    }

    public CompletableFuture<JsonObject> getPatientCaregiversAsync(String token) {
        return executeGatewayGetAsync(
                "/patient/caregivers",
                null,
                token,
                true,
                "Error al obtener cuidadores"
        );
    }

    public CompletableFuture<JsonObject> getPatientCareTeamAsync(String token) {
        return executeGatewayGetAsync(
                "/patient/care-team",
                null,
                token,
                true,
                "Error al obtener equipo de cuidado"
        );
    }

    /**
     * Sube o actualiza la foto de perfil de un paciente
     * Ruta: POST/PUT /media/patients/{patientId}/photo
     * 
     * @param token Token de autenticación del paciente
     * @param patientId ID del paciente
     * @param photoFile Archivo de la foto a subir
     * @param isUpdate true para PUT (actualizar), false para POST (crear)
     * @return CompletableFuture con la respuesta que incluye la URL de la foto
     */
    public CompletableFuture<JsonObject> uploadPatientPhotoAsync(String token, String patientId, 
                                                                  java.io.File photoFile, boolean isUpdate) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String url = gatewayUrl + "/media/patients/" + patientId + "/photo";
                
                // Determinar el content type basado en la extensión del archivo
                String fileName = photoFile.getName().toLowerCase();
                String contentType = "image/jpeg"; // default
                if (fileName.endsWith(".png")) {
                    contentType = "image/png";
                } else if (fileName.endsWith(".jpg") || fileName.endsWith(".jpeg")) {
                    contentType = "image/jpeg";
                } else if (fileName.endsWith(".webp")) {
                    contentType = "image/webp";
                }
                
                RequestBody fileBody = RequestBody.create(
                        photoFile,
                        MediaType.parse(contentType)
                );
                
                RequestBody requestBody = new MultipartBody.Builder()
                        .setType(MultipartBody.FORM)
                        .addFormDataPart("photo", photoFile.getName(), fileBody)
                        .build();
                
                Request.Builder requestBuilder = new Request.Builder()
                        .url(url)
                        .addHeader("Authorization", "Bearer " + token);
                
                if (isUpdate) {
                    requestBuilder.put(requestBody);
                } else {
                    requestBuilder.post(requestBody);
                }
                
                Request request = requestBuilder.build();
                
                Response response = httpClient.newCall(request).execute();
                String responseBody = response.body() != null ? response.body().string() : "{}";
                
                if (!response.isSuccessful()) {
                    JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                    String errorMessage = errorObj.has("message") 
                            ? errorObj.get("message").getAsString() 
                            : "Error al subir la foto";
                    throw new RuntimeException(new ApiException(errorMessage, response.code(), "photo_upload_error", responseBody));
                }
                
                response.close();
                return gson.fromJson(responseBody, JsonObject.class);
            } catch (IOException e) {
                throw new RuntimeException(new ApiException("Error al subir la foto: " + e.getMessage(), e));
            }
        });
    }

    /**
     * Elimina la foto de perfil de un paciente
     * Ruta: DELETE /media/patients/{patientId}/photo
     * 
     * @param token Token de autenticación del paciente
     * @param patientId ID del paciente
     * @return CompletableFuture con la respuesta de confirmación
     */
    public CompletableFuture<JsonObject> deletePatientPhotoAsync(String token, String patientId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String url = gatewayUrl + "/media/patients/" + patientId + "/photo";
                
                Request request = new Request.Builder()
                        .url(url)
                        .delete()
                        .addHeader("Authorization", "Bearer " + token)
                        .build();
                
                Response response = httpClient.newCall(request).execute();
                String responseBody = response.body() != null ? response.body().string() : "{}";
                
                if (!response.isSuccessful()) {
                    JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                    String errorMessage = errorObj.has("message") 
                            ? errorObj.get("message").getAsString() 
                            : "Error al eliminar la foto";
                    throw new RuntimeException(new ApiException(errorMessage, response.code(), "photo_delete_error", responseBody));
                }
                
                response.close();
                return gson.fromJson(responseBody, JsonObject.class);
            } catch (IOException e) {
                throw new RuntimeException(new ApiException("Error al eliminar la foto: " + e.getMessage(), e));
            }
        });
    }

    /**
     * Sube o actualiza la foto de perfil de un usuario
     * Ruta: POST/PUT /media/users/{userId}/photo
     * 
     * @param token Token de autenticación del usuario
     * @param userId ID del usuario
     * @param photoFile Archivo de la foto a subir
     * @param isUpdate true para PUT (actualizar), false para POST (crear)
     * @return CompletableFuture con la respuesta que incluye la URL de la foto
     */
    public CompletableFuture<JsonObject> uploadUserPhotoAsync(String token, String userId, 
                                                               java.io.File photoFile, boolean isUpdate) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String url = gatewayUrl + "/media/users/" + userId + "/photo";
                
                // Determinar el content type basado en la extensión del archivo
                String fileName = photoFile.getName().toLowerCase();
                String contentType = "image/jpeg"; // default
                if (fileName.endsWith(".png")) {
                    contentType = "image/png";
                } else if (fileName.endsWith(".jpg") || fileName.endsWith(".jpeg")) {
                    contentType = "image/jpeg";
                } else if (fileName.endsWith(".webp")) {
                    contentType = "image/webp";
                }
                
                RequestBody fileBody = RequestBody.create(
                        photoFile,
                        MediaType.parse(contentType)
                );
                
                RequestBody requestBody = new MultipartBody.Builder()
                        .setType(MultipartBody.FORM)
                        .addFormDataPart("photo", photoFile.getName(), fileBody)
                        .build();
                
                Request.Builder requestBuilder = new Request.Builder()
                        .url(url)
                        .addHeader("Authorization", "Bearer " + token);
                
                if (isUpdate) {
                    requestBuilder.put(requestBody);
                } else {
                    requestBuilder.post(requestBody);
                }
                
                Request request = requestBuilder.build();
                
                Response response = httpClient.newCall(request).execute();
                String responseBody = response.body() != null ? response.body().string() : "{}";
                
                if (!response.isSuccessful()) {
                    JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                    String errorMessage = errorObj.has("message") 
                            ? errorObj.get("message").getAsString() 
                            : "Error al subir la foto";
                    throw new RuntimeException(new ApiException(errorMessage, response.code(), "photo_upload_error", responseBody));
                }
                
                response.close();
                return gson.fromJson(responseBody, JsonObject.class);
            } catch (IOException e) {
                throw new RuntimeException(new ApiException("Error al subir la foto: " + e.getMessage(), e));
            }
        });
    }

    /**
     * Elimina la foto de perfil de un usuario
     * Ruta: DELETE /media/users/{userId}/photo
     * 
     * @param token Token de autenticación del usuario
     * @param userId ID del usuario
     * @return CompletableFuture con la respuesta de confirmación
     */
    public CompletableFuture<JsonObject> deleteUserPhotoAsync(String token, String userId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String url = gatewayUrl + "/media/users/" + userId + "/photo";
                
                Request request = new Request.Builder()
                        .url(url)
                        .delete()
                        .addHeader("Authorization", "Bearer " + token)
                        .build();
                
                Response response = httpClient.newCall(request).execute();
                String responseBody = response.body() != null ? response.body().string() : "{}";
                
                if (!response.isSuccessful()) {
                    JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                    String errorMessage = errorObj.has("message") 
                            ? errorObj.get("message").getAsString() 
                            : "Error al eliminar la foto";
                    throw new RuntimeException(new ApiException(errorMessage, response.code(), "photo_delete_error", responseBody));
                }
                
                response.close();
                return gson.fromJson(responseBody, JsonObject.class);
            } catch (IOException e) {
                throw new RuntimeException(new ApiException("Error al eliminar la foto: " + e.getMessage(), e));
            }
        });
    }
    
    /**
     * Obtiene los signos vitales más recientes de un paciente desde InfluxDB vía Gateway.
     * Ruta: GET /realtime/patients/{patientId}/vital-signs
     * 
     * @param patientId ID del paciente
     * @param deviceId ID del dispositivo (opcional)
     * @param limit Número máximo de registros (default: 10)
     * @return JsonObject con los datos de signos vitales
     * @throws ApiException si hay error en la petición
     */
    public JsonObject getPatientVitalSigns(String patientId, String deviceId, int limit) throws ApiException {
        HttpUrl.Builder urlBuilder = HttpUrl.parse(gatewayUrl + "/realtime/patients/" + patientId + "/vital-signs").newBuilder();
        
        if (deviceId != null && !deviceId.isEmpty()) {
            urlBuilder.addQueryParameter("device_id", deviceId);
        }
        urlBuilder.addQueryParameter("limit", String.valueOf(limit));
        
        String url = urlBuilder.build().toString();
        
        Request.Builder requestBuilder = new Request.Builder()
                .url(url)
                .get();
        
        if (accessToken != null) {
            requestBuilder.addHeader("Authorization", "Bearer " + accessToken);
        }
        
        Request request = requestBuilder.build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "{}";
            
            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorMessage = errorObj.has("message") 
                        ? errorObj.get("message").getAsString() 
                        : "Error al obtener signos vitales";
                throw new ApiException(errorMessage, response.code(), "vital_signs_fetch_error", responseBody);
            }
            
            return gson.fromJson(responseBody, JsonObject.class);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al obtener signos vitales: " + e.getMessage(), e);
        }
    }
}

