package com.heartguard.desktop.ui;

import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import javafx.application.Platform;
import javafx.embed.swing.JFXPanel;
import javafx.scene.Scene;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.MatteBorder;
import java.awt.*;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutionException;
import netscape.javascript.JSObject;

/**
 * Panel de dashboard para pacientes
 * Muestra información personal, estadísticas, alertas recientes y equipo de cuidado
 */
public class PatientDashboardPanel extends JPanel {
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
    private OpenStreetMapPanel mapPanel;

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

        // Sección 3: Alertas Recientes
        panel.add(createAlertsSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 4: Equipo de Cuidado
        panel.add(createCareTeamSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 5: Cuidadores (Caregivers)
        panel.add(createCaregiversSection());
        panel.add(Box.createVerticalStrut(SECTION_SPACING));

        // Sección 6: Ubicación Reciente
        panel.add(createLocationSection());

        return panel;
    }

    private JPanel createProfileSection() {
        JPanel content = new JPanel(new GridLayout(0, 2, 18, 18));
        content.setOpaque(false);

        nameLabel = createInfoValueLabel("--");
        emailLabel = createInfoValueLabel("--");
        birthdateLabel = createInfoValueLabel("--");
        riskLevelLabel = createInfoValueLabel("--");
        riskLevelLabel.setFont(new Font("Segoe UI", Font.BOLD, 15));
        orgLabel = createInfoValueLabel("--");

        content.add(createFieldLabel("Nombre"));
        content.add(nameLabel);
        content.add(createFieldLabel("Email"));
        content.add(emailLabel);
        content.add(createFieldLabel("Fecha de Nacimiento"));
        content.add(birthdateLabel);
        content.add(createFieldLabel("Nivel de Riesgo"));
        content.add(riskLevelLabel);
        content.add(createFieldLabel("Organización"));
        content.add(orgLabel);

        return createCardSection("👤 Información Personal", content);
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
        mapPanel = new OpenStreetMapPanel();
        mapPanel.setPreferredSize(new Dimension(900, 500));

        return createCardSection("🗺️ Ubicaciones del Paciente", mapPanel, mapPanel.getStatusDisplay());
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
        System.out.println("DEBUG: updateLocationsSection llamado");
        if (locationsResponse == null || !locationsResponse.has("locations")) {
            System.out.println("DEBUG: locationsResponse es null o no tiene 'locations'");
            // No hay ubicaciones disponibles - mostrar mensaje en el mapa
            if (mapPanel != null) {
                mapPanel.showNoDataMessage();
            }
            return;
        }

        JsonArray locations = locationsResponse.getAsJsonArray("locations");
        System.out.println("DEBUG: Cantidad de ubicaciones: " + locations.size());

        if (locations.size() == 0) {
            if (mapPanel != null) {
                mapPanel.showNoDataMessage();
            }
            return;
        }

        // Actualizar el mapa con todas las ubicaciones
        if (mapPanel != null) {
            mapPanel.updateLocations(locations);
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

        cardWrapper.add(infoPanel, BorderLayout.CENTER);

        return cardWrapper;
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

    /**
     * Panel con mapa usando JavaFX WebView y Leaflet.js
     */
    private static class OpenStreetMapPanel extends JPanel {
        private static final Dimension DEFAULT_MAP_SIZE = new Dimension(900, 500);

        private final JLabel statusLabel;
        private final JFXPanel jfxPanel;

        private WebEngine webEngine;
        private volatile boolean mapReady = false;
        private volatile String pendingLocationsJson = null;

        OpenStreetMapPanel() {
            setLayout(new BorderLayout());
            setOpaque(false);

            statusLabel = buildStatusLabel();

            jfxPanel = new JFXPanel();
            jfxPanel.setPreferredSize(DEFAULT_MAP_SIZE);
            add(jfxPanel, BorderLayout.CENTER);

            jfxPanel.addComponentListener(new ComponentAdapter() {
                @Override
                public void componentResized(ComponentEvent e) {
                    if (!mapReady) {
                        return;
                    }
                    Platform.runLater(() -> {
                        try {
                            if (webEngine != null) {
                                webEngine.executeScript("if (window && typeof window.forceResize === 'function') { window.forceResize(); }");
                            }
                        } catch (Exception ex) {
                            System.err.println("[MAP] Error forcing resize: " + ex.getMessage());
                        }
                    });
                }
            });

            Platform.runLater(this::initializeWebView);
        }

        private JLabel buildStatusLabel() {
            JLabel label = new JLabel("Cargando mapa...");
            label.setFont(CAPTION_FONT);
            label.setForeground(PRIMARY_DARK);
            label.setBorder(new CompoundBorder(
                    new MatteBorder(1, 1, 1, 1, NEUTRAL_BORDER_COLOR),
                    new EmptyBorder(6, 12, 6, 12)
            ));
            label.setOpaque(true);
            label.setBackground(new Color(235, 246, 255));
            return label;
        }

        public JLabel getStatusDisplay() {
            return statusLabel;
        }

        private void initializeWebView() {
            WebView webView = new WebView();
            webView.setContextMenuEnabled(false);

            webEngine = webView.getEngine();
            webEngine.setJavaScriptEnabled(true);
            webEngine.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");

            webEngine.getLoadWorker().stateProperty().addListener((obs, oldState, newState) -> {
                switch (newState) {
                    case SUCCEEDED -> {
                        mapReady = true;
                        SwingUtilities.invokeLater(() -> statusLabel.setText("Mapa listo. Esperando datos..."));
                        String payload = pendingLocationsJson != null ? pendingLocationsJson : "[]";
                        pendingLocationsJson = null;
                        sendLocationsJson(payload);
                    }
                    case FAILED -> {
                        Throwable exception = webEngine.getLoadWorker().getException();
                        System.err.println("[MAP] Error al cargar el mapa" + (exception != null ? ": " + exception.getMessage() : ""));
                        if (exception != null) {
                            exception.printStackTrace();
                        }
                        SwingUtilities.invokeLater(() -> statusLabel.setText("No se pudo cargar el mapa."));
                    }
                    default -> {
                    }
                }
            });

            webEngine.loadContent(generateLeafletHtml());

            Scene scene = new Scene(webView);
            jfxPanel.setScene(scene);
        }

        public void showNoDataMessage() {
            SwingUtilities.invokeLater(() -> statusLabel.setText("Sin ubicaciones recientes."));
            Platform.runLater(() -> {
                try {
                    if (webEngine != null) {
                        JSObject windowObject = (JSObject) webEngine.executeScript("window");
                        if (windowObject != null) {
                            windowObject.call("clearLocations");
                        }
                    }
                } catch (Exception ex) {
                    System.err.println("[MAP] Error limpiando ubicaciones: " + ex.getMessage());
                }
            });
        }

        public void updateLocations(JsonArray locations) {
            if (locations == null || locations.size() == 0) {
                showNoDataMessage();
                return;
            }

            SwingUtilities.invokeLater(() -> statusLabel.setText("Mostrando " + locations.size() + " ubicaciones."));
            sendLocationsJson(locations.toString());
        }

        private void sendLocationsJson(String locationsJson) {
            if (!mapReady || webEngine == null) {
                pendingLocationsJson = locationsJson;
                return;
            }

            final String payload = locationsJson == null ? "[]" : locationsJson;
            Platform.runLater(() -> {
                try {
                    JSObject windowObject = (JSObject) webEngine.executeScript("window");
                    if (windowObject != null) {
                        windowObject.call("renderLocationsFromJava", payload);
                    }
                } catch (Exception ex) {
                    System.err.println("[MAP] Error enviando ubicaciones: " + ex.getMessage());
                    ex.printStackTrace();
                }
            });
        }

        private String generateLeafletHtml() {
            return """
                    <!DOCTYPE html>
                    <html lang=\"es\">
                    <head>
                        <meta charset=\"utf-8\" />
                        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, user-scalable=no\" />
                        <meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\" />
                        <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css\" crossorigin=\"anonymous\" />
                        <style>
                            * { margin: 0; padding: 0; box-sizing: border-box; }
                            html, body { height: 100%; width: 100%; background: #f8fafc; font-family: 'Segoe UI', Arial, sans-serif; }
                            #map-container { position: relative; height: 100%; width: 100%; }
                            #map { height: 100%; width: 100%; background: #e5e7eb; }
                            #no-data-banner { position: absolute; inset: 0; display: none; align-items: center; justify-content: center; background: rgba(255,255,255,0.92); color: #455A64; font-size: 16px; font-weight: bold; z-index: 500; }
                            .leaflet-container { background: #e5e7eb; }
                            .leaflet-tile-container { opacity: 1; }
                            .leaflet-tile { opacity: 1 !important; image-rendering: optimizeQuality; transition: opacity 0.25s ease-out; will-change: transform; }
                            .leaflet-zoom-animated { will-change: transform; }
                            .fallback-pane img { opacity: 0.55; filter: saturate(0.85) brightness(1.08); image-rendering: optimizeSpeed; }
                            .location-badge { pointer-events: none; }
                            .location-badge .badge { border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; box-shadow: 0 2px 6px rgba(0,0,0,0.25); }
                            .location-badge .badge.latest { background: #2E7D32; border: 3px solid #fff; width: 30px; height: 30px; font-size: 16px; }
                            .location-badge .badge.history { background: #1565C0; border: 2px solid #fff; width: 26px; height: 26px; font-size: 13px; }
                            .popup { font-size: 13px; min-width: 230px; }
                            .popup table { width: 100%; border-collapse: collapse; }
                            .popup td { padding: 3px 4px; vertical-align: top; }
                            .popup tr td:first-child { font-weight: 600; color: #424242; }
                        </style>
                    </head>
                    <body>
                        <div id=\"map-container\">
                            <div id=\"map\"></div>
                            <div id=\"no-data-banner\">Sin ubicaciones para mostrar</div>
                        </div>
                        <script src=\"https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js\" crossorigin=\"anonymous\"></script>
                        <script>
                            (function(){
                                const DEFAULT_CENTER = [19.4326, -99.1332];
                                const DEFAULT_ZOOM = 12;
                                const latestStyle = { radius: 14, fillColor: '#4CAF50', color: '#1B5E20', weight: 3, fillOpacity: 0.9 };
                                const historyStyle = { radius: 10, fillColor: '#1E88E5', color: '#0D47A1', weight: 2, fillOpacity: 0.72 };

                                const map = L.map('map', {
                                    zoomAnimation: false,
                                    fadeAnimation: false,
                                    markerZoomAnimation: false,
                                    zoomSnap: 1,
                                    zoomDelta: 1,
                                    trackResize: true,
                                    minZoom: 2,
                                    maxZoom: 18,
                                    worldCopyJump: true,
                                    preferCanvas: false,
                                    inertia: false,
                                    zoomControl: true
                                }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

                                const fallbackPane = map.createPane('fallbackPane');
                                fallbackPane.style.zIndex = '200';
                                const primaryPane = map.getPane('tilePane');
                                primaryPane.style.zIndex = '310';

                                const fallbackLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                                    attribution: '',
                                    pane: 'fallbackPane',
                                    maxZoom: 18,
                                    maxNativeZoom: 6,
                                    minZoom: 0,
                                    tileSize: 256,
                                    keepBuffer: 1,
                                    updateWhenIdle: true,
                                    updateWhenZooming: false,
                                    reuseTiles: true,
                                    detectRetina: false,
                                    opacity: 1,
                                    bounds: [[-90, -180], [90, 180]],
                                    noWrap: false,
                                    crossOrigin: 'anonymous'
                                }).addTo(map);

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
                                    crossOrigin: 'anonymous'
                                }).addTo(map);

                                const tileRetry = new Map();
                                tileLayer.on('loading', () => tileRetry.clear());
                                tileLayer.on('tileloadstart', e => { if (e.tile) { e.tile.style.opacity = '0'; } });
                                tileLayer.on('tileload', e => {
                                    if (e.tile) {
                                        requestAnimationFrame(() => {
                                            e.tile.style.transition = 'opacity 120ms ease-out';
                        
                                            e.tile.style.opacity = '1';
                                        });
                                    }
                                });
                                tileLayer.on('tileerror', (e) => {
                                    const url = (e.tile && e.tile.src) ? e.tile.src : '';
                                    const count = tileRetry.get(url) || 0;
                                    if (count >= 2) {
                                        console.warn('[MAP] Tile abandonado tras reintentos:', url);
                                        return;
                                    }
                                    const delay = count === 0 ? 600 : 1600;
                                    setTimeout(() => {
                                        try {
                                            if (e.tile) {
                                                const base = url.split('#')[0];
                                                const sep = base.includes('?') ? '&' : '?';
                                                const newUrl = base + sep + 'retry=' + (count + 1) + '&ts=' + Date.now();
                                                e.tile.src = newUrl;
                                                tileRetry.set(url, count + 1);
                                                tileRetry.set(newUrl, count + 1);
                                            }
                                        } catch (err) {
                                            console.error('[MAP] Error reintentando tile:', err);
                                        }
                                    }, delay);
                                });

                                const noDataBanner = document.getElementById('no-data-banner');
                                const markersLayer = L.layerGroup().addTo(map);
                                const overlayLayer = L.layerGroup().addTo(map);
                                const pathLayer = L.polyline([], { color: '#1976D2', weight: 3, opacity: 0.65, dashArray: '8,4' }).addTo(map);

                                let hasInitialBounds = false;
                                let resizeTimer = null;

                                const showNoData = (show) => {
                                    if (noDataBanner) {
                                        noDataBanner.style.display = show ? 'flex' : 'none';
                                    }
                                };

                                const scheduleResize = (delay = 150) => {
                                    if (map._animatingZoom) {
                                        if (resizeTimer) clearTimeout(resizeTimer);
                                        resizeTimer = setTimeout(() => scheduleResize(delay), 140);
                                        return;
                                    }
                                    if (resizeTimer) clearTimeout(resizeTimer);
                                    resizeTimer = setTimeout(() => {
                                        try {
                                            map.invalidateSize({ animate: false, pan: false, debounceMoveend: true });
                                        } catch (err) {
                                            console.error('[MAP] Error en scheduleResize:', err);
                                        }
                                    }, delay);
                                };

                                map.on('zoomstart', () => {
                                    if (resizeTimer) {
                                        clearTimeout(resizeTimer);
                                        resizeTimer = null;
                                    }
                                });
                                map.on('zoomend', () => scheduleResize(160));
                                map.on('moveend', () => scheduleResize(180));

                                const isValidNumber = value => typeof value === 'number' && !Number.isNaN(value);
                                const formatTimestamp = value => {
                                    if (!value) return 'N/A';
                                    const date = new Date(value);
                                    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
                                };
                                const formatAccuracy = value => typeof value === 'number' ? value.toFixed(2) + ' m' : 'N/A';

                                const buildPopupHtml = (loc, isLatest, order) => {
                                    const titleColor = isLatest ? '#2E7D32' : '#1565C0';
                                    const title = isLatest ? 'Ubicación más reciente' : 'Ubicación #' + order;
                                    const rows = [
                                        ['Latitud', loc.latitude.toFixed(6)],
                                        ['Longitud', loc.longitude.toFixed(6)],
                                        ['Fecha/Hora', formatTimestamp(loc.timestamp)],
                                        ['Fuente', loc.source || 'desconocida'],
                                        ['Precisión', formatAccuracy(loc.accuracy_meters)]
                                    ];
                                    let html = `<div class='popup'><h3 style='margin:0 0 8px 0; color:${titleColor}; font-size:15px;'>${title}</h3><table>`;
                                    rows.forEach(row => { html += `<tr><td>${row[0]}</td><td>${row[1]}</td></tr>`; });
                                    html += '</table></div>';
                                    return html;
                                };

                                const render = (locations) => {
                                    markersLayer.clearLayers();
                                    overlayLayer.clearLayers();
                                    pathLayer.setLatLngs([]);

                                    if (!Array.isArray(locations) || locations.length === 0) {
                                        showNoData(true);
                                        hasInitialBounds = false;
                                        map.setView(DEFAULT_CENTER, DEFAULT_ZOOM, { animate: false });
                                        scheduleResize(180);
                                        return;
                                    }

                                    const validLocations = locations.filter(loc => loc && isValidNumber(loc.latitude) && isValidNumber(loc.longitude));
                                    if (validLocations.length === 0) {
                                        showNoData(true);
                                        hasInitialBounds = false;
                                        map.setView(DEFAULT_CENTER, DEFAULT_ZOOM, { animate: false });
                                        scheduleResize(180);
                                        return;
                                    }

                                    showNoData(false);
                                    validLocations.sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0));

                                    const latLngs = [];
                                    validLocations.forEach((loc, index) => {
                                        const latLng = [loc.latitude, loc.longitude];
                                        latLngs.push(latLng);
                                        const isLatest = index === 0;
                                        const marker = L.circleMarker(latLng, isLatest ? latestStyle : historyStyle).addTo(markersLayer);
                                        marker.bindPopup(buildPopupHtml(loc, isLatest, index + 1));

                                        const badgeHtml = `<div class='badge ${isLatest ? "latest" : "history"}'>${index + 1}</div>`;
                                        L.marker(latLng, {
                                            icon: L.divIcon({ className: 'location-badge', html: badgeHtml, iconSize: isLatest ? [30, 30] : [26, 26] })
                                        }).addTo(overlayLayer);
                                    });

                                    if (latLngs.length > 1) {
                                        pathLayer.setLatLngs(latLngs);
                                    }

                                    if (!hasInitialBounds) {
                                        hasInitialBounds = true;
                                        if (latLngs.length === 1) {
                                            map.setView(latLngs[0], 15, { animate: false });
                                        } else {
                                            const bounds = L.latLngBounds(latLngs);
                                            map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16, animate: false });
                                        }
                                        scheduleResize(200);
                                    } else {
                                        scheduleResize(160);
                                    }
                                };

                                window.renderLocationsFromJava = payload => {
                                    try {
                                        const data = JSON.parse(payload || '[]');
                                        render(data);
                                    } catch (err) {
                                        console.error('[MAP] Error parseando ubicaciones', err);
                                        showNoData(true);
                                    }
                                };

                                window.forceResize = () => scheduleResize(140);
                                window.clearLocations = () => {
                                    markersLayer.clearLayers();
                                    overlayLayer.clearLayers();
                                    pathLayer.setLatLngs([]);
                                    showNoData(true);
                                    hasInitialBounds = false;
                                    map.setView(DEFAULT_CENTER, DEFAULT_ZOOM, { animate: false });
                                    scheduleResize(180);
                                };

                                render([]);
                            })();
                        </script>
                    </body>
                    </html>
                    """;
        }
    }
}
