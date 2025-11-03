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
 */
public class ApiClient {
    private static final String DEFAULT_GATEWAY_URL = "http://localhost:8000";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    
    private final String gatewayUrl;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private String accessToken;

    public ApiClient() {
        this(DEFAULT_GATEWAY_URL);
    }

    public ApiClient(String gatewayUrl) {
        this.gatewayUrl = gatewayUrl;
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

        String url = gatewayUrl + "/auth/login/user";
        return executeLogin(url, payload);
    }

    /**
     * Login para paciente
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
     */
    public LoginResponse registerUser(String email, String password, String firstName, 
                                     String lastName, String phoneNumber, 
                                     String organizationCode, String roleCode) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("email", email);
        payload.addProperty("password", password);
        payload.addProperty("name", firstName + " " + lastName); // Nombre completo

        String url = gatewayUrl + "/auth/register/user";
        return executeLogin(url, payload);
    }

    /**
     * Registro de paciente
     */
    public LoginResponse registerPatient(String email, String password, String firstName,
                                        String lastName, String phoneNumber,
                                        String dateOfBirth, String gender,
                                        String organizationCode) throws ApiException {
        JsonObject payload = new JsonObject();
        payload.addProperty("email", email);
        payload.addProperty("password", password);
        payload.addProperty("name", firstName + " " + lastName); // Nombre completo
        payload.addProperty("org_code", organizationCode); // Enviar como org_code
        payload.addProperty("birthdate", dateOfBirth); // birthdate en lugar de date_of_birth
        payload.addProperty("sex_code", gender); // sex_code en lugar de gender

        String url = gatewayUrl + "/auth/register/patient";
        return executeLogin(url, payload);
    }

    /**
     * Verifica el token de acceso actual
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
     * Obtiene la URL del gateway configurada
     */
    public String getGatewayUrl() {
        return gatewayUrl;
    }
}
