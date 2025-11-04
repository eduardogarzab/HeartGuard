package com.heartguard.desktop.ui;

import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Panel de dashboard para pacientes
 * Muestra información personal, estadísticas, alertas recientes y equipo de cuidado
 */
public class PatientDashboardPanel extends JPanel {
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
    
    public PatientDashboardPanel(ApiClient apiClient, String accessToken, String patientId) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.patientId = patientId;
        
        initComponents();
        loadDashboardData();
    }
    
    private void initComponents() {
        setLayout(new BorderLayout(10, 10));
        setBorder(new EmptyBorder(20, 20, 20, 20));
        
        // Panel de encabezado
        JPanel headerPanel = createHeaderPanel();
        add(headerPanel, BorderLayout.NORTH);
        
        // Panel central con scroll
        JPanel centerPanel = createCenterPanel();
        JScrollPane scrollPane = new JScrollPane(centerPanel);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        scrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        add(scrollPane, BorderLayout.CENTER);
        
        // Panel de acciones
        JPanel actionsPanel = createActionsPanel();
        add(actionsPanel, BorderLayout.SOUTH);
    }
    
    private JPanel createHeaderPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(new Color(41, 128, 185));
        panel.setBorder(new EmptyBorder(20, 20, 20, 20));
        
        JLabel titleLabel = new JLabel("Mi Portal de Salud");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 28));
        titleLabel.setForeground(Color.WHITE);
        
        JButton logoutButton = new JButton("Cerrar Sesión");
        logoutButton.addActionListener(e -> logout());
        
        panel.add(titleLabel, BorderLayout.WEST);
        panel.add(logoutButton, BorderLayout.EAST);
        
        return panel;
    }
    
    private JPanel createCenterPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(Color.WHITE);
        
        // Sección 1: Información Personal
        panel.add(createProfileSection());
        panel.add(Box.createVerticalStrut(20));
        
        // Sección 2: Estadísticas
        panel.add(createStatsSection());
        panel.add(Box.createVerticalStrut(20));
        
        // Sección 3: Alertas Recientes
        panel.add(createAlertsSection());
        panel.add(Box.createVerticalStrut(20));
        
        // Sección 4: Equipo de Cuidado
        panel.add(createCareTeamSection());
        panel.add(Box.createVerticalStrut(20));
        
        // Sección 5: Cuidadores (Caregivers)
        panel.add(createCaregiversSection());
        
        return panel;
    }
    
    private JPanel createProfileSection() {
        JPanel panel = new JPanel(new GridLayout(5, 2, 10, 10));
        panel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(Color.LIGHT_GRAY, 1),
            "Información Personal",
            TitledBorder.LEFT,
            TitledBorder.TOP,
            new Font("Arial", Font.BOLD, 16)
        ));
        panel.setBackground(Color.WHITE);
        
        nameLabel = createInfoLabel("");
        emailLabel = createInfoLabel("");
        birthdateLabel = createInfoLabel("");
        riskLevelLabel = createInfoLabel("");
        orgLabel = createInfoLabel("");
        
        panel.add(new JLabel("Nombre:"));
        panel.add(nameLabel);
        panel.add(new JLabel("Email:"));
        panel.add(emailLabel);
        panel.add(new JLabel("Fecha de Nacimiento:"));
        panel.add(birthdateLabel);
        panel.add(new JLabel("Nivel de Riesgo:"));
        panel.add(riskLevelLabel);
        panel.add(new JLabel("Organización:"));
        panel.add(orgLabel);
        
        return panel;
    }
    
    private JPanel createStatsSection() {
        JPanel panel = new JPanel(new GridLayout(2, 2, 15, 15));
        panel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(Color.LIGHT_GRAY, 1),
            "Resumen de Salud",
            TitledBorder.LEFT,
            TitledBorder.TOP,
            new Font("Arial", Font.BOLD, 16)
        ));
        panel.setBackground(Color.WHITE);
        
        totalAlertsLabel = createStatsLabel("0", "Total de Alertas");
        pendingAlertsLabel = createStatsLabel("0", "Alertas Pendientes");
        devicesCountLabel = createStatsLabel("0", "Dispositivos");
        lastReadingLabel = createStatsLabel("N/A", "Última Lectura");
        
        panel.add(createStatCard(totalAlertsLabel, new Color(52, 152, 219)));
        panel.add(createStatCard(pendingAlertsLabel, new Color(231, 76, 60)));
        panel.add(createStatCard(devicesCountLabel, new Color(46, 204, 113)));
        panel.add(createStatCard(lastReadingLabel, new Color(155, 89, 182)));
        
        return panel;
    }
    
    private JPanel createAlertsSection() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(Color.LIGHT_GRAY, 1),
            "Alertas Recientes",
            TitledBorder.LEFT,
            TitledBorder.TOP,
            new Font("Arial", Font.BOLD, 16)
        ));
        panel.setBackground(Color.WHITE);
        
        alertsPanel = new JPanel();
        alertsPanel.setLayout(new BoxLayout(alertsPanel, BoxLayout.Y_AXIS));
        alertsPanel.setBackground(Color.WHITE);
        
        panel.add(alertsPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createCareTeamSection() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(Color.LIGHT_GRAY, 1),
            "Equipo de Cuidado",
            TitledBorder.LEFT,
            TitledBorder.TOP,
            new Font("Arial", Font.BOLD, 16)
        ));
        panel.setBackground(Color.WHITE);
        
        careTeamPanel = new JPanel();
        careTeamPanel.setLayout(new BoxLayout(careTeamPanel, BoxLayout.Y_AXIS));
        careTeamPanel.setBackground(Color.WHITE);
        
        panel.add(careTeamPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createCaregiversSection() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(Color.LIGHT_GRAY, 1),
            "Cuidadores",
            TitledBorder.LEFT,
            TitledBorder.TOP,
            new Font("Arial", Font.BOLD, 16)
        ));
        panel.setBackground(Color.WHITE);
        
        caregiversPanel = new JPanel();
        caregiversPanel.setLayout(new BoxLayout(caregiversPanel, BoxLayout.Y_AXIS));
        caregiversPanel.setBackground(Color.WHITE);
        
        panel.add(caregiversPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createActionsPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER, 15, 10));
        panel.setBackground(Color.WHITE);
        
        JButton viewAllAlertsBtn = new JButton("Ver Todas las Alertas");
        viewAllAlertsBtn.addActionListener(e -> viewAllAlerts());
        
        JButton viewDevicesBtn = new JButton("Ver Dispositivos");
        viewDevicesBtn.addActionListener(e -> viewDevices());
        
        JButton refreshBtn = new JButton("Actualizar");
        refreshBtn.addActionListener(e -> loadDashboardData());
        
        panel.add(viewAllAlertsBtn);
        panel.add(viewDevicesBtn);
        panel.add(refreshBtn);
        
        return panel;
    }
    
    private JLabel createInfoLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(new Font("Arial", Font.PLAIN, 14));
        return label;
    }
    
    private JLabel createStatsLabel(String value, String description) {
        JLabel label = new JLabel("<html><center><div style='font-size:24px; font-weight:bold;'>" + 
                                   value + "</div><div style='font-size:12px; color:gray;'>" + 
                                   description + "</div></center></html>");
        label.setHorizontalAlignment(SwingConstants.CENTER);
        return label;
    }
    
    private JPanel createStatCard(JLabel label, Color color) {
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(color);
        card.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(color.darker(), 2),
            new EmptyBorder(15, 15, 15, 15)
        ));
        label.setForeground(Color.WHITE);
        card.add(label, BorderLayout.CENTER);
        return card;
    }
    
    private void loadDashboardData() {
        SwingUtilities.invokeLater(() -> {
            try {
                // Llamar al endpoint de dashboard
                JsonObject dashboard = apiClient.getPatientDashboard(accessToken);
                
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
                
            } catch (ApiException e) {
                JOptionPane.showMessageDialog(
                    this,
                    "Error al cargar dashboard: " + e.getMessage(),
                    "Error",
                    JOptionPane.ERROR_MESSAGE
                );
            }
        });
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
        Color color = Color.BLACK;
        if (riskLevel.toLowerCase().contains("bajo")) {
            color = new Color(46, 204, 113);
        } else if (riskLevel.toLowerCase().contains("medio")) {
            color = new Color(241, 196, 15);
        } else if (riskLevel.toLowerCase().contains("alto")) {
            color = new Color(230, 126, 34);
        } else if (riskLevel.toLowerCase().contains("crítico")) {
            color = new Color(231, 76, 60);
        }
        riskLevelLabel.setForeground(color);
        riskLevelLabel.setFont(new Font("Arial", Font.BOLD, 14));
    }
    
    private void updateStatsSection(JsonObject stats) {
        int totalAlerts = stats.get("total_alerts").getAsInt();
        int pendingAlerts = stats.get("pending_alerts").getAsInt();
        int devicesCount = stats.get("devices_count").getAsInt();
        String lastReading = stats.has("last_reading") && !stats.get("last_reading").isJsonNull()
            ? formatDate(stats.get("last_reading").getAsString()) : "N/A";
        
        totalAlertsLabel.setText("<html><center><div style='font-size:24px; font-weight:bold;'>" + 
                                totalAlerts + "</div><div style='font-size:12px;'>Total de Alertas</div></center></html>");
        pendingAlertsLabel.setText("<html><center><div style='font-size:24px; font-weight:bold;'>" + 
                                   pendingAlerts + "</div><div style='font-size:12px;'>Alertas Pendientes</div></center></html>");
        devicesCountLabel.setText("<html><center><div style='font-size:24px; font-weight:bold;'>" + 
                                  devicesCount + "</div><div style='font-size:12px;'>Dispositivos</div></center></html>");
        lastReadingLabel.setText("<html><center><div style='font-size:14px; font-weight:bold;'>" + 
                                lastReading + "</div><div style='font-size:12px;'>Última Lectura</div></center></html>");
    }
    
    private void updateAlertsSection(JsonArray alerts) {
        alertsPanel.removeAll();
        
        if (alerts.size() == 0) {
            JLabel noAlerts = new JLabel("No hay alertas recientes");
            noAlerts.setFont(new Font("Arial", Font.ITALIC, 14));
            noAlerts.setForeground(Color.GRAY);
            alertsPanel.add(noAlerts);
        } else {
            for (int i = 0; i < alerts.size(); i++) {
                JsonObject alert = alerts.get(i).getAsJsonObject();
                JPanel alertCard = createAlertCard(alert);
                alertsPanel.add(alertCard);
                if (i < alerts.size() - 1) {
                    alertsPanel.add(Box.createVerticalStrut(10));
                }
            }
        }
        
        alertsPanel.revalidate();
        alertsPanel.repaint();
    }
    
    private JPanel createAlertCard(JsonObject alert) {
        JPanel card = new JPanel(new BorderLayout(10, 5));
        card.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Color.LIGHT_GRAY, 1),
            new EmptyBorder(10, 10, 10, 10)
        ));
        card.setBackground(new Color(245, 245, 245));
        
        // Nivel y tipo
        String level = alert.get("level_label").getAsString();
        String type = alert.has("type") && !alert.get("type").isJsonNull() 
            ? alert.get("type").getAsString() : "Sin tipo";
        JLabel typeLabel = new JLabel(type + " - " + level);
        typeLabel.setFont(new Font("Arial", Font.BOLD, 14));
        typeLabel.setForeground(getAlertLevelColor(alert.get("level").getAsString()));
        
        // Descripción
        String description = alert.has("description") && !alert.get("description").isJsonNull()
            ? alert.get("description").getAsString() : "Sin descripción";
        JLabel descLabel = new JLabel(description);
        descLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        
        // Fecha
        String createdAt = formatDate(alert.get("created_at").getAsString());
        JLabel dateLabel = new JLabel(createdAt);
        dateLabel.setFont(new Font("Arial", Font.ITALIC, 11));
        dateLabel.setForeground(Color.GRAY);
        
        // Estado
        String status = alert.get("status_label").getAsString();
        JLabel statusLabel = new JLabel("Estado: " + status);
        statusLabel.setFont(new Font("Arial", Font.PLAIN, 11));
        
        JPanel infoPanel = new JPanel();
        infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));
        infoPanel.setBackground(new Color(245, 245, 245));
        infoPanel.add(typeLabel);
        infoPanel.add(Box.createVerticalStrut(5));
        infoPanel.add(descLabel);
        infoPanel.add(Box.createVerticalStrut(5));
        infoPanel.add(dateLabel);
        infoPanel.add(statusLabel);
        
        card.add(infoPanel, BorderLayout.CENTER);
        
        return card;
    }
    
    private Color getAlertLevelColor(String level) {
        switch (level.toLowerCase()) {
            case "low": return new Color(46, 204, 113);
            case "medium": return new Color(241, 196, 15);
            case "high": return new Color(230, 126, 34);
            case "critical": return new Color(231, 76, 60);
            default: return Color.BLACK;
        }
    }
    
    private void updateCareTeamSection(JsonArray teams) {
        careTeamPanel.removeAll();
        
        if (teams.size() == 0) {
            JLabel noTeam = new JLabel("No hay equipo de cuidado asignado");
            noTeam.setFont(new Font("Arial", Font.ITALIC, 14));
            noTeam.setForeground(Color.GRAY);
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
            noCaregivers.setFont(new Font("Arial", Font.ITALIC, 14));
            noCaregivers.setForeground(Color.GRAY);
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
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(52, 152, 219), 2),
            new EmptyBorder(10, 10, 10, 10)
        ));
        panel.setBackground(Color.WHITE);
        
        JLabel teamNameLabel = new JLabel(team.get("team_name").getAsString());
        teamNameLabel.setFont(new Font("Arial", Font.BOLD, 15));
        teamNameLabel.setForeground(new Color(52, 152, 219));
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
        panel.setBackground(Color.WHITE);
        
        String name = member.has("name") && !member.get("name").isJsonNull()
            ? member.get("name").getAsString() : "Sin nombre";
        String role = member.has("role") && !member.get("role").isJsonNull()
            ? member.get("role").getAsString() : "Sin rol";
        String email = member.has("email") && !member.get("email").isJsonNull()
            ? member.get("email").getAsString() : "Sin email";
        
        JLabel nameLabel = new JLabel("• " + name);
        nameLabel.setFont(new Font("Arial", Font.BOLD, 13));
        
        JLabel roleLabel = new JLabel("  Rol: " + role);
        roleLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        roleLabel.setForeground(Color.DARK_GRAY);
        
        JLabel emailLabel = new JLabel("  Email: " + email);
        emailLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        emailLabel.setForeground(Color.GRAY);
        
        panel.add(nameLabel);
        panel.add(roleLabel);
        panel.add(emailLabel);
        
        return panel;
    }
    
    private JPanel createCaregiverPanel(JsonObject caregiver) {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(155, 89, 182), 2),
            new EmptyBorder(10, 10, 10, 10)
        ));
        panel.setBackground(Color.WHITE);
        
        // Nombre con indicador de principal
        String name = caregiver.has("name") && !caregiver.get("name").isJsonNull()
            ? caregiver.get("name").getAsString() : "Sin nombre";
        boolean isPrimary = caregiver.has("is_primary") && caregiver.get("is_primary").getAsBoolean();
        boolean isActive = caregiver.has("active") && caregiver.get("active").getAsBoolean();
        
        String nameText = name + (isPrimary ? " ⭐ Principal" : "");
        JLabel nameLabel = new JLabel(nameText);
        nameLabel.setFont(new Font("Arial", Font.BOLD, 14));
        nameLabel.setForeground(isActive ? new Color(155, 89, 182) : Color.GRAY);
        panel.add(nameLabel);
        panel.add(Box.createVerticalStrut(5));
        
        // Relación
        String relationship = caregiver.has("relationship_label") && !caregiver.get("relationship_label").isJsonNull()
            ? caregiver.get("relationship_label").getAsString() : "Cuidador";
        JLabel relationshipLabel = new JLabel("Relación: " + relationship);
        relationshipLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        relationshipLabel.setForeground(Color.DARK_GRAY);
        panel.add(relationshipLabel);
        
        // Email
        String email = caregiver.has("email") && !caregiver.get("email").isJsonNull()
            ? caregiver.get("email").getAsString() : "Sin email";
        JLabel emailLabel = new JLabel("Email: " + email);
        emailLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        emailLabel.setForeground(Color.GRAY);
        panel.add(emailLabel);
        
        // Estado
        String status = isActive ? "✓ Activo" : "✗ Inactivo";
        JLabel statusLabel = new JLabel("Estado: " + status);
        statusLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        statusLabel.setForeground(isActive ? new Color(46, 204, 113) : new Color(231, 76, 60));
        panel.add(statusLabel);
        
        // Nota (si existe)
        if (caregiver.has("note") && !caregiver.get("note").isJsonNull()) {
            String note = caregiver.get("note").getAsString();
            if (!note.isEmpty()) {
                panel.add(Box.createVerticalStrut(5));
                JLabel noteLabel = new JLabel("<html><i>Nota: " + note + "</i></html>");
                noteLabel.setFont(new Font("Arial", Font.ITALIC, 11));
                noteLabel.setForeground(Color.GRAY);
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
    
    private void viewAllAlerts() {
        JOptionPane.showMessageDialog(
            this,
            "Funcionalidad en desarrollo: Ver todas las alertas",
            "Próximamente",
            JOptionPane.INFORMATION_MESSAGE
        );
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
}
