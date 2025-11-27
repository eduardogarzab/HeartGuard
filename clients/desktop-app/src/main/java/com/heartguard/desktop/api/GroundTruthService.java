package com.heartguard.desktop.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.heartguard.desktop.models.alert.*;
import okhttp3.*;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Servicio para gestionar Ground Truth Labels (validación de alertas de IA)
 */
public class GroundTruthService {
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    
    private final String gatewayUrl;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private String accessToken;
    
    public GroundTruthService(String gatewayUrl) {
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
    
    public void setAccessToken(String accessToken) {
        this.accessToken = accessToken;
    }
    
    /**
     * Valida una alerta como verdadero positivo (True Positive)
     * POST /admin/organizations/{org_id}/patients/{patient_id}/ground-truth
     * 
     * Crea un registro de ground truth confirmando que el evento detectado por la IA fue real
     */
    public GroundTruthLabel validateAsTruePositive(
            String orgId,
            String alertId,
            String patientId,
            EventType eventType,
            Instant onset,
            Instant offsetAt,
            String annotatedByUserId,
            String note
    ) throws ApiException {
        String url = gatewayUrl + "/organizations/" + orgId + "/patients/" + patientId + "/ground-truth/";
        
        JsonObject payload = new JsonObject();
        payload.addProperty("alert_id", alertId);
        payload.addProperty("event_type_code", eventType.getCode());
        payload.addProperty("onset", onset.toString());
        if (offsetAt != null) {
            payload.addProperty("offset_at", offsetAt.toString());
        }
        payload.addProperty("annotated_by_user_id", annotatedByUserId);
        payload.addProperty("source", GroundTruthSource.AI_MODEL.getCode());
        if (note != null && !note.isEmpty()) {
            payload.addProperty("note", note);
        }
        
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + accessToken)
                .post(body)
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al validar como verdadero positivo: " + response.code() + " - " + responseBody);
            }
            
            JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
            JsonObject gtObject = jsonResponse.has("ground_truth_label") ? jsonResponse.getAsJsonObject("ground_truth_label") : jsonResponse;
            
            return parseGroundTruthLabel(gtObject);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al validar verdadero positivo: " + e.getMessage(), e);
        }
    }
    
    /**
     * Marca una alerta como falso positivo (False Positive)
     * POST /ground-truth/validate-false-positive
     * 
     * No crea registro de ground truth, solo marca la alerta con metadata
     */
    public void validateAsFalsePositive(
            String alertId,
            String userId,
            String reason
    ) throws ApiException {
        String url = gatewayUrl + "/ground-truth/validate-false-positive";
        
        JsonObject payload = new JsonObject();
        payload.addProperty("alert_id", alertId);
        payload.addProperty("validated_by_user_id", userId);
        if (reason != null && !reason.isEmpty()) {
            payload.addProperty("reason", reason);
        }
        
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + accessToken)
                .post(body)
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al marcar como falso positivo: " + response.code() + " - " + responseBody);
            }
        } catch (IOException e) {
            throw new ApiException("Error de conexión al marcar falso positivo: " + e.getMessage(), e);
        }
    }
    
    /**
     * Crea una etiqueta de ground truth manualmente (sin alerta asociada)
     * POST /ground-truth/create-manual
     * 
     * Para eventos detectados manualmente por el personal médico
     */
    public GroundTruthLabel createManualGroundTruth(
            String patientId,
            EventType eventType,
            Instant onset,
            Instant offsetAt,
            String annotatedByUserId,
            String note
    ) throws ApiException {
        String url = gatewayUrl + "/ground-truth/create-manual";
        
        JsonObject payload = new JsonObject();
        payload.addProperty("patient_id", patientId);
        payload.addProperty("event_type_code", eventType.getCode());
        payload.addProperty("onset", onset.toString());
        if (offsetAt != null) {
            payload.addProperty("offset_at", offsetAt.toString());
        }
        payload.addProperty("annotated_by_user_id", annotatedByUserId);
        payload.addProperty("source", GroundTruthSource.MANUAL.getCode());
        if (note != null && !note.isEmpty()) {
            payload.addProperty("note", note);
        }
        
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + accessToken)
                .post(body)
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al crear ground truth manual: " + response.code() + " - " + responseBody);
            }
            
            JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
            JsonObject gtObject = jsonResponse.has("ground_truth_label") ? jsonResponse.getAsJsonObject("ground_truth_label") : jsonResponse;
            
            return parseGroundTruthLabel(gtObject);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al crear ground truth manual: " + e.getMessage(), e);
        }
    }
    
    /**
     * Obtiene todas las etiquetas de ground truth de un paciente
     * GET /ground-truth/patient/{patient_id}
     */
    public List<GroundTruthLabel> getPatientGroundTruthLabels(String patientId) throws ApiException {
        String url = gatewayUrl + "/ground-truth/patient/" + patientId;
        
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + accessToken)
                .get()
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al obtener ground truth del paciente: " + response.code() + " - " + responseBody);
            }
            
            JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
            JsonArray labelsArray = jsonResponse.has("labels") ? jsonResponse.getAsJsonArray("labels") : new JsonArray();
            
            return parseGroundTruthList(labelsArray);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al obtener ground truth: " + e.getMessage(), e);
        }
    }
    
    /**
     * Obtiene estadísticas de precisión del modelo de IA
     * GET /ground-truth/stats?start_date=...&end_date=...
     */
    public JsonObject getModelAccuracyStats(Instant startDate, Instant endDate) throws ApiException {
        StringBuilder urlBuilder = new StringBuilder(gatewayUrl);
        urlBuilder.append("/ground-truth/stats");
        
        List<String> params = new ArrayList<>();
        if (startDate != null) {
            params.add("start_date=" + startDate.toString());
        }
        if (endDate != null) {
            params.add("end_date=" + endDate.toString());
        }
        
        if (!params.isEmpty()) {
            urlBuilder.append("?");
            for (int i = 0; i < params.size(); i++) {
                if (i > 0) urlBuilder.append("&");
                urlBuilder.append(params.get(i));
            }
        }
        
        Request request = new Request.Builder()
                .url(urlBuilder.toString())
                .header("Authorization", "Bearer " + accessToken)
                .get()
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al obtener estadísticas: " + response.code() + " - " + responseBody);
            }
            
            return gson.fromJson(responseBody, JsonObject.class);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al obtener estadísticas: " + e.getMessage(), e);
        }
    }
    
    /**
     * Parsea un JsonArray de ground truth labels a una lista
     */
    private List<GroundTruthLabel> parseGroundTruthList(JsonArray labelsArray) {
        List<GroundTruthLabel> labels = new ArrayList<>();
        for (JsonElement element : labelsArray) {
            JsonObject labelObject = element.getAsJsonObject();
            labels.add(parseGroundTruthLabel(labelObject));
        }
        return labels;
    }
    
    /**
     * Parsea un JsonObject a un objeto GroundTruthLabel
     */
    private GroundTruthLabel parseGroundTruthLabel(JsonObject json) {
        GroundTruthLabel.Builder builder = GroundTruthLabel.builder();
        
        if (json.has("id") && !json.get("id").isJsonNull()) {
            builder.id(json.get("id").getAsString());
        }
        if (json.has("patient_id") && !json.get("patient_id").isJsonNull()) {
            builder.patientId(json.get("patient_id").getAsString());
        }
        if (json.has("event_type_code") && !json.get("event_type_code").isJsonNull()) {
            String eventTypeCode = json.get("event_type_code").getAsString();
            builder.eventType(EventType.fromCode(eventTypeCode));
        } else if (json.has("event_type") && !json.get("event_type").isJsonNull()) {
            String eventTypeCode = json.get("event_type").getAsString();
            builder.eventType(EventType.fromCode(eventTypeCode));
        }
        if (json.has("onset") && !json.get("onset").isJsonNull()) {
            builder.onset(Instant.parse(json.get("onset").getAsString()));
        }
        if (json.has("offset_at") && !json.get("offset_at").isJsonNull()) {
            builder.offsetAt(Instant.parse(json.get("offset_at").getAsString()));
        }
        if (json.has("annotated_by_user_id") && !json.get("annotated_by_user_id").isJsonNull()) {
            builder.annotatedByUserId(json.get("annotated_by_user_id").getAsString());
        }
        if (json.has("annotated_by_user_name") && !json.get("annotated_by_user_name").isJsonNull()) {
            builder.annotatedByUserName(json.get("annotated_by_user_name").getAsString());
        }
        if (json.has("source") && !json.get("source").isJsonNull()) {
            String sourceCode = json.get("source").getAsString();
            builder.source(GroundTruthSource.fromCode(sourceCode));
        }
        if (json.has("note") && !json.get("note").isJsonNull()) {
            builder.note(json.get("note").getAsString());
        }
        if (json.has("created_at") && !json.get("created_at").isJsonNull()) {
            builder.createdAt(Instant.parse(json.get("created_at").getAsString()));
        }
        if (json.has("updated_at") && !json.get("updated_at").isJsonNull()) {
            builder.updatedAt(Instant.parse(json.get("updated_at").getAsString()));
        }
        
        return builder.build();
    }
}
