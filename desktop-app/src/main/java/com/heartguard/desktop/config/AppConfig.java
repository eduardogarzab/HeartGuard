package com.heartguard.desktop.config;

import io.github.cdimascio.dotenv.Dotenv;

/**
 * Clase centralizada para manejar la configuración de la aplicación.
 * Lee valores desde archivo .env o variables de entorno del sistema.
 * 
 * NO incluye valores hardcodeados - todo viene de .env
 * 
 * ARQUITECTURA: El desktop app se comunica SOLO con el gateway.
 * El gateway se encarga de enrutar a los microservicios (auth, user, patient, media, realtime, etc.)
 * NO se conecta directamente a InfluxDB - usa el endpoint /realtime/patients/{id}/vital-signs
 */
public class AppConfig {
    private static AppConfig instance;
    private final Dotenv dotenv;
    
    // Gateway Configuration
    private final String gatewayBaseUrl;
    
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
        
        // Log de configuración
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
     * Log de configuración cargada
     */
    private void logConfig() {
        System.out.println("=".repeat(60));
        System.out.println("HeartGuard Desktop App - Configuration Loaded");
        System.out.println("=".repeat(60));
        System.out.println("Gateway URL: " + gatewayBaseUrl);
        System.out.println("Note: All data queries go through Gateway");
        System.out.println("=".repeat(60));
    }
    
    // Getters
    
    public String getGatewayBaseUrl() {
        return gatewayBaseUrl;
    }
}

