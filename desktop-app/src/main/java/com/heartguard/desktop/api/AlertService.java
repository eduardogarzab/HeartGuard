package com.heartguard.desktop.api;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.heartguard.desktop.models.alert.*;
import okhttp3.*;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.IOException;
import java.io.StringReader;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Servicio para gestionar alertas desde el backend
 * Todas las peticiones pasan por el Gateway API
 */
public class AlertService {
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    
    private final String gatewayUrl;
    private final OkHttpClient httpClient;
    private final Gson gson;
    private String accessToken;
    
    public AlertService(String gatewayUrl) {
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
     * Obtiene todas las alertas de una organización
     * GET /admin/organizations/{org_id}/alerts
     */
    public List<Alert> getOrganizationAlerts(String orgId) throws ApiException {
        return getOrganizationAlerts(orgId, null, null);
    }
    
    /**
     * Obtiene alertas de una organización con filtros opcionales
     * GET /admin/organizations/{org_id}/alerts?status=created,notified&level=high,critical
     */
    public List<Alert> getOrganizationAlerts(String orgId, List<AlertStatus> statuses, List<AlertLevel> levels) throws ApiException {
        StringBuilder urlBuilder = new StringBuilder(gatewayUrl);
        urlBuilder.append("/admin/organizations/").append(orgId).append("/alerts");
        
        List<String> queryParams = new ArrayList<>();
        if (statuses != null && !statuses.isEmpty()) {
            StringBuilder statusCodes = new StringBuilder();
            for (int i = 0; i < statuses.size(); i++) {
                if (i > 0) statusCodes.append(",");
                statusCodes.append(statuses.get(i).getCode());
            }
            queryParams.add("status=" + statusCodes.toString());
        }
        if (levels != null && !levels.isEmpty()) {
            StringBuilder levelCodes = new StringBuilder();
            for (int i = 0; i < levels.size(); i++) {
                if (i > 0) levelCodes.append(",");
                levelCodes.append(levels.get(i).getCode());
            }
            queryParams.add("level=" + levelCodes.toString());
        }
        
        if (!queryParams.isEmpty()) {
            urlBuilder.append("?");
            for (int i = 0; i < queryParams.size(); i++) {
                if (i > 0) urlBuilder.append("&");
                urlBuilder.append(queryParams.get(i));
            }
        }
        
        String finalUrl = urlBuilder.toString();
        System.out.println("[AlertService] 🌐 GET " + finalUrl);
        System.out.println("[AlertService] 🔑 org_id = " + orgId);
        
        Request request = new Request.Builder()
                .url(finalUrl)
                .header("Authorization", "Bearer " + accessToken)
                .get()
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            System.out.println("[AlertService] 📡 Response Code: " + response.code());
            System.out.println("[AlertService] 📄 Response Body: " + responseBody.substring(0, Math.min(500, responseBody.length())));
            
            if (!response.isSuccessful()) {
                System.err.println("[AlertService] ❌ Error HTTP " + response.code());
                throw new ApiException("Error al obtener alertas: " + response.code() + " - " + responseBody);
            }
            
            // El backend devuelve XML, no JSON
            List<Alert> alerts = parseXmlAlertList(responseBody);
            
            System.out.println("[AlertService] 📊 Alertas parseadas: " + alerts.size());
            
            return alerts;
        } catch (IOException e) {
            System.err.println("[AlertService] 🔥 IOException: " + e.getMessage());
            throw new ApiException("Error de conexión al obtener alertas: " + e.getMessage(), e);
        }
    }
    
    /**
     * Obtiene alertas de un paciente específico
     * GET /patient/{patient_id}/alerts
     */
    public List<Alert> getPatientAlerts(String patientId) throws ApiException {
        return getPatientAlerts(patientId, null, null);
    }
    
    /**
     * Obtiene alertas de un paciente con filtros
     */
    public List<Alert> getPatientAlerts(String patientId, List<AlertStatus> statuses, List<AlertLevel> levels) throws ApiException {
        StringBuilder urlBuilder = new StringBuilder(gatewayUrl);
        urlBuilder.append("/patient/").append(patientId).append("/alerts");
        
        List<String> queryParams = new ArrayList<>();
        if (statuses != null && !statuses.isEmpty()) {
            StringBuilder statusCodes = new StringBuilder();
            for (int i = 0; i < statuses.size(); i++) {
                if (i > 0) statusCodes.append(",");
                statusCodes.append(statuses.get(i).getCode());
            }
            queryParams.add("status=" + statusCodes.toString());
        }
        if (levels != null && !levels.isEmpty()) {
            StringBuilder levelCodes = new StringBuilder();
            for (int i = 0; i < levels.size(); i++) {
                if (i > 0) levelCodes.append(",");
                levelCodes.append(levels.get(i).getCode());
            }
            queryParams.add("level=" + levelCodes.toString());
        }
        
        if (!queryParams.isEmpty()) {
            urlBuilder.append("?");
            for (int i = 0; i < queryParams.size(); i++) {
                if (i > 0) urlBuilder.append("&");
                urlBuilder.append(queryParams.get(i));
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
                throw new ApiException("Error al obtener alertas del paciente: " + response.code() + " - " + responseBody);
            }
            
            JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
            JsonArray alertsArray = jsonResponse.has("alerts") ? jsonResponse.getAsJsonArray("alerts") : new JsonArray();
            
            return parseAlertList(alertsArray);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al obtener alertas del paciente: " + e.getMessage(), e);
        }
    }
    
    /**
     * Reconoce una alerta (marca como acknowledged)
     * PUT /alerts/{alert_id}/acknowledge
     */
    public Alert acknowledgeAlert(String alertId, String userId) throws ApiException {
        String url = gatewayUrl + "/alerts/" + alertId + "/acknowledge";
        
        JsonObject payload = new JsonObject();
        payload.addProperty("user_id", userId);
        
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + accessToken)
                .put(body)
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al reconocer alerta: " + response.code() + " - " + responseBody);
            }
            
            JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
            JsonObject alertObject = jsonResponse.has("alert") ? jsonResponse.getAsJsonObject("alert") : jsonResponse;
            
            return parseAlert(alertObject);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al reconocer alerta: " + e.getMessage(), e);
        }
    }
    
    /**
     * Resuelve una alerta
     * PUT /alerts/{alert_id}/resolve
     */
    public Alert resolveAlert(String alertId, String userId, String notes) throws ApiException {
        String url = gatewayUrl + "/alerts/" + alertId + "/resolve";
        
        JsonObject payload = new JsonObject();
        payload.addProperty("user_id", userId);
        if (notes != null && !notes.isEmpty()) {
            payload.addProperty("notes", notes);
        }
        
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + accessToken)
                .put(body)
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al resolver alerta: " + response.code() + " - " + responseBody);
            }
            
            JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
            JsonObject alertObject = jsonResponse.has("alert") ? jsonResponse.getAsJsonObject("alert") : jsonResponse;
            
            return parseAlert(alertObject);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al resolver alerta: " + e.getMessage(), e);
        }
    }
    
    /**
     * Cierra una alerta
     * PUT /alerts/{alert_id}/close
     */
    public Alert closeAlert(String alertId, String userId) throws ApiException {
        String url = gatewayUrl + "/alerts/" + alertId + "/close";
        
        JsonObject payload = new JsonObject();
        payload.addProperty("user_id", userId);
        
        RequestBody body = RequestBody.create(gson.toJson(payload), JSON);
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + accessToken)
                .put(body)
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al cerrar alerta: " + response.code() + " - " + responseBody);
            }
            
            JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
            JsonObject alertObject = jsonResponse.has("alert") ? jsonResponse.getAsJsonObject("alert") : jsonResponse;
            
            return parseAlert(alertObject);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al cerrar alerta: " + e.getMessage(), e);
        }
    }
    
    /**
     * Obtiene detalles de una alerta específica
     * GET /alerts/{alert_id}
     */
    public Alert getAlert(String alertId) throws ApiException {
        String url = gatewayUrl + "/alerts/" + alertId;
        
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + accessToken)
                .get()
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";
            
            if (!response.isSuccessful()) {
                throw new ApiException("Error al obtener alerta: " + response.code() + " - " + responseBody);
            }
            
            JsonObject jsonResponse = gson.fromJson(responseBody, JsonObject.class);
            JsonObject alertObject = jsonResponse.has("alert") ? jsonResponse.getAsJsonObject("alert") : jsonResponse;
            
            return parseAlert(alertObject);
        } catch (IOException e) {
            throw new ApiException("Error de conexión al obtener alerta: " + e.getMessage(), e);
        }
    }
    
    /**
     * Parsea un JsonArray de alertas a una lista de objetos Alert
     */
    private List<Alert> parseAlertList(JsonArray alertsArray) {
        List<Alert> alerts = new ArrayList<>();
        for (JsonElement element : alertsArray) {
            JsonObject alertObject = element.getAsJsonObject();
            alerts.add(parseAlert(alertObject));
        }
        return alerts;
    }
    
    /**
     * Parsea un JsonObject a un objeto Alert
     */
    private Alert parseAlert(JsonObject json) {
        Alert.Builder builder = Alert.builder();
        
        if (json.has("id") && !json.get("id").isJsonNull()) {
            builder.id(json.get("id").getAsString());
        }
        if (json.has("patient_id") && !json.get("patient_id").isJsonNull()) {
            builder.patientId(json.get("patient_id").getAsString());
        }
        if (json.has("patient_name") && !json.get("patient_name").isJsonNull()) {
            builder.patientName(json.get("patient_name").getAsString());
        }
        if (json.has("type") && !json.get("type").isJsonNull()) {
            String typeCode = json.get("type").getAsString();
            builder.type(AlertType.fromCode(typeCode));
        }
        if (json.has("alert_level") && !json.get("alert_level").isJsonNull()) {
            String levelCode = json.get("alert_level").getAsString();
            builder.alertLevel(AlertLevel.fromCode(levelCode));
        }
        if (json.has("status") && !json.get("status").isJsonNull()) {
            String statusCode = json.get("status").getAsString();
            builder.status(AlertStatus.fromCode(statusCode));
        }
        if (json.has("description") && !json.get("description").isJsonNull()) {
            builder.description(json.get("description").getAsString());
        }
        if (json.has("created_at") && !json.get("created_at").isJsonNull()) {
            builder.createdAt(Instant.parse(json.get("created_at").getAsString()));
        }
        if (json.has("acknowledged_at") && !json.get("acknowledged_at").isJsonNull()) {
            builder.acknowledgedAt(Instant.parse(json.get("acknowledged_at").getAsString()));
        }
        if (json.has("resolved_at") && !json.get("resolved_at").isJsonNull()) {
            builder.resolvedAt(Instant.parse(json.get("resolved_at").getAsString()));
        }
        if (json.has("created_by_model_id") && !json.get("created_by_model_id").isJsonNull()) {
            builder.createdByModelId(json.get("created_by_model_id").getAsString());
        }
        if (json.has("source_inference_id") && !json.get("source_inference_id").isJsonNull()) {
            builder.sourceInferenceId(json.get("source_inference_id").getAsString());
        }
        if (json.has("latitude") && !json.get("latitude").isJsonNull()) {
            builder.latitude(json.get("latitude").getAsDouble());
        }
        if (json.has("longitude") && !json.get("longitude").isJsonNull()) {
            builder.longitude(json.get("longitude").getAsDouble());
        }
        if (json.has("acknowledged_by_user_id") && !json.get("acknowledged_by_user_id").isJsonNull()) {
            builder.acknowledgedByUserId(json.get("acknowledged_by_user_id").getAsString());
        }
        if (json.has("resolved_by_user_id") && !json.get("resolved_by_user_id").isJsonNull()) {
            builder.resolvedByUserId(json.get("resolved_by_user_id").getAsString());
        }
        
        return builder.build();
    }
    
    /**
     * Parsea una respuesta XML del backend con la lista de alertas
     * Formato: <response><alerts><alert>...</alert><alert>...</alert></alerts></response>
     */
    private List<Alert> parseXmlAlertList(String xmlResponse) throws ApiException {
        List<Alert> alerts = new ArrayList<>();
        
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(new InputSource(new StringReader(xmlResponse)));
            doc.getDocumentElement().normalize();
            
            NodeList alertNodes = doc.getElementsByTagName("alert");
            System.out.println("[AlertService] 📋 Encontrados " + alertNodes.getLength() + " nodos <alert> en XML");
            
            for (int i = 0; i < alertNodes.getLength(); i++) {
                Node alertNode = alertNodes.item(i);
                if (alertNode.getNodeType() == Node.ELEMENT_NODE) {
                    Element alertElement = (Element) alertNode;
                    Alert alert = parseXmlAlert(alertElement);
                    if (alert != null) {
                        alerts.add(alert);
                    }
                }
            }
            
        } catch (Exception e) {
            System.err.println("[AlertService] ❌ Error parseando XML: " + e.getMessage());
            e.printStackTrace();
            throw new ApiException("Error parseando respuesta XML: " + e.getMessage(), e);
        }
        
        return alerts;
    }
    
    /**
     * Parsea un elemento XML <alert> a un objeto Alert
     */
    private Alert parseXmlAlert(Element alertElement) {
        try {
            Alert.Builder alertBuilder = Alert.builder();
            
            String id = getXmlTextContent(alertElement, "id");
            if (id != null) alertBuilder.id(id);
            
            String patientId = getXmlTextContent(alertElement, "patient_id");
            if (patientId != null) alertBuilder.patientId(patientId);
            
            String patientName = getXmlTextContent(alertElement, "patient_name");
            if (patientName != null) alertBuilder.patientName(patientName);
            
            String typeCode = getXmlTextContent(alertElement, "type_code");
            if (typeCode != null) {
                AlertType type = AlertType.fromCode(typeCode);
                if (type != null) alertBuilder.type(type);
            }
            
            String levelCode = getXmlTextContent(alertElement, "level_code");
            if (levelCode != null) {
                AlertLevel level = AlertLevel.fromCode(levelCode);
                if (level != null) alertBuilder.alertLevel(level);
            }
            
            String statusCode = getXmlTextContent(alertElement, "status_code");
            if (statusCode != null) {
                AlertStatus status = AlertStatus.fromCode(statusCode);
                if (status != null) alertBuilder.status(status);
            }
            
            String description = getXmlTextContent(alertElement, "description");
            if (description != null) alertBuilder.description(description);
            
            String createdAt = getXmlTextContent(alertElement, "created_at");
            if (createdAt != null) {
                try {
                    // Parsear timestamp de PostgreSQL: "2025-11-24 04:53:32.553801"
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSSSSS");
                    LocalDateTime ldt = LocalDateTime.parse(createdAt, formatter);
                    Instant instant = ldt.atZone(ZoneId.systemDefault()).toInstant();
                    alertBuilder.createdAt(instant);
                } catch (Exception e) {
                    System.err.println("[AlertService] ⚠️ Error parseando created_at: " + createdAt);
                }
            }
            
            return alertBuilder.build();
            
        } catch (Exception e) {
            System.err.println("[AlertService] ⚠️ Error parseando alerta individual: " + e.getMessage());
            return null;
        }
    }
    
    /**
     * Obtiene el contenido de texto de un elemento XML hijo
     */
    private String getXmlTextContent(Element parent, String tagName) {
        NodeList nodeList = parent.getElementsByTagName(tagName);
        if (nodeList.getLength() > 0) {
            Node node = nodeList.item(0);
            if (node != null) {
                String content = node.getTextContent();
                return (content != null && !content.trim().isEmpty()) ? content.trim() : null;
            }
        }
        return null;
    }
}
