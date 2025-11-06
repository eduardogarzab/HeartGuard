package com.heartguard.desktop.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
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

    private JsonObject executeGatewayGet(
            String path,
            Map<String, String> queryParams,
            String token,
            boolean requiresToken,
            String defaultErrorMessage
    ) throws ApiException {
        if (requiresToken && (token == null || token.isEmpty())) {
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

        if (token != null && !token.isEmpty()) {
            requestBuilder.addHeader("Authorization", "Bearer " + token);
        }

        try (Response response = httpClient.newCall(requestBuilder.build()).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            if (!response.isSuccessful()) {
                JsonObject errorPayload = null;
                if (!responseBody.isEmpty()) {
                    try {
                        errorPayload = gson.fromJson(responseBody, JsonObject.class);
                    } catch (Exception ignored) {
                        errorPayload = null;
                    }
                }

                String errorCode = "unknown_error";
                String errorMessage = defaultErrorMessage;

                if (errorPayload != null) {
                    if (errorPayload.has("error") && !errorPayload.get("error").isJsonNull()) {
                        errorCode = errorPayload.get("error").getAsString();
                    }
                    if (errorPayload.has("message") && !errorPayload.get("message").isJsonNull()) {
                        errorMessage = errorPayload.get("message").getAsString();
                    }
                }

                throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
            }

            if (responseBody.isEmpty()) {
                return new JsonObject();
            }

            JsonObject payload = gson.fromJson(responseBody, JsonObject.class);
            return payload != null ? payload : new JsonObject();
        } catch (IOException e) {
            throw new ApiException("Error de conexión con el gateway: " + e.getMessage(), e);
        }
    }
}
