package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.heartguard.desktop.util.JsonUtils;
import javafx.application.Platform;
import javafx.embed.swing.JFXPanel;
import javafx.scene.Scene;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;
import netscape.javascript.JSObject;

import javax.swing.*;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;
import java.awt.event.HierarchyEvent;

/**
 * Panel que encapsula un mapa Leaflet con clustering para ubicaciones.
 * Altura máxima 320px, borde gris claro #dfe3e6, redimensionable con WebView en ScrollPane.
 */
public class UserMapPanel extends JPanel {
    private static final Color BORDER_MAP = new Color(223, 227, 230);
    
    private final JFXPanel fxPanel;
    private WebEngine webEngine;
    private boolean mapReady = false;
    private boolean mapInitialized = false;
    private JsonArray pendingPatients;
    private JsonArray pendingMembers;

    public UserMapPanel() {
        setLayout(new BorderLayout());
        setBackground(Color.WHITE);
        setBorder(new LineBorder(BORDER_MAP, 1));
        
        fxPanel = new JFXPanel();
        fxPanel.setPreferredSize(new Dimension(800, 360));
        fxPanel.setMinimumSize(new Dimension(320, 240));
        add(fxPanel, BorderLayout.CENTER);

        addHierarchyListener(e -> {
            if ((e.getChangeFlags() & HierarchyEvent.SHOWING_CHANGED) != 0 && isShowing()) {
                // Intentar inicializar el mapa cuando se muestra por primera vez
                if (!mapInitialized) {
                    initializeMap();
                }
                requestResize();
            }
        });

        addComponentListener(new ComponentAdapter() {
            @Override
            public void componentShown(ComponentEvent e) {
                // Intentar inicializar el mapa cuando se muestra por primera vez
                if (!mapInitialized) {
                    initializeMap();
                }
                requestResize();
            }

            @Override
            public void componentResized(ComponentEvent e) {
                requestResize();
            }
        });

        // Inicializar el mapa después de que el componente esté añadido
        SwingUtilities.invokeLater(this::initializeMap);
    }

    private void initializeMap() {
        if (mapInitialized) {
            System.out.println("[UserMapPanel] Mapa ya inicializado, omitiendo...");
            return;
        }
        mapInitialized = true;
        System.out.println("[UserMapPanel] Iniciando inicialización del mapa...");
        
        // Asegurar que Platform.runLater se ejecute incluso si el toolkit no está inicializado
        try {
            Platform.runLater(() -> {
                try {
                    initializeMapOnFxThread();
                } catch (Exception e) {
                    System.err.println("[UserMapPanel] Error al inicializar mapa en FX Thread: " + e.getMessage());
                    e.printStackTrace();
                    // Si falla, marcar como no inicializado para reintentar
                    mapInitialized = false;
                }
            });
        } catch (Exception e) {
            System.err.println("[UserMapPanel] Error al programar inicialización: " + e.getMessage());
            e.printStackTrace();
            mapInitialized = false;
        }
    }

    public void reset() {
        mapReady = false;
        pendingPatients = null;
        pendingMembers = null;
        if (webEngine != null) {
            Platform.runLater(() -> {
                try {
                    JSObject window = getWindowObject();
                    if (window != null) {
                        window.call("clearEntities");
                    }
                } catch (Exception ignored) {
                }
            });
        }
    }

    private void initializeMapOnFxThread() {
        try {
            WebView webView = new WebView();
            webView.setContextMenuEnabled(false); // Desactivar menú contextual
            
            webEngine = webView.getEngine();
            webEngine.setJavaScriptEnabled(true);
            webEngine.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
            
            // Listener para detectar errores de carga
            webEngine.getLoadWorker().exceptionProperty().addListener((obs, oldEx, newEx) -> {
                if (newEx != null) {
                    System.err.println("[UserMapPanel] Error al cargar el contenido del mapa: " + newEx.getMessage());
                }
            });
            
            webEngine.loadContent(buildHtml());
            webEngine.getLoadWorker().stateProperty().addListener((obs, oldState, newState) -> {
                switch (newState) {
                    case SUCCEEDED -> {
                        System.out.println("[UserMapPanel] Mapa cargado exitosamente");
                        // Esperar a que el DOM esté completamente listo
                        Platform.runLater(() -> {
                            try {
                                // Verificar que Leaflet esté cargado
                                Object leafletCheck = webEngine.executeScript("typeof L !== 'undefined'");
                                if (Boolean.TRUE.equals(leafletCheck)) {
                                    mapReady = true;
                                    System.out.println("[UserMapPanel] Leaflet verificado y listo");
                                    if (pendingPatients != null || pendingMembers != null) {
                                        updateLocations(pendingPatients, pendingMembers);
                                    }
                                    // Forzar redimensión inicial
                                    SwingUtilities.invokeLater(() -> {
                                        requestResize();
                                    });
                                } else {
                                    System.err.println("[UserMapPanel] Leaflet no está disponible");
                                }
                            } catch (Exception e) {
                                System.err.println("[UserMapPanel] Error verificando Leaflet: " + e.getMessage());
                            }
                        });
                    }
                    case FAILED -> {
                        mapReady = false;
                        System.err.println("[UserMapPanel] Falló la carga del mapa");
                    }
                    case CANCELLED -> {
                        System.err.println("[UserMapPanel] Carga del mapa cancelada");
                    }
                }
            });
            
            Scene scene = new Scene(webView);
            fxPanel.setScene(scene);
            
        } catch (Exception e) {
            System.err.println("[UserMapPanel] Error en initializeMapOnFxThread: " + e.getMessage());
            e.printStackTrace();
            mapInitialized = false;
        }
    }

    public void updateLocations(JsonArray patients, JsonArray members) {
        pendingPatients = patients;
        pendingMembers = members;
        if (!mapReady || webEngine == null) {
            return;
        }
        Platform.runLater(() -> {
            String patientsJson = patients != null ? JsonUtils.GSON.toJson(patients) : "[]";
            String membersJson = members != null ? JsonUtils.GSON.toJson(members) : "[]";
            try {
                JSObject window = getWindowObject();
                if (window != null) {
                    window.call("updateEntitiesFromJava", patientsJson, membersJson);
                }
            } catch (Exception ignored) {
            }
        });
    }

    public void clear() {
        pendingPatients = null;
        pendingMembers = null;
        if (mapReady && webEngine != null) {
            Platform.runLater(() -> {
                try {
                    JSObject window = getWindowObject();
                    if (window != null) {
                        window.call("clearEntities");
                    }
                } catch (Exception ignored) {
                }
            });
        }
    }

    private JSObject getWindowObject() {
        try {
            return (JSObject) webEngine.executeScript("window");
        } catch (Exception ex) {
            return null;
        }
    }

    private void requestResize() {
        if (!mapReady || webEngine == null) {
            return;
        }
        Platform.runLater(() -> {
            try {
                webEngine.executeScript("if(window.resizeMap){ window.resizeMap(); }");
            } catch (Exception ignored) {
            }
        });
    }

    private String buildHtml() {
        return """
                <!DOCTYPE html>
                <html lang=\"es\">
                <head>
                    <meta charset=\"UTF-8\" />
                    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, user-scalable=no\" />
                    <meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\" />
                    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css\" crossorigin=\"anonymous\" />
                    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.css\" />
                    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css\" />
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        html, body { 
                            height: 100%; 
                            width: 100%;
                            overflow: hidden;
                            background: #fff;
                        }
                        #map { 
                            width: 100%; 
                            height: 100%;
                            background: #e5e7eb;
                        }
                        .leaflet-container {
                            background: #e5e7eb;
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        }
                        .leaflet-tile-container {
                            opacity: 1;
                        }
                        .leaflet-tile {
                            opacity: 1 !important;
                            image-rendering: optimizeQuality;
                            transition: none !important;
                            will-change: transform;
                        }
                        .leaflet-tile-loaded {
                            opacity: 1 !important;
                            visibility: visible !important;
                        }
                        .leaflet-zoom-animated {
                            will-change: transform;
                        }
                        .marker-patient { border-radius: 50%; width: 18px; height: 18px; border: 2px solid #fff; box-shadow: 0 0 4px rgba(0,0,0,0.2); }
                        .marker-member { width: 20px; height: 20px; border-radius: 6px; border: 2px solid #fff; box-shadow: 0 0 4px rgba(0,0,0,0.2); }
                    </style>
                </head>
                <body>
                    <div id=\"map\"></div>
                    <script src=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js\" crossorigin=\"anonymous\"></script>
                    <script src=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js\"></script>
                    <script>
                        console.log('[MAP] Inicializando Leaflet...');
                        
                        const map = L.map('map', {
                            zoomAnimation: false,
                            fadeAnimation: false,
                            markerZoomAnimation: false,
                            zoomSnap: 1,
                            zoomDelta: 1,
                            trackResize: true,
                            minZoom: 2,
                            maxZoom: 15,
                            worldCopyJump: true,
                            preferCanvas: false,
                            inertia: false,
                            zoomControl: true
                        }).setView([20, -30], 3);

                        console.log('[MAP] Mapa creado');

                        let resizeTimeout = null;
                        const resizeMap = () => {
                            if (!map) return;
                            if (map._animatingZoom) {
                                if (resizeTimeout) clearTimeout(resizeTimeout);
                                resizeTimeout = setTimeout(resizeMap, 120);
                                return;
                            }
                            if (resizeTimeout) clearTimeout(resizeTimeout);
                            resizeTimeout = setTimeout(() => {
                                try {
                                    map.invalidateSize({
                                        animate: false,
                                        pan: false,
                                        debounceMoveend: true
                                    });
                                    console.log('[MAP] Redimensionado');
                                } catch (e) {
                                    console.error('[MAP] Error resize:', e);
                                }
                            }, 150);
                        };
                        window.resizeMap = resizeMap;
                        
                        const fitMapToBounds = () => {
                            if (!map) return;
                            try {
                                const allBounds = [];
                                currentPatients.forEach(p => {
                                    if (p.location && p.location.latitude !== null && p.location.longitude !== null) {
                                        allBounds.push([p.location.latitude, p.location.longitude]);
                                    }
                                });
                                currentMembers.forEach(m => {
                                    if (m.location && m.location.latitude !== null && m.location.longitude !== null) {
                                        allBounds.push([m.location.latitude, m.location.longitude]);
                                    }
                                });
                                
                                if (allBounds.length > 0) {
                                    map.fitBounds(allBounds, { 
                                        padding: [50, 50], 
                                        maxZoom: 12,
                                        animate: false 
                                    });
                                } else {
                                    map.setView([20, -30], 3, { animate: false });
                                }
                            } catch (e) {
                                console.error('[MAP] Error fitBounds:', e);
                            }
                        };

                        const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '© OpenStreetMap contributors',
                            maxZoom: 18,
                            maxNativeZoom: 17,
                            minZoom: 2,
                            tileSize: 256,
                            zoomOffset: 0,
                            keepBuffer: 6,
                            updateWhenIdle: false,
                            updateWhenZooming: true,
                            updateInterval: 90,
                            reuseTiles: true,
                            bounds: [[-90, -180], [90, 180]],
                            noWrap: false,
                            crossOrigin: 'anonymous',
                            errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAH+wJ1qvH0LwAAAABJRU5ErkJggg=='
                        });
                        
                        let tileLoadCount = 0;
                        let tileErrorCount = 0;
                        const tileRetry = new Map();
                        
                        tileLayer.on('loading', () => {
                            console.log('[MAP] Cargando tiles...');
                            tileLoadCount = 0;
                            tileErrorCount = 0;
                            tileRetry.clear();
                        });
                        
                        tileLayer.on('load', () => {
                            console.log('[MAP] Tiles cargados:', tileLoadCount, 'errores:', tileErrorCount);
                        });
                        
                        tileLayer.on('tileload', () => {
                            tileLoadCount++;
                        });
                        
                        tileLayer.on('tileerror', (e) => {
                            tileErrorCount++;
                            const url = (e.tile && e.tile.src) ? e.tile.src : '';
                            const count = tileRetry.get(url) || 0;
                            console.warn('[MAP] Tile error:', url, 'retry:', count);
                            if (count < 2) {
                                const delay = count === 0 ? 600 : 1600;
                                setTimeout(() => {
                                    try {
                                        if (e.tile) {
                                            const base = url.split('#')[0];
                                            const sep = base.includes('?') ? '&' : '?';
                                            const newUrl = base + sep + 'retry=' + (count + 1) + '&ts=' + Date.now();
                                            e.tile.src = newUrl;
                                            tileRetry.set(newUrl, count + 1);
                                        }
                                    } catch (ex) {
                                        console.error('[MAP] Error en retry de tile:', ex);
                                    }
                                }, delay);
                            } else {
                                console.warn('[MAP] Tile abandonado tras reintentos:', url);
                            }
                        });
                        
                        tileLayer.addTo(map);
                        console.log('[MAP] Tile layer añadido');
                        
                        let zoomDebounce = null;
                        map.on('zoomstart', () => {
                            if (zoomDebounce) clearTimeout(zoomDebounce);
                        });
                        
                        map.on('zoomend', () => {
                            if (zoomDebounce) clearTimeout(zoomDebounce);
                            zoomDebounce = setTimeout(() => {
                                console.log('[MAP] Zoom finalizado en nivel:', map.getZoom());
                            }, 120);
                        });
                        
                        map.on('moveend', () => {
                            console.log('[MAP] Movimiento finalizado');
                        });

                        const patientCluster = L.markerClusterGroup({
                            showCoverageOnHover: false,
                            spiderfyDistanceMultiplier: 1.4,
                            maxClusterRadius: 48,
                            animate: false,
                            chunkedLoading: true
                        });
                        const memberCluster = L.markerClusterGroup({
                            showCoverageOnHover: false,
                            maxClusterRadius: 50,
                            animate: false,
                            chunkedLoading: true,
                            iconCreateFunction: (cluster) => {
                                const count = cluster.getChildCount();
                                return L.divIcon({
                                    html: `<div style=\"background:#1e88e5;color:white;border-radius:18px;padding:6px 10px;font-weight:600;\">${count}</div>`,
                                    className: 'member-cluster-icon',
                                    iconSize: L.point(30, 30)
                                });
                            }
                        });

                        map.addLayer(patientCluster);
                        map.addLayer(memberCluster);

                        const riskColors = {
                            low: '#2ecc71',
                            medium: '#f1c40f',
                            high: '#e74c3c'
                        };

                        const getRiskColor = (risk) => {
                            if (!risk) return '#2c98f0';
                            const code = (risk.code || '').toLowerCase();
                            if (code.includes('high') || code.includes('alto')) return riskColors.high;
                            if (code.includes('medium') || code.includes('moder')) return riskColors.medium;
                            return riskColors.low;
                        };

                        let currentPatients = [];
                        let currentMembers = [];
                        let hasInitialBounds = false;

                        const renderPatients = () => {
                            try {
                                patientCluster.clearLayers();
                                currentPatients.forEach(p => {
                                    if (!p.location || p.location.latitude === null || p.location.longitude === null) {
                                        return;
                                    }
                                    const color = getRiskColor(p.risk_level);
                                    const el = document.createElement('div');
                                    el.className = 'marker-patient';
                                    el.style.background = color;
                                    const marker = L.marker([p.location.latitude, p.location.longitude], {
                                        icon: L.divIcon({
                                            html: el.outerHTML,
                                            className: '',
                                            iconSize: [20, 20]
                                        })
                                    });
                                    marker.on('click', () => {
                                        const alertSection = p.alert ? `<div style=\"margin-top:6px;font-size:12px;color:#e74c3c;\">⚠️ ${p.alert.label || 'Alerta'} · ${p.alert.level?.label || ''}</div>` : '';
                                        const html = `
                                            <div style=\"font-family:'Segoe UI',sans-serif;\">
                                                <div style=\"font-weight:600;color:#1b2733;font-size:14px;\">${p.name || 'Paciente'}</div>
                                                <div style=\"font-size:12px;color:#607489;margin-top:4px;\">${p.organization?.name || ''}</div>
                                                <div style=\"font-size:12px;color:#607489;margin-top:4px;\">Equipo: ${p.care_team?.name || '-'}</div>
                                                ${alertSection}
                                            </div>`;
                                        sidePanel.show(html);
                                    });
                                    patientCluster.addLayer(marker);
                                });
                                console.log('[MAP] Renderizados', currentPatients.length, 'pacientes');
                            } catch (e) {
                                console.error('[MAP] Error renderizando pacientes:', e);
                            }
                        };

                        const renderMembers = () => {
                            try {
                                memberCluster.clearLayers();
                                currentMembers.forEach(m => {
                                    if (!m.location) return;
                                    const marker = L.marker([m.location.latitude, m.location.longitude], {
                                        icon: L.divIcon({
                                            html: `<div class=\"marker-member\" style=\"background:#42a5f5\"></div>`,
                                            className: '',
                                            iconSize: [22, 22]
                                        })
                                    });
                                    marker.on('click', () => {
                                        const html = `
                                            <div style=\"font-family:'Segoe UI',sans-serif;\">
                                                <div style=\"font-weight:600;color:#1b2733;font-size:14px;\">${m.name || 'Miembro de equipo'}</div>
                                                <div style=\"font-size:12px;color:#607489;margin-top:4px;\">${m.organization?.name || ''}</div>
                                                <div style=\"font-size:12px;color:#607489;margin-top:4px;\">Rol: ${m.role?.label || m.role?.code || '-'}</div>
                                            </div>`;
                                        sidePanel.show(html);
                                    });
                                    memberCluster.addLayer(marker);
                                });
                                console.log('[MAP] Renderizados', currentMembers.length, 'miembros');
                            } catch (e) {
                                console.error('[MAP] Error renderizando miembros:', e);
                            }
                        };

                        const sidePanel = (() => {
                            const container = document.createElement('div');
                            container.style.position = 'absolute';
                            container.style.top = '16px';
                            container.style.right = '16px';
                            container.style.width = '260px';
                            container.style.maxWidth = '50%';
                            container.style.zIndex = '1000';
                            container.style.display = 'none';
                            container.style.boxShadow = '0 12px 32px rgba(15,23,42,0.18)';
                            container.style.borderRadius = '18px';
                            container.style.background = 'rgba(255,255,255,0.96)';
                            container.style.padding = '18px';
                            container.style.backdropFilter = 'blur(8px)';
                            container.innerHTML = '<div id="panel-content"></div>';
                            document.body.appendChild(container);
                            return {
                                show: (html) => {
                                    container.querySelector('#panel-content').innerHTML = html;
                                    container.style.display = 'block';
                                },
                                hide: () => {
                                    container.style.display = 'none';
                                }
                            };
                        })();

                        map.on('click', () => sidePanel.hide());

                        window.updateEntities = (patients, members) => {
                            try {
                                currentPatients = Array.isArray(patients) ? patients : [];
                                currentMembers = Array.isArray(members) ? members : [];
                                console.log('[MAP] updateEntities:', currentPatients.length, 'pacientes,', currentMembers.length, 'miembros');
                                renderPatients();
                                renderMembers();
                                if (!hasInitialBounds) {
                                    setTimeout(() => {
                                        fitMapToBounds();
                                        hasInitialBounds = true;
                                        setTimeout(resizeMap, 150);
                                    }, 80);
                                } else {
                                    setTimeout(resizeMap, 180);
                                }
                            } catch (e) {
                                console.error('[MAP] Error en updateEntities:', e);
                            }
                        };

                        window.updateEntitiesFromJava = (patientsJson, membersJson) => {
                            try {
                                const patients = JSON.parse(patientsJson || '[]');
                                const members = JSON.parse(membersJson || '[]');
                                window.updateEntities(patients, members);
                            } catch (err) {
                                console.error('[MAP] Error parseando:', err);
                            }
                        };

                        window.clearEntities = () => {
                            try {
                                currentPatients = [];
                                currentMembers = [];
                                patientCluster.clearLayers();
                                memberCluster.clearLayers();
                                sidePanel.hide();
                                hasInitialBounds = false;
                                console.log('[MAP] Entidades limpiadas');
                            } catch (e) {
                                console.error('[MAP] Error limpiando:', e);
                            }
                        };

                        window.forceRefreshTiles = () => {
                            if (!map || !tileLayer) return;
                            try {
                                tileLayer.redraw();
                                map.invalidateSize({ animate: false });
                                console.log('[MAP] Tiles refrescados manualmente');
                            } catch (e) {
                                console.error('[MAP] Error refrescando tiles:', e);
                            }
                        };

                        setTimeout(() => {
                            resizeMap();
                            console.log('[MAP] Inicialización completada');
                        }, 250);
                    </script>
                </body>
                </html>
                """;
    }
}
