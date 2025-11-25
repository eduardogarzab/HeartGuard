package com.heartguard.desktop.ui;

import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.ui.patient.PatientEmbeddedMapPanel;
import com.heartguard.desktop.ui.patient.ProfilePhotoPanel;
import com.heartguard.desktop.ui.user.VitalSignsChartPanel;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.MatteBorder;
import java.awt.*;
import java.awt.Desktop;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutionException;

/**
 * Panel de dashboard para pacientes
 * Muestra información personal, estadísticas, alertas recientes y equipo de cuidado
 */
public class PatientDashboardPanel extends JPanel {
        // Campos para selector y paneles de dispositivos
        private JPanel vitalSignsChartContainerPanel;
        private JComboBox<String> deviceSelector;
        private JLabel deviceInfoLabel;
        private java.util.List<DeviceInfo> patientDevices = new java.util.ArrayList<>();
        private final java.util.Map<String, VitalSignsChartPanel> chartPanelCache = new java.util.HashMap<>();
        private VitalSignsChartPanel chartPanel;
    private static final Color BACKGROUND_COLOR = new Color(240, 244, 249);
    private static final Color SURFACE_COLOR = Color.WHITE;
    private static final Color PRIMARY_COLOR = new Color(33, 150, 243);
    private static final Color PRIMARY_DARK = new Color(25, 118, 210);
    private static final Color ACCENT_COLOR = new Color(0, 188, 212);
    private static final Color TEXT_PRIMARY_COLOR = new Color(35, 52, 70);
    private static final Color TEXT_SECONDARY_COLOR = new Color(104, 120, 138);
    private static final Color NEUTRAL_BORDER_COLOR = new Color(225, 231, 238);
    private static final Color SUCCESS_COLOR = new Color(46, 204, 113);
    private static final Color WARNING_COLOR = new Color(255, 179, 0);
    private static final Color INFO_COLOR = new Color(155, 89, 182);
    private static final Color DANGER_COLOR = new Color(231, 76, 60);
    private static final int CARD_CORNER_RADIUS = 26;
    private static final int SECTION_SPACING = 20;

    private static final Font TITLE_FONT = new Font("Segoe UI", Font.BOLD, 28);
    private static final Font SUBTITLE_FONT = new Font("Segoe UI", Font.PLAIN, 15);
    private static final Font SECTION_TITLE_FONT = new Font("Segoe UI", Font.BOLD, 19);
    private static final Font BODY_FONT = new Font("Segoe UI", Font.PLAIN, 14);
    private static final Font CAPTION_FONT = new Font("Segoe UI", Font.PLAIN, 12);
    private static final Font METRIC_VALUE_FONT = new Font("Segoe UI", Font.BOLD, 32);
    private static final Font METRIC_DESC_FONT = new Font("Segoe UI", Font.PLAIN, 13);
    private static final Font BUTTON_FONT = new Font("Segoe UI", Font.BOLD, 14);

    private final ApiClient apiClient;
    private final String accessToken;
    private final String patientId;

    // Componentes UI
    private JLabel nameLabel;
    private JLabel emailLabel;
    private JLabel birthdateLabel;
    private JLabel riskLevelLabel;
    private JLabel orgLabel;

    private JLabel totalAlertsLabel;
    private JLabel pendingAlertsLabel;
    private JLabel devicesCountLabel;
    private JLabel lastReadingLabel;

    private JPanel alertsPanel;
    private JPanel careTeamPanel;
    private JPanel caregiversPanel;
    private JLabel mapStatusLabel;
    private PatientEmbeddedMapPanel embeddedMapPanel;
    private ProfilePhotoPanel profilePhotoPanel;
    private JsonArray cachedLocationsData = new JsonArray();

    public PatientDashboardPanel(ApiClient apiClient, String accessToken, String patientId) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.patientId = patientId;

        initComponents();
        loadDashboardData();
    }

    private void initComponents() {
        setLayout(new BorderLayout(10, 10));
        setBorder(new EmptyBorder(24, 24, 24, 24));
        setBackground(BACKGROUND_COLOR);

        // Panel de encabezado
        JPanel headerPanel = createHeaderPanel();
        add(headerPanel, BorderLayout.NORTH);

        // Panel central con scroll
        JPanel centerPanel = createCenterPanel();
        JScrollPane scrollPane = new JScrollPane(centerPanel);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        scrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        scrollPane.setBorder(null);
        scrollPane.getViewport().setBackground(BACKGROUND_COLOR);
        scrollPane.setBackground(BACKGROUND_COLOR);
        add(scrollPane, BorderLayout.CENTER);

        // Panel de acciones
        JPanel actionsPanel = createActionsPanel();
        add(actionsPanel, BorderLayout.SOUTH);
    }

    private JPanel createHeaderPanel() {
        GradientPanel panel = new GradientPanel(PRIMARY_DARK, PRIMARY_COLOR);
        panel.setLayout(new BorderLayout());
        panel.setBorder(new EmptyBorder(28, 32, 28, 32));

        JPanel titleWrapper = new JPanel();
        titleWrapper.setOpaque(false);
        titleWrapper.setLayout(new BoxLayout(titleWrapper, BoxLayout.Y_AXIS));

        JLabel titleLabel = new JLabel("Mi Portal de Salud");
        titleLabel.setFont(TITLE_FONT);
        titleLabel.setForeground(Color.WHITE);

        JLabel subtitleLabel = new JLabel("Resumen personalizado de tu bienestar y seguimiento clínico");
        subtitleLabel.setFont(SUBTITLE_FONT);
        subtitleLabel.setForeground(new Color(255, 255, 255, 200));

        titleWrapper.add(titleLabel);
        titleWrapper.add(Box.createVerticalStrut(6));
        titleWrapper.add(subtitleLabel);

        JButton logoutButton = new RoundedButton(
                "Cerrar Sesión",
                new Color(255, 255, 255, 70),
                new Color(255, 255, 255, 140),
                Color.WHITE
        );
        logoutButton.addActionListener(e -> logout());

        panel.add(titleWrapper, BorderLayout.CENTER);
        panel.add(logoutButton, BorderLayout.EAST);

        return panel;
    }

    private JPanel createCenterPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setOpaque(false);

        // Sección 1: Información Personal
        panel.add(createProfileSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 2: Estadísticas
        panel.add(createStatsSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 3: Signos Vitales en Tiempo Real
        panel.add(createVitalSignsSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 4: Alertas Recientes
        panel.add(createAlertsSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 5: Equipo de Cuidado
        panel.add(createCareTeamSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 6: Cuidadores (Caregivers)
        panel.add(createCaregiversSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 7: Ubicación Reciente
        panel.add(createLocationSection());

        return panel;
    }

    private JPanel createProfileSection() {
        // Crear panel principal con BorderLayout
        JPanel mainContent = new JPanel(new BorderLayout(20, 0));
        mainContent.setOpaque(false);
        
        // Panel izquierdo: Foto de perfil
        profilePhotoPanel = new ProfilePhotoPanel(apiClient, accessToken, patientId);
        profilePhotoPanel.setOnPhotoChangedCallback(() -> {
            // Recargar el dashboard cuando la foto cambie
            loadDashboardData();
        });
        
        JPanel photoContainer = new JPanel(new FlowLayout(FlowLayout.CENTER));
        photoContainer.setOpaque(false);
        photoContainer.add(profilePhotoPanel);
        
        mainContent.add(photoContainer, BorderLayout.WEST);
        
        // Panel derecho: Información del perfil
        JPanel infoContent = new JPanel(new GridLayout(0, 2, 18, 18));
        infoContent.setOpaque(false);

        nameLabel = createInfoValueLabel("--");
        emailLabel = createInfoValueLabel("--");
        birthdateLabel = createInfoValueLabel("--");
        riskLevelLabel = createInfoValueLabel("--");
        riskLevelLabel.setFont(new Font("Segoe UI", Font.BOLD, 15));
        orgLabel = createInfoValueLabel("--");

        infoContent.add(createFieldLabel("Nombre"));
        infoContent.add(nameLabel);
        infoContent.add(createFieldLabel("Email"));
        infoContent.add(emailLabel);
        infoContent.add(createFieldLabel("Fecha de Nacimiento"));
        infoContent.add(birthdateLabel);
        infoContent.add(createFieldLabel("Nivel de Riesgo"));
        infoContent.add(riskLevelLabel);
        infoContent.add(createFieldLabel("Organización"));
        infoContent.add(orgLabel);

        mainContent.add(infoContent, BorderLayout.CENTER);

        return createCardSection("👤 Información Personal", mainContent);
    }

    private JPanel createStatsSection() {
        JPanel grid = new JPanel(new GridLayout(2, 2, 18, 18));
        grid.setOpaque(false);

        totalAlertsLabel = createMetricValueLabel("0");
        grid.add(createMetricCard("🚨", totalAlertsLabel, "Total de Alertas", PRIMARY_COLOR));

        pendingAlertsLabel = createMetricValueLabel("0");
        grid.add(createMetricCard("⏳", pendingAlertsLabel, "Alertas Pendientes", WARNING_COLOR));

        devicesCountLabel = createMetricValueLabel("0");
        grid.add(createMetricCard("🩺", devicesCountLabel, "Dispositivos", ACCENT_COLOR));

        lastReadingLabel = createMetricValueLabel("N/A");
        lastReadingLabel.setFont(new Font("Segoe UI", Font.BOLD, 20));
        grid.add(createMetricCard("🕒", lastReadingLabel, "Última Lectura", INFO_COLOR));

        return createCardSection("📊 Indicadores Clave", grid);
    }

    private JPanel createVitalSignsSection() {
        JPanel chartContainer = new JPanel(new BorderLayout(0, 12));
        chartContainer.setOpaque(false);

        // Panel superior con información y selector
        JPanel topPanel = new JPanel(new BorderLayout());
        topPanel.setOpaque(false);
        topPanel.setBorder(new EmptyBorder(0, 0, 12, 0));

        JLabel desc = new JLabel("Gráficas en tiempo real de signos vitales");
        desc.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        desc.setForeground(TEXT_SECONDARY_COLOR);
        topPanel.add(desc, BorderLayout.WEST);

        JPanel devicePanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        devicePanel.setOpaque(false);
        deviceInfoLabel = new JLabel("");
        deviceInfoLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        deviceInfoLabel.setForeground(TEXT_SECONDARY_COLOR);
        devicePanel.add(deviceInfoLabel);
        deviceSelector = new JComboBox<>();
        deviceSelector.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        deviceSelector.setVisible(false);
        deviceSelector.addActionListener(e -> onDeviceSelected());
        devicePanel.add(deviceSelector);
        topPanel.add(devicePanel, BorderLayout.EAST);

        chartContainer.add(topPanel, BorderLayout.NORTH);

        // Panel de gráficas
        vitalSignsChartContainerPanel = new JPanel(new BorderLayout());
        vitalSignsChartContainerPanel.setOpaque(false);
        vitalSignsChartContainerPanel.setPreferredSize(new Dimension(800, 500));
        vitalSignsChartContainerPanel.setMinimumSize(new Dimension(600, 400));
        chartContainer.add(vitalSignsChartContainerPanel, BorderLayout.CENTER);

        // Cargar dispositivos y mostrar panel
        loadDevicesForVitalSigns();

        return createCardSection("📈 Signos Vitales en Tiempo Real", chartContainer);
    }

    private JPanel createAlertsSection() {
        alertsPanel = new JPanel();
        alertsPanel.setLayout(new BoxLayout(alertsPanel, BoxLayout.Y_AXIS));
        alertsPanel.setOpaque(false);

        return createCardSection("🚨 Alertas Recientes", alertsPanel);
    }

    private JPanel createCareTeamSection() {
        careTeamPanel = new JPanel();
        careTeamPanel.setLayout(new BoxLayout(careTeamPanel, BoxLayout.Y_AXIS));
        careTeamPanel.setOpaque(false);

        return createCardSection("👥 Equipo de Cuidado", careTeamPanel);
    }

    private JPanel createCaregiversSection() {
        caregiversPanel = new JPanel();
        caregiversPanel.setLayout(new BoxLayout(caregiversPanel, BoxLayout.Y_AXIS));
        caregiversPanel.setOpaque(false);

        return createCardSection("🤝 Cuidadores", caregiversPanel);
    }

    private JPanel createLocationSection() {
        JPanel mapContainer = new JPanel(new BorderLayout(0, 12));
        mapContainer.setOpaque(false);

        // Panel superior con información del mapa
        JPanel topPanel = new JPanel(new BorderLayout());
        topPanel.setOpaque(false);
        topPanel.setBorder(new EmptyBorder(0, 0, 12, 0));
        
        // Descripción
        JLabel mapDesc = new JLabel("Ubicaciones recientes del paciente");
        mapDesc.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        mapDesc.setForeground(TEXT_SECONDARY_COLOR);
        topPanel.add(mapDesc, BorderLayout.WEST);
        
        // Estado del mapa
        mapStatusLabel = new JLabel("Cargando...");
        mapStatusLabel.setFont(CAPTION_FONT);
        mapStatusLabel.setForeground(TEXT_SECONDARY_COLOR);
        topPanel.add(mapStatusLabel, BorderLayout.EAST);
        
        mapContainer.add(topPanel, BorderLayout.NORTH);

        // Panel del mapa embebido
        JPanel mapPanel = new JPanel(new BorderLayout());
        mapPanel.setOpaque(false);
        mapPanel.setPreferredSize(new Dimension(800, 450));
        mapPanel.setMinimumSize(new Dimension(600, 400));
        
        try {
            embeddedMapPanel = new PatientEmbeddedMapPanel();
            mapPanel.add(embeddedMapPanel, BorderLayout.CENTER);
        } catch (Exception e) {
            System.err.println("Error al crear el mapa embebido: " + e.getMessage());
            e.printStackTrace();
            JLabel errorLabel = new JLabel("Error al cargar el mapa", SwingConstants.CENTER);
            errorLabel.setForeground(DANGER_COLOR);
            errorLabel.setFont(BODY_FONT);
            mapPanel.add(errorLabel, BorderLayout.CENTER);
        }
        
        mapContainer.add(mapPanel, BorderLayout.CENTER);
        
        // Botón para abrir en navegador (opcional)
        JPanel bottomPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 10, 8));
        bottomPanel.setOpaque(false);
        
        JButton openInBrowserBtn = new RoundedButton("Abrir en Navegador", SURFACE_COLOR, PRIMARY_COLOR, PRIMARY_DARK);
        openInBrowserBtn.addActionListener(e -> openPatientMapInBrowser());
        openInBrowserBtn.setPreferredSize(new Dimension(200, 36));
        bottomPanel.add(openInBrowserBtn);
        
        mapContainer.add(bottomPanel, BorderLayout.SOUTH);

        return createCardSection("🗺️ Ubicaciones del Paciente", mapContainer);
    }

    private JPanel createActionsPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER, 18, 16));
        panel.setOpaque(false);

        JButton viewAllAlertsBtn = new RoundedButton("Ver todas las alertas", PRIMARY_COLOR, null, Color.WHITE);
        viewAllAlertsBtn.addActionListener(e -> viewAllAlerts());

        JButton viewDevicesBtn = new RoundedButton("Ver dispositivos", ACCENT_COLOR, null, Color.WHITE);
        viewDevicesBtn.addActionListener(e -> viewDevices());

        JButton refreshBtn = new RoundedButton("Actualizar", SURFACE_COLOR, PRIMARY_COLOR, PRIMARY_DARK);
        refreshBtn.addActionListener(e -> loadDashboardData());

        panel.add(viewAllAlertsBtn);
        panel.add(viewDevicesBtn);
        panel.add(refreshBtn);

        return panel;
    }

    private JPanel createCardSection(String title, JComponent content) {
        return createCardSection(title, content, null);
    }

    private JPanel createCardSection(String title, JComponent content, JComponent trailingComponent) {
        CardPanel card = new CardPanel();
        card.add(buildSectionHeader(title, trailingComponent), BorderLayout.NORTH);

        JPanel body = new JPanel(new BorderLayout());
        body.setOpaque(false);
        body.add(content, BorderLayout.CENTER);
        card.add(body, BorderLayout.CENTER);

        return card;
    }

    private JPanel buildSectionHeader(String title, JComponent trailingComponent) {
        JPanel headerRow = new JPanel(new BorderLayout());
        headerRow.setOpaque(false);
        headerRow.setBorder(new EmptyBorder(0, 0, 12, 0));

        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(SECTION_TITLE_FONT);
        titleLabel.setForeground(PRIMARY_DARK);
        headerRow.add(titleLabel, BorderLayout.WEST);

        if (trailingComponent != null) {
            JPanel trailingWrapper = new JPanel(new FlowLayout(FlowLayout.RIGHT, 0, 0));
            trailingWrapper.setOpaque(false);
            trailingWrapper.add(trailingComponent);
            headerRow.add(trailingWrapper, BorderLayout.EAST);
        }

        JSeparator separator = new JSeparator();
        separator.setForeground(new Color(0, 0, 0, 25));

        JPanel header = new JPanel(new BorderLayout());
        header.setOpaque(false);
        header.add(headerRow, BorderLayout.CENTER);
        header.add(separator, BorderLayout.SOUTH);

        return header;
    }

    private JLabel createFieldLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(BODY_FONT);
        label.setForeground(TEXT_SECONDARY_COLOR);
        return label;
    }

    private JLabel createInfoValueLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(BODY_FONT);
        label.setForeground(TEXT_PRIMARY_COLOR);
        return label;
    }

    private JLabel createMetricValueLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(METRIC_VALUE_FONT);
        label.setForeground(Color.WHITE);
        label.setAlignmentX(Component.CENTER_ALIGNMENT);
        label.setHorizontalAlignment(SwingConstants.CENTER);
        return label;
    }

    private JPanel createMetricCard(String icon, JLabel valueLabel, String description, Color baseColor) {
        MetricCardPanel card = new MetricCardPanel(baseColor);

        JLabel iconLabel = new JLabel(icon);
        iconLabel.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 28));
        iconLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        JLabel descriptionLabel = new JLabel(description);
        descriptionLabel.setFont(METRIC_DESC_FONT);
        descriptionLabel.setForeground(new Color(255, 255, 255, 210));
        descriptionLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        JPanel column = new JPanel();
        column.setOpaque(false);
        column.setLayout(new BoxLayout(column, BoxLayout.Y_AXIS));
        column.add(iconLabel);
        column.add(Box.createVerticalStrut(8));
        column.add(valueLabel);
        column.add(Box.createVerticalStrut(6));
        column.add(descriptionLabel);

        card.add(column, BorderLayout.CENTER);
        return card;
    }

    private void loadDashboardData() {
        CompletableFuture<JsonObject> dashboardFuture = apiClient.getPatientDashboardAsync(accessToken);
        CompletableFuture<JsonObject> locationsFuture = apiClient.getPatientLocationsAsync(accessToken, 6);
        CompletableFuture<JsonObject> caregiversFuture = apiClient.getPatientCaregiversAsync(accessToken);
        CompletableFuture<JsonObject> careTeamFuture = apiClient.getPatientCareTeamAsync(accessToken);

        CompletableFuture<PatientDashboardData> dataFuture = CompletableFuture.allOf(
                        dashboardFuture,
                        locationsFuture,
                        caregiversFuture,
                        careTeamFuture
                )
                .thenApplyAsync(ignored -> {
                    PatientDashboardData data = new PatientDashboardData();
                    data.dashboard = dashboardFuture.join();
                    data.locations = locationsFuture.join();
                    data.caregivers = caregiversFuture.join();
                    data.careTeam = careTeamFuture.join();
                    return data;
                });

        dataFuture.thenAccept(data -> SwingUtilities.invokeLater(() -> renderDashboardData(data)))
                .exceptionally(ex -> {
                    handleAsyncError(ex, "Error al cargar dashboard");
                    return null;
                });
    }

    private void renderDashboardData(PatientDashboardData data) {
        try {
            JsonArray careTeamArray = null;
            JsonArray caregiversArray = null;

            JsonObject dashboard = data.dashboard;
            JsonObject locationsResponse = data.locations;
            JsonObject caregiversResponse = data.caregivers;
            JsonObject careTeamResponse = data.careTeam;

            if (dashboard != null) {
                JsonObject patientObj = dashboard.has("patient") && dashboard.get("patient").isJsonObject()
                        ? dashboard.getAsJsonObject("patient") : null;
                if (patientObj != null) {
                    updateProfileSection(patientObj);
                }

                JsonObject statsObj = dashboard.has("stats") && dashboard.get("stats").isJsonObject()
                        ? dashboard.getAsJsonObject("stats") : null;
                if (statsObj != null) {
                    updateStatsSection(statsObj);
                }

                JsonArray alertsArray = dashboard.has("recent_alerts") && dashboard.get("recent_alerts").isJsonArray()
                        ? dashboard.getAsJsonArray("recent_alerts") : null;
                updateAlertsSection(alertsArray);

                if (dashboard.has("care_team")) {
                    JsonElement careTeamElement = dashboard.get("care_team");
                    if (careTeamElement.isJsonArray()) {
                        careTeamArray = careTeamElement.getAsJsonArray();
                    } else if (careTeamElement.isJsonObject()) {
                        JsonObject careTeamObj = careTeamElement.getAsJsonObject();
                        if (careTeamObj.has("teams") && careTeamObj.get("teams").isJsonArray()) {
                            careTeamArray = careTeamObj.getAsJsonArray("teams");
                        }
                    }
                }

                if (dashboard.has("caregivers")) {
                    JsonElement caregiversElement = dashboard.get("caregivers");
                    if (caregiversElement.isJsonArray()) {
                        caregiversArray = caregiversElement.getAsJsonArray();
                    } else if (caregiversElement.isJsonObject()) {
                        JsonObject caregiversObj = caregiversElement.getAsJsonObject();
                        if (caregiversObj.has("caregivers") && caregiversObj.get("caregivers").isJsonArray()) {
                            caregiversArray = caregiversObj.getAsJsonArray("caregivers");
                        }
                    }
                }
            } else {
                updateAlertsSection(null);
            }

            if (careTeamResponse != null && careTeamResponse.has("teams") && careTeamResponse.get("teams").isJsonArray()) {
                careTeamArray = careTeamResponse.getAsJsonArray("teams");
            }

            if (caregiversResponse != null && caregiversResponse.has("caregivers") && caregiversResponse.get("caregivers").isJsonArray()) {
                caregiversArray = caregiversResponse.getAsJsonArray("caregivers");
            }

            updateCareTeamSection(careTeamArray);
            updateCaregiversSection(caregiversArray);

            if (locationsResponse != null) {
                updateLocationsSection(locationsResponse);
            } else {
                updateLocationsSection(null);
            }
        } catch (Exception e) {
            e.printStackTrace();
            JOptionPane.showMessageDialog(
                    PatientDashboardPanel.this,
                    "Error al actualizar la interfaz: " + e.getMessage(),
                    "Error",
                    JOptionPane.ERROR_MESSAGE
            );
        }
    }

    private void updateLocationsSection(JsonObject locationsResponse) {
        if (locationsResponse == null || !locationsResponse.has("locations")) {
            // No hay ubicaciones disponibles
            cachedLocationsData = new JsonArray();
            if (mapStatusLabel != null) {
                mapStatusLabel.setText("Sin ubicaciones disponibles");
            }
            if (embeddedMapPanel != null) {
                embeddedMapPanel.updateLocations(new JsonArray());
            }
            return;
        }

        JsonArray locations = locationsResponse.getAsJsonArray("locations");

        // Guardar ubicaciones para el mapa
        cachedLocationsData = locations;

        if (locations.size() == 0) {
            if (mapStatusLabel != null) {
                mapStatusLabel.setText("Sin ubicaciones registradas");
            }
            if (embeddedMapPanel != null) {
                embeddedMapPanel.updateLocations(new JsonArray());
            }
        } else {
            if (mapStatusLabel != null) {
                mapStatusLabel.setText(locations.size() + " ubicación(es) disponible(s)");
            }
            
            // Actualizar el mapa embebido con las ubicaciones
            if (embeddedMapPanel != null) {
                embeddedMapPanel.updateLocations(locations);
            }
        }
    }

    private void updateProfileSection(JsonObject patient) {
        nameLabel.setText(patient.get("name").getAsString());
        emailLabel.setText(patient.get("email").getAsString());

        String birthdate = patient.has("birthdate") && !patient.get("birthdate").isJsonNull()
                ? patient.get("birthdate").getAsString() : "No especificado";
        birthdateLabel.setText(birthdate);

        String riskLevel = patient.has("risk_level") && !patient.get("risk_level").isJsonNull()
                ? patient.get("risk_level").getAsString() : "No especificado";
        riskLevelLabel.setText(riskLevel);
        setRiskLevelColor(riskLevel);

        String orgName = patient.has("org_name") && !patient.get("org_name").isJsonNull()
                ? patient.get("org_name").getAsString() : "Sin organización";
        orgLabel.setText(orgName);
        
        // Actualizar la foto de perfil
        String photoUrl = patient.has("profile_photo_url") && !patient.get("profile_photo_url").isJsonNull()
                ? patient.get("profile_photo_url").getAsString() : null;
        if (profilePhotoPanel != null) {
            profilePhotoPanel.setPhotoUrl(photoUrl);
        }
    }

    private void setRiskLevelColor(String riskLevel) {
        if (riskLevel == null) {
            riskLevelLabel.setForeground(TEXT_SECONDARY_COLOR);
            return;
        }

        String normalized = riskLevel.toLowerCase();
        Color color = TEXT_PRIMARY_COLOR;
        if (normalized.contains("bajo")) {
            color = SUCCESS_COLOR;
        } else if (normalized.contains("medio")) {
            color = WARNING_COLOR;
        } else if (normalized.contains("alto")) {
            color = INFO_COLOR.darker();
        } else if (normalized.contains("crítico") || normalized.contains("critico")) {
            color = DANGER_COLOR;
        }
        riskLevelLabel.setForeground(color);
        riskLevelLabel.setFont(new Font("Segoe UI", Font.BOLD, 15));
    }

    private void updateStatsSection(JsonObject stats) {
        int totalAlerts = stats.get("total_alerts").getAsInt();
        int pendingAlerts = stats.get("pending_alerts").getAsInt();
        int devicesCount = stats.get("devices_count").getAsInt();
        String lastReading = stats.has("last_reading") && !stats.get("last_reading").isJsonNull()
                ? formatDate(stats.get("last_reading").getAsString()) : "N/A";

    totalAlertsLabel.setText(String.valueOf(totalAlerts));
    pendingAlertsLabel.setText(String.valueOf(pendingAlerts));
    devicesCountLabel.setText(String.valueOf(devicesCount));
    lastReadingLabel.setText(lastReading);
    }

    private void updateAlertsSection(JsonArray alerts) {
        alertsPanel.removeAll();

        if (alerts == null || alerts.size() == 0) {
            JPanel emptyState = new JPanel(new FlowLayout(FlowLayout.CENTER));
            emptyState.setOpaque(false);
            JLabel noAlerts = new JLabel("No hay alertas recientes");
            noAlerts.setFont(BODY_FONT.deriveFont(Font.ITALIC, 14f));
            noAlerts.setForeground(TEXT_SECONDARY_COLOR);
            emptyState.add(noAlerts);
            alertsPanel.add(emptyState);
        } else {
            for (int i = 0; i < alerts.size(); i++) {
                if (alerts.get(i).isJsonObject()) {
                    JsonObject alert = alerts.get(i).getAsJsonObject();
                    JPanel alertCard = createAlertCard(alert);
                    alertCard.setMaximumSize(new Dimension(Integer.MAX_VALUE, alertCard.getPreferredSize().height));
                    alertsPanel.add(alertCard);
                    if (i < alerts.size() - 1) {
                        alertsPanel.add(Box.createVerticalStrut(12));
                    }
                }
            }
        }

        alertsPanel.revalidate();
        alertsPanel.repaint();
    }

    private JPanel createAlertCard(JsonObject alert) {
        Color accentColor = getAlertLevelColor(alert.get("level").getAsString());

        CardPanel cardWrapper = new CardPanel();
        cardWrapper.setBorder(new CompoundBorder(
                new MatteBorder(0, 4, 0, 0, accentColor),
                new EmptyBorder(16, 20, 16, 20)
        ));
        cardWrapper.setLayout(new BorderLayout(12, 8));

        String level = alert.get("level_label").getAsString();
        String type = alert.has("type") && !alert.get("type").isJsonNull()
                ? alert.get("type").getAsString() : "Sin tipo";
        JLabel typeLabel = new JLabel(type + " · " + level);
        typeLabel.setFont(new Font("Segoe UI", Font.BOLD, 15));
        typeLabel.setForeground(TEXT_PRIMARY_COLOR);

        String description = alert.has("description") && !alert.get("description").isJsonNull()
                ? alert.get("description").getAsString() : "Sin descripción";
        JLabel descLabel = new JLabel(description);
        descLabel.setFont(BODY_FONT);
        descLabel.setForeground(TEXT_SECONDARY_COLOR);

        String createdAt = formatDate(alert.get("created_at").getAsString());
        JLabel dateLabel = new JLabel(createdAt);
        dateLabel.setFont(CAPTION_FONT);
        dateLabel.setForeground(TEXT_SECONDARY_COLOR);

        String status = alert.get("status_label").getAsString();
        JLabel statusChip = new JLabel(" " + status.toUpperCase() + " ");
        statusChip.setFont(CAPTION_FONT);
        statusChip.setForeground(accentColor.darker());
        statusChip.setOpaque(true);
        statusChip.setBackground(new Color(accentColor.getRed(), accentColor.getGreen(), accentColor.getBlue(), 30));
        statusChip.setBorder(new CompoundBorder(
                new MatteBorder(1, 1, 1, 1, accentColor),
                new EmptyBorder(4, 10, 4, 10)
        ));

        JPanel metaRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        metaRow.setOpaque(false);
        metaRow.add(dateLabel);
        metaRow.add(statusChip);
        
        // ✨ NUEVO: Indicador de IA y Ground Truth
        boolean isAIGenerated = alert.has("created_by_model_id") && 
                                !alert.get("created_by_model_id").isJsonNull();
        
        if (isAIGenerated) {
            JLabel aiChip = new JLabel(" 🤖 IA ");
            aiChip.setFont(CAPTION_FONT);
            aiChip.setForeground(new Color(103, 58, 183)); // Deep purple
            aiChip.setOpaque(true);
            aiChip.setBackground(new Color(103, 58, 183, 30));
            aiChip.setBorder(new CompoundBorder(
                    new MatteBorder(1, 1, 1, 1, new Color(103, 58, 183)),
                    new EmptyBorder(4, 10, 4, 10)
            ));
            aiChip.setToolTipText("Alerta generada por modelo de Inteligencia Artificial");
            metaRow.add(aiChip);
        }

        JPanel infoPanel = new JPanel();
        infoPanel.setOpaque(false);
        infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));

        typeLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        descLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        metaRow.setAlignmentX(Component.LEFT_ALIGNMENT);

        infoPanel.add(typeLabel);
        infoPanel.add(Box.createVerticalStrut(6));
        infoPanel.add(descLabel);
        infoPanel.add(Box.createVerticalStrut(10));
        infoPanel.add(metaRow);
        
        // ✨ NUEVO: Panel de información de IA y Ground Truth
        if (isAIGenerated) {
            JPanel aiInfoPanel = createAIInfoPanel(alert);
            if (aiInfoPanel != null) {
                aiInfoPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
                infoPanel.add(Box.createVerticalStrut(12));
                infoPanel.add(aiInfoPanel);
            }
        }

        cardWrapper.add(infoPanel, BorderLayout.CENTER);

        return cardWrapper;
    }
    
    /**
     * ✨ NUEVO: Crea un panel con información de IA y validación médica
     */
    private JPanel createAIInfoPanel(JsonObject alert) {
        JPanel panel = new JPanel();
        panel.setOpaque(true);
        panel.setBackground(new Color(248, 250, 252)); // Light gray-blue
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBorder(new CompoundBorder(
                new MatteBorder(1, 1, 1, 1, new Color(226, 232, 240)),
                new EmptyBorder(10, 12, 10, 12)
        ));
        
        boolean hasContent = false;
        
        // Extraer probabilidad de la descripción si está disponible
        String description = alert.has("description") && !alert.get("description").isJsonNull()
                ? alert.get("description").getAsString() : "";
        
        Double probability = extractProbabilityFromDescription(description);
        if (probability != null) {
            JPanel probPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
            probPanel.setOpaque(false);
            
            JLabel probLabel = new JLabel("Probabilidad de IA:");
            probLabel.setFont(new Font("Segoe UI", Font.BOLD, 12));
            probLabel.setForeground(new Color(71, 85, 105)); // Slate-600
            
            JLabel probValue = new JLabel(String.format("%.1f%%", probability * 100));
            probValue.setFont(new Font("Segoe UI", Font.BOLD, 13));
            probValue.setForeground(getProbabilityColor(probability));
            
            probPanel.add(probLabel);
            probPanel.add(probValue);
            
            probPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
            panel.add(probPanel);
            hasContent = true;
        }
        
        // Información del modelo
        if (alert.has("created_by_model_id") && !alert.get("created_by_model_id").isJsonNull()) {
            if (hasContent) {
                panel.add(Box.createVerticalStrut(6));
            }
            
            JPanel modelPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
            modelPanel.setOpaque(false);
            
            JLabel modelLabel = new JLabel("Modelo:");
            modelLabel.setFont(CAPTION_FONT);
            modelLabel.setForeground(TEXT_SECONDARY_COLOR);
            
            JLabel modelValue = new JLabel("RandomForest");
            modelValue.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            modelValue.setForeground(new Color(100, 116, 139)); // Slate-500
            
            modelPanel.add(modelLabel);
            modelPanel.add(modelValue);
            
            modelPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
            panel.add(modelPanel);
            hasContent = true;
        }
        
        // Estado de validación médica (Ground Truth)
        if (alert.has("ground_truth_validated") && alert.get("ground_truth_validated").getAsBoolean()) {
            if (hasContent) {
                panel.add(Box.createVerticalStrut(8));
            }
            
            JSeparator separator = new JSeparator();
            separator.setForeground(new Color(226, 232, 240));
            separator.setMaximumSize(new Dimension(Integer.MAX_VALUE, 1));
            panel.add(separator);
            panel.add(Box.createVerticalStrut(8));
            
            JPanel gtPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
            gtPanel.setOpaque(false);
            
            JLabel gtIcon = new JLabel("✅");
            gtIcon.setFont(new Font("Segoe UI", Font.PLAIN, 14));
            
            JLabel gtLabel = new JLabel("Validado por médico");
            gtLabel.setFont(new Font("Segoe UI", Font.BOLD, 12));
            gtLabel.setForeground(new Color(22, 163, 74)); // Green-600
            
            gtPanel.add(gtIcon);
            gtPanel.add(gtLabel);
            
            if (alert.has("ground_truth_doctor") && !alert.get("ground_truth_doctor").isJsonNull()) {
                JLabel doctorLabel = new JLabel("(" + alert.get("ground_truth_doctor").getAsString() + ")");
                doctorLabel.setFont(CAPTION_FONT);
                doctorLabel.setForeground(TEXT_SECONDARY_COLOR);
                gtPanel.add(doctorLabel);
            }
            
            gtPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
            panel.add(gtPanel);
            
            if (alert.has("ground_truth_note") && !alert.get("ground_truth_note").isJsonNull()) {
                panel.add(Box.createVerticalStrut(4));
                JLabel noteLabel = new JLabel("Nota: " + alert.get("ground_truth_note").getAsString());
                noteLabel.setFont(CAPTION_FONT);
                noteLabel.setForeground(TEXT_SECONDARY_COLOR);
                noteLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
                panel.add(noteLabel);
            }
            
            hasContent = true;
        } else if (alert.has("created_by_model_id") && !alert.get("created_by_model_id").isJsonNull()) {
            // Alerta de IA no validada aún
            if (hasContent) {
                panel.add(Box.createVerticalStrut(8));
            }
            
            JSeparator separator = new JSeparator();
            separator.setForeground(new Color(226, 232, 240));
            separator.setMaximumSize(new Dimension(Integer.MAX_VALUE, 1));
            panel.add(separator);
            panel.add(Box.createVerticalStrut(8));
            
            JPanel pendingPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
            pendingPanel.setOpaque(false);
            
            JLabel pendingIcon = new JLabel("⏳");
            pendingIcon.setFont(new Font("Segoe UI", Font.PLAIN, 14));
            
            JLabel pendingLabel = new JLabel("Pendiente de validación médica");
            pendingLabel.setFont(new Font("Segoe UI", Font.ITALIC, 12));
            pendingLabel.setForeground(new Color(180, 83, 9)); // Amber-700
            
            pendingPanel.add(pendingIcon);
            pendingPanel.add(pendingLabel);
            
            pendingPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
            panel.add(pendingPanel);
            hasContent = true;
        }
        
        return hasContent ? panel : null;
    }
    
    /**
     * ✨ NUEVO: Extrae la probabilidad de la descripción de la alerta
     */
    private Double extractProbabilityFromDescription(String description) {
        if (description == null || description.isEmpty()) {
            return null;
        }
        
        // Buscar patrones como "Probabilidad: 0.85" o "85%" en la descripción
        java.util.regex.Pattern pattern1 = java.util.regex.Pattern.compile("Probabilidad[:\\s]+([0-9]*\\.?[0-9]+)");
        java.util.regex.Matcher matcher1 = pattern1.matcher(description);
        if (matcher1.find()) {
            try {
                return Double.parseDouble(matcher1.group(1));
            } catch (NumberFormatException e) {
                // Ignorar
            }
        }
        
        // Buscar patrón de porcentaje
        java.util.regex.Pattern pattern2 = java.util.regex.Pattern.compile("([0-9]+(?:\\.[0-9]+)?)%");
        java.util.regex.Matcher matcher2 = pattern2.matcher(description);
        if (matcher2.find()) {
            try {
                double percent = Double.parseDouble(matcher2.group(1));
                return percent / 100.0;
            } catch (NumberFormatException e) {
                // Ignorar
            }
        }
        
        return null;
    }
    
    /**
     * ✨ NUEVO: Obtiene el color según la probabilidad
     */
    private Color getProbabilityColor(double probability) {
        if (probability >= 0.8) {
            return new Color(220, 38, 38); // Red-600 - Alta probabilidad
        } else if (probability >= 0.6) {
            return new Color(234, 88, 12); // Orange-600 - Media-alta
        } else if (probability >= 0.4) {
            return new Color(202, 138, 4); // Yellow-600 - Media
        } else {
            return new Color(22, 163, 74); // Green-600 - Baja
        }
    }

    private Color getAlertLevelColor(String level) {
        switch (level.toLowerCase()) {
            case "low":
                return new Color(46, 204, 113);
            case "medium":
                return new Color(241, 196, 15);
            case "high":
                return new Color(230, 126, 34);
            case "critical":
                return new Color(231, 76, 60);
            default:
                return Color.BLACK;
        }
    }

    private void updateCareTeamSection(JsonArray teams) {
        careTeamPanel.removeAll();

        if (teams == null || teams.size() == 0) {
            JLabel noTeam = new JLabel("No hay equipo de cuidado asignado");
            noTeam.setFont(BODY_FONT.deriveFont(Font.ITALIC, 14f));
            noTeam.setForeground(TEXT_SECONDARY_COLOR);
            careTeamPanel.add(noTeam);
        } else {
            for (int i = 0; i < teams.size(); i++) {
                if (teams.get(i).isJsonObject()) {
                    JsonObject team = teams.get(i).getAsJsonObject();
                    JPanel teamPanel = createTeamPanel(team);
                    careTeamPanel.add(teamPanel);
                    if (i < teams.size() - 1) {
                        careTeamPanel.add(Box.createVerticalStrut(15));
                    }
                }
            }
        }

        careTeamPanel.revalidate();
        careTeamPanel.repaint();
    }

    private void updateCaregiversSection(JsonArray caregivers) {
        caregiversPanel.removeAll();

        if (caregivers == null || caregivers.size() == 0) {
            JLabel noCaregivers = new JLabel("No hay cuidadores asignados");
            noCaregivers.setFont(BODY_FONT.deriveFont(Font.ITALIC, 14f));
            noCaregivers.setForeground(TEXT_SECONDARY_COLOR);
            caregiversPanel.add(noCaregivers);
        } else {
            for (int i = 0; i < caregivers.size(); i++) {
                if (caregivers.get(i).isJsonObject()) {
                    JsonObject caregiver = caregivers.get(i).getAsJsonObject();
                    JPanel caregiverPanel = createCaregiverPanel(caregiver);
                    caregiversPanel.add(caregiverPanel);
                    if (i < caregivers.size() - 1) {
                        caregiversPanel.add(Box.createVerticalStrut(10));
                    }
                }
            }
        }

        caregiversPanel.revalidate();
        caregiversPanel.repaint();
    }

    private JPanel createTeamPanel(JsonObject team) {
        JPanel panel = new JPanel();
        panel.setOpaque(false);
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBorder(new CompoundBorder(
                new MatteBorder(1, 1, 1, 1, NEUTRAL_BORDER_COLOR),
                new EmptyBorder(14, 18, 14, 18)
        ));

        String teamName = team.has("team_name") && !team.get("team_name").isJsonNull()
                ? team.get("team_name").getAsString()
                : "Equipo sin nombre";
        JLabel teamNameLabel = new JLabel(teamName);
        teamNameLabel.setFont(new Font("Segoe UI", Font.BOLD, 15));
        teamNameLabel.setForeground(PRIMARY_DARK);
        panel.add(teamNameLabel);
        panel.add(Box.createVerticalStrut(10));

        JsonArray members = team.has("members") && team.get("members").isJsonArray()
                ? team.getAsJsonArray("members")
                : new JsonArray();

        for (int i = 0; i < members.size(); i++) {
            if (members.get(i).isJsonObject()) {
                JsonObject member = members.get(i).getAsJsonObject();
                JPanel memberPanel = createMemberPanel(member);
                panel.add(memberPanel);
                if (i < members.size() - 1) {
                    panel.add(Box.createVerticalStrut(5));
                }
            }
        }

        return panel;
    }

    private JPanel createMemberPanel(JsonObject member) {
    JPanel panel = new JPanel(new GridLayout(3, 1, 0, 2));
    panel.setOpaque(false);

        String name = member.has("name") && !member.get("name").isJsonNull()
                ? member.get("name").getAsString() : "Sin nombre";
        String role = member.has("role") && !member.get("role").isJsonNull()
                ? member.get("role").getAsString() : "Sin rol";
        String email = member.has("email") && !member.get("email").isJsonNull()
                ? member.get("email").getAsString() : "Sin email";

    JLabel nameLabel = new JLabel("• " + name);
    nameLabel.setFont(new Font("Segoe UI", Font.BOLD, 13));
    nameLabel.setForeground(TEXT_PRIMARY_COLOR);

    JLabel roleLabel = new JLabel("  Rol: " + role);
    roleLabel.setFont(CAPTION_FONT);
    roleLabel.setForeground(TEXT_SECONDARY_COLOR);

    JLabel emailLabel = new JLabel("  Email: " + email);
    emailLabel.setFont(CAPTION_FONT);
    emailLabel.setForeground(TEXT_SECONDARY_COLOR);

        panel.add(nameLabel);
        panel.add(roleLabel);
        panel.add(emailLabel);

        return panel;
    }

    private JPanel createCaregiverPanel(JsonObject caregiver) {
    JPanel panel = new JPanel();
    panel.setOpaque(false);
    panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
    panel.setBorder(new CompoundBorder(
        new MatteBorder(0, 4, 0, 0, INFO_COLOR),
        new EmptyBorder(14, 18, 14, 18)
    ));

        // Nombre con indicador de principal
        String name = caregiver.has("name") && !caregiver.get("name").isJsonNull()
                ? caregiver.get("name").getAsString() : "Sin nombre";
        boolean isPrimary = caregiver.has("is_primary") && caregiver.get("is_primary").getAsBoolean();
        boolean isActive = caregiver.has("active") && caregiver.get("active").getAsBoolean();

        String nameText = name + (isPrimary ? " ⭐ Principal" : "");
        JLabel nameLabel = new JLabel(nameText);
    nameLabel.setFont(new Font("Segoe UI", Font.BOLD, 14));
    nameLabel.setForeground(isActive ? INFO_COLOR.darker() : TEXT_SECONDARY_COLOR);
        panel.add(nameLabel);
        panel.add(Box.createVerticalStrut(5));

        // Relación
        String relationship = caregiver.has("relationship_label") && !caregiver.get("relationship_label").isJsonNull()
                ? caregiver.get("relationship_label").getAsString() : "Cuidador";
    JLabel relationshipLabel = new JLabel("Relación: " + relationship);
    relationshipLabel.setFont(BODY_FONT);
    relationshipLabel.setForeground(TEXT_SECONDARY_COLOR);
        panel.add(relationshipLabel);

        // Email
        String email = caregiver.has("email") && !caregiver.get("email").isJsonNull()
                ? caregiver.get("email").getAsString() : "Sin email";
    JLabel emailLabel = new JLabel("Email: " + email);
    emailLabel.setFont(CAPTION_FONT);
    emailLabel.setForeground(TEXT_SECONDARY_COLOR);
        panel.add(emailLabel);

        // Estado
        String status = isActive ? "✓ Activo" : "✗ Inactivo";
        JLabel statusLabel = new JLabel("Estado: " + status);
    statusLabel.setFont(CAPTION_FONT);
    statusLabel.setForeground(isActive ? SUCCESS_COLOR.darker() : DANGER_COLOR);
        panel.add(statusLabel);

        // Nota (si existe)
        if (caregiver.has("note") && !caregiver.get("note").isJsonNull()) {
            String note = caregiver.get("note").getAsString();
            if (!note.isEmpty()) {
                panel.add(Box.createVerticalStrut(5));
                JLabel noteLabel = new JLabel("<html><i>Nota: " + note + "</i></html>");
        noteLabel.setFont(CAPTION_FONT);
        noteLabel.setForeground(TEXT_SECONDARY_COLOR);
                panel.add(noteLabel);
            }
        }

        return panel;
    }

    private String formatDate(String isoDate) {
        try {
            SimpleDateFormat inputFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss");
            SimpleDateFormat outputFormat = new SimpleDateFormat("dd/MM/yyyy HH:mm");
            Date date = inputFormat.parse(isoDate);
            return outputFormat.format(date);
        } catch (Exception e) {
            return isoDate;
        }
    }

    private static Color blendColor(Color color1, Color color2, double ratio) {
        double clamped = Math.max(0, Math.min(1, ratio));
        int red = (int) Math.round(color1.getRed() * (1 - clamped) + color2.getRed() * clamped);
        int green = (int) Math.round(color1.getGreen() * (1 - clamped) + color2.getGreen() * clamped);
        int blue = (int) Math.round(color1.getBlue() * (1 - clamped) + color2.getBlue() * clamped);
        int alpha = (int) Math.round(color1.getAlpha() * (1 - clamped) + color2.getAlpha() * clamped);
        return new Color(red, green, blue, alpha);
    }

    private static class CardPanel extends JPanel {
        CardPanel() {
            super(new BorderLayout());
            setOpaque(false);
            setBorder(new EmptyBorder(24, 24, 24, 24));
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(SURFACE_COLOR);
            g2.fillRoundRect(0, 0, getWidth(), getHeight(), CARD_CORNER_RADIUS, CARD_CORNER_RADIUS);
            g2.setColor(new Color(0, 0, 0, 20));
            g2.drawRoundRect(0, 0, getWidth() - 1, getHeight() - 1, CARD_CORNER_RADIUS, CARD_CORNER_RADIUS);
            g2.dispose();
            super.paintComponent(g);
        }
    }

    private static class GradientPanel extends JPanel {
        private final Color startColor;
        private final Color endColor;

        GradientPanel(Color startColor, Color endColor) {
            this.startColor = startColor;
            this.endColor = endColor;
            setOpaque(false);
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            GradientPaint gradient = new GradientPaint(0, 0, startColor, getWidth(), getHeight(), endColor);
            g2.setPaint(gradient);
            g2.fillRect(0, 0, getWidth(), getHeight());
            g2.dispose();
            super.paintComponent(g);
        }
    }

    private static class MetricCardPanel extends JPanel {
        private final Color baseColor;

        MetricCardPanel(Color baseColor) {
            super(new BorderLayout());
            this.baseColor = baseColor;
            setOpaque(false);
            setBorder(new EmptyBorder(20, 20, 20, 20));
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            Color endColor = blendColor(baseColor, Color.BLACK, 0.2);
            GradientPaint gradient = new GradientPaint(0, 0, baseColor, getWidth(), getHeight(), endColor);
            g2.setPaint(gradient);
            g2.fillRoundRect(0, 0, getWidth(), getHeight(), CARD_CORNER_RADIUS, CARD_CORNER_RADIUS);
            g2.dispose();
            super.paintComponent(g);
        }
    }

    private static class RoundedButton extends JButton {
        private final Color baseColor;
        private final Color borderColor;

        RoundedButton(String text, Color baseColor, Color borderColor, Color textColor) {
            super(text);
            this.baseColor = baseColor;
            this.borderColor = borderColor;
            setFont(BUTTON_FONT);
            setForeground(textColor);
            setFocusPainted(false);
            setContentAreaFilled(false);
            setOpaque(false);
            setBorder(new EmptyBorder(10, 28, 10, 28));
            setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int arc = 36;
            Color fill = baseColor != null ? baseColor : SURFACE_COLOR;
            if (getModel().isPressed()) {
                fill = blendColor(fill, Color.BLACK, 0.15);
            } else if (getModel().isRollover()) {
                fill = blendColor(fill, Color.WHITE, 0.12);
            }

            g2.setColor(fill);
            g2.fillRoundRect(0, 0, getWidth(), getHeight(), arc, arc);

            Color stroke = borderColor != null ? borderColor : blendColor(fill, Color.BLACK, 0.18);
            g2.setColor(stroke);
            g2.drawRoundRect(0, 0, getWidth() - 1, getHeight() - 1, arc, arc);

            g2.dispose();
            super.paintComponent(g);
        }
    }

    private static class PatientDashboardData {
        JsonObject dashboard;
        JsonObject locations;
        JsonObject caregivers;
        JsonObject careTeam;
    }

    private void openPatientMapInBrowser() {
        try {
            // Crear archivo HTML temporal con el mapa
            File tempFile = File.createTempFile("heartguard_patient_map_", ".html");
            tempFile.deleteOnExit();

            String htmlContent = generatePatientMapHtml();

            try (FileWriter writer = new FileWriter(tempFile)) {
                writer.write(htmlContent);
            }

            // Abrir en navegador
            if (Desktop.isDesktopSupported()) {
                Desktop.getDesktop().browse(tempFile.toURI());
            } else {
                JOptionPane.showMessageDialog(
                    this,
                    "No se puede abrir el navegador automáticamente",
                    "Error",
                    JOptionPane.WARNING_MESSAGE
                );
            }

        } catch (IOException e) {
            System.err.println("Error al crear mapa temporal: " + e.getMessage());
            JOptionPane.showMessageDialog(
                this,
                "Error al abrir el mapa: " + e.getMessage(),
                "Error",
                JOptionPane.ERROR_MESSAGE
            );
        }
    }

    private String generatePatientMapHtml() {
        StringBuilder html = new StringBuilder();
        html.append("<!DOCTYPE html>");
        html.append("<html><head>");
        html.append("<meta charset='utf-8'/>");
        html.append("<title>Mapa de Ubicaciones - Paciente</title>");
        html.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'/>");
        html.append("<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'/>");
        html.append("<script src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'></script>");
        html.append("<style>");
        html.append("body{margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;}");
        html.append("#map{position:absolute;top:0;bottom:0;width:100%;height:100vh;}");
        html.append(".leaflet-popup-content-wrapper{border-radius:8px;padding:0;}");
        html.append(".leaflet-popup-content{margin:16px;font-size:14px;}");
        html.append(".popup-title{font-size:16px;font-weight:bold;color:#1976D2;margin-bottom:8px;}");
        html.append(".popup-info{margin:4px 0;color:#555;}");
        html.append(".popup-label{font-weight:600;color:#333;}");
        html.append("</style>");
        html.append("</head><body>");
        html.append("<div id='map'></div>");
        html.append("<script>");

        // Inicializar mapa
        html.append("var map = L.map('map').setView([19.432608, -99.133209], 6);");
        html.append("L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {");
        html.append("  attribution: '&copy; OpenStreetMap contributors',");
        html.append("  maxZoom: 19");
        html.append("}).addTo(map);");

        // Agregar marcadores de ubicaciones
        if (cachedLocationsData != null && cachedLocationsData.size() > 0) {
            html.append("var markers = [];");
            for (JsonElement element : cachedLocationsData) {
                if (!element.isJsonObject()) continue;
                JsonObject location = element.getAsJsonObject();

                double lat = location.has("latitude") && !location.get("latitude").isJsonNull()
                    ? location.get("latitude").getAsDouble() : 0;
                double lng = location.has("longitude") && !location.get("longitude").isJsonNull()
                    ? location.get("longitude").getAsDouble() : 0;

                if (lat == 0 && lng == 0) continue;

                String timestamp = location.has("timestamp") && !location.get("timestamp").isJsonNull()
                    ? location.get("timestamp").getAsString() : "Desconocido";
                String accuracy = location.has("accuracy") && !location.get("accuracy").isJsonNull()
                    ? String.format("%.2f m", location.get("accuracy").getAsDouble()) : "N/A";

                html.append("var marker = L.marker([").append(lat).append(",").append(lng).append("]);");
                html.append("marker.bindPopup('");
                html.append("<div class=\"popup-title\">📍 Ubicación del Paciente</div>");
                html.append("<div class=\"popup-info\"><span class=\"popup-label\">Fecha:</span> ").append(escapeHtml(timestamp)).append("</div>");
                html.append("<div class=\"popup-info\"><span class=\"popup-label\">Precisión:</span> ").append(accuracy).append("</div>");
                html.append("<div class=\"popup-info\"><span class=\"popup-label\">Coordenadas:</span> ").append(lat).append(", ").append(lng).append("</div>");
                html.append("');");
                html.append("marker.addTo(map);");
                html.append("markers.push(marker);");
            }

            // Ajustar vista para mostrar todos los marcadores
            html.append("if(markers.length > 0){");
            html.append("  var group = new L.featureGroup(markers);");
            html.append("  map.fitBounds(group.getBounds().pad(0.1));");
            html.append("}");
        } else {
            html.append("alert('No hay ubicaciones disponibles para mostrar');");
        }

        html.append("</script>");
        html.append("</body></html>");

        return html.toString();
    }

    private String escapeHtml(String text) {
        if (text == null) return "";
        return text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\"", "&quot;")
                   .replace("'", "&#39;");
    }

    private void viewAllAlerts() {
        apiClient.getPatientAlertsAsync(accessToken, 100)
                .thenApplyAsync(response -> {
                    if (response != null && response.has("alerts")) {
                        return response.getAsJsonArray("alerts");
                    }
                    return new JsonArray();
                })
                .thenAccept(alerts -> SwingUtilities.invokeLater(() -> showAllAlertsDialog(alerts)))
                .exceptionally(ex -> {
                    handleAsyncError(ex, "Error al cargar las alertas");
                    return null;
                });
    }

    private void showAllAlertsDialog(JsonArray alerts) {
        JDialog dialog = new JDialog((Window) SwingUtilities.getWindowAncestor(this), "Todas las Alertas", Dialog.ModalityType.APPLICATION_MODAL);
        dialog.setSize(900, 650);
        dialog.setLocationRelativeTo(this);

        JPanel mainPanel = new JPanel(new BorderLayout(0, 16));
        mainPanel.setBackground(BACKGROUND_COLOR);
        mainPanel.setBorder(new EmptyBorder(24, 24, 24, 24));

        // Header
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setOpaque(false);
        JLabel titleLabel = new JLabel("📋 Todas las Alertas (" + alerts.size() + ")");
        titleLabel.setFont(new Font("Segoe UI", Font.BOLD, 22));
        titleLabel.setForeground(PRIMARY_DARK);
        headerPanel.add(titleLabel, BorderLayout.WEST);

        JButton closeButton = new RoundedButton("Cerrar", SURFACE_COLOR, NEUTRAL_BORDER_COLOR, TEXT_PRIMARY_COLOR);
        closeButton.addActionListener(e -> dialog.dispose());
        headerPanel.add(closeButton, BorderLayout.EAST);

        mainPanel.add(headerPanel, BorderLayout.NORTH);

        // Alerts list
        JPanel alertsContainer = new JPanel();
        alertsContainer.setLayout(new BoxLayout(alertsContainer, BoxLayout.Y_AXIS));
        alertsContainer.setOpaque(false);

        if (alerts.size() == 0) {
            JPanel emptyState = new JPanel(new FlowLayout(FlowLayout.CENTER));
            emptyState.setOpaque(false);
            JLabel noAlertsLabel = new JLabel("No hay alertas disponibles");
            noAlertsLabel.setFont(BODY_FONT.deriveFont(Font.ITALIC, 15f));
            noAlertsLabel.setForeground(TEXT_SECONDARY_COLOR);
            emptyState.add(noAlertsLabel);
            alertsContainer.add(emptyState);
        } else {
            for (int i = 0; i < alerts.size(); i++) {
                JsonObject alert = alerts.get(i).getAsJsonObject();
                JPanel alertCard = createAlertCard(alert);
                alertCard.setMaximumSize(new Dimension(Integer.MAX_VALUE, alertCard.getPreferredSize().height));
                alertsContainer.add(alertCard);
                if (i < alerts.size() - 1) {
                    alertsContainer.add(Box.createVerticalStrut(12));
                }
            }
        }

        JScrollPane scrollPane = new JScrollPane(alertsContainer);
        scrollPane.setBorder(null);
        scrollPane.setBackground(BACKGROUND_COLOR);
        scrollPane.getViewport().setBackground(BACKGROUND_COLOR);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        mainPanel.add(scrollPane, BorderLayout.CENTER);

        dialog.setContentPane(mainPanel);
        dialog.setVisible(true);
    }

    private void viewDevices() {
        // Obtener dispositivos en background
        apiClient.getPatientDevicesAsync(accessToken)
                .thenApplyAsync(response -> {
                    if (response != null && response.has("devices")) {
                        return response.getAsJsonArray("devices");
                    }
                    return new JsonArray();
                })
                .thenAccept(devices -> SwingUtilities.invokeLater(() -> showAllDevicesDialog(devices)))
                .exceptionally(ex -> {
                    handleAsyncError(ex, "No se pudieron cargar los dispositivos");
                    return null;
                });
    }

    private void handleAsyncError(Throwable throwable, String fallbackMessage) {
        Throwable cause = unwrapCompletionException(throwable);
        if (cause instanceof ApiException apiException) {
            SwingUtilities.invokeLater(() -> JOptionPane.showMessageDialog(
                    PatientDashboardPanel.this,
                    apiException.getMessage(),
                    "Error",
                    JOptionPane.ERROR_MESSAGE
            ));
            return;
        }
        String message = (cause != null && cause.getMessage() != null && !cause.getMessage().isBlank())
                ? cause.getMessage()
                : fallbackMessage;
        SwingUtilities.invokeLater(() -> JOptionPane.showMessageDialog(
                PatientDashboardPanel.this,
                message,
                "Error",
                JOptionPane.ERROR_MESSAGE
        ));
    }

    private Throwable unwrapCompletionException(Throwable throwable) {
        if (throwable instanceof CompletionException completion && completion.getCause() != null) {
            return completion.getCause();
        }
        if (throwable instanceof ExecutionException execution && execution.getCause() != null) {
            return execution.getCause();
        }
        return throwable;
    }

    private void showAllDevicesDialog(JsonArray devices) {
        JDialog dialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(this), "Todos los Dispositivos", true);
        dialog.setSize(700, 500);
        dialog.setLocationRelativeTo(this);

        JPanel mainPanel = new JPanel(new BorderLayout(0, SECTION_SPACING));
        mainPanel.setBackground(BACKGROUND_COLOR);
        mainPanel.setBorder(BorderFactory.createEmptyBorder(SECTION_SPACING, SECTION_SPACING, SECTION_SPACING, SECTION_SPACING));

        // Header
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(BACKGROUND_COLOR);
        headerPanel.setOpaque(false);

        JLabel titleLabel = new JLabel("Dispositivos Registrados");
        titleLabel.setFont(TITLE_FONT);
        titleLabel.setForeground(TEXT_PRIMARY_COLOR);
        headerPanel.add(titleLabel, BorderLayout.WEST);

        JLabel countLabel = new JLabel(devices.size() + " dispositivos");
        countLabel.setFont(BODY_FONT);
        countLabel.setForeground(TEXT_SECONDARY_COLOR);
        headerPanel.add(countLabel, BorderLayout.EAST);

        mainPanel.add(headerPanel, BorderLayout.NORTH);

        // Content
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setBackground(BACKGROUND_COLOR);
        contentPanel.setOpaque(false);

        if (devices.size() == 0) {
            JPanel emptyPanel = new JPanel(new GridBagLayout());
            emptyPanel.setBackground(BACKGROUND_COLOR);
            emptyPanel.setOpaque(false);

            JLabel emptyLabel = new JLabel("No hay dispositivos registrados");
            emptyLabel.setFont(BODY_FONT);
            emptyLabel.setForeground(TEXT_SECONDARY_COLOR);
            emptyPanel.add(emptyLabel);

            contentPanel.add(emptyPanel);
        } else {
            for (int i = 0; i < devices.size(); i++) {
                JsonObject device = devices.get(i).getAsJsonObject();
                contentPanel.add(createDeviceCard(device));
                if (i < devices.size() - 1) {
                    contentPanel.add(Box.createVerticalStrut(12));
                }
            }
        }

        JScrollPane scrollPane = new JScrollPane(contentPanel);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        scrollPane.setBackground(BACKGROUND_COLOR);
        scrollPane.getViewport().setBackground(BACKGROUND_COLOR);

        mainPanel.add(scrollPane, BorderLayout.CENTER);

        // Footer con botón de cerrar
        JPanel footerPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        footerPanel.setBackground(BACKGROUND_COLOR);
        footerPanel.setOpaque(false);

        RoundedButton closeButton = new RoundedButton("Cerrar", TEXT_SECONDARY_COLOR, SURFACE_COLOR, TEXT_PRIMARY_COLOR);
        closeButton.addActionListener(e -> dialog.dispose());
        footerPanel.add(closeButton);

        mainPanel.add(footerPanel, BorderLayout.SOUTH);

        dialog.add(mainPanel);
        dialog.setVisible(true);
    }

    private CardPanel createDeviceCard(JsonObject device) {
        CardPanel card = new CardPanel();
        card.setLayout(new BorderLayout(SECTION_SPACING, 12));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 120));

        // Indicador de estado (izquierda)
        boolean isActive = device.has("active") && device.get("active").getAsBoolean();
        Color statusColor = isActive ? SUCCESS_COLOR : TEXT_SECONDARY_COLOR;

        JPanel statusBar = new JPanel();
        statusBar.setPreferredSize(new Dimension(4, 100));
        statusBar.setBackground(statusColor);
        card.add(statusBar, BorderLayout.WEST);

        // Contenido principal
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setOpaque(false);
        contentPanel.setBorder(BorderFactory.createEmptyBorder(12, 12, 12, 12));

        // Línea 1: Serial y tipo
        JPanel firstLine = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        firstLine.setOpaque(false);

        String serial = device.has("serial") ? device.get("serial").getAsString() : "N/A";
        JLabel serialLabel = new JLabel("Serial: " + serial);
        serialLabel.setFont(SECTION_TITLE_FONT);
        serialLabel.setForeground(TEXT_PRIMARY_COLOR);
        firstLine.add(serialLabel);

        // Chip de estado
        String statusText = isActive ? "Activo" : "Inactivo";
        JLabel statusChip = new JLabel(" " + statusText + " ");
        statusChip.setFont(CAPTION_FONT);
        statusChip.setForeground(Color.WHITE);
        statusChip.setOpaque(true);
        statusChip.setBackground(statusColor);
        statusChip.setBorder(BorderFactory.createEmptyBorder(2, 8, 2, 8));
        firstLine.add(statusChip);

        contentPanel.add(firstLine);
        contentPanel.add(Box.createVerticalStrut(6));

        // Línea 2: Marca y modelo
        String brand = device.has("brand") && !device.get("brand").isJsonNull()
            ? device.get("brand").getAsString() : "Sin marca";
        String model = device.has("model") && !device.get("model").isJsonNull()
            ? device.get("model").getAsString() : "Sin modelo";

        JLabel brandModelLabel = new JLabel(brand + " - " + model);
        brandModelLabel.setFont(BODY_FONT);
        brandModelLabel.setForeground(TEXT_SECONDARY_COLOR);
        brandModelLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        contentPanel.add(brandModelLabel);

        contentPanel.add(Box.createVerticalStrut(6));

        // Línea 3: Tipo de dispositivo
        if (device.has("type") && !device.get("type").isJsonNull()) {
            String type = device.get("type").getAsString();
            JLabel typeLabel = new JLabel("Tipo: " + type);
            typeLabel.setFont(CAPTION_FONT);
            typeLabel.setForeground(TEXT_SECONDARY_COLOR);
            typeLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
            contentPanel.add(typeLabel);
        }

        // Línea 4: Fecha de registro
        if (device.has("registered_at") && !device.get("registered_at").isJsonNull()) {
            String registeredAt = device.get("registered_at").getAsString();
            JLabel dateLabel = new JLabel("Registrado: " + formatDate(registeredAt));
            dateLabel.setFont(CAPTION_FONT);
            dateLabel.setForeground(TEXT_SECONDARY_COLOR);
            dateLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
            contentPanel.add(dateLabel);
        }

        card.add(contentPanel, BorderLayout.CENTER);

        return card;
    }

    private void logout() {
        int confirm = JOptionPane.showConfirmDialog(
                this,
                "¿Está seguro que desea cerrar sesión?",
                "Confirmar",
                JOptionPane.YES_NO_OPTION
        );

        if (confirm == JOptionPane.YES_OPTION) {
            // Volver a la ventana de login
            Window window = SwingUtilities.getWindowAncestor(this);
            window.dispose();
            new LoginFrame().setVisible(true);
        }
    }

    // Clase interna para almacenar información de dispositivos
    private static class DeviceInfo {
        String id;
        String serial;
        String brand;
        String model;
        String typeLabel;
        boolean hasActiveStream;

        public String getDisplayName() {
            return String.format("%s - %s %s", serial, brand != null ? brand : "N/A", model != null ? model : "N/A");
        }

        public String getShortInfo() {
            return String.format("%s | %s", serial, typeLabel != null ? typeLabel : "Dispositivo");
        }
    }

    // Cargar dispositivos del paciente y actualizar UI
    private void loadDevicesForVitalSigns() {
        patientDevices.clear();
        deviceSelector.removeAllItems();
        deviceSelector.setVisible(false);
        deviceInfoLabel.setText("");
        vitalSignsChartContainerPanel.removeAll();

        // Llamada asíncrona para obtener dispositivos
        apiClient.getPatientDevicesAsync(accessToken)
            .thenApplyAsync(response -> {
                if (response != null && response.has("devices")) {
                    return response.getAsJsonArray("devices");
                }
                return new JsonArray();
            })
            .thenAccept(devicesArray -> SwingUtilities.invokeLater(() -> processDevicesForVitalSigns(devicesArray)))
            .exceptionally(ex -> {
                JLabel errorLabel = new JLabel("<html><div style='text-align:center;padding:40px;'>" +
                        "<b>Error al cargar dispositivos</b><br><br>" +
                        "No se pudieron cargar los dispositivos del paciente." +
                        "</div></html>");
                errorLabel.setHorizontalAlignment(SwingConstants.CENTER);
                errorLabel.setForeground(DANGER_COLOR);
                vitalSignsChartContainerPanel.add(errorLabel, BorderLayout.CENTER);
                vitalSignsChartContainerPanel.revalidate();
                vitalSignsChartContainerPanel.repaint();
                return null;
            });
    }

    // Procesar dispositivos y actualizar UI
    private void processDevicesForVitalSigns(JsonArray devicesArray) {
        patientDevices.clear();
        chartPanelCache.clear();
        vitalSignsChartContainerPanel.removeAll();

        if (devicesArray == null || devicesArray.size() == 0) {
            deviceInfoLabel.setText("");
            deviceSelector.setVisible(false);
            JLabel noDeviceLabel = new JLabel("<html><div style='text-align:center;padding:40px;'>" +
                    "<b>Sin dispositivos activos</b><br><br>" +
                    "Este paciente no tiene dispositivos asignados o<br>" +
                    "ninguno está generando datos actualmente." +
                    "</div></html>");
            noDeviceLabel.setHorizontalAlignment(SwingConstants.CENTER);
            noDeviceLabel.setFont(new Font("Segoe UI", Font.PLAIN, 14));
            noDeviceLabel.setForeground(TEXT_SECONDARY_COLOR);
            vitalSignsChartContainerPanel.add(noDeviceLabel, BorderLayout.CENTER);
            vitalSignsChartContainerPanel.revalidate();
            vitalSignsChartContainerPanel.repaint();
            return;
        }

        // Parsear dispositivos
        for (JsonElement element : devicesArray) {
            if (!element.isJsonObject()) continue;
            JsonObject deviceObj = element.getAsJsonObject();

            DeviceInfo device = new DeviceInfo();
            device.id = deviceObj.has("id") ? deviceObj.get("id").getAsString() : null;
            device.serial = deviceObj.has("serial") ? deviceObj.get("serial").getAsString() : "N/A";
            device.brand = deviceObj.has("brand") && !deviceObj.get("brand").isJsonNull()
                    ? deviceObj.get("brand").getAsString() : null;
            device.model = deviceObj.has("model") && !deviceObj.get("model").isJsonNull()
                    ? deviceObj.get("model").getAsString() : null;

            JsonObject deviceType = deviceObj.has("device_type") && deviceObj.get("device_type").isJsonObject()
                    ? deviceObj.getAsJsonObject("device_type")
                    : null;
            device.typeLabel = deviceType != null ? (deviceType.has("label") ? deviceType.get("label").getAsString() : null) : null;

            JsonObject stream = deviceObj.has("stream") && deviceObj.get("stream").isJsonObject()
                    ? deviceObj.getAsJsonObject("stream")
                    : null;
            device.hasActiveStream = stream != null && stream.has("is_active") && stream.get("is_active").getAsBoolean();

            // Incluir todos los dispositivos del paciente (con o sin stream activo)
            patientDevices.add(device);
        }

        if (patientDevices.size() == 1) {
            DeviceInfo device = patientDevices.get(0);
            deviceInfoLabel.setText("📱 " + device.getShortInfo());
            deviceSelector.setVisible(false);
            loadChartsForDevice(device);
        } else {
            deviceSelector.removeAllItems();
            for (DeviceInfo device : patientDevices) {
                deviceSelector.addItem(device.getDisplayName());
            }
            deviceSelector.setVisible(true);
            if (deviceSelector.getItemCount() > 0) {
                DeviceInfo firstDevice = patientDevices.get(0);
                deviceInfoLabel.setText("📱 " + firstDevice.getShortInfo());
                deviceSelector.setSelectedIndex(0);
                loadChartsForDevice(firstDevice);
            }
        }
        vitalSignsChartContainerPanel.revalidate();
        vitalSignsChartContainerPanel.repaint();
    }

    // Callback cuando se selecciona un dispositivo del combo box
    private void onDeviceSelected() {
        int selectedIndex = deviceSelector.getSelectedIndex();
        if (selectedIndex >= 0 && selectedIndex < patientDevices.size()) {
            DeviceInfo selectedDevice = patientDevices.get(selectedIndex);
            if (chartPanel != null && chartPanelCache.containsKey(selectedDevice.id)) {
                VitalSignsChartPanel existingPanel = chartPanelCache.get(selectedDevice.id);
                if (existingPanel == chartPanel) {
                    deviceInfoLabel.setText("📱 " + selectedDevice.getShortInfo());
                    return;
                }
            }
            deviceInfoLabel.setText("📱 " + selectedDevice.getShortInfo());
            loadChartsForDevice(selectedDevice);
        }
    }

    // Carga las gráficas para un dispositivo específico (con caché para rendimiento)
    private void loadChartsForDevice(DeviceInfo device) {
        if (chartPanel != null) {
            vitalSignsChartContainerPanel.remove(chartPanel);
        }
        VitalSignsChartPanel cachedPanel = chartPanelCache.get(device.id);
        if (cachedPanel != null) {
            chartPanel = cachedPanel;
            vitalSignsChartContainerPanel.add(chartPanel, BorderLayout.CENTER);
            vitalSignsChartContainerPanel.revalidate();
            vitalSignsChartContainerPanel.repaint();
        } else {
            JPanel loadingPanel = new JPanel(new BorderLayout());
            loadingPanel.setOpaque(false);
            JLabel loadingLabel = new JLabel("<html><div style='text-align:center;padding:40px;'>" +
                    "<b style='font-size:16px;'>📈 Cargando gráficas...</b><br><br>" +
                    "<span style='color:#64748b;'>Obteniendo datos de " + device.serial + "</span>" +
                    "</div></html>");
            loadingLabel.setHorizontalAlignment(SwingConstants.CENTER);
            loadingLabel.setFont(new Font("Segoe UI", Font.PLAIN, 14));
            loadingPanel.add(loadingLabel, BorderLayout.CENTER);
            vitalSignsChartContainerPanel.add(loadingPanel, BorderLayout.CENTER);
            vitalSignsChartContainerPanel.revalidate();
            vitalSignsChartContainerPanel.repaint();

            SwingWorker<VitalSignsChartPanel, Void> chartWorker = new SwingWorker<>() {
                @Override
                protected VitalSignsChartPanel doInBackground() throws Exception {
                    return new VitalSignsChartPanel(patientId, device.id, apiClient, 10);
                }
                @Override
                protected void done() {
                    try {
                        VitalSignsChartPanel newPanel = get();
                        vitalSignsChartContainerPanel.remove(loadingPanel);
                        chartPanel = newPanel;
                        chartPanelCache.put(device.id, chartPanel);
                        vitalSignsChartContainerPanel.add(chartPanel, BorderLayout.CENTER);
                        vitalSignsChartContainerPanel.revalidate();
                        vitalSignsChartContainerPanel.repaint();
                        SwingUtilities.invokeLater(() -> chartPanel.startDataLoading());
                    } catch (Exception e) {
                        vitalSignsChartContainerPanel.remove(loadingPanel);
                        JLabel errorLabel = new JLabel("<html><div style='text-align:center;padding:40px;'>" +
                                "<b style='color:#dc3545;font-size:16px;'>Error al cargar gráficas</b><br><br>" +
                                "<span style='color:#64748b;'>" + e.getMessage() + "</span>" +
                                "</div></html>");
                        errorLabel.setHorizontalAlignment(SwingConstants.CENTER);
                        vitalSignsChartContainerPanel.add(errorLabel, BorderLayout.CENTER);
                        vitalSignsChartContainerPanel.revalidate();
                        vitalSignsChartContainerPanel.repaint();
                    }
                }
            };
            chartWorker.execute();
        }
    }
}

