package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Panel de dashboard personal del caregiver.
 * Muestra:
 * - Pacientes personales (relación caregiver_patient)
 * - Ubicaciones en mapa
 * - Alertas recientes
 * - Métricas personales
 * 
 * NO muestra dispositivos médicos (solo existen en contexto organizacional)
 */
public class CaregiverDashboardPanel extends JPanel {
    // Paleta de colores
    private static final Color GLOBAL_BACKGROUND = new Color(247, 249, 251);
    private static final Color CARD_BACKGROUND = Color.WHITE;
    private static final Color PRIMARY_BLUE = new Color(0, 120, 215);
    private static final Color SECONDARY_GREEN = new Color(40, 167, 69);
    private static final Color WARNING_ORANGE = new Color(255, 152, 0);
    private static final Color DANGER_RED = new Color(220, 53, 69);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER_LIGHT = new Color(223, 227, 230);
    
    private final ApiClient apiClient;
    private final String accessToken;
    private final Consumer<Exception> exceptionHandler;
    private final BiConsumer<String, Boolean> snackbarHandler;
    
    // Componentes
    private final JLabel totalPatientsLabel = new JLabel("0");
    private final JLabel activeAlertsLabel = new JLabel("0");
    private final JLabel lastUpdateLabel = new JLabel("--");
    private final JPanel patientsListPanel = new JPanel();
    private final JPanel alertsPanel = new JPanel();
    private EmbeddedMapPanel mapPanel;
    
    private JsonArray caregiverPatients;
    private JsonArray patientLocations;
    
    public CaregiverDashboardPanel(
            ApiClient apiClient,
            String accessToken,
            Consumer<Exception> exceptionHandler,
            BiConsumer<String, Boolean> snackbarHandler
    ) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.exceptionHandler = exceptionHandler;
        this.snackbarHandler = snackbarHandler;
        
        setLayout(new BorderLayout());
        setOpaque(false);
        
        initUI();
    }
    
    private void initUI() {
        // Panel principal con scroll
        JPanel mainContent = new JPanel();
        mainContent.setLayout(new BoxLayout(mainContent, BoxLayout.Y_AXIS));
        mainContent.setOpaque(false);
        mainContent.setBorder(new EmptyBorder(16, 16, 16, 16));
        
        // Título de sección
        JLabel titleLabel = new JLabel("Mis Pacientes Personales");
        titleLabel.setFont(new Font("Inter", Font.BOLD, 28));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(titleLabel);
        mainContent.add(Box.createVerticalStrut(8));
        
        JLabel subtitleLabel = new JLabel("Vista de tus pacientes bajo cuidado personal");
        subtitleLabel.setFont(new Font("Inter", Font.PLAIN, 15));
        subtitleLabel.setForeground(TEXT_SECONDARY);
        subtitleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(subtitleLabel);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Métricas cards
        JPanel metricsPanel = createMetricsPanel();
        metricsPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(metricsPanel);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Grid 2 columnas: Pacientes | Mapa
        JPanel gridPanel = new JPanel(new GridLayout(1, 2, 16, 0));
        gridPanel.setOpaque(false);
        gridPanel.setMaximumSize(new Dimension(Integer.MAX_VALUE, 600));
        gridPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Columna 1: Lista de pacientes
        JPanel patientsCard = createCard("👥 Pacientes", patientsListPanel);
        gridPanel.add(patientsCard);
        
        // Columna 2: Mapa
        JPanel mapCard = createMapCard();
        gridPanel.add(mapCard);
        
        mainContent.add(gridPanel);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Panel de alertas recientes
        JPanel alertsCard = createCard("🚨 Alertas Recientes", alertsPanel);
        alertsCard.setMaximumSize(new Dimension(Integer.MAX_VALUE, 400));
        alertsCard.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(alertsCard);
        mainContent.add(Box.createVerticalGlue());
        
        // ScrollPane
        JScrollPane scrollPane = new JScrollPane(mainContent);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        scrollPane.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        scrollPane.getViewport().setBackground(GLOBAL_BACKGROUND);
        
        add(scrollPane, BorderLayout.CENTER);
    }
    
    private JPanel createMetricsPanel() {
        JPanel panel = new JPanel(new GridLayout(1, 3, 16, 0));
        panel.setOpaque(false);
        panel.setMaximumSize(new Dimension(Integer.MAX_VALUE, 120));
        
        // Card 1: Total Pacientes
        JPanel card1 = createMetricCard(
                "📊 Mis Pacientes",
                totalPatientsLabel,
                PRIMARY_BLUE
        );
        
        // Card 2: Alertas Activas
        JPanel card2 = createMetricCard(
                "🚨 Alertas Activas",
                activeAlertsLabel,
                DANGER_RED
        );
        
        // Card 3: Última Actualización
        JPanel card3 = createMetricCard(
                "📍 Última Actualización",
                lastUpdateLabel,
                SECONDARY_GREEN
        );
        
        panel.add(card1);
        panel.add(card2);
        panel.add(card3);
        
        return panel;
    }
    
    private JPanel createMetricCard(String title, JLabel valueLabel, Color accentColor) {
        JPanel card = new JPanel();
        card.setLayout(new BorderLayout(16, 8));
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 24, 20, 24)
        ));
        
        // Título
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        titleLabel.setForeground(TEXT_SECONDARY);
        card.add(titleLabel, BorderLayout.NORTH);
        
        // Valor
        valueLabel.setFont(new Font("Inter", Font.BOLD, 36));
        valueLabel.setForeground(accentColor);
        card.add(valueLabel, BorderLayout.CENTER);
        
        return card;
    }
    
    private JPanel createCard(String title, JPanel contentPanel) {
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 24, 20, 24)
        ));
        
        // Header
        JLabel headerLabel = new JLabel(title);
        headerLabel.setFont(new Font("Inter", Font.BOLD, 18));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        card.add(headerLabel, BorderLayout.NORTH);
        
        // Content
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setOpaque(false);
        
        JScrollPane scrollPane = new JScrollPane(contentPanel);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(12);
        scrollPane.setOpaque(false);
        scrollPane.getViewport().setOpaque(false);
        card.add(scrollPane, BorderLayout.CENTER);
        
        return card;
    }
    
    private JPanel createMapCard() {
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 24, 20, 24)
        ));
        
        // Header
        JLabel headerLabel = new JLabel("🗺️ Ubicaciones");
        headerLabel.setFont(new Font("Inter", Font.BOLD, 18));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        card.add(headerLabel, BorderLayout.NORTH);
        
        // Mapa
        try {
            mapPanel = new EmbeddedMapPanel();
            card.add(mapPanel, BorderLayout.CENTER);
        } catch (Exception e) {
            JLabel errorLabel = new JLabel("Error al cargar el mapa");
            errorLabel.setHorizontalAlignment(SwingConstants.CENTER);
            errorLabel.setForeground(DANGER_RED);
            card.add(errorLabel, BorderLayout.CENTER);
            exceptionHandler.accept(e);
        }
        
        return card;
    }
    
    /**
     * Carga datos del caregiver
     */
    public void loadData() {
        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            private JsonArray patients;
            private JsonArray locations;
            private JsonObject metrics;
            private Exception loadError;
            
            @Override
            protected Void doInBackground() throws Exception {
                try {
                    
                    // Cargar pacientes personales
                    JsonObject patientsResponse = apiClient.getCaregiverPatients(accessToken);
                    
                    if (patientsResponse.has("data") && patientsResponse.get("data").isJsonObject()) {
                        JsonObject dataObj = patientsResponse.getAsJsonObject("data");
                        patients = dataObj.has("patients") && dataObj.get("patients").isJsonArray()
                                ? dataObj.getAsJsonArray("patients")
                                : new JsonArray();
                    } else {
                        patients = new JsonArray();
                    }
                    
                    // Cargar ubicaciones (con parámetros vacíos)
                    JsonObject locationsResponse = apiClient.getCaregiverPatientLocations(accessToken, null);
                    
                    if (locationsResponse.has("data") && locationsResponse.get("data").isJsonObject()) {
                        JsonObject dataObj = locationsResponse.getAsJsonObject("data");
                        locations = dataObj.has("patients") && dataObj.get("patients").isJsonArray()
                                ? dataObj.getAsJsonArray("patients")
                                : new JsonArray();
                    } else {
                        locations = new JsonArray();
                    }
                    
                    // Métricas básicas (calcular desde los datos)
                    metrics = new JsonObject();
                    metrics.addProperty("total_patients", patients.size());
                    // TODO: Calcular alertas activas cuando tengamos ese endpoint
                    metrics.addProperty("open_alerts", 0);
                    
                } catch (Exception ex) {
                    ex.printStackTrace();
                    loadError = ex;
                }
                
                return null;
            }
            
            @Override
            protected void done() {
                try {
                    get();
                    
                    if (loadError != null) {
                        exceptionHandler.accept(loadError);
                        return;
                    }
                    
                    caregiverPatients = patients;
                    patientLocations = locations;
                    
                    updateMetrics(metrics);
                    updatePatientsList(patients);
                    updateMap(locations);
                    
                    snackbarHandler.accept("Datos cargados correctamente", true);
                } catch (Exception ex) {
                    ex.printStackTrace();
                    exceptionHandler.accept(ex);
                }
            }
        };
        worker.execute();
    }
    
    private void updateMetrics(JsonObject metrics) {
        // Actualizar métricas desde datos
        if (caregiverPatients != null) {
            totalPatientsLabel.setText(String.valueOf(caregiverPatients.size()));
        }
        
        if (metrics.has("open_alerts")) {
            activeAlertsLabel.setText(String.valueOf(metrics.get("open_alerts").getAsInt()));
        }
        
        if (metrics.has("latest_update_at") && !metrics.get("latest_update_at").isJsonNull()) {
            String timestamp = metrics.get("latest_update_at").getAsString();
            lastUpdateLabel.setText(formatTimestamp(timestamp));
        } else {
            lastUpdateLabel.setText("Sin datos");
        }
    }
    
    private void updatePatientsList(JsonArray patients) {
        patientsListPanel.removeAll();
        
        if (patients == null || patients.size() == 0) {
            JLabel emptyLabel = new JLabel("No tienes pacientes personales");
            emptyLabel.setFont(new Font("Inter", Font.PLAIN, 14));
            emptyLabel.setForeground(TEXT_SECONDARY);
            emptyLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
            patientsListPanel.add(Box.createVerticalGlue());
            patientsListPanel.add(emptyLabel);
            patientsListPanel.add(Box.createVerticalGlue());
        } else {
            for (int i = 0; i < patients.size(); i++) {
                JsonObject patient = patients.get(i).getAsJsonObject();
                JPanel patientRow = createPatientRow(patient);
                patientRow.setAlignmentX(Component.LEFT_ALIGNMENT);
                patientsListPanel.add(patientRow);
                if (i < patients.size() - 1) {
                    patientsListPanel.add(Box.createVerticalStrut(8));
                }
            }
        }
        
        patientsListPanel.revalidate();
        patientsListPanel.repaint();
    }
    
    private JPanel createPatientRow(JsonObject patient) {
        JPanel row = new JPanel(new BorderLayout(12, 0));
        row.setBackground(new Color(248, 249, 250));
        row.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(12, 16, 12, 16)
        ));
        row.setMaximumSize(new Dimension(Integer.MAX_VALUE, 70));
        
        // Nombre
        String name = patient.has("name") ? patient.get("name").getAsString() : "Sin nombre";
        JLabel nameLabel = new JLabel(name);
        nameLabel.setFont(new Font("Inter", Font.BOLD, 14));
        nameLabel.setForeground(TEXT_PRIMARY);
        
        // Info adicional
        String relationship = "";
        if (patient.has("relationship_label") && !patient.get("relationship_label").isJsonNull()) {
            relationship = patient.get("relationship_label").getAsString();
        }
        
        JLabel infoLabel = new JLabel(relationship);
        infoLabel.setFont(new Font("Inter", Font.PLAIN, 12));
        infoLabel.setForeground(TEXT_SECONDARY);
        
        JPanel leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setOpaque(false);
        leftPanel.add(nameLabel);
        leftPanel.add(Box.createVerticalStrut(4));
        leftPanel.add(infoLabel);
        
        row.add(leftPanel, BorderLayout.WEST);
        
        // Botón ver detalle
        JButton detailButton = new JButton("Ver detalle");
        detailButton.setFont(new Font("Inter", Font.PLAIN, 12));
        detailButton.setForeground(PRIMARY_BLUE);
        detailButton.setBackground(Color.WHITE);
        detailButton.setBorder(new CompoundBorder(
                new LineBorder(PRIMARY_BLUE, 1, true),
                new EmptyBorder(6, 16, 6, 16)
        ));
        detailButton.setFocusPainted(false);
        detailButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        detailButton.addActionListener(e -> showPatientDetail(patient));
        
        row.add(detailButton, BorderLayout.EAST);
        
        return row;
    }
    
    private void updateMap(JsonArray locations) {
        if (mapPanel != null && locations != null) {
            // Actualizar mapa con ubicaciones de pacientes personales
            mapPanel.updateLocations(locations);
        }
    }
    
    private void showPatientDetail(JsonObject patient) {
        String patientId = patient.has("id") ? patient.get("id").getAsString() : null;
        String patientName = patient.has("name") ? patient.get("name").getAsString() : "Sin nombre";
        
        if (patientId == null) {
            snackbarHandler.accept("ID de paciente no disponible", false);
            return;
        }
        
        Frame parentWindow = (Frame) SwingUtilities.getWindowAncestor(this);
        
        System.out.println("[CaregiverDashboard] Opening PatientDetailDialog for patient: " + patientName + " (ID: " + patientId + ")");
        
        // Usar el diálogo profesional con gráficas de signos vitales
        // Para caregiver, orgId es null
        PatientDetailDialog dialog = new PatientDetailDialog(
            parentWindow,
            apiClient,
            accessToken,
            null, // orgId es null para pacientes de caregiver
            patientId,
            patientName
        );
        
        dialog.setVisible(true);
    }
    
    private void showPatientDetailModal(JsonObject patient, JsonArray alerts, JsonArray notes) {
        JDialog dialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(this), "Detalle del Paciente", true);
        dialog.setLayout(new BorderLayout(16, 16));
        dialog.setSize(900, 600);
        dialog.setLocationRelativeTo(this);
        
        // Panel principal
        JPanel mainPanel = new JPanel(new BorderLayout(16, 16));
        mainPanel.setBackground(GLOBAL_BACKGROUND);
        mainPanel.setBorder(new EmptyBorder(20, 20, 20, 20));
        
        // Header con info del paciente (ahora con avatar)
        JPanel headerPanel = new JPanel(new BorderLayout(16, 12));
        headerPanel.setBackground(Color.WHITE);
        headerPanel.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(16, 20, 16, 20)
        ));
        
        // Avatar circular en el lado izquierdo
        JLabel avatarLabel = new JLabel();
        avatarLabel.setPreferredSize(new Dimension(64, 64));
        avatarLabel.setOpaque(true);
        avatarLabel.setBackground(PRIMARY_BLUE);
        avatarLabel.setHorizontalAlignment(SwingConstants.CENTER);
        avatarLabel.setVerticalAlignment(SwingConstants.CENTER);
        
        String name = patient.has("name") ? patient.get("name").getAsString() : "Sin nombre";
        String initials = getInitials(name);
        avatarLabel.setText(initials);
        avatarLabel.setFont(new Font("Inter", Font.BOLD, 24));
        avatarLabel.setForeground(Color.WHITE);
        avatarLabel.setBorder(new LineBorder(Color.WHITE, 3, true));
        
        // Información del paciente
        JPanel infoPanel = new JPanel();
        infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));
        infoPanel.setOpaque(false);
        
        JLabel nameLabel = new JLabel(name);
        nameLabel.setFont(new Font("Inter", Font.BOLD, 20));
        nameLabel.setForeground(TEXT_PRIMARY);
        nameLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        String email = patient.has("email") ? patient.get("email").getAsString() : "";
        JLabel emailLabel = new JLabel("📧 " + email);
        emailLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        emailLabel.setForeground(TEXT_SECONDARY);
        emailLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        infoPanel.add(nameLabel);
        infoPanel.add(Box.createVerticalStrut(6));
        infoPanel.add(emailLabel);
        
        headerPanel.add(avatarLabel, BorderLayout.WEST);
        headerPanel.add(infoPanel, BorderLayout.CENTER);
        
        mainPanel.add(headerPanel, BorderLayout.NORTH);
        
        // Panel de contenido: 2 columnas (Alertas | Notas)
        JPanel contentPanel = new JPanel(new GridLayout(1, 2, 16, 0));
        contentPanel.setOpaque(false);
        
        // Columna 1: Alertas
        JPanel alertsPanel = new JPanel(new BorderLayout());
        alertsPanel.setBackground(Color.WHITE);
        alertsPanel.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(16, 20, 16, 20)
        ));
        
        JLabel alertsTitle = new JLabel("🚨 Alertas Recientes");
        alertsTitle.setFont(new Font("Inter", Font.BOLD, 16));
        alertsTitle.setForeground(TEXT_PRIMARY);
        alertsTitle.setBorder(new EmptyBorder(0, 0, 12, 0));
        alertsPanel.add(alertsTitle, BorderLayout.NORTH);
        
        JPanel alertsListPanel = new JPanel();
        alertsListPanel.setLayout(new BoxLayout(alertsListPanel, BoxLayout.Y_AXIS));
        alertsListPanel.setOpaque(false);
        
        if (alerts == null || alerts.size() == 0) {
            JLabel emptyLabel = new JLabel("Sin alertas recientes");
            emptyLabel.setFont(new Font("Inter", Font.PLAIN, 13));
            emptyLabel.setForeground(TEXT_SECONDARY);
            alertsListPanel.add(emptyLabel);
        } else {
            for (int i = 0; i < alerts.size(); i++) {
                JsonObject alert = alerts.get(i).getAsJsonObject();
                JPanel alertCard = createAlertCard(alert);
                alertCard.setAlignmentX(Component.LEFT_ALIGNMENT);
                alertsListPanel.add(alertCard);
                if (i < alerts.size() - 1) {
                    alertsListPanel.add(Box.createVerticalStrut(8));
                }
            }
        }
        
        JScrollPane alertsScroll = new JScrollPane(alertsListPanel);
        alertsScroll.setBorder(null);
        alertsScroll.setOpaque(false);
        alertsScroll.getViewport().setOpaque(false);
        alertsPanel.add(alertsScroll, BorderLayout.CENTER);
        
        // Columna 2: Notas
        JPanel notesPanel = new JPanel(new BorderLayout());
        notesPanel.setBackground(Color.WHITE);
        notesPanel.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(16, 20, 16, 20)
        ));
        
        // Header con título y botón de agregar
        JPanel notesHeaderPanel = new JPanel(new BorderLayout());
        notesHeaderPanel.setOpaque(false);
        
        JLabel notesTitle = new JLabel("📝 Notas Médicas");
        notesTitle.setFont(new Font("Inter", Font.BOLD, 16));
        notesTitle.setForeground(TEXT_PRIMARY);
        
        JButton addNoteButton = new JButton("+ Nueva Nota");
        addNoteButton.setFont(new Font("Inter", Font.BOLD, 12));
        addNoteButton.setBackground(SECONDARY_GREEN);
        addNoteButton.setForeground(Color.WHITE);
        addNoteButton.setBorder(new EmptyBorder(6, 12, 6, 12));
        addNoteButton.setFocusPainted(false);
        addNoteButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        addNoteButton.addActionListener(e -> {
            String patientId = patient.has("id") ? patient.get("id").getAsString() : null;
            if (patientId != null) {
                showAddNoteDialog(patientId, dialog);
            }
        });
        
        notesHeaderPanel.add(notesTitle, BorderLayout.WEST);
        notesHeaderPanel.add(addNoteButton, BorderLayout.EAST);
        notesHeaderPanel.setBorder(new EmptyBorder(0, 0, 12, 0));
        notesPanel.add(notesHeaderPanel, BorderLayout.NORTH);
        
        JPanel notesListPanel = new JPanel();
        notesListPanel.setLayout(new BoxLayout(notesListPanel, BoxLayout.Y_AXIS));
        notesListPanel.setOpaque(false);
        
        if (notes == null || notes.size() == 0) {
            JLabel emptyLabel = new JLabel("Sin notas médicas");
            emptyLabel.setFont(new Font("Inter", Font.PLAIN, 13));
            emptyLabel.setForeground(TEXT_SECONDARY);
            notesListPanel.add(emptyLabel);
        } else {
            for (int i = 0; i < notes.size(); i++) {
                JsonObject note = notes.get(i).getAsJsonObject();
                JPanel noteCard = createNoteCard(note);
                noteCard.setAlignmentX(Component.LEFT_ALIGNMENT);
                notesListPanel.add(noteCard);
                if (i < notes.size() - 1) {
                    notesListPanel.add(Box.createVerticalStrut(8));
                }
            }
        }
        
        JScrollPane notesScroll = new JScrollPane(notesListPanel);
        notesScroll.setBorder(null);
        notesScroll.setOpaque(false);
        notesScroll.getViewport().setOpaque(false);
        notesPanel.add(notesScroll, BorderLayout.CENTER);
        
        contentPanel.add(alertsPanel);
        contentPanel.add(notesPanel);
        
        mainPanel.add(contentPanel, BorderLayout.CENTER);
        
        // Botón cerrar
        JPanel footerPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        footerPanel.setOpaque(false);
        
        JButton closeButton = new JButton("Cerrar");
        closeButton.setFont(new Font("Inter", Font.BOLD, 13));
        closeButton.setBackground(PRIMARY_BLUE);
        closeButton.setForeground(Color.WHITE);
        closeButton.setBorder(new EmptyBorder(10, 24, 10, 24));
        closeButton.setFocusPainted(false);
        closeButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        closeButton.addActionListener(e -> dialog.dispose());
        
        footerPanel.add(closeButton);
        mainPanel.add(footerPanel, BorderLayout.SOUTH);
        
        dialog.add(mainPanel);
        dialog.setVisible(true);
    }
    
    private JPanel createAlertCard(JsonObject alert) {
        JPanel card = new JPanel();
        card.setLayout(new BoxLayout(card, BoxLayout.Y_AXIS));
        card.setBackground(new Color(254, 252, 248));
        card.setBorder(new CompoundBorder(
                new LineBorder(WARNING_ORANGE, 1, true),
                new EmptyBorder(10, 12, 10, 12)
        ));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 100));
        
        String label = alert.has("label") ? alert.get("label").getAsString() : "Alerta";
        JLabel titleLabel = new JLabel(label);
        titleLabel.setFont(new Font("Inter", Font.BOLD, 13));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        String timestamp = alert.has("created_at") ? alert.get("created_at").getAsString() : "";
        JLabel timeLabel = new JLabel("🕐 " + timestamp);
        timeLabel.setFont(new Font("Inter", Font.PLAIN, 11));
        timeLabel.setForeground(TEXT_SECONDARY);
        timeLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        card.add(titleLabel);
        card.add(Box.createVerticalStrut(4));
        card.add(timeLabel);
        
        return card;
    }
    
    private JPanel createNoteCard(JsonObject note) {
        // DEBUG: Imprimir el JSON completo de la nota
        
        JPanel card = new JPanel();
        card.setLayout(new BoxLayout(card, BoxLayout.Y_AXIS));
        card.setBackground(new Color(248, 252, 255));
        card.setBorder(new CompoundBorder(
                new LineBorder(PRIMARY_BLUE, 1, true),
                new EmptyBorder(10, 12, 10, 12)
        ));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 120));
        
        // Obtener el tipo de evento
        String eventLabel = "Desconocido";
        if (note.has("event") && note.get("event").isJsonObject()) {
            JsonObject event = note.getAsJsonObject("event");
            if (event.has("label")) {
                eventLabel = event.get("label").getAsString();
            } else {
            }
        } else {
        }
        
        // Título con tipo de evento
        JLabel eventTitleLabel = new JLabel("📋 " + eventLabel);
        eventTitleLabel.setFont(new Font("Inter", Font.BOLD, 13));
        eventTitleLabel.setForeground(PRIMARY_BLUE);
        eventTitleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Contenido de la nota
        String content = note.has("note") ? note.get("note").getAsString() : "";
        if (content.isEmpty()) {
            content = "<em>Sin contenido</em>";
        }
        JLabel contentLabel = new JLabel("<html><body style='width: 100%'>" + content + "</body></html>");
        contentLabel.setFont(new Font("Inter", Font.PLAIN, 12));
        contentLabel.setForeground(TEXT_PRIMARY);
        contentLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Autor y fecha
        String author = "Desconocido";
        if (note.has("annotated_by") && note.get("annotated_by").isJsonObject()) {
            JsonObject annotatedBy = note.getAsJsonObject("annotated_by");
            if (annotatedBy.has("name") && !annotatedBy.get("name").isJsonNull()) {
                author = annotatedBy.get("name").getAsString();
            }
        }
        String timestamp = note.has("onset") ? note.get("onset").getAsString() : "";
        JLabel metaLabel = new JLabel("👤 " + author + " • " + timestamp);
        metaLabel.setFont(new Font("Inter", Font.PLAIN, 10));
        metaLabel.setForeground(TEXT_SECONDARY);
        metaLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        card.add(eventTitleLabel);
        card.add(Box.createVerticalStrut(4));
        card.add(contentLabel);
        card.add(Box.createVerticalStrut(6));
        card.add(metaLabel);
        
        return card;
    }
    
    private String getInitials(String name) {
        if (name == null || name.trim().isEmpty()) {
            return "??";
        }
        String[] parts = name.trim().split("\\s+");
        if (parts.length == 1) {
            return parts[0].substring(0, Math.min(2, parts[0].length())).toUpperCase();
        }
        return (parts[0].charAt(0) + "" + parts[parts.length - 1].charAt(0)).toUpperCase();
    }
    
    private void showAddNoteDialog(String patientId, JDialog parentDialog) {
        JDialog noteDialog = new JDialog(parentDialog, "Agregar Nota Médica", true);
        noteDialog.setLayout(new BorderLayout(16, 16));
        noteDialog.setSize(500, 450);
        noteDialog.setLocationRelativeTo(parentDialog);
        
        JPanel mainPanel = new JPanel(new BorderLayout(12, 12));
        mainPanel.setBackground(GLOBAL_BACKGROUND);
        mainPanel.setBorder(new EmptyBorder(20, 20, 20, 20));
        
        // Título
        JLabel titleLabel = new JLabel("Nueva Nota Médica");
        titleLabel.setFont(new Font("Inter", Font.BOLD, 18));
        titleLabel.setForeground(TEXT_PRIMARY);
        mainPanel.add(titleLabel, BorderLayout.NORTH);
        
        // Panel central con formulario
        JPanel formPanel = new JPanel();
        formPanel.setLayout(new BoxLayout(formPanel, BoxLayout.Y_AXIS));
        formPanel.setOpaque(false);
        
        // Selector de tipo de evento
        JLabel eventLabel = new JLabel("Tipo de Evento:");
        eventLabel.setFont(new Font("Inter", Font.BOLD, 13));
        eventLabel.setForeground(TEXT_PRIMARY);
        eventLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Cargar tipos de evento desde el API
        JComboBox<String> eventCombo = new JComboBox<>();
        eventCombo.setFont(new Font("Inter", Font.PLAIN, 13));
        eventCombo.setMaximumSize(new Dimension(Integer.MAX_VALUE, 35));
        eventCombo.setAlignmentX(Component.LEFT_ALIGNMENT);
        eventCombo.addItem("Cargando...");
        eventCombo.setEnabled(false);
        
        // Cargar tipos de evento en segundo plano
        SwingWorker<Void, Void> loadEventsWorker = new SwingWorker<>() {
            private List<JsonObject> eventTypes = new ArrayList<>();
            
            @Override
            protected Void doInBackground() {
                try {
                    JsonObject response = apiClient.getEventTypes();
                    if (response.has("data") && response.getAsJsonObject("data").has("event_types")) {
                        JsonArray eventsArray = response.getAsJsonObject("data").getAsJsonArray("event_types");
                        for (int i = 0; i < eventsArray.size(); i++) {
                            eventTypes.add(eventsArray.get(i).getAsJsonObject());
                        }
                    }
                } catch (Exception ex) {
                    ex.printStackTrace();
                }
                return null;
            }
            
            @Override
            protected void done() {
                eventCombo.removeAllItems();
                if (eventTypes.isEmpty()) {
                    eventCombo.addItem("No hay tipos de evento disponibles");
                    eventCombo.setEnabled(false);
                } else {
                    for (JsonObject eventType : eventTypes) {
                        String code = eventType.get("code").getAsString();
                        String description = eventType.get("description").getAsString();
                        eventCombo.addItem(code + " - " + description);
                    }
                    eventCombo.setEnabled(true);
                }
            }
        };
        loadEventsWorker.execute();
        
        formPanel.add(eventLabel);
        formPanel.add(Box.createVerticalStrut(6));
        formPanel.add(eventCombo);
        formPanel.add(Box.createVerticalStrut(16));
        
        // Etiqueta de nota
        JLabel noteLabel = new JLabel("Nota:");
        noteLabel.setFont(new Font("Inter", Font.BOLD, 13));
        noteLabel.setForeground(TEXT_PRIMARY);
        noteLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        formPanel.add(noteLabel);
        formPanel.add(Box.createVerticalStrut(6));
        
        // Área de texto
        JTextArea noteTextArea = new JTextArea();
        noteTextArea.setFont(new Font("Inter", Font.PLAIN, 13));
        noteTextArea.setLineWrap(true);
        noteTextArea.setWrapStyleWord(true);
        noteTextArea.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(12, 12, 12, 12)
        ));
        
        JScrollPane scrollPane = new JScrollPane(noteTextArea);
        scrollPane.setBorder(null);
        scrollPane.setAlignmentX(Component.LEFT_ALIGNMENT);
        formPanel.add(scrollPane);
        
        mainPanel.add(formPanel, BorderLayout.CENTER);
        
        // Botones
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        buttonPanel.setOpaque(false);
        
        JButton cancelButton = new JButton("Cancelar");
        cancelButton.setFont(new Font("Inter", Font.PLAIN, 13));
        cancelButton.setBackground(Color.WHITE);
        cancelButton.setForeground(TEXT_PRIMARY);
        cancelButton.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(8, 16, 8, 16)
        ));
        cancelButton.setFocusPainted(false);
        cancelButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        cancelButton.addActionListener(e -> noteDialog.dispose());
        
        JButton saveButton = new JButton("Guardar Nota");
        saveButton.setFont(new Font("Inter", Font.BOLD, 13));
        saveButton.setBackground(PRIMARY_BLUE);
        saveButton.setForeground(Color.WHITE);
        saveButton.setBorder(new EmptyBorder(8, 16, 8, 16));
        saveButton.setFocusPainted(false);
        saveButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        saveButton.addActionListener(e -> {
            String content = noteTextArea.getText().trim();
            if (content.isEmpty()) {
                snackbarHandler.accept("La nota no puede estar vacía", false);
                return;
            }
            
            // Extraer el código del evento del combo
            String selectedEvent = (String) eventCombo.getSelectedItem();
            String eventCode = selectedEvent.split(" - ")[0]; // Toma "GENERAL" de "GENERAL - Nota general"
            
            // Guardar nota
            SwingWorker<Boolean, Void> worker = new SwingWorker<>() {
                private Exception error;
                
                @Override
                protected Boolean doInBackground() {
                    try {
                        JsonObject noteData = new JsonObject();
                        noteData.addProperty("event_code", eventCode);
                        noteData.addProperty("note", content);
                        noteData.addProperty("source", "caregiver_note");
                        
                        JsonObject response = apiClient.createCaregiverPatientNote(accessToken, patientId, noteData);
                        return response.has("status") && response.get("status").getAsString().equals("success");
                    } catch (Exception ex) {
                        error = ex;
                        return false;
                    }
                }
                
                @Override
                protected void done() {
                    try {
                        Boolean success = get();
                        if (success) {
                            snackbarHandler.accept("Nota guardada correctamente", true);
                            noteDialog.dispose();
                            parentDialog.dispose();
                            // Recargar datos para mostrar la nueva nota
                            loadData();
                        } else if (error != null) {
                            exceptionHandler.accept(error);
                        } else {
                            snackbarHandler.accept("Error al guardar la nota", false);
                        }
                    } catch (Exception ex) {
                        exceptionHandler.accept(ex);
                    }
                }
            };
            worker.execute();
        });
        
        buttonPanel.add(cancelButton);
        buttonPanel.add(saveButton);
        mainPanel.add(buttonPanel, BorderLayout.SOUTH);
        
        noteDialog.add(mainPanel);
        noteDialog.setVisible(true);
    }
    
    private String formatTimestamp(String timestamp) {
        // TODO: Implementar formato de fecha relativo (ej: "Hace 10 minutos")
        return timestamp;
    }
}
