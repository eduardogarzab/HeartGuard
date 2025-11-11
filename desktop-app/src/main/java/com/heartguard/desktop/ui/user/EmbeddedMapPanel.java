package com.heartguard.desktop.ui.user;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.teamdev.jxbrowser.browser.Browser;
import com.teamdev.jxbrowser.engine.Engine;
import com.teamdev.jxbrowser.engine.EngineOptions;
import com.teamdev.jxbrowser.engine.RenderingMode;
import com.teamdev.jxbrowser.view.swing.BrowserView;
import io.github.cdimascio.dotenv.Dotenv;

import javax.swing.*;
import java.awt.*;

/**
 * Panel que incrusta un mapa interactivo usando JxBrowser (Chromium).
 * Aprovecha el motor de Chromium completo para renderizar Leaflet con excelente rendimiento.
 * Usa lazy initialization para no bloquear el arranque de la aplicación.
 */
public class EmbeddedMapPanel extends JPanel {
    private static final Gson GSON = new Gson();
    
    private Engine engine;
    private Browser browser;
    private BrowserView view;
    
    private JsonArray currentPatients = new JsonArray();
    
    private boolean isInitialized = false;
    
    public EmbeddedMapPanel() {
        setLayout(new BorderLayout());
        setBackground(Color.WHITE);
        
        // Mostrar mensaje de carga mientras se inicializa
        JLabel loadingLabel = new JLabel("Cargando mapa...", SwingConstants.CENTER);
        loadingLabel.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        loadingLabel.setForeground(new Color(120, 130, 140));
        add(loadingLabel, BorderLayout.CENTER);
        
        // NO inicializar JxBrowser aquí, solo cuando sea necesario
    }
    
    /**
     * Inicializa JxBrowser de forma lazy (solo cuando se necesita)
     */
    private void ensureInitialized() {
        if (isInitialized) {
            return;
        }
        
        // Eliminar el mensaje de carga
        removeAll();
        
        try {
            // Cargar variables de entorno desde .env
            Dotenv dotenv = Dotenv.configure()
                    .directory(".")
                    .ignoreIfMissing()
                    .load();
            
            String licenseKey = dotenv.get("JXBROWSER_LICENSE_KEY");
            if (licenseKey == null || licenseKey.isEmpty()) {
                throw new IllegalStateException("JXBROWSER_LICENSE_KEY no encontrada en .env");
            }
            
            // Crear engine de JxBrowser con configuración optimizada y licencia
            EngineOptions options = EngineOptions.newBuilder(RenderingMode.HARDWARE_ACCELERATED)
                    .licenseKey(licenseKey)
                    .build();
            
            engine = Engine.newInstance(options);
            browser = engine.newBrowser();
            
            // Crear vista Swing del browser
            view = BrowserView.newInstance(browser);
            add(view, BorderLayout.CENTER);
            
            // Cargar mapa inicial
            loadInitialMap();
            
            isInitialized = true;
            
            revalidate();
            repaint();
        } catch (Exception e) {
            System.err.println("Error inicializando JxBrowser: " + e.getMessage());
            e.printStackTrace();
            
            // Mostrar mensaje de error
            JLabel errorLabel = new JLabel("Error al cargar el mapa", SwingConstants.CENTER);
            errorLabel.setForeground(Color.RED);
            add(errorLabel, BorderLayout.CENTER);
            revalidate();
            repaint();
        }
    }
    
    private void loadInitialMap() {
        String html = generateMapHtml(new JsonArray());
        
        // Esperar a que la página cargue completamente antes de marcar como inicializado
        browser.navigation().on(com.teamdev.jxbrowser.navigation.event.FrameLoadFinished.class, event -> {
            System.out.println("[MAPA JAVA] Página cargada completamente");
            isInitialized = true;
            
            // Si hay datos pendientes de actualizar, actualizarlos ahora
            if (currentPatients.size() > 0) {
                System.out.println("[MAPA JAVA] Actualizando datos pendientes...");
                updateLocations(currentPatients);
            }
        });
        
        browser.navigation().loadUrl("data:text/html;charset=utf-8," + encodeHtml(html));
    }
    
    /**
     * Actualiza el mapa con nuevos datos de pacientes
     */
    public void updateLocations(JsonArray patients) {
        this.currentPatients = patients != null ? patients : new JsonArray();
        
        System.out.println("[MAPA] Actualizando ubicaciones:");
        System.out.println("  - Pacientes: " + currentPatients.size());
        
        // Inicializar JxBrowser si aún no se ha hecho
        ensureInitialized();
        
        if (!isInitialized || browser == null) {
            System.out.println("[MAPA JAVA] Mapa no inicializado todavía, esperando...");
            return;
        }
        
        SwingUtilities.invokeLater(() -> {
            String patientsJson = GSON.toJson(currentPatients);
            
            System.out.println("[MAPA JAVA] patientsJson: " + patientsJson);
            
            // Ejecutar JavaScript para actualizar el mapa
            String script = String.format(
                "if (typeof updateMapData === 'function') { updateMapData(%s); } else { console.error('[MAPA JS] updateMapData function not found!'); }",
                patientsJson
            );
            
            try {
                System.out.println("[MAPA JAVA] Ejecutando script JavaScript...");
                browser.mainFrame().ifPresent(frame -> {
                    System.out.println("[MAPA JAVA] Frame presente, ejecutando...");
                    frame.executeJavaScript(script);
                });
                System.out.println("[MAPA JAVA] Script ejecutado correctamente");
            } catch (Exception e) {
                System.err.println("[MAPA JAVA] Error actualizando mapa: " + e.getMessage());
                e.printStackTrace();
                // Si falla, recargar completamente el mapa
                System.out.println("[MAPA JAVA] Recargando HTML completo del mapa...");
                String html = generateMapHtml(currentPatients);
                browser.navigation().loadUrl("data:text/html;charset=utf-8," + encodeHtml(html));
            }
        });
    }
    
    /**
     * Reinicia el mapa a su estado inicial
     */
    public void reset() {
        currentPatients = new JsonArray();
        
        if (isInitialized && browser != null) {
            loadInitialMap();
        }
    }
    
    /**
     * Limpia recursos al cerrar
     */
    public void dispose() {
        if (browser != null) {
            try {
                browser.close();
            } catch (Exception e) {
                System.err.println("Error cerrando browser: " + e.getMessage());
            }
        }
        if (engine != null) {
            try {
                engine.close();
            } catch (Exception e) {
                System.err.println("Error cerrando engine: " + e.getMessage());
            }
        }
    }
    
    private String encodeHtml(String html) {
        try {
            return java.net.URLEncoder.encode(html, "UTF-8")
                    .replace("+", "%20");
        } catch (Exception e) {
            return html;
        }
    }
    
    private String generateMapHtml(JsonArray patients) {
        String patientsJson = GSON.toJson(patients);
        
        StringBuilder html = new StringBuilder();
        html.append("<!DOCTYPE html>\n");
        html.append("<html lang=\"es\">\n");
        html.append("<head>\n");
        html.append("    <meta charset=\"UTF-8\">\n");
        html.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n");
        html.append("    <title>Mapa - HeartGuard</title>\n");
        html.append("    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css\">\n");
        html.append("    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.css\">\n");
        html.append("    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css\">\n");
        html.append("    <style>\n");
        html.append("        * { margin: 0; padding: 0; box-sizing: border-box; }\n");
        html.append("        html, body { \n");
        html.append("            height: 100%; \n");
        html.append("            overflow: hidden; \n");
        html.append("            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\n");
        html.append("        }\n");
        html.append("        #map { \n");
        html.append("            height: 100%; \n");
        html.append("            width: 100%;\n");
        html.append("        }\n");
        html.append("        .leaflet-popup-content {\n");
        html.append("            margin: 12px;\n");
        html.append("            line-height: 1.6;\n");
        html.append("        }\n");
        html.append("        .leaflet-popup-content strong {\n");
        html.append("            color: #2563eb;\n");
        html.append("        }\n");
        html.append("        .info-badge {\n");
        html.append("            position: absolute;\n");
        html.append("            top: 10px;\n");
        html.append("            right: 10px;\n");
        html.append("            background: rgba(255, 255, 255, 0.95);\n");
        html.append("            padding: 12px 16px;\n");
        html.append("            border-radius: 8px;\n");
        html.append("            box-shadow: 0 2px 8px rgba(0,0,0,0.15);\n");
        html.append("            z-index: 1000;\n");
        html.append("            font-size: 13px;\n");
        html.append("            line-height: 1.6;\n");
        html.append("        }\n");
        html.append("        .info-badge strong {\n");
        html.append("            color: #1e40af;\n");
        html.append("            display: block;\n");
        html.append("            margin-bottom: 4px;\n");
        html.append("        }\n");
        html.append("    </style>\n");
        html.append("</head>\n");
        html.append("<body>\n");
        html.append("    <div id=\"map\"></div>\n");
        html.append("    <div class=\"info-badge\">\n");
        html.append("        <strong>📍 Ubicaciones</strong>\n");
        html.append("        <div>Pacientes: <span id=\"patient-count\">0</span></div>\n");
        html.append("    </div>\n");
        html.append("    \n");
        html.append("    <script src=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js\"></script>\n");
        html.append("    <script src=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js\"></script>\n");
        html.append("    <script>\n");
        html.append("        let map;\n");
        html.append("        let patientCluster;\n");
        html.append("        \n");
        html.append("        // Inicializar mapa\n");
        html.append("        function initMap() {\n");
        html.append("            map = L.map('map', {\n");
        html.append("                zoomControl: true,\n");
        html.append("                attributionControl: true\n");
        html.append("            }).setView([25.6866, -100.3161], 10);\n");
        html.append("            \n");
        html.append("            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {\n");
        html.append("                attribution: '© OpenStreetMap contributors',\n");
        html.append("                maxZoom: 18\n");
        html.append("            }).addTo(map);\n");
        html.append("            \n");
        html.append("            patientCluster = L.markerClusterGroup({\n");
        html.append("                iconCreateFunction: function(cluster) {\n");
        html.append("                    const count = cluster.getChildCount();\n");
        html.append("                    return L.divIcon({\n");
        html.append("                        html: '<div style=\"background:#ef4444;color:white;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:14px;box-shadow:0 2px 6px rgba(0,0,0,0.2);\">' + count + '</div>',\n");
        html.append("                        className: '',\n");
        html.append("                        iconSize: L.point(40, 40)\n");
        html.append("                    });\n");
        html.append("                }\n");
        html.append("            });\n");
        html.append("            \n");
        html.append("            map.addLayer(patientCluster);\n");
        html.append("        }\n");
        html.append("        \n");
        html.append("        const riskColors = {\n");
        html.append("            low: '#22c55e',\n");
        html.append("            medium: '#f59e0b',\n");
        html.append("            high: '#ef4444'\n");
        html.append("        };\n");
        html.append("        \n");
        html.append("        function getRiskColor(risk) {\n");
        html.append("            if (!risk) return '#3b82f6';\n");
        html.append("            const code = (risk.code || '').toLowerCase();\n");
        html.append("            if (code.includes('high') || code.includes('alto')) return riskColors.high;\n");
        html.append("            if (code.includes('medium') || code.includes('moder')) return riskColors.medium;\n");
        html.append("            return riskColors.low;\n");
        html.append("        }\n");
        html.append("        \n");
        html.append("        function updateMapData(patients) {\n");
        html.append("            console.log('[MAPA JS] updateMapData called');\n");
        html.append("            console.log('[MAPA JS] Patients:', patients);\n");
        html.append("            \n");
        html.append("            if (!map) {\n");
        html.append("                console.error('[MAPA JS] Map not initialized!');\n");
        html.append("                return;\n");
        html.append("            }\n");
        html.append("            \n");
        html.append("            patientCluster.clearLayers();\n");
        html.append("            \n");
        html.append("            const bounds = [];\n");
        html.append("            \n");
        html.append("            patients.forEach((p, index) => {\n");
        html.append("                console.log('[MAPA JS] Processing patient', index, ':', p);\n");
        html.append("                \n");
        html.append("                // Soportar dos formatos: p.latitude o p.location.latitude\n");
        html.append("                const lat = p.latitude !== undefined ? p.latitude : (p.location ? p.location.latitude : null);\n");
        html.append("                const lng = p.longitude !== undefined ? p.longitude : (p.location ? p.location.longitude : null);\n");
        html.append("                \n");
        html.append("                console.log('[MAPA JS] Patient coords:', lat, lng);\n");
        html.append("                \n");
        html.append("                if (lat === null || lng === null) {\n");
        html.append("                    console.warn('[MAPA JS] Skipping patient - no coords');\n");
        html.append("                    return;\n");
        html.append("                }\n");
        html.append("                \n");
        html.append("                const color = getRiskColor(p.risk_level);\n");
        html.append("                \n");
        html.append("                const marker = L.marker([lat, lng], {\n");
        html.append("                    icon: L.divIcon({\n");
        html.append("                        html: `<div style=\"border-radius:50%;width:24px;height:24px;border:3px solid white;background:${color};box-shadow:0 2px 6px rgba(0,0,0,0.3);\"></div>`,\n");
        html.append("                        className: '',\n");
        html.append("                        iconSize: [28, 28]\n");
        html.append("                    })\n");
        html.append("                });\n");
        html.append("                \n");
        html.append("                const lastAlert = p.last_alert || p.alert;\n");
        html.append("                const alertInfo = lastAlert\n");
        html.append("                    ? `<br><strong>⚠️ Alerta:</strong> ${lastAlert.label || 'Alerta activa'}` \n");
        html.append("                    : '';\n");
        html.append("                \n");
        html.append("                marker.bindPopup(`\n");
        html.append("                    <div style=\"min-width:200px;\">\n");
        html.append("                        <strong style=\"font-size:15px;color:#1e40af;\">👤 ${p.name || 'Paciente'}</strong><br>\n");
        html.append("                        <strong>Email:</strong> ${p.email || 'N/A'}<br>\n");
        html.append("                        <strong>Equipo:</strong> ${p.care_team_name || p.care_team?.name || 'N/A'}<br>\n");
        html.append("                        <strong>Riesgo:</strong> <span style=\"color:${color}\">●</span> ${p.risk_level?.label || 'N/A'}\n");
        html.append("                        ${alertInfo}\n");
        html.append("                    </div>\n");
        html.append("                `);\n");
        html.append("                \n");
        html.append("                patientCluster.addLayer(marker);\n");
        html.append("                bounds.push([lat, lng]);\n");
        html.append("            });\n");
        html.append("            \n");
        html.append("            document.getElementById('patient-count').textContent = patients.length;\n");
        html.append("            \n");
        html.append("            if (bounds.length > 0) {\n");
        html.append("                map.fitBounds(bounds, { \n");
        html.append("                    padding: [50, 50], \n");
        html.append("                    maxZoom: 14,\n");
        html.append("                    animate: true,\n");
        html.append("                    duration: 0.5\n");
        html.append("                });\n");
        html.append("            }\n");
        html.append("        }\n");
        html.append("        \n");
        html.append("        initMap();\n");
        html.append("        \n");
        html.append("        const initialPatients = ").append(patientsJson).append(";\n");
        html.append("        updateMapData(initialPatients);\n");
        html.append("    </script>\n");
        html.append("</body>\n");
        html.append("</html>\n");
        
        return html.toString();
    }
}
