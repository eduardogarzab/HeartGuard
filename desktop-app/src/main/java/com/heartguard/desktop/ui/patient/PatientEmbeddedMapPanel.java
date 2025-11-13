package com.heartguard.desktop.ui.patient;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.teamdev.jxbrowser.browser.Browser;
import com.teamdev.jxbrowser.engine.Engine;
import com.teamdev.jxbrowser.engine.EngineOptions;
import com.teamdev.jxbrowser.engine.RenderingMode;
import com.teamdev.jxbrowser.view.swing.BrowserView;
import io.github.cdimascio.dotenv.Dotenv;

import javax.swing.*;
import java.awt.*;

/**
 * Panel que incrusta un mapa interactivo para mostrar ubicaciones de un paciente.
 * Muestra múltiples puntos de ubicación y diferencia visualmente la ubicación más reciente.
 */
public class PatientEmbeddedMapPanel extends JPanel {
    private static final Gson GSON = new Gson();
    
    private Engine engine;
    private Browser browser;
    private BrowserView view;
    
    private JsonArray currentLocations = new JsonArray();
    
    private boolean isInitialized = false;
    
    public PatientEmbeddedMapPanel() {
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
            // Intentar cargar la licencia desde múltiples ubicaciones
            String licenseKey = loadJxBrowserLicense();
            
            if (licenseKey == null || licenseKey.isEmpty()) {
                throw new IllegalStateException("JXBROWSER_LICENSE_KEY no encontrada. Revisa el archivo .env");
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
            
            // Mostrar mensaje de error detallado
            JPanel errorPanel = new JPanel();
            errorPanel.setLayout(new BoxLayout(errorPanel, BoxLayout.Y_AXIS));
            errorPanel.setBackground(Color.WHITE);
            
            JLabel errorIcon = new JLabel("⚠️", SwingConstants.CENTER);
            errorIcon.setFont(new Font("Segoe UI", Font.PLAIN, 48));
            errorIcon.setAlignmentX(Component.CENTER_ALIGNMENT);
            
            JLabel errorLabel = new JLabel("Error al cargar el mapa", SwingConstants.CENTER);
            errorLabel.setForeground(Color.RED);
            errorLabel.setFont(new Font("Segoe UI", Font.BOLD, 14));
            errorLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
            
            JLabel errorDetail = new JLabel(e.getMessage(), SwingConstants.CENTER);
            errorDetail.setForeground(new Color(100, 100, 100));
            errorDetail.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            errorDetail.setAlignmentX(Component.CENTER_ALIGNMENT);
            
            errorPanel.add(Box.createVerticalGlue());
            errorPanel.add(errorIcon);
            errorPanel.add(Box.createVerticalStrut(10));
            errorPanel.add(errorLabel);
            errorPanel.add(Box.createVerticalStrut(5));
            errorPanel.add(errorDetail);
            errorPanel.add(Box.createVerticalGlue());
            
            add(errorPanel, BorderLayout.CENTER);
            revalidate();
            repaint();
        }
    }
    
    /**
     * Carga la licencia de JxBrowser desde múltiples ubicaciones posibles
     */
    private String loadJxBrowserLicense() {
        // Lista de directorios donde buscar el archivo .env
        String[] searchPaths = {
            ".",                                    // Directorio actual
            "desktop-app",                          // Subdirectorio desktop-app
            System.getProperty("user.dir"),         // Directorio de trabajo
            System.getProperty("user.dir") + "/desktop-app",
            System.getProperty("user.home") + "/.heartguard"  // Home del usuario
        };
        
        
        for (String path : searchPaths) {
            try {
                Dotenv dotenv = Dotenv.configure()
                        .directory(path)
                        .ignoreIfMissing()
                        .load();
                
                String licenseKey = dotenv.get("JXBROWSER_LICENSE_KEY");
                if (licenseKey != null && !licenseKey.isEmpty()) {
                    return licenseKey;
                }
            } catch (Exception e) {
                // Continuar con la siguiente ubicación
            }
        }
        
        System.err.println("[MAPA PACIENTE] ✗ No se encontró JXBROWSER_LICENSE_KEY en ninguna ubicación");
        System.err.println("[MAPA PACIENTE] Directorio actual: " + System.getProperty("user.dir"));
        
        return null;
    }
    
    private void loadInitialMap() {
        String html = generateMapHtml(new JsonArray());
        
        // Esperar a que la página cargue completamente antes de marcar como inicializado
        browser.navigation().on(com.teamdev.jxbrowser.navigation.event.FrameLoadFinished.class, event -> {
            isInitialized = true;
            
            // Si hay datos pendientes de actualizar, actualizarlos ahora
            if (currentLocations.size() > 0) {
                updateLocations(currentLocations);
            }
        });
        
        browser.navigation().loadUrl("data:text/html;charset=utf-8," + encodeHtml(html));
    }
    
    /**
     * Actualiza las ubicaciones en el mapa
     */
    public void updateLocations(JsonArray locations) {
        this.currentLocations = locations != null ? locations : new JsonArray();
        
        // Inicializar JxBrowser si aún no se ha hecho
        ensureInitialized();
        
        if (!isInitialized || browser == null) {
            return;
        }
        
        SwingUtilities.invokeLater(() -> {
            String locationsJson = GSON.toJson(currentLocations);
            
            
            // Ejecutar JavaScript para actualizar el mapa
            String script = String.format(
                "if (typeof updateMapData === 'function') { updateMapData(%s); } else { console.error('[MAPA PACIENTE JS] updateMapData function not found!'); }",
                locationsJson
            );
            
            try {
                browser.mainFrame().ifPresent(frame -> {
                    frame.executeJavaScript(script);
                });
            } catch (Exception e) {
                System.err.println("[MAPA PACIENTE] Error actualizando mapa: " + e.getMessage());
                e.printStackTrace();
                // Si falla, recargar completamente el mapa
                String html = generateMapHtml(currentLocations);
                browser.navigation().loadUrl("data:text/html;charset=utf-8," + encodeHtml(html));
            }
        });
    }
    
    /**
     * Reinicia el mapa a su estado inicial
     */
    public void reset() {
        currentLocations = new JsonArray();
        
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
    
    private String generateMapHtml(JsonArray locations) {
        String locationsJson = GSON.toJson(locations);
        
        StringBuilder html = new StringBuilder();
        html.append("<!DOCTYPE html>\n");
        html.append("<html lang=\"es\">\n");
        html.append("<head>\n");
        html.append("    <meta charset=\"UTF-8\">\n");
        html.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n");
        html.append("    <title>Mapa de Ubicaciones - Paciente</title>\n");
        html.append("    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css\">\n");
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
        html.append("        .legend {\n");
        html.append("            position: absolute;\n");
        html.append("            bottom: 30px;\n");
        html.append("            right: 10px;\n");
        html.append("            background: rgba(255, 255, 255, 0.95);\n");
        html.append("            padding: 10px 14px;\n");
        html.append("            border-radius: 6px;\n");
        html.append("            box-shadow: 0 2px 6px rgba(0,0,0,0.1);\n");
        html.append("            z-index: 1000;\n");
        html.append("            font-size: 12px;\n");
        html.append("        }\n");
        html.append("        .legend-item {\n");
        html.append("            display: flex;\n");
        html.append("            align-items: center;\n");
        html.append("            margin: 4px 0;\n");
        html.append("        }\n");
        html.append("        .legend-icon {\n");
        html.append("            width: 16px;\n");
        html.append("            height: 16px;\n");
        html.append("            border-radius: 50%;\n");
        html.append("            margin-right: 8px;\n");
        html.append("            border: 2px solid white;\n");
        html.append("            box-shadow: 0 1px 3px rgba(0,0,0,0.3);\n");
        html.append("        }\n");
        html.append("        .legend-icon.recent {\n");
        html.append("            background: #ef4444;\n");
        html.append("            width: 20px;\n");
        html.append("            height: 20px;\n");
        html.append("        }\n");
        html.append("        .legend-icon.historical {\n");
        html.append("            background: #3b82f6;\n");
        html.append("        }\n");
        html.append("    </style>\n");
        html.append("</head>\n");
        html.append("<body>\n");
        html.append("    <div id=\"map\"></div>\n");
        html.append("    <div class=\"info-badge\">\n");
        html.append("        <strong>📍 Ubicaciones del Paciente</strong>\n");
        html.append("        <div>Total: <span id=\"location-count\">0</span></div>\n");
        html.append("    </div>\n");
        html.append("    <div class=\"legend\">\n");
        html.append("        <div class=\"legend-item\">\n");
        html.append("            <div class=\"legend-icon recent\"></div>\n");
        html.append("            <span>Más reciente</span>\n");
        html.append("        </div>\n");
        html.append("        <div class=\"legend-item\">\n");
        html.append("            <div class=\"legend-icon historical\"></div>\n");
        html.append("            <span>Históricas</span>\n");
        html.append("        </div>\n");
        html.append("    </div>\n");
        html.append("    \n");
        html.append("    <script src=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js\"></script>\n");
        html.append("    <script>\n");
        html.append("        let map;\n");
        html.append("        let markers = [];\n");
        html.append("        let polyline = null;\n");
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
        html.append("        }\n");
        html.append("        \n");
        html.append("        function formatDate(dateStr) {\n");
        html.append("            if (!dateStr) return 'Desconocido';\n");
        html.append("            try {\n");
        html.append("                const date = new Date(dateStr);\n");
        html.append("                return date.toLocaleString('es-MX', {\n");
        html.append("                    year: 'numeric',\n");
        html.append("                    month: 'short',\n");
        html.append("                    day: 'numeric',\n");
        html.append("                    hour: '2-digit',\n");
        html.append("                    minute: '2-digit'\n");
        html.append("                });\n");
        html.append("            } catch (e) {\n");
        html.append("                return dateStr;\n");
        html.append("            }\n");
        html.append("        }\n");
        html.append("        \n");
        html.append("        function updateMapData(locations) {\n");
        html.append("            console.log('[MAPA PACIENTE JS] updateMapData called');\n");
        html.append("            console.log('[MAPA PACIENTE JS] Locations:', locations);\n");
        html.append("            \n");
        html.append("            if (!map) {\n");
        html.append("                console.error('[MAPA PACIENTE JS] Map not initialized!');\n");
        html.append("                return;\n");
        html.append("            }\n");
        html.append("            \n");
        html.append("            // Limpiar marcadores previos\n");
        html.append("            markers.forEach(m => map.removeLayer(m));\n");
        html.append("            markers = [];\n");
        html.append("            \n");
        html.append("            // Limpiar polyline previa\n");
        html.append("            if (polyline) {\n");
        html.append("                map.removeLayer(polyline);\n");
        html.append("                polyline = null;\n");
        html.append("            }\n");
        html.append("            \n");
        html.append("            const bounds = [];\n");
        html.append("            const pathCoords = [];\n");
        html.append("            \n");
        html.append("            locations.forEach((loc, index) => {\n");
        html.append("                console.log('[MAPA PACIENTE JS] Processing location', index, ':', loc);\n");
        html.append("                \n");
        html.append("                const lat = loc.latitude;\n");
        html.append("                const lng = loc.longitude;\n");
        html.append("                \n");
        html.append("                if (lat === null || lat === undefined || lng === null || lng === undefined) {\n");
        html.append("                    console.warn('[MAPA PACIENTE JS] Skipping location - no coords');\n");
        html.append("                    return;\n");
        html.append("                }\n");
        html.append("                \n");
        html.append("                // El primer elemento es el más reciente\n");
        html.append("                const isRecent = index === 0;\n");
        html.append("                const color = isRecent ? '#ef4444' : '#3b82f6';\n");
        html.append("                const size = isRecent ? 32 : 20;\n");
        html.append("                const zIndex = isRecent ? 1000 : 100;\n");
        html.append("                \n");
        html.append("                const marker = L.marker([lat, lng], {\n");
        html.append("                    icon: L.divIcon({\n");
        html.append("                        html: `<div style=\"border-radius:50%;width:${size}px;height:${size}px;border:3px solid white;background:${color};box-shadow:0 2px 6px rgba(0,0,0,0.4);\"></div>`,\n");
        html.append("                        className: '',\n");
        html.append("                        iconSize: [size + 4, size + 4]\n");
        html.append("                    }),\n");
        html.append("                    zIndexOffset: zIndex\n");
        html.append("                });\n");
        html.append("                \n");
        html.append("                const timestamp = formatDate(loc.timestamp || loc.ts);\n");
        html.append("                const accuracy = loc.accuracy || loc.accuracy_m;\n");
        html.append("                const accuracyText = accuracy ? `${accuracy.toFixed(1)} m` : 'N/A';\n");
        html.append("                \n");
        html.append("                const locationLabel = isRecent \n");
        html.append("                    ? '<strong style=\"color:#ef4444;\">🔴 Ubicación Más Reciente</strong>' \n");
        html.append("                    : `<strong style=\"color:#3b82f6;\">📍 Ubicación Histórica #${locations.length - index}</strong>`;\n");
        html.append("                \n");
        html.append("                marker.bindPopup(`\n");
        html.append("                    <div style=\"min-width:220px;\">\n");
        html.append("                        ${locationLabel}<br>\n");
        html.append("                        <strong>Fecha:</strong> ${timestamp}<br>\n");
        html.append("                        <strong>Precisión:</strong> ${accuracyText}<br>\n");
        html.append("                        <strong>Coordenadas:</strong> ${lat.toFixed(5)}, ${lng.toFixed(5)}\n");
        html.append("                    </div>\n");
        html.append("                `);\n");
        html.append("                \n");
        html.append("                marker.addTo(map);\n");
        html.append("                markers.push(marker);\n");
        html.append("                bounds.push([lat, lng]);\n");
        html.append("                pathCoords.push([lat, lng]);\n");
        html.append("            });\n");
        html.append("            \n");
        html.append("            // Dibujar línea conectando las ubicaciones (de la más antigua a la más reciente)\n");
        html.append("            if (pathCoords.length > 1) {\n");
        html.append("                const reversedPath = [...pathCoords].reverse();\n");
        html.append("                polyline = L.polyline(reversedPath, {\n");
        html.append("                    color: '#6b7280',\n");
        html.append("                    weight: 2,\n");
        html.append("                    opacity: 0.6,\n");
        html.append("                    dashArray: '5, 10'\n");
        html.append("                }).addTo(map);\n");
        html.append("            }\n");
        html.append("            \n");
        html.append("            document.getElementById('location-count').textContent = locations.length;\n");
        html.append("            \n");
        html.append("            if (bounds.length > 0) {\n");
        html.append("                if (bounds.length === 1) {\n");
        html.append("                    // Si solo hay una ubicación, centrar en ella\n");
        html.append("                    map.setView(bounds[0], 14);\n");
        html.append("                } else {\n");
        html.append("                    // Si hay múltiples ubicaciones, ajustar para mostrar todas\n");
        html.append("                    map.fitBounds(bounds, { \n");
        html.append("                        padding: [50, 50], \n");
        html.append("                        maxZoom: 15,\n");
        html.append("                        animate: true,\n");
        html.append("                        duration: 0.5\n");
        html.append("                    });\n");
        html.append("                }\n");
        html.append("            }\n");
        html.append("        }\n");
        html.append("        \n");
        html.append("        initMap();\n");
        html.append("        \n");
        html.append("        const initialLocations = ").append(locationsJson).append(";\n");
        html.append("        updateMapData(initialLocations);\n");
        html.append("    </script>\n");
        html.append("</body>\n");
        html.append("</html>\n");
        
        return html.toString();
    }
}
