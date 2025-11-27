package com.heartguard.desktop.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.heartguard.desktop.config.AppConfig;
import com.heartguard.desktop.models.AIPrediction;
import com.heartguard.desktop.models.AIAlert;
import okhttp3.*;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Cliente para el servicio de predicción de IA
 * Consume endpoints del servicio ai-prediction a través del Gateway
 */
public class AIService {
    private static final Logger LOGGER = Logger.getLogger(AIService.class.getName());
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    
    private final String gatewayUrl;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private String accessToken;
    
    // Singleton
    private static AIService instance;
    
    private AIService() {
        this.gatewayUrl = AppConfig.getInstance().getGatewayBaseUrl();
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .writeTimeout(10, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .build();
        this.gson = new GsonBuilder()
                .setDateFormat("yyyy-MM-dd'T'HH:mm:ss")
                .create();
    }
    
    public static synchronized AIService getInstance() {
        if (instance == null) {
            instance = new AIService();
        }
        return instance;
    }
    
    /**
     * Establece el token de acceso para autenticación
     */
    public void setAccessToken(String accessToken) {
        this.accessToken = accessToken;
    }
    
    /**
     * Realiza una predicción de salud basada en signos vitales
     * 
     * @param gpsLongitude Longitud GPS
     * @param gpsLatitude Latitud GPS
     * @param heartRate Frecuencia cardíaca (bpm)
     * @param spo2 Saturación de oxígeno (%)
     * @param systolicBp Presión arterial sistólica (mmHg)
     * @param diastolicBp Presión arterial diastólica (mmHg)
     * @param temperature Temperatura corporal (°C)
     * @return Predicción de IA con probabilidad y alertas
     * @throws AIServiceException Si hay error en la predicción
     */
    public AIPrediction predictHealth(
            double gpsLongitude,
            double gpsLatitude,
            double heartRate,
            double spo2,
            double systolicBp,
            double diastolicBp,
            double temperature
    ) throws AIServiceException {
        return predictHealth(gpsLongitude, gpsLatitude, heartRate, spo2, 
                           systolicBp, diastolicBp, temperature, 0.6);
    }
    
    /**
     * Realiza una predicción de salud con threshold personalizado
     * 
     * @param threshold Umbral de probabilidad (0.0 - 1.0)
     */
    public AIPrediction predictHealth(
            double gpsLongitude,
            double gpsLatitude,
            double heartRate,
            double spo2,
            double systolicBp,
            double diastolicBp,
            double temperature,
            double threshold
    ) throws AIServiceException {
        // Construir payload JSON
        JsonObject payload = new JsonObject();
        payload.addProperty("gps_longitude", gpsLongitude);
        payload.addProperty("gps_latitude", gpsLatitude);
        payload.addProperty("heart_rate", heartRate);
        payload.addProperty("spo2", spo2);
        payload.addProperty("systolic_bp", systolicBp);
        payload.addProperty("diastolic_bp", diastolicBp);
        payload.addProperty("temperature", temperature);
        payload.addProperty("threshold", threshold);
        
        String url = gatewayUrl + "/ai/predict";
        
        LOGGER.log(Level.INFO, "Llamando al servicio de IA: {0}", url);
        LOGGER.log(Level.FINE, "Payload: {0}", payload.toString());
        
        try {
            RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
            Request.Builder requestBuilder = new Request.Builder()
                    .url(url)
                    .post(body);
            
            // Agregar token de autenticación si existe
            if (accessToken != null && !accessToken.isEmpty()) {
                requestBuilder.header("Authorization", "Bearer " + accessToken);
            }
            
            Request request = requestBuilder.build();
            
            try (Response response = httpClient.newCall(request).execute()) {
                String responseBody = response.body() != null ? response.body().string() : "";
                
                if (!response.isSuccessful()) {
                    LOGGER.log(Level.WARNING, 
                              "Error en predicción: Status {0}, Body: {1}", 
                              new Object[]{response.code(), responseBody});
                    throw new AIServiceException(
                        "Error en predicción: " + response.code() + " - " + responseBody
                    );
                }
                
                // Parsear respuesta
                JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
                
                boolean hasProblem = jsonResponse.get("has_problem").getAsBoolean();
                double probability = jsonResponse.get("probability").getAsDouble();
                String processedAt = jsonResponse.get("processed_at").getAsString();
                
                // Parsear alertas
                List<AIAlert> alerts = new ArrayList<>();
                JsonArray alertsArray = jsonResponse.getAsJsonArray("alerts");
                if (alertsArray != null) {
                    for (JsonElement alertElement : alertsArray) {
                        JsonObject alertObj = alertElement.getAsJsonObject();
                        
                        String type = alertObj.get("type").getAsString();
                        String severity = alertObj.get("severity").getAsString();
                        String message = alertObj.get("message").getAsString();
                        
                        // Campos opcionales
                        Double value = alertObj.has("value") ? 
                                      alertObj.get("value").getAsDouble() : null;
                        String unit = alertObj.has("unit") ? 
                                     alertObj.get("unit").getAsString() : null;
                        Double alertProbability = alertObj.has("probability") ? 
                                                  alertObj.get("probability").getAsDouble() : null;
                        
                        AIAlert alert = new AIAlert(type, severity, message, 
                                                    value, unit, alertProbability);
                        alerts.add(alert);
                    }
                }
                
                AIPrediction prediction = new AIPrediction(
                    hasProblem, probability, alerts, processedAt
                );
                
                LOGGER.log(Level.INFO, 
                          "Predicción exitosa: hasProblem={0}, probability={1}, alerts={2}", 
                          new Object[]{hasProblem, probability, alerts.size()});
                
                return prediction;
                
            }
        } catch (IOException e) {
            LOGGER.log(Level.SEVERE, "Error de I/O en llamada al servicio de IA", e);
            throw new AIServiceException("Error de conexión con el servicio de IA: " + e.getMessage(), e);
        }
    }
    
    /**
     * Verifica el estado del servicio de IA
     * 
     * @return true si el servicio está operativo
     */
    public boolean isHealthy() {
        String url = gatewayUrl + "/ai/health";
        
        try {
            Request request = new Request.Builder()
                    .url(url)
                    .get()
                    .build();
            
            try (Response response = httpClient.newCall(request).execute()) {
                if (response.isSuccessful()) {
                    String responseBody = response.body() != null ? response.body().string() : "";
                    JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
                    String status = jsonResponse.get("status").getAsString();
                    return "healthy".equals(status);
                }
                return false;
            }
        } catch (IOException e) {
            LOGGER.log(Level.WARNING, "Error verificando health del servicio de IA", e);
            return false;
        }
    }
    
    /**
     * Obtiene información del modelo de IA
     * 
     * @return JsonObject con información del modelo
     */
    public JsonObject getModelInfo() throws AIServiceException {
        String url = gatewayUrl + "/ai/model/info";
        
        try {
            Request request = new Request.Builder()
                    .url(url)
                    .get()
                    .build();
            
            try (Response response = httpClient.newCall(request).execute()) {
                String responseBody = response.body() != null ? response.body().string() : "";
                
                if (!response.isSuccessful()) {
                    throw new AIServiceException("Error obteniendo info del modelo: " + response.code());
                }
                
                return gson.fromJson(responseBody, JsonObject.class);
            }
        } catch (IOException e) {
            throw new AIServiceException("Error de I/O obteniendo info del modelo", e);
        }
    }
    
    /**
     * Excepción personalizada para errores del servicio de IA
     */
    public static class AIServiceException extends Exception {
        public AIServiceException(String message) {
            super(message);
        }
        
        public AIServiceException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
