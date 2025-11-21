package com.heartguard.desktop.config;

import io.github.cdimascio.dotenv.Dotenv;

/**
 * Clase centralizada para manejar la configuración de la aplicación.
 * Lee valores desde archivo .env o variables de entorno del sistema.
 * 
 * NO incluye valores hardcodeados - todo viene de .env
 */
public class AppConfig {
    private static AppConfig instance;
    private final Dotenv dotenv;
    
    // Gateway Configuration
    private final String gatewayBaseUrl;
    
    // InfluxDB Configuration
    private final String influxdbUrl;
    private final String influxdbToken;
    private final String influxdbOrg;
    private final String influxdbBucket;
    
    private AppConfig() {
        // Intentar cargar el archivo .env desde el directorio actual
        // Si no existe, usar las variables de entorno del sistema
        Dotenv env = null;
        try {
            env = Dotenv.configure()
                    .ignoreIfMissing()
                    .load();
        } catch (Exception e) {
            System.err.println("Warning: Could not load .env file: " + e.getMessage());
            System.err.println("Using system environment variables only");
        }
        this.dotenv = env;
        
        // Cargar configuración del Gateway
        this.gatewayBaseUrl = getEnv("GATEWAY_BASE_URL", "http://localhost:8080");
        
        // Cargar configuración de InfluxDB
        this.influxdbUrl = getEnv("INFLUXDB_URL", null);
        this.influxdbToken = getEnv("INFLUXDB_TOKEN", null);
        this.influxdbOrg = getEnv("INFLUXDB_ORG", "heartguard");
        this.influxdbBucket = getEnv("INFLUXDB_BUCKET", "timeseries");
        
        // Validar configuración requerida
        validateConfig();
        
        // Log de configuración (sin exponer valores sensibles)
        logConfig();
    }
    
    /**
     * Obtener instancia singleton de la configuración
     */
    public static synchronized AppConfig getInstance() {
        if (instance == null) {
            instance = new AppConfig();
        }
        return instance;
    }
    
    /**
     * Obtener valor de variable de entorno, primero desde .env, luego desde sistema
     */
    private String getEnv(String key, String defaultValue) {
        String value = null;
        
        // Primero intentar desde archivo .env
        if (dotenv != null) {
            value = dotenv.get(key);
        }
        
        // Si no existe, intentar desde variables de entorno del sistema
        if (value == null || value.isEmpty()) {
            value = System.getenv(key);
        }
        
        // Si aún no existe, usar valor por defecto
        if (value == null || value.isEmpty()) {
            value = defaultValue;
        }
        
        return value;
    }
    
    /**
     * Validar que las configuraciones requeridas estén presentes
     */
    private void validateConfig() {
        if (influxdbUrl == null || influxdbUrl.isEmpty()) {
            throw new IllegalStateException(
                "INFLUXDB_URL is required. Please set it in .env file or environment variables."
            );
        }
        
        if (influxdbToken == null || influxdbToken.isEmpty()) {
            throw new IllegalStateException(
                "INFLUXDB_TOKEN is required. Please set it in .env file or environment variables."
            );
        }
    }
    
    /**
     * Log de configuración cargada (sin exponer datos sensibles)
     */
    private void logConfig() {
        System.out.println("=".repeat(60));
        System.out.println("HeartGuard Desktop App - Configuration Loaded");
        System.out.println("=".repeat(60));
        System.out.println("Gateway URL: " + gatewayBaseUrl);
        System.out.println("InfluxDB URL: " + influxdbUrl);
        System.out.println("InfluxDB Org: " + influxdbOrg);
        System.out.println("InfluxDB Bucket: " + influxdbBucket);
        System.out.println("InfluxDB Token: " + maskSensitiveData(influxdbToken));
        System.out.println("=".repeat(60));
    }
    
    /**
     * Enmascarar datos sensibles para logs
     */
    private String maskSensitiveData(String data) {
        if (data == null || data.isEmpty()) {
            return "[NOT SET]";
        }
        if (data.length() <= 8) {
            return "***";
        }
        return data.substring(0, 4) + "..." + data.substring(data.length() - 4);
    }
    
    // Getters
    
    public String getGatewayBaseUrl() {
        return gatewayBaseUrl;
    }
    
    public String getInfluxdbUrl() {
        return influxdbUrl;
    }
    
    public String getInfluxdbToken() {
        return influxdbToken;
    }
    
    public String getInfluxdbOrg() {
        return influxdbOrg;
    }
    
    public String getInfluxdbBucket() {
        return influxdbBucket;
    }
}
