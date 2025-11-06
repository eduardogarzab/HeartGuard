package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.heartguard.desktop.util.JsonUtils;
import javafx.application.Platform;
import javafx.embed.swing.JFXPanel;
import javafx.scene.Scene;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;

/**
 * Panel que encapsula un mapa Leaflet con clustering para ubicaciones de pacientes y equipos.
 */
public class UserMapPanel extends JPanel {
    private final JFXPanel fxPanel;
    private WebEngine webEngine;
    private boolean mapReady = false;
    private JsonArray pendingPatients;
    private JsonArray pendingMembers;

    public UserMapPanel() {
        setLayout(new BorderLayout());
        setBackground(Color.WHITE);
        fxPanel = new JFXPanel();
        add(fxPanel, BorderLayout.CENTER);

        addHierarchyListener(e -> {
            if (isShowing() && !mapReady) {
                initializeMap();
            }
        });

        addComponentListener(new ComponentAdapter() {
            @Override
            public void componentResized(ComponentEvent e) {
                if (mapReady) {
                    Platform.runLater(() -> {
                        if (webEngine != null) {
                            webEngine.executeScript("if(window.resizeMap){window.resizeMap();}");
                        }
                    });
                }
            }
        });
    }

    private void initializeMap() {
        Platform.runLater(() -> {
            WebView webView = new WebView();
            webEngine = webView.getEngine();
            webEngine.setJavaScriptEnabled(true);
            webEngine.loadContent(buildHtml());
            webEngine.getLoadWorker().stateProperty().addListener((obs, oldState, newState) -> {
                switch (newState) {
                    case SUCCEEDED -> {
                        mapReady = true;
                        if (pendingPatients != null || pendingMembers != null) {
                            updateLocations(pendingPatients, pendingMembers);
                        }
                    }
                }
            });
            fxPanel.setScene(new Scene(webView));
        });
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
            webEngine.executeScript(String.format("window.updateEntities(%s, %s);", patientsJson, membersJson));
        });
    }

    public void clear() {
        pendingPatients = null;
        pendingMembers = null;
        if (mapReady && webEngine != null) {
            Platform.runLater(() -> webEngine.executeScript("window.clearEntities();"));
        }
    }

    private String buildHtml() {
        return """
                <!DOCTYPE html>
                <html lang=\"es\">
                <head>
                    <meta charset=\"UTF-8\" />
                    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
                    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css\" />
                    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.css\" />
                    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css\" />
                    <style>
                        html, body { height: 100%; margin: 0; }
                        #map { width: 100%; height: 100%; }
                        .marker-patient { border-radius: 50%; width: 18px; height: 18px; border: 2px solid #fff; box-shadow: 0 0 4px rgba(0,0,0,0.2); }
                        .marker-member { width: 20px; height: 20px; border-radius: 6px; border: 2px solid #fff; box-shadow: 0 0 4px rgba(0,0,0,0.2); }
                    </style>
                </head>
                <body>
                    <div id=\"map\"></div>
                    <script src=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js\"></script>
                    <script src=\"https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js\"></script>
                    <script>
                        const map = L.map('map', {
                            zoomSnap: 0.25,
                            minZoom: 2,
                            maxZoom: 19,
                            worldCopyJump: true
                        }).setView([20, -30], 3);

                        const resizeMap = () => {
                            requestAnimationFrame(() => {
                                map.invalidateSize();
                                if (map.resize) {
                                    map.resize();
                                }
                            });
                        };
                        window.resizeMap = resizeMap;

                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '© OpenStreetMap contributors'
                        }).addTo(map);

                        const patientCluster = L.markerClusterGroup({
                            showCoverageOnHover: false,
                            spiderfyDistanceMultiplier: 1.4,
                            maxClusterRadius: 48
                        });
                        const memberCluster = L.markerClusterGroup({
                            showCoverageOnHover: false,
                            maxClusterRadius: 50,
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

                        const renderPatients = () => {
                            patientCluster.clearLayers();
                            const bounds = [];
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
                                bounds.push([p.location.latitude, p.location.longitude]);
                            });
                            if (bounds.length) {
                                map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
                            }
                        };

                        const renderMembers = () => {
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
                            currentPatients = Array.isArray(patients) ? patients : [];
                            currentMembers = Array.isArray(members) ? members : [];
                            renderPatients();
                            renderMembers();
                        };

                        window.clearEntities = () => {
                            currentPatients = [];
                            currentMembers = [];
                            patientCluster.clearLayers();
                            memberCluster.clearLayers();
                            sidePanel.hide();
                        };

                        setTimeout(resizeMap, 100);
                    </script>
                </body>
                </html>
                """;
    }
}
