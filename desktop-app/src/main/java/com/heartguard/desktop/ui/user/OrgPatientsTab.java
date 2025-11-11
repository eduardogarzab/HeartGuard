package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.models.user.OrgMembership;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import javax.swing.table.DefaultTableModel;
import javax.swing.table.TableRowSorter;
import java.awt.*;
import java.util.HashMap;
import java.util.Map;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Tab de Pacientes de una organización.
 * Muestra TODOS los pacientes de los care teams de la org (donde el usuario es miembro).
 * 
 * Estructura:
 * - Pacientes están en care_teams dentro de la organización
 * - Endpoint: /orgs/{org_id}/care-team-patients/locations
 * - Retorna: pacientes agrupados por care team con ubicaciones
 * 
 * Layout:
 * - Panel superior: Filtros (por care team, nivel riesgo, con alertas)
 * - Grid 2 columnas: Tabla de pacientes (50%) + Mapa (50%)
 */
public class OrgPatientsTab extends JPanel {
    // Colores
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
    private final OrgMembership organization;
    private final Consumer<Exception> exceptionHandler;
    private final BiConsumer<String, Boolean> snackbarHandler;
    
    // Componentes
    private final JComboBox<String> careTeamFilter = new JComboBox<>();
    private final JComboBox<String> riskLevelFilter = new JComboBox<>();
    private final JCheckBox withAlertsFilter = new JCheckBox("Solo con alertas activas");
    private final JLabel totalPatientsLabel = new JLabel("0 pacientes");
    
    private final JPanel patientsListPanel = new JPanel(); // Panel de tarjetas en lugar de tabla
    private EmbeddedMapPanel mapPanel;
    
    // Datos
    private JsonArray patientsData; // Datos completos del endpoint
    private Map<String, String> careTeamsMap = new HashMap<>(); // id -> nombre
    
    public OrgPatientsTab(
            ApiClient apiClient,
            String accessToken,
            OrgMembership organization,
            Consumer<Exception> exceptionHandler,
            BiConsumer<String, Boolean> snackbarHandler
    ) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.organization = organization;
        this.exceptionHandler = exceptionHandler;
        this.snackbarHandler = snackbarHandler;
        
        setLayout(new BorderLayout());
        setOpaque(false);
        setBorder(new EmptyBorder(24, 24, 24, 24));
        
        // Configurar panel de lista de pacientes
        patientsListPanel.setLayout(new BoxLayout(patientsListPanel, BoxLayout.Y_AXIS));
        patientsListPanel.setOpaque(false);
        
        initUI();
    }
    
    private void initUI() {
        JPanel mainContent = new JPanel();
        mainContent.setLayout(new BoxLayout(mainContent, BoxLayout.Y_AXIS));
        mainContent.setOpaque(false);
        
        // Título
        JLabel titleLabel = new JLabel("🗺️ Pacientes de la Organización");
        titleLabel.setFont(new Font("Inter", Font.BOLD, 24));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(titleLabel);
        mainContent.add(Box.createVerticalStrut(8));
        
        JLabel subtitleLabel = new JLabel("Pacientes de todos los care teams donde eres miembro");
        subtitleLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        subtitleLabel.setForeground(TEXT_SECONDARY);
        subtitleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(subtitleLabel);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Panel de filtros
        JPanel filtersPanel = createFiltersPanel();
        filtersPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(filtersPanel);
        mainContent.add(Box.createVerticalStrut(16));
        
        // Grid: Tabla + Mapa
        JPanel gridPanel = new JPanel(new GridLayout(1, 2, 16, 0));
        gridPanel.setOpaque(false);
        gridPanel.setMaximumSize(new Dimension(Integer.MAX_VALUE, 600));
        gridPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Columna 1: Tabla de pacientes
        JPanel tableCard = createTableCard();
        gridPanel.add(tableCard);
        
        // Columna 2: Mapa
        JPanel mapCard = createMapCard();
        gridPanel.add(mapCard);
        
        mainContent.add(gridPanel);
        mainContent.add(Box.createVerticalGlue());
        
        // ScrollPane
        JScrollPane scrollPane = new JScrollPane(mainContent);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        scrollPane.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        scrollPane.getViewport().setBackground(GLOBAL_BACKGROUND);
        
        add(scrollPane, BorderLayout.CENTER);
    }
    
    private JPanel createFiltersPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT, 16, 0));
        panel.setOpaque(false);
        panel.setMaximumSize(new Dimension(Integer.MAX_VALUE, 50));
        
        // Filtro por Care Team
        JLabel careTeamLabel = new JLabel("Care Team:");
        careTeamLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        careTeamLabel.setForeground(TEXT_PRIMARY);
        
        careTeamFilter.setPreferredSize(new Dimension(200, 35));
        careTeamFilter.setFont(new Font("Inter", Font.PLAIN, 13));
        careTeamFilter.addItem("Todos");
        careTeamFilter.addActionListener(e -> applyFilters());
        
        // Filtro por Nivel de Riesgo
        JLabel riskLabel = new JLabel("Riesgo:");
        riskLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        riskLabel.setForeground(TEXT_PRIMARY);
        
        riskLevelFilter.setPreferredSize(new Dimension(150, 35));
        riskLevelFilter.setFont(new Font("Inter", Font.PLAIN, 13));
        riskLevelFilter.addItem("Todos");
        riskLevelFilter.addItem("Alto");
        riskLevelFilter.addItem("Medio");
        riskLevelFilter.addItem("Bajo");
        riskLevelFilter.addActionListener(e -> applyFilters());
        
        // Checkbox alertas
        withAlertsFilter.setFont(new Font("Inter", Font.PLAIN, 13));
        withAlertsFilter.setOpaque(false);
        withAlertsFilter.addActionListener(e -> applyFilters());
        
        // Total pacientes
        totalPatientsLabel.setFont(new Font("Inter", Font.BOLD, 14));
        totalPatientsLabel.setForeground(PRIMARY_BLUE);
        
        panel.add(careTeamLabel);
        panel.add(careTeamFilter);
        panel.add(Box.createHorizontalStrut(8));
        panel.add(riskLabel);
        panel.add(riskLevelFilter);
        panel.add(Box.createHorizontalStrut(8));
        panel.add(withAlertsFilter);
        panel.add(Box.createHorizontalStrut(16));
        panel.add(totalPatientsLabel);
        
        return panel;
    }
    
    private JPanel createTableCard() {
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 20, 20, 20)
        ));
        
        // Header
        JLabel headerLabel = new JLabel("Lista de Pacientes");
        headerLabel.setFont(new Font("Inter", Font.BOLD, 16));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        card.add(headerLabel, BorderLayout.NORTH);
        
        // Panel de tarjetas con scroll
        JScrollPane listScroll = new JScrollPane(patientsListPanel);
        listScroll.setBorder(null);
        listScroll.getVerticalScrollBar().setUnitIncrement(16);
        listScroll.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        card.add(listScroll, BorderLayout.CENTER);
        
        return card;
    }
    
    private JPanel createMapCard() {
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 20, 20, 20)
        ));
        
        // Header
        JLabel headerLabel = new JLabel("Ubicaciones");
        headerLabel.setFont(new Font("Inter", Font.BOLD, 16));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        card.add(headerLabel, BorderLayout.NORTH);
        
        // Mapa
        try {
            mapPanel = new EmbeddedMapPanel();
            card.add(mapPanel, BorderLayout.CENTER);
        } catch (Exception e) {
            JLabel errorLabel = new JLabel("Error al cargar el mapa", SwingConstants.CENTER);
            errorLabel.setForeground(DANGER_RED);
            card.add(errorLabel, BorderLayout.CENTER);
            exceptionHandler.accept(e);
        }
        
        return card;
    }
    
    /**
     * Carga todos los pacientes de los care teams de la organización
     */
    public void loadData() {
        SwingWorker<JsonArray, Void> worker = new SwingWorker<>() {
            @Override
            protected JsonArray doInBackground() throws Exception {
                System.out.println("[OrgPatientsTab] Cargando pacientes para org: " + organization.getOrgName());
                // Obtener pacientes de care teams con ubicaciones
                // Endpoint: /orgs/{org_id}/care-team-patients/locations
                // Retorna: [{care_team_id, care_team_name, patients: [...]}, ...]
                JsonObject response = apiClient.getOrganizationCareTeamPatientsLocations(
                        accessToken, 
                        organization.getOrgId()
                );
                
                System.out.println("[OrgPatientsTab] Respuesta completa: " + response.toString());
                
                // La respuesta tiene estructura: {data: {care_teams: [...]}}
                if (response.has("data") && response.get("data").isJsonObject()) {
                    JsonObject dataObj = response.getAsJsonObject("data");
                    System.out.println("[OrgPatientsTab] Data object: " + dataObj.toString());
                    if (dataObj.has("care_teams") && dataObj.get("care_teams").isJsonArray()) {
                        JsonArray careTeams = dataObj.getAsJsonArray("care_teams");
                        System.out.println("[OrgPatientsTab] Care teams encontrados: " + careTeams.size());
                        return careTeams;
                    }
                }
                
                System.out.println("[OrgPatientsTab] No se encontraron care teams");
                return new JsonArray();
            }
            
            @Override
            protected void done() {
                try {
                    patientsData = get();
                    System.out.println("[OrgPatientsTab] Procesando " + patientsData.size() + " care teams");
                    processPatientsData();
                    updateTable();
                    updateMap();
                    snackbarHandler.accept("Datos de pacientes cargados", true);
                } catch (Exception ex) {
                    System.err.println("[OrgPatientsTab] ERROR: " + ex.getMessage());
                    ex.printStackTrace();
                    exceptionHandler.accept(ex);
                }
            }
        };
        worker.execute();
    }
    
    /**
     * Procesa los datos agrupados por care team
     */
    private void processPatientsData() {
        careTeamsMap.clear();
        careTeamFilter.removeAllItems();
        careTeamFilter.addItem("Todos");
        
        if (patientsData == null) return;
        
        // Extraer care teams y construir mapa
        for (int i = 0; i < patientsData.size(); i++) {
            JsonObject careTeam = patientsData.get(i).getAsJsonObject();
            System.out.println("[processPatientsData] Care Team " + i + ": " + careTeam.toString());
            
            String teamId = careTeam.has("id") ? careTeam.get("id").getAsString() : "";
            String teamName = careTeam.has("name") ? careTeam.get("name").getAsString() : "Sin nombre";
            
            // Verificar si tiene pacientes
            if (careTeam.has("patients")) {
                if (careTeam.get("patients").isJsonArray()) {
                    JsonArray patients = careTeam.getAsJsonArray("patients");
                    System.out.println("  → Tiene " + patients.size() + " pacientes");
                    if (patients.size() > 0) {
                        System.out.println("  → Primer paciente: " + patients.get(0).toString());
                    }
                } else {
                    System.out.println("  → Campo 'patients' NO es un array");
                }
            } else {
                System.out.println("  → NO tiene campo 'patients'");
            }
            
            if (!teamId.isEmpty()) {
                careTeamsMap.put(teamId, teamName);
                careTeamFilter.addItem(teamName);
            }
        }
    }
    
    private void updateTable() {
        patientsListPanel.removeAll();
        
        if (patientsData == null) {
            totalPatientsLabel.setText("0 pacientes");
            return;
        }
        
        String selectedCareTeam = (String) careTeamFilter.getSelectedItem();
        String selectedRisk = (String) riskLevelFilter.getSelectedItem();
        boolean onlyWithAlerts = withAlertsFilter.isSelected();
        
        // Si no hay selección, usar "Todos" por defecto
        if (selectedCareTeam == null) selectedCareTeam = "Todos";
        if (selectedRisk == null) selectedRisk = "Todos";
        
        int totalCount = 0;
        
        // Iterar sobre care teams
        for (int i = 0; i < patientsData.size(); i++) {
            JsonObject careTeam = patientsData.get(i).getAsJsonObject();
            String teamName = careTeam.has("name") ? careTeam.get("name").getAsString() : "Sin nombre";
            
            // Filtro por care team
            if (!selectedCareTeam.equals("Todos") && !teamName.equals(selectedCareTeam)) {
                continue;
            }
            
            // Procesar pacientes del care team
            if (careTeam.has("patients") && careTeam.get("patients").isJsonArray()) {
                JsonArray patients = careTeam.getAsJsonArray("patients");
                
                for (int j = 0; j < patients.size(); j++) {
                    JsonObject patient = patients.get(j).getAsJsonObject();
                    
                    // Extraer datos
                    String patientName = patient.has("name") ? patient.get("name").getAsString() : "Sin nombre";
                    String email = patient.has("email") && !patient.get("email").isJsonNull() 
                            ? patient.get("email").getAsString() : "N/A";
                    
                    // Risk level
                    String riskLevel = "N/A";
                    String riskCode = "";
                    if (patient.has("risk_level") && patient.get("risk_level").isJsonObject()) {
                        JsonObject riskObj = patient.getAsJsonObject("risk_level");
                        if (riskObj.has("label") && !riskObj.get("label").isJsonNull()) {
                            riskLevel = riskObj.get("label").getAsString();
                        }
                        if (riskObj.has("code") && !riskObj.get("code").isJsonNull()) {
                            riskCode = riskObj.get("code").getAsString();
                        }
                    }
                    
                    // Location
                    String lastUpdate = "Sin ubicación";
                    if (patient.has("location") && patient.get("location").isJsonObject()) {
                        JsonObject location = patient.getAsJsonObject("location");
                        if (location.has("last_update") && !location.get("last_update").isJsonNull()) {
                            lastUpdate = location.get("last_update").getAsString();
                        }
                    }
                    
                    // Alert level
                    String alertLevel = "Sin alertas";
                    if (patient.has("last_alert") && patient.get("last_alert").isJsonObject()) {
                        JsonObject lastAlert = patient.getAsJsonObject("last_alert");
                        if (lastAlert.has("level") && lastAlert.get("level").isJsonObject()) {
                            JsonObject level = lastAlert.getAsJsonObject("level");
                            if (level.has("label") && !level.get("label").isJsonNull()) {
                                alertLevel = level.get("label").getAsString();
                            }
                        }
                    }
                    
                    // Aplicar filtros
                    if (!selectedRisk.equals("Todos") && !riskLevel.contains(selectedRisk)) {
                        continue;
                    }
                    
                    if (onlyWithAlerts && alertLevel.equals("Sin alertas")) {
                        continue;
                    }
                    
                    // Crear tarjeta del paciente
                    JPanel patientCard = createPatientCard(patientName, email, teamName, riskLevel, riskCode, lastUpdate, alertLevel, patient);
                    patientCard.setAlignmentX(Component.LEFT_ALIGNMENT);
                    patientsListPanel.add(patientCard);
                    patientsListPanel.add(Box.createVerticalStrut(12));
                    
                    totalCount++;
                }
            }
        }
        
        if (totalCount == 0) {
            JLabel emptyLabel = new JLabel("No se encontraron pacientes");
            emptyLabel.setFont(new Font("Inter", Font.ITALIC, 14));
            emptyLabel.setForeground(TEXT_SECONDARY);
            emptyLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
            patientsListPanel.add(Box.createVerticalGlue());
            patientsListPanel.add(emptyLabel);
            patientsListPanel.add(Box.createVerticalGlue());
        }
        
        totalPatientsLabel.setText(totalCount + " paciente" + (totalCount != 1 ? "s" : ""));
        patientsListPanel.revalidate();
        patientsListPanel.repaint();
    }
    
    /**
     * Crea una tarjeta visual para un paciente
     */
    private JPanel createPatientCard(String name, String email, String careTeam, 
                                     String riskLevel, String riskCode, 
                                     String location, String alertLevel, JsonObject patientData) {
        JPanel card = new JPanel(new BorderLayout(16, 0));
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, true),
            new EmptyBorder(20, 20, 20, 20)
        ));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 110));
        card.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        
        // Panel izquierdo con info principal
        JPanel leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setOpaque(false);
        
        // Nombre del paciente
        JLabel nameLabel = new JLabel(name);
        nameLabel.setFont(new Font("Inter", Font.BOLD, 16));
        nameLabel.setForeground(TEXT_PRIMARY);
        nameLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Email
        JLabel emailLabel = new JLabel("✉️ " + email);
        emailLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        emailLabel.setForeground(TEXT_SECONDARY);
        emailLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Care Team
        JLabel teamLabel = new JLabel("👥 " + careTeam);
        teamLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        teamLabel.setForeground(TEXT_SECONDARY);
        teamLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        leftPanel.add(nameLabel);
        leftPanel.add(Box.createVerticalStrut(4));
        leftPanel.add(emailLabel);
        leftPanel.add(Box.createVerticalStrut(2));
        leftPanel.add(teamLabel);
        
        card.add(leftPanel, BorderLayout.CENTER);
        
        // Panel derecho con badges y ubicación
        JPanel rightPanel = new JPanel();
        rightPanel.setLayout(new BoxLayout(rightPanel, BoxLayout.Y_AXIS));
        rightPanel.setOpaque(false);
        
        // Badge de riesgo
        JLabel riskBadge = new JLabel(riskLevel);
        riskBadge.setFont(new Font("Inter", Font.BOLD, 12));
        riskBadge.setOpaque(true);
        riskBadge.setBorder(new EmptyBorder(4, 12, 4, 12));
        riskBadge.setAlignmentX(Component.RIGHT_ALIGNMENT);
        
        if (riskCode.equalsIgnoreCase("high")) {
            riskBadge.setBackground(new Color(255, 230, 230));
            riskBadge.setForeground(DANGER_RED);
        } else if (riskCode.equalsIgnoreCase("medium")) {
            riskBadge.setBackground(new Color(255, 245, 230));
            riskBadge.setForeground(WARNING_ORANGE);
        } else {
            riskBadge.setBackground(new Color(230, 255, 240));
            riskBadge.setForeground(SECONDARY_GREEN);
        }
        
        // Ubicación
        JLabel locationLabel = new JLabel("📍 " + formatTimestamp(location));
        locationLabel.setFont(new Font("Inter", Font.PLAIN, 11));
        locationLabel.setForeground(TEXT_SECONDARY);
        locationLabel.setAlignmentX(Component.RIGHT_ALIGNMENT);
        
        // Alerta
        JLabel alertLabel = new JLabel("🚨 " + alertLevel);
        alertLabel.setFont(new Font("Inter", Font.PLAIN, 11));
        alertLabel.setForeground(alertLevel.equals("Sin alertas") ? TEXT_SECONDARY : DANGER_RED);
        alertLabel.setAlignmentX(Component.RIGHT_ALIGNMENT);
        
        rightPanel.add(riskBadge);
        rightPanel.add(Box.createVerticalStrut(6));
        rightPanel.add(locationLabel);
        rightPanel.add(Box.createVerticalStrut(2));
        rightPanel.add(alertLabel);
        
        card.add(rightPanel, BorderLayout.EAST);
        
        // Flecha indicadora
        JLabel arrowLabel = new JLabel("→");
        arrowLabel.setFont(new Font("Segoe UI Symbol", Font.PLAIN, 24));
        arrowLabel.setForeground(PRIMARY_BLUE);
        card.add(arrowLabel, BorderLayout.LINE_END);
        
        // Efecto hover
        final Color originalBg = CARD_BACKGROUND;
        final Color hoverBg = new Color(240, 245, 255);
        
        card.addMouseListener(new java.awt.event.MouseAdapter() {
            @Override
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                card.setBackground(hoverBg);
                card.setBorder(new CompoundBorder(
                    new LineBorder(PRIMARY_BLUE, 2, true),
                    new EmptyBorder(19, 19, 19, 19)
                ));
            }
            
            @Override
            public void mouseExited(java.awt.event.MouseEvent evt) {
                card.setBackground(originalBg);
                card.setBorder(new CompoundBorder(
                    new LineBorder(BORDER_LIGHT, 1, true),
                    new EmptyBorder(20, 20, 20, 20)
                ));
            }
            
            @Override
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                showPatientDetailByData(patientData);
            }
        });
        
        return card;
    }
    
    private void updateMap() {
        if (mapPanel == null || patientsData == null) return;
        
        System.out.println("[updateMap] Iniciando actualización del mapa...");
        System.out.println("[updateMap] Número de care teams: " + patientsData.size());
        
        // Convertir datos agrupados a formato flat para el mapa
        JsonArray flatPatients = new JsonArray();
        
        for (int i = 0; i < patientsData.size(); i++) {
            JsonObject careTeam = patientsData.get(i).getAsJsonObject();
            System.out.println("[updateMap] Care Team " + i + ": " + (careTeam.has("name") ? careTeam.get("name").getAsString() : "Sin nombre"));
            
            if (careTeam.has("patients") && careTeam.get("patients").isJsonArray()) {
                JsonArray patients = careTeam.getAsJsonArray("patients");
                System.out.println("  → Tiene " + patients.size() + " pacientes");
                
                for (int j = 0; j < patients.size(); j++) {
                    JsonObject patient = patients.get(j).getAsJsonObject();
                    System.out.println("    → Paciente " + j + ": " + (patient.has("name") ? patient.get("name").getAsString() : "Sin nombre"));
                    
                    // Verificar si tiene ubicación válida dentro del objeto location
                    if (patient.has("location") && patient.get("location").isJsonObject()) {
                        JsonObject location = patient.getAsJsonObject("location");
                        System.out.println("      → Tiene objeto location");
                        System.out.println("      → Location keys: " + location.keySet().toString());
                        
                        if (location.has("latitude") && location.has("longitude")
                                && !location.get("latitude").isJsonNull()
                                && !location.get("longitude").isJsonNull()) {
                            
                            System.out.println("      → ✓ Tiene coordenadas válidas: " + 
                                location.get("latitude").getAsString() + ", " + 
                                location.get("longitude").getAsString());
                            
                            // Crear copia del paciente con datos aplanados para el mapa
                            JsonObject flatPatient = new JsonObject();
                            
                            // Copiar datos básicos del paciente
                            if (patient.has("id")) flatPatient.add("id", patient.get("id"));
                            if (patient.has("name")) flatPatient.add("name", patient.get("name"));
                            if (patient.has("email")) flatPatient.add("email", patient.get("email"));
                            
                            // Agregar coordenadas al nivel raíz (formato esperado por el mapa)
                            flatPatient.add("latitude", location.get("latitude"));
                            flatPatient.add("longitude", location.get("longitude"));
                            
                            // Agregar referencia al care team
                            flatPatient.addProperty("care_team_name", 
                                    careTeam.has("name") ? careTeam.get("name").getAsString() : "Sin nombre");
                            
                            // Agregar risk level si existe
                            if (patient.has("risk_level")) {
                                flatPatient.add("risk_level", patient.get("risk_level"));
                            }
                            
                            // Agregar último alert si existe
                            if (patient.has("last_alert")) {
                                flatPatient.add("last_alert", patient.get("last_alert"));
                            }
                            
                            flatPatients.add(flatPatient);
                        } else {
                            System.out.println("      → ✗ No tiene coordenadas válidas");
                        }
                    } else {
                        System.out.println("      → ✗ No tiene objeto location");
                    }
                }
            } else {
                System.out.println("  → ✗ No tiene array de pacientes");
            }
        }
        
        // Debug: Imprimir cantidad de pacientes con ubicación
        System.out.println("📍 OrgPatientsTab - Pacientes con ubicación para el mapa: " + flatPatients.size());
        if (flatPatients.size() > 0) {
            System.out.println("   Primer paciente: " + flatPatients.get(0).toString());
        }
        
        // Actualizar mapa
        mapPanel.updateLocations(flatPatients);
    }
    
    private void applyFilters() {
        updateTable();
        updateMap();
    }
    
    private String formatTimestamp(String timestamp) {
        // TODO: Implementar formato de fecha relativo
        if (timestamp == null || timestamp.equals("Sin ubicación")) {
            return timestamp;
        }
        // Por ahora retornar como está
        return timestamp.length() > 19 ? timestamp.substring(0, 19) : timestamp;
    }
    
    /**
     * Muestra el detalle completo del paciente seleccionado en un modal.
     * @deprecated Ya no se usa el modelo de tabla. Usar showPatientDetailByData() en su lugar.
     */
    @Deprecated
    private void showPatientDetail(int row) {
        // MÉTODO DEPRECADO - Ya no usamos tabla, ahora usamos tarjetas
        // Este método se mantiene por compatibilidad pero no se llama
    }
    
    /**
     * Muestra el detalle del paciente a partir del objeto JSON completo.
     * Método usado por las tarjetas de pacientes (cards).
     */
    private void showPatientDetailByData(JsonObject patientData) {
        if (patientData == null) {
            snackbarHandler.accept("Datos de paciente inválidos", false);
            return;
        }
        
        String patientId = patientData.has("id") ? patientData.get("id").getAsString() : "";
        String patientName = patientData.has("name") ? patientData.get("name").getAsString() : "Sin nombre";
        
        if (patientId.isEmpty()) {
            snackbarHandler.accept("ID de paciente inválido", false);
            return;
        }
        
        // Cargar detalles completos del paciente en background
        SwingUtilities.invokeLater(() -> {
            loadPatientDetailsAndShowModal(patientId, patientName);
        });
    }
    
    /**
     * Busca un paciente por nombre en los datos cargados.
     */
    private JsonObject findPatientByName(String name) {
        if (patientsData == null) return null;
        
        for (int i = 0; i < patientsData.size(); i++) {
            JsonObject careTeam = patientsData.get(i).getAsJsonObject();
            if (careTeam.has("patients") && careTeam.get("patients").isJsonArray()) {
                JsonArray patients = careTeam.getAsJsonArray("patients");
                for (int j = 0; j < patients.size(); j++) {
                    JsonObject patient = patients.get(j).getAsJsonObject();
                    String patientName = patient.has("name") ? patient.get("name").getAsString() : "";
                    if (patientName.equals(name)) {
                        return patient;
                    }
                }
            }
        }
        return null;
    }
    
    /**
     * Carga los detalles completos del paciente y muestra el modal.
     */
    private void loadPatientDetailsAndShowModal(String patientId, String patientName) {
        // Crear un dialog de loading
        JDialog loadingDialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(this), "Cargando...", true);
        loadingDialog.setLayout(new BorderLayout());
        loadingDialog.setSize(300, 100);
        loadingDialog.setLocationRelativeTo(SwingUtilities.getWindowAncestor(this));
        
        JLabel loadingLabel = new JLabel("Cargando detalles del paciente...", SwingConstants.CENTER);
        loadingLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        loadingDialog.add(loadingLabel, BorderLayout.CENTER);
        
        // Cargar en background thread
        new Thread(() -> {
            try {
                // Llamadas API usando los métodos específicos del ApiClient
                JsonObject detailResponse = apiClient.getOrganizationPatientDetail(accessToken, organization.getOrgId(), patientId);
                JsonObject alertsResponse = apiClient.getOrganizationPatientAlerts(accessToken, organization.getOrgId(), patientId, 10);
                JsonObject notesResponse = apiClient.getOrganizationPatientNotes(accessToken, organization.getOrgId(), patientId, 10);
                
                // Cerrar loading dialog
                SwingUtilities.invokeLater(() -> {
                    loadingDialog.dispose();
                    
                    // Mostrar modal con los datos
                    showPatientDetailModal(patientId, patientName, detailResponse, alertsResponse, notesResponse);
                });
                
            } catch (Exception e) {
                SwingUtilities.invokeLater(() -> {
                    loadingDialog.dispose();
                    exceptionHandler.accept(e);
                    snackbarHandler.accept("Error al cargar detalles: " + e.getMessage(), false);
                });
            }
        }).start();
        
        loadingDialog.setVisible(true);
    }
    
    /**
     * Muestra el modal con todos los detalles del paciente.
     */
    private void showPatientDetailModal(String patientId, String patientName, 
                                       JsonObject detailResponse, 
                                       JsonObject alertsResponse,
                                       JsonObject notesResponse) {
        
        Frame parentWindow = (Frame) SwingUtilities.getWindowAncestor(this);
        JDialog dialog = new JDialog(parentWindow, "Detalle de Paciente", Dialog.ModalityType.APPLICATION_MODAL);
        dialog.setLayout(new BorderLayout());
        dialog.setSize(1000, 750);
        dialog.setLocationRelativeTo(parentWindow);
        
        // Panel principal con BorderLayout para mejor control del ancho
        JPanel mainPanel = new JPanel(new BorderLayout(0, 24));
        mainPanel.setBackground(GLOBAL_BACKGROUND);
        mainPanel.setBorder(new EmptyBorder(24, 24, 24, 24));
        
        // Extraer datos del paciente
        JsonObject patientData = detailResponse.has("data") && detailResponse.getAsJsonObject("data").has("patient") 
            ? detailResponse.getAsJsonObject("data").getAsJsonObject("patient") 
            : new JsonObject();
        
        String email = patientData.has("email") ? patientData.get("email").getAsString() : "N/A";
        String birthdate = patientData.has("birthdate") && !patientData.get("birthdate").isJsonNull() 
            ? patientData.get("birthdate").getAsString() : "N/A";
        String riskLevel = "N/A";
        String riskCode = "";
        if (patientData.has("risk_level") && patientData.get("risk_level").isJsonObject()) {
            JsonObject risk = patientData.getAsJsonObject("risk_level");
            if (risk.has("label")) riskLevel = risk.get("label").getAsString();
            if (risk.has("code")) riskCode = risk.get("code").getAsString();
        }
        String sex = "N/A";
        if (patientData.has("sex") && patientData.get("sex").isJsonObject()) {
            JsonObject sexObj = patientData.getAsJsonObject("sex");
            if (sexObj.has("label")) sex = sexObj.get("label").getAsString();
        }
        String photoUrl = patientData.has("profile_photo_url") && !patientData.get("profile_photo_url").isJsonNull()
            ? patientData.get("profile_photo_url").getAsString() : null;
        
        // Header con info del paciente (en NORTH)
        JPanel headerPanel = createPatientHeaderPanel(patientName, email, birthdate, sex, riskLevel, riskCode, photoUrl);
        mainPanel.add(headerPanel, BorderLayout.NORTH);
        
        // Grid de 2 columnas: Alertas | Notas (en CENTER para que ocupe todo el ancho)
        JPanel gridPanel = new JPanel(new GridLayout(1, 2, 24, 0));
        gridPanel.setOpaque(false);
        
        // Columna 1: Alertas Recientes
        JPanel alertsSection = createAlertsSection(alertsResponse);
        gridPanel.add(alertsSection);
        
        // Columna 2: Notas
        JPanel notesSection = createNotesSection(notesResponse);
        gridPanel.add(notesSection);
        
        mainPanel.add(gridPanel, BorderLayout.CENTER);
        
        JScrollPane scrollPane = new JScrollPane(mainPanel);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        
        dialog.add(scrollPane, BorderLayout.CENTER);
        
        // Botón de cerrar
        JPanel footerPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        footerPanel.setBackground(Color.WHITE);
        footerPanel.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, false),
            new EmptyBorder(12, 16, 12, 16)
        ));
        
        JButton closeButton = new JButton("Cerrar");
        closeButton.setFont(new Font("Inter", Font.PLAIN, 14));
        closeButton.addActionListener(e -> dialog.dispose());
        footerPanel.add(closeButton);
        
        dialog.add(footerPanel, BorderLayout.SOUTH);
        dialog.setVisible(true);
    }
    
    private JPanel createPatientHeaderPanel(String name, String email, String birthdate, 
                                           String sex, String riskLevel, String riskCode, String photoUrl) {
        JPanel panel = new JPanel(new BorderLayout(24, 0));
        panel.setBackground(CARD_BACKGROUND);
        panel.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, true),
            new EmptyBorder(24, 24, 24, 24)
        ));
        
        // Avatar
        JPanel avatarPanel = createLargeAvatarPanel(name, photoUrl);
        panel.add(avatarPanel, BorderLayout.WEST);
        
        // Info del paciente
        JPanel infoPanel = new JPanel();
        infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));
        infoPanel.setOpaque(false);
        
        JLabel nameLabel = new JLabel(name);
        nameLabel.setFont(new Font("Inter", Font.BOLD, 24));
        nameLabel.setForeground(TEXT_PRIMARY);
        nameLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel emailLabel = new JLabel("✉️ " + email);
        emailLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        emailLabel.setForeground(TEXT_SECONDARY);
        emailLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel birthdateLabel = new JLabel("🎂 " + birthdate);
        birthdateLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        birthdateLabel.setForeground(TEXT_SECONDARY);
        birthdateLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel sexLabel = new JLabel("👤 " + sex);
        sexLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        sexLabel.setForeground(TEXT_SECONDARY);
        sexLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Risk level badge
        JLabel riskBadge = new JLabel(riskLevel);
        riskBadge.setFont(new Font("Inter", Font.BOLD, 12));
        riskBadge.setOpaque(true);
        riskBadge.setBorder(new EmptyBorder(4, 12, 4, 12));
        riskBadge.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        if (riskCode.equalsIgnoreCase("high")) {
            riskBadge.setBackground(new Color(255, 230, 230));
            riskBadge.setForeground(DANGER_RED);
        } else if (riskCode.equalsIgnoreCase("medium")) {
            riskBadge.setBackground(new Color(255, 245, 230));
            riskBadge.setForeground(WARNING_ORANGE);
        } else {
            riskBadge.setBackground(new Color(230, 255, 240));
            riskBadge.setForeground(SECONDARY_GREEN);
        }
        
        infoPanel.add(nameLabel);
        infoPanel.add(Box.createVerticalStrut(8));
        infoPanel.add(emailLabel);
        infoPanel.add(Box.createVerticalStrut(4));
        infoPanel.add(birthdateLabel);
        infoPanel.add(Box.createVerticalStrut(4));
        infoPanel.add(sexLabel);
        infoPanel.add(Box.createVerticalStrut(12));
        infoPanel.add(riskBadge);
        
        panel.add(infoPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createLargeAvatarPanel(String name, String photoUrl) {
        JPanel container = new JPanel(new BorderLayout());
        container.setPreferredSize(new Dimension(120, 120));
        container.setMinimumSize(new Dimension(120, 120));
        container.setMaximumSize(new Dimension(120, 120));
        container.setOpaque(false);
        
        JPanel avatar = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                
                // Dibujar círculo
                g2.setColor(PRIMARY_BLUE);
                g2.fillOval(0, 0, getWidth(), getHeight());
                
                // Dibujar iniciales
                String initials = getInitials(name);
                g2.setColor(Color.WHITE);
                g2.setFont(new Font("Inter", Font.BOLD, 36));
                FontMetrics fm = g2.getFontMetrics();
                int x = (getWidth() - fm.stringWidth(initials)) / 2;
                int y = ((getHeight() - fm.getHeight()) / 2) + fm.getAscent();
                g2.drawString(initials, x, y);
            }
        };
        avatar.setOpaque(false);
        avatar.setPreferredSize(new Dimension(120, 120));
        
        container.add(avatar, BorderLayout.CENTER);
        return container;
    }
    
    private JPanel createAlertsSection(JsonObject alertsResponse) {
        JPanel section = new JPanel();
        section.setLayout(new BoxLayout(section, BoxLayout.Y_AXIS));
        section.setBackground(CARD_BACKGROUND);
        section.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, true),
            new EmptyBorder(16, 16, 16, 16)
        ));
        section.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel titleLabel = new JLabel("🚨 Alertas Recientes");
        titleLabel.setFont(new Font("Inter", Font.BOLD, 18));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        section.add(titleLabel);
        section.add(Box.createVerticalStrut(12));
        
        // Extraer alertas
        JsonArray alerts = new JsonArray();
        if (alertsResponse.has("data") && alertsResponse.getAsJsonObject("data").has("alerts")) {
            alerts = alertsResponse.getAsJsonObject("data").getAsJsonArray("alerts");
        }
        
        if (alerts.size() == 0) {
            JLabel emptyLabel = new JLabel("No hay alertas recientes");
            emptyLabel.setFont(new Font("Inter", Font.ITALIC, 14));
            emptyLabel.setForeground(TEXT_SECONDARY);
            emptyLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
            section.add(emptyLabel);
        } else {
            // Lista de alertas (max 5 visibles)
            JPanel alertsList = new JPanel();
            alertsList.setLayout(new BoxLayout(alertsList, BoxLayout.Y_AXIS));
            alertsList.setOpaque(false);
            
            for (int i = 0; i < Math.min(alerts.size(), 5); i++) {
                JsonObject alert = alerts.get(i).getAsJsonObject();
                JPanel alertCard = createAlertCard(alert);
                alertsList.add(alertCard);
                if (i < Math.min(alerts.size(), 5) - 1) {
                    alertsList.add(Box.createVerticalStrut(8));
                }
            }
            
            JScrollPane scrollPane = new JScrollPane(alertsList);
            scrollPane.setBorder(null);
            scrollPane.setOpaque(false);
            scrollPane.getViewport().setOpaque(false);
            scrollPane.setPreferredSize(new Dimension(Integer.MAX_VALUE, 350));
            section.add(scrollPane);
        }
        
        return section;
    }
    
    private JPanel createAlertCard(JsonObject alert) {
        JPanel card = new JPanel(new BorderLayout(12, 0));
        card.setBackground(new Color(250, 250, 250));
        card.setBorder(new EmptyBorder(12, 12, 12, 12));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 60));
        
        String description = alert.has("description") ? alert.get("description").getAsString() : "Sin descripción";
        String createdAt = alert.has("created_at") ? alert.get("created_at").getAsString() : "N/A";
        String levelLabel = "N/A";
        String levelCode = "";
        
        if (alert.has("level") && alert.get("level").isJsonObject()) {
            JsonObject level = alert.getAsJsonObject("level");
            if (level.has("label")) levelLabel = level.get("label").getAsString();
            if (level.has("code")) levelCode = level.get("code").getAsString();
        }
        
        JLabel descLabel = new JLabel(description);
        descLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        descLabel.setForeground(TEXT_PRIMARY);
        
        JLabel dateLabel = new JLabel(formatTimestamp(createdAt));
        dateLabel.setFont(new Font("Inter", Font.PLAIN, 11));
        dateLabel.setForeground(TEXT_SECONDARY);
        
        JLabel levelBadge = new JLabel(levelLabel);
        levelBadge.setFont(new Font("Inter", Font.BOLD, 11));
        levelBadge.setOpaque(true);
        levelBadge.setBorder(new EmptyBorder(2, 8, 2, 8));
        
        if (levelCode.equalsIgnoreCase("critical") || levelCode.equalsIgnoreCase("high")) {
            levelBadge.setBackground(new Color(255, 230, 230));
            levelBadge.setForeground(DANGER_RED);
        } else if (levelCode.equalsIgnoreCase("medium") || levelCode.equalsIgnoreCase("warning")) {
            levelBadge.setBackground(new Color(255, 245, 230));
            levelBadge.setForeground(WARNING_ORANGE);
        } else {
            levelBadge.setBackground(new Color(230, 245, 255));
            levelBadge.setForeground(PRIMARY_BLUE);
        }
        
        JPanel leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setOpaque(false);
        descLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        dateLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        leftPanel.add(descLabel);
        leftPanel.add(Box.createVerticalStrut(4));
        leftPanel.add(dateLabel);
        
        card.add(leftPanel, BorderLayout.CENTER);
        card.add(levelBadge, BorderLayout.EAST);
        
        return card;
    }
    
    private JPanel createNotesSection(JsonObject notesResponse) {
        JPanel section = new JPanel();
        section.setLayout(new BoxLayout(section, BoxLayout.Y_AXIS));
        section.setBackground(CARD_BACKGROUND);
        section.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, true),
            new EmptyBorder(16, 16, 16, 16)
        ));
        section.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel titleLabel = new JLabel("📝 Notas Médicas");
        titleLabel.setFont(new Font("Inter", Font.BOLD, 18));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        section.add(titleLabel);
        section.add(Box.createVerticalStrut(12));
        
        // Extraer notas
        JsonArray notes = new JsonArray();
        if (notesResponse.has("data") && notesResponse.getAsJsonObject("data").has("notes")) {
            notes = notesResponse.getAsJsonObject("data").getAsJsonArray("notes");
        }
        
        if (notes.size() == 0) {
            JLabel emptyLabel = new JLabel("No hay notas médicas registradas");
            emptyLabel.setFont(new Font("Inter", Font.ITALIC, 14));
            emptyLabel.setForeground(TEXT_SECONDARY);
            emptyLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
            section.add(emptyLabel);
        } else {
            // Lista de notas
            JPanel notesList = new JPanel();
            notesList.setLayout(new BoxLayout(notesList, BoxLayout.Y_AXIS));
            notesList.setOpaque(false);
            
            for (int i = 0; i < Math.min(notes.size(), 5); i++) {
                JsonObject note = notes.get(i).getAsJsonObject();
                JPanel noteCard = createNoteCard(note);
                notesList.add(noteCard);
                if (i < Math.min(notes.size(), 5) - 1) {
                    notesList.add(Box.createVerticalStrut(8));
                }
            }
            
            JScrollPane scrollPane = new JScrollPane(notesList);
            scrollPane.setBorder(null);
            scrollPane.setOpaque(false);
            scrollPane.getViewport().setOpaque(false);
            scrollPane.setPreferredSize(new Dimension(Integer.MAX_VALUE, 350));
            section.add(scrollPane);
        }
        
        return section;
    }
    
    private JPanel createNoteCard(JsonObject note) {
        JPanel card = new JPanel();
        card.setLayout(new BoxLayout(card, BoxLayout.Y_AXIS));
        card.setBackground(new Color(250, 250, 250));
        card.setBorder(new EmptyBorder(12, 12, 12, 12));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 100));
        
        String noteText = note.has("note") && !note.get("note").isJsonNull() ? note.get("note").getAsString() : "Sin nota";
        String onset = note.has("onset") ? note.get("onset").getAsString() : "N/A";
        String eventLabel = "N/A";
        
        if (note.has("event") && note.get("event").isJsonObject()) {
            JsonObject event = note.getAsJsonObject("event");
            if (event.has("label") && !event.get("label").isJsonNull()) {
                eventLabel = event.get("label").getAsString();
            }
        }
        
        String authorName = "Desconocido";
        if (note.has("annotated_by") && note.get("annotated_by").isJsonObject()) {
            JsonObject author = note.getAsJsonObject("annotated_by");
            if (author.has("name") && !author.get("name").isJsonNull()) {
                authorName = author.get("name").getAsString();
            }
        }
        
        JLabel eventLabel_UI = new JLabel("📌 " + eventLabel);
        eventLabel_UI.setFont(new Font("Inter", Font.BOLD, 13));
        eventLabel_UI.setForeground(PRIMARY_BLUE);
        eventLabel_UI.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel noteLabel = new JLabel("<html><body style='width: 100%'>" + noteText + "</body></html>");
        noteLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        noteLabel.setForeground(TEXT_PRIMARY);
        noteLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel metaLabel = new JLabel("👤 " + authorName + "  •  📅 " + formatTimestamp(onset));
        metaLabel.setFont(new Font("Inter", Font.PLAIN, 11));
        metaLabel.setForeground(TEXT_SECONDARY);
        metaLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        card.add(eventLabel_UI);
        card.add(Box.createVerticalStrut(4));
        card.add(noteLabel);
        card.add(Box.createVerticalStrut(6));
        card.add(metaLabel);
        
        return card;
    }
    
    private String getInitials(String name) {
        if (name == null || name.trim().isEmpty()) return "?";
        String[] parts = name.trim().split("\\s+");
        if (parts.length >= 2) {
            return (parts[0].substring(0, 1) + parts[1].substring(0, 1)).toUpperCase();
        }
        return name.substring(0, Math.min(2, name.length())).toUpperCase();
    }
}
