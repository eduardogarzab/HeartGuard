package com.heartguard.desktop.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.heartguard.desktop.models.LoginResponse;
import com.heartguard.desktop.models.Patient;
import com.heartguard.desktop.models.User;
import okhttp3.*;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

/**
 * Cliente HTTP para comunicarse con el Gateway API
 * Los microservicios corren en localhost, pero el backend está en 136.115.53.140
 */
public class ApiClient {
    private static final String DEFAULT_GATEWAY_URL = "http://localhost:8000";
    private static final String DEFAULT_AUTH_SERVICE_URL = "http://localhost:5001";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    
    private final String gatewayUrl;
    private final String authServiceUrl;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private String accessToken;

    public ApiClient() {
        this(DEFAULT_GATEWAY_URL, DEFAULT_AUTH_SERVICE_URL);
    }

    public ApiClient(String gatewayUrl) {
        this(gatewayUrl, DEFAULT_AUTH_SERVICE_URL);
    }

    public ApiClient(String gatewayUrl, String authServiceUrl) {
        this.gatewayUrl = gatewayUrl;
        this.authServiceUrl = authServiceUrl;
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
     */
    public LoginResponse loginUser(String email, String password) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("email", email);
        payload.addProperty("password", password);

        String url = authServiceUrl + "/auth/login/user";
        return executeLogin(url, payload);
    }

    /**
     * Login para paciente
     */
    public LoginResponse loginPatient(String email, String password) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("email", email);
        payload.addProperty("password", password);

        String url = authServiceUrl + "/auth/login/patient";
        return executeLogin(url, payload);
    }

    /**
     * Registro de usuario (staff)
     * Según el README, solo requiere: name, email, password
     * Se crea sin organización inicial (se agregan por invitaciones)
     */
    public LoginResponse registerUser(String email, String password, String name) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("name", name);
        payload.addProperty("email", email);
        payload.addProperty("password", password);

        String url = authServiceUrl + "/auth/register/user";
        
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

        String url = authServiceUrl + "/auth/register/patient";
        
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
     */
    public boolean verifyToken() throws ApiException {
        if (accessToken == null || accessToken.isEmpty()) {
            return false;
        }

        String url = authServiceUrl + "/auth/verify";
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
     */
    public LoginResponse getMe() throws ApiException {
        if (accessToken == null || accessToken.isEmpty()) {
            throw new ApiException("No hay token de acceso");
        }

        String url = authServiceUrl + "/auth/me";
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
        if (token == null || token.isEmpty()) {
            throw new ApiException("Token de acceso no proporcionado");
        }

        String url = gatewayUrl + "/patient/dashboard";
        
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer " + token)
                .get()
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorCode = errorObj.has("error") ? errorObj.get("error").getAsString() : "unknown_error";
                String errorMessage = errorObj.has("message") ? errorObj.get("message").getAsString() : "Error al obtener dashboard";
                throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
            }

            return gson.fromJson(responseBody, JsonObject.class);
        } catch (IOException e) {
            throw new ApiException("Error de conexión con el servicio de pacientes: " + e.getMessage(), e);
        }
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
        if (token == null || token.isEmpty()) {
            throw new ApiException("Token de acceso no proporcionado");
        }

        String url = gatewayUrl + "/patient/alerts?limit=" + limit + "&offset=0";
        
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer " + token)
                .get()
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorCode = errorObj.has("error") ? errorObj.get("error").getAsString() : "unknown_error";
                String errorMessage = errorObj.has("message") ? errorObj.get("message").getAsString() : "Error al obtener alertas";
                throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
            }

            return gson.fromJson(responseBody, JsonObject.class);
        } catch (IOException e) {
            throw new ApiException("Error de conexión con el servicio de pacientes: " + e.getMessage(), e);
        }
    }

    /**
     * Obtiene todos los dispositivos del paciente
     * 
     * @param token Token de acceso del paciente
     * @return JsonObject con los dispositivos del paciente
     * @throws ApiException si hay error en la petición
     */
    public JsonObject getPatientDevices(String token) throws ApiException {
        if (token == null || token.isEmpty()) {
            throw new ApiException("Token de acceso no proporcionado");
        }

        String url = gatewayUrl + "/patient/devices";
        
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer " + token)
                .get()
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorCode = errorObj.has("error") ? errorObj.get("error").getAsString() : "unknown_error";
                String errorMessage = errorObj.has("message") ? errorObj.get("message").getAsString() : "Error al obtener dispositivos";
                throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
            }

            return gson.fromJson(responseBody, JsonObject.class);
        } catch (IOException e) {
            throw new ApiException("Error de conexión con el servicio de pacientes: " + e.getMessage(), e);
        }
    }

    /**
     * Obtiene la última ubicación del paciente
     */
    public JsonObject getPatientLatestLocation(String token) throws ApiException {
        if (token == null || token.isEmpty()) {
            throw new ApiException("Token de acceso no proporcionado");
        }

        String url = gatewayUrl + "/patient/location/latest";
        
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer " + token)
                .get()
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorCode = errorObj.has("error") ? errorObj.get("error").getAsString() : "unknown_error";
                String errorMessage = errorObj.has("message") ? errorObj.get("message").getAsString() : "Error al obtener ubicación";
                throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
            }

            return gson.fromJson(responseBody, JsonObject.class);
        } catch (IOException e) {
            throw new ApiException("Error de conexión con el servicio de pacientes: " + e.getMessage(), e);
        }
    }
    
    /**
     * Obtiene las últimas N ubicaciones del paciente
     */
    public JsonObject getPatientLocations(String token, int limit) throws ApiException {
        if (token == null || token.isEmpty()) {
            throw new ApiException("Token de acceso no proporcionado");
        }

        String url = gatewayUrl + "/patient/locations?limit=" + limit + "&offset=0";
        
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer " + token)
                .get()
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            if (!response.isSuccessful()) {
                JsonObject errorObj = gson.fromJson(responseBody, JsonObject.class);
                String errorCode = errorObj.has("error") ? errorObj.get("error").getAsString() : "unknown_error";
                String errorMessage = errorObj.has("message") ? errorObj.get("message").getAsString() : "Error al obtener ubicaciones";
                throw new ApiException(errorMessage, response.code(), errorCode, responseBody);
            }

            return gson.fromJson(responseBody, JsonObject.class);
        } catch (IOException e) {
            throw new ApiException("Error de conexión con el servicio de pacientes: " + e.getMessage(), e);
        }
    }

    /**
     * Obtiene la URL del gateway configurada
     */
    public String getGatewayUrl() {
        return gatewayUrl;
    }
}
