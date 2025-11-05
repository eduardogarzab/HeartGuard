package com.heartguard.desktop.ui;

import com.heartguard.desktop.api.ApiClient;
import com.google.gson.JsonArray;
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
        // Usar SwingWorker para operaciones en segundo plano
        SwingWorker<Void, Void> worker = new SwingWorker<Void, Void>() {
            private JsonObject dashboard;
            private JsonObject locationsResponse;
            private Exception dashboardError;
            private Exception locationsError;

            @Override
            protected Void doInBackground() throws Exception {
                // Cargar dashboard
                try {
                    dashboard = apiClient.getPatientDashboard(accessToken);
                } catch (Exception e) {
                    dashboardError = e;
                    System.err.println("Error al cargar dashboard: " + e.getMessage());
                }

                // Cargar ubicaciones
                try {
                    locationsResponse = apiClient.getPatientLocations(accessToken, 6);
                    System.out.println("DEBUG: Ubicaciones cargadas exitosamente");
                    if (locationsResponse != null) {
                        System.out.println("DEBUG: Respuesta de ubicaciones: " + locationsResponse.toString());
                    }
                } catch (Exception e) {
                    locationsError = e;
                    System.err.println("Error al cargar ubicaciones: " + e.getMessage());
                    e.printStackTrace();
                }

                return null;
            }

            @Override
            protected void done() {
                try {
                    if (dashboard != null) {
                        // Actualizar información personal
                        updateProfileSection(dashboard.getAsJsonObject("patient"));

                        // Actualizar estadísticas
                        updateStatsSection(dashboard.getAsJsonObject("stats"));

                        // Actualizar alertas recientes
                        updateAlertsSection(dashboard.getAsJsonArray("recent_alerts"));

                        // Actualizar equipo de cuidado
                        updateCareTeamSection(dashboard.getAsJsonArray("care_team"));

                        // Actualizar cuidadores
                        updateCaregiversSection(dashboard.getAsJsonArray("caregivers"));
                    } else if (dashboardError != null) {
                        JOptionPane.showMessageDialog(
                                PatientDashboardPanel.this,
                                "Error al cargar dashboard: " + dashboardError.getMessage(),
                                "Error",
                                JOptionPane.ERROR_MESSAGE
                        );
                    }

                    if (locationsResponse != null) {
                        // Actualizar ubicaciones
                        updateLocationsSection(locationsResponse);
                    } else if (locationsError != null) {
                        // Si falla, mostrar mensaje en el panel de ubicaciones
                        System.err.println("No se pudieron cargar las ubicaciones: " + locationsError.getMessage());
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
        };

        worker.execute();
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

        if (alerts.size() == 0) {
            JPanel emptyState = new JPanel(new FlowLayout(FlowLayout.CENTER));
            emptyState.setOpaque(false);
            JLabel noAlerts = new JLabel("No hay alertas recientes");
            noAlerts.setFont(BODY_FONT.deriveFont(Font.ITALIC, 14f));
            noAlerts.setForeground(TEXT_SECONDARY_COLOR);
            emptyState.add(noAlerts);
            alertsPanel.add(emptyState);
        } else {
            for (int i = 0; i < alerts.size(); i++) {
                JsonObject alert = alerts.get(i).getAsJsonObject();
                JPanel alertCard = createAlertCard(alert);
                alertCard.setMaximumSize(new Dimension(Integer.MAX_VALUE, alertCard.getPreferredSize().height));
                alertsPanel.add(alertCard);
                if (i < alerts.size() - 1) {
                    alertsPanel.add(Box.createVerticalStrut(12));
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

        if (teams.size() == 0) {
            JLabel noTeam = new JLabel("No hay equipo de cuidado asignado");
            noTeam.setFont(BODY_FONT.deriveFont(Font.ITALIC, 14f));
            noTeam.setForeground(TEXT_SECONDARY_COLOR);
            careTeamPanel.add(noTeam);
        } else {
            for (int i = 0; i < teams.size(); i++) {
                JsonObject team = teams.get(i).getAsJsonObject();
                JPanel teamPanel = createTeamPanel(team);
                careTeamPanel.add(teamPanel);
                if (i < teams.size() - 1) {
                    careTeamPanel.add(Box.createVerticalStrut(15));
                }
            }
        }

        careTeamPanel.revalidate();
        careTeamPanel.repaint();
    }

    private void updateCaregiversSection(JsonArray caregivers) {
        caregiversPanel.removeAll();

        if (caregivers.size() == 0) {
            JLabel noCaregivers = new JLabel("No hay cuidadores asignados");
            noCaregivers.setFont(BODY_FONT.deriveFont(Font.ITALIC, 14f));
            noCaregivers.setForeground(TEXT_SECONDARY_COLOR);
            caregiversPanel.add(noCaregivers);
        } else {
            for (int i = 0; i < caregivers.size(); i++) {
                JsonObject caregiver = caregivers.get(i).getAsJsonObject();
                JPanel caregiverPanel = createCaregiverPanel(caregiver);
                caregiversPanel.add(caregiverPanel);
                if (i < caregivers.size() - 1) {
                    caregiversPanel.add(Box.createVerticalStrut(10));
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

    JLabel teamNameLabel = new JLabel(team.get("team_name").getAsString());
    teamNameLabel.setFont(new Font("Segoe UI", Font.BOLD, 15));
    teamNameLabel.setForeground(PRIMARY_DARK);
    panel.add(teamNameLabel);
    panel.add(Box.createVerticalStrut(10));

        JsonArray members = team.getAsJsonArray("members");
        for (int i = 0; i < members.size(); i++) {
            JsonObject member = members.get(i).getAsJsonObject();
            JPanel memberPanel = createMemberPanel(member);
            panel.add(memberPanel);
            if (i < members.size() - 1) {
                panel.add(Box.createVerticalStrut(5));
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

    private void viewAllAlerts() {
        SwingWorker<JsonArray, Void> worker = new SwingWorker<JsonArray, Void>() {
            private Exception error;

            @Override
            protected JsonArray doInBackground() throws Exception {
                try {
                    JsonObject response = apiClient.getPatientAlerts(accessToken, 100);
                    if (response != null && response.has("alerts")) {
                        return response.getAsJsonArray("alerts");
                    }
                    return new JsonArray();
                } catch (Exception e) {
                    error = e;
                    System.err.println("Error al cargar todas las alertas: " + e.getMessage());
                    return new JsonArray();
                }
            }

            @Override
            protected void done() {
                try {
                    JsonArray allAlerts = get();
                    if (error != null) {
                        JOptionPane.showMessageDialog(
                                PatientDashboardPanel.this,
                                "Error al cargar las alertas: " + error.getMessage(),
                                "Error",
                                JOptionPane.ERROR_MESSAGE
                        );
                        return;
                    }
                    showAllAlertsDialog(allAlerts);
                } catch (Exception e) {
                    e.printStackTrace();
                    JOptionPane.showMessageDialog(
                            PatientDashboardPanel.this,
                            "Error inesperado al mostrar alertas",
                            "Error",
                            JOptionPane.ERROR_MESSAGE
                    );
                }
            }
        };
        worker.execute();
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
        JOptionPane.showMessageDialog(
                this,
                "Funcionalidad en desarrollo: Ver dispositivos",
                "Próximamente",
                JOptionPane.INFORMATION_MESSAGE
        );
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
            webEngine = webView.getEngine();
            webEngine.setJavaScriptEnabled(true);

            webEngine.getLoadWorker().stateProperty().addListener((obs, oldState, newState) -> {
                if (newState == javafx.concurrent.Worker.State.SUCCEEDED) {
                    mapReady = true;
                    SwingUtilities.invokeLater(() -> statusLabel.setText("Mapa listo. Esperando datos..."));
                    if (pendingLocationsJson != null) {
                        String payload = pendingLocationsJson;
                        pendingLocationsJson = null;
                        sendLocationsJson(payload);
                    } else {
                        sendLocationsJson("[]");
                    }
                } else if (newState == javafx.concurrent.Worker.State.FAILED) {
                    Throwable exception = webEngine.getLoadWorker().getException();
                    System.err.println("[MAP] Error al cargar el mapa" + (exception != null ? ": " + exception.getMessage() : ""));
                    if (exception != null) {
                        exception.printStackTrace();
                    }
                    SwingUtilities.invokeLater(() -> statusLabel.setText("No se pudo cargar el mapa."));
                }
            });

            webEngine.loadContent(generateLeafletHtml());

            Scene scene = new Scene(webView);
            jfxPanel.setScene(scene);
        }

        public void showNoDataMessage() {
            SwingUtilities.invokeLater(() -> statusLabel.setText("Sin ubicaciones recientes."));
            sendLocationsJson("[]");
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
            StringBuilder html = new StringBuilder();
            html.append("<!DOCTYPE html>");
            html.append("<html><head>");
            html.append("<meta charset='utf-8'/>");
            html.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>");
            html.append("<link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'");
            html.append(" integrity='sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=' crossorigin='' />");
            html.append("<script src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'");
            html.append(" integrity='sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=' crossorigin=''></script>");
            html.append("<style>");
            html.append("html, body { height: 100%; width: 100%; margin: 0; font-family: Arial, sans-serif; }");
            html.append("#map-container { position: relative; height: 100%; width: 100%; }");
            html.append("#map { height: 100%; width: 100%; }");
            html.append(".location-badge { pointer-events: none; }");
            html.append(".location-badge .badge { border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }");
            html.append(".location-badge .badge.latest { background: #2E7D32; border: 3px solid #fff; width: 30px; height: 30px; font-size: 16px; }");
            html.append(".location-badge .badge.historic { background: #1565C0; border: 2px solid #fff; width: 26px; height: 26px; font-size: 13px; }");
            html.append(".popup { font-size: 13px; min-width: 220px; }");
            html.append(".popup table { width: 100%; border-collapse: collapse; }");
            html.append(".popup td { padding: 3px 4px; vertical-align: top; }");
            html.append(".popup tr td:first-child { font-weight: bold; color: #424242; }");
            html.append("#no-data-banner { position: absolute; inset: 0; display: none; align-items: center; justify-content: center; background: rgba(255,255,255,0.92); color: #455A64; font-size: 16px; font-weight: bold; z-index: 500; }");
            html.append("</style></head><body>");
            html.append("<div id='map-container'>");
            html.append("<div id='map'></div>");
            html.append("<div id='no-data-banner'>Sin ubicaciones para mostrar</div>");
            html.append("</div>");
            html.append("<script>");
            html.append("(function(){");
            html.append("const DEFAULT_CENTER = [19.4326, -99.1332];");
            html.append("const DEFAULT_ZOOM = 12;");
            html.append("const latestStyle = { radius: 14, fillColor: '#4CAF50', color: '#1B5E20', weight: 3, fillOpacity: 0.9 };");
            html.append("const historyStyle = { radius: 10, fillColor: '#2196F3', color: '#0D47A1', weight: 2, fillOpacity: 0.7 };");
            html.append("const map = L.map('map', { zoomControl: true, attributionControl: true }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);");
            html.append("L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);");
            html.append("const markersLayer = L.layerGroup().addTo(map);");
            html.append("const pathLayer = L.polyline([], { color: '#1976D2', weight: 3, opacity: 0.6, dashArray: '8,4' }).addTo(map);");
            html.append("const noDataBanner = document.getElementById('no-data-banner');");
            html.append("function showNoData(show){ if (noDataBanner){ noDataBanner.style.display = show ? 'flex' : 'none'; } }");
            html.append("function isValidNumber(value){ return typeof value === 'number' && !isNaN(value); }");
            html.append("function formatTimestamp(value){ if(!value){ return 'N/A'; } const date = new Date(value); if(isNaN(date.getTime())){ return value; } return date.toLocaleString(); }");
            html.append("function formatAccuracy(value){ return typeof value === 'number' ? value.toFixed(2) + ' m' : 'N/A'; }");
            html.append("function buildPopupHtml(loc, isLatest, order){ const titleColor = isLatest ? '#2E7D32' : '#1565C0'; const title = isLatest ? 'Ubicación más reciente' : 'Ubicación #' + order; const rows = [ ['Latitud', loc.latitude.toFixed(6)], ['Longitud', loc.longitude.toFixed(6)], ['Fecha/Hora', formatTimestamp(loc.timestamp)], ['Fuente', loc.source || 'desconocida'], ['Precisión', formatAccuracy(loc.accuracy_meters)] ]; let html = '<div class=\'popup\'>' + '<h3 style=\'margin:0 0 8px 0; color:' + titleColor + '; font-size:15px;\'>' + title + '</h3>' + '<table>'; rows.forEach(function(row){ html += '<tr><td>' + row[0] + '</td><td>' + row[1] + '</td></tr>'; }); html += '</table></div>'; return html; }");
            html.append("function render(locations){ markersLayer.clearLayers(); pathLayer.setLatLngs([]); if(!Array.isArray(locations) || locations.length === 0){ showNoData(true); map.setView(DEFAULT_CENTER, DEFAULT_ZOOM); return; } const validLocations = locations.filter(function(loc){ return loc && isValidNumber(loc.latitude) && isValidNumber(loc.longitude); }); if(validLocations.length === 0){ showNoData(true); map.setView(DEFAULT_CENTER, DEFAULT_ZOOM); return; } showNoData(false); validLocations.sort(function(a, b){ return new Date(b.timestamp || 0) - new Date(a.timestamp || 0); }); const latLngs = []; validLocations.forEach(function(loc, index){ const latLng = [loc.latitude, loc.longitude]; latLngs.push(latLng); const isLatest = index === 0; const marker = L.circleMarker(latLng, isLatest ? latestStyle : historyStyle).addTo(markersLayer); marker.bindPopup(buildPopupHtml(loc, isLatest, index + 1)); const badgeHtml = isLatest ? '<div class=\"badge latest\">1</div>' : '<div class=\"badge historic\">' + (index + 1) + '</div>'; L.marker(latLng, { icon: L.divIcon({ className: 'location-badge', html: badgeHtml, iconSize: isLatest ? [30, 30] : [26, 26] }) }).addTo(markersLayer); }); if (latLngs.length > 1){ pathLayer.setLatLngs(latLngs); } if (latLngs.length === 1){ map.setView(latLngs[0], 15); } else { map.fitBounds(L.latLngBounds(latLngs), { padding: [40, 40], maxZoom: 16 }); } setTimeout(function(){ map.invalidateSize(); }, 200); }");
            html.append("window.renderLocationsFromJava = function(payload){ try { const data = JSON.parse(payload || '[]'); render(data); } catch (err) { console.error('[MAP] Error parseando ubicaciones', err); showNoData(true); } };");
            html.append("window.forceResize = function(){ setTimeout(function(){ map.invalidateSize(); }, 100); };");
            html.append("render([]);");
            html.append("})();");
            html.append("</script></body></html>");
            return html.toString();
        }
    }
}
