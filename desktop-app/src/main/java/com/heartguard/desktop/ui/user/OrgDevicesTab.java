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
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Tab de Dispositivos de una organización.
 * Muestra TODOS los dispositivos médicos de los care teams de la org.
 * 
 * Estructura:
 * - Dispositivos pertenecen a la org (org_id)
 * - Están asignados a pacientes (owner_patient_id)
 * - Pacientes están en care teams
 * 
 * Endpoints:
 * - GET /orgs/{org_id}/care-teams - Lista de care teams
 * - GET /orgs/{org_id}/care-teams/{team_id}/devices - Dispositivos del team
 * - GET /orgs/{org_id}/care-teams/{team_id}/devices/disconnected - Desconectados
 * 
 * Layout:
 * - Panel superior: Resumen (Total, Activos, Desconectados) + Filtros
 * - Tabla: Serial | Marca | Modelo | Care Team | Paciente | Estado | Última Conexión
 */
public class OrgDevicesTab extends JPanel {
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
    
    // Componentes de resumen
    private final JLabel totalDevicesLabel = new JLabel("0");
    private final JLabel activeDevicesLabel = new JLabel("0");
    private final JLabel disconnectedDevicesLabel = new JLabel("0");
    
    // Filtros
    private final JComboBox<String> careTeamFilter = new JComboBox<>();
    private final JCheckBox showOnlyDisconnectedFilter = new JCheckBox("Solo desconectados");
    
    // Tabla
    private final DefaultTableModel tableModel;
    private final JTable devicesTable;
    
    // Datos
    private JsonArray careTeams; // Lista de care teams
    private List<DeviceRow> allDevices = new ArrayList<>(); // Todos los dispositivos
    private Map<String, String> careTeamsMap = new HashMap<>(); // id -> nombre
    
    public OrgDevicesTab(
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
        
        // Modelo de tabla
        String[] columnNames = {"Serial", "Marca", "Modelo", "Care Team", "Paciente", "Estado", "Última Conexión"};
        tableModel = new DefaultTableModel(columnNames, 0) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return false;
            }
        };
        
        devicesTable = new JTable(tableModel);
        devicesTable.setRowHeight(40);
        devicesTable.setFont(new Font("Inter", Font.PLAIN, 13));
        devicesTable.getTableHeader().setFont(new Font("Inter", Font.BOLD, 13));
        devicesTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        
        initUI();
    }
    
    private void initUI() {
        JPanel mainContent = new JPanel();
        mainContent.setLayout(new BoxLayout(mainContent, BoxLayout.Y_AXIS));
        mainContent.setOpaque(false);
        
        // Título
        JLabel titleLabel = new JLabel("📱 Dispositivos Médicos");
        titleLabel.setFont(new Font("Inter", Font.BOLD, 24));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(titleLabel);
        mainContent.add(Box.createVerticalStrut(8));
        
        JLabel subtitleLabel = new JLabel("Dispositivos de todos los care teams de la organización");
        subtitleLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        subtitleLabel.setForeground(TEXT_SECONDARY);
        subtitleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(subtitleLabel);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Cards de resumen
        JPanel summaryPanel = createSummaryPanel();
        summaryPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(summaryPanel);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Filtros
        JPanel filtersPanel = createFiltersPanel();
        filtersPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(filtersPanel);
        mainContent.add(Box.createVerticalStrut(16));
        
        // Tabla de dispositivos
        JPanel tableCard = createTableCard();
        tableCard.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(tableCard);
        mainContent.add(Box.createVerticalGlue());
        
        // ScrollPane
        JScrollPane scrollPane = new JScrollPane(mainContent);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        scrollPane.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        scrollPane.getViewport().setBackground(GLOBAL_BACKGROUND);
        
        add(scrollPane, BorderLayout.CENTER);
    }
    
    private JPanel createSummaryPanel() {
        JPanel panel = new JPanel(new GridLayout(1, 3, 16, 0));
        panel.setOpaque(false);
        panel.setMaximumSize(new Dimension(Integer.MAX_VALUE, 120));
        
        // Card 1: Total Dispositivos
        panel.add(createMetricCard("📊 Total Dispositivos", totalDevicesLabel, PRIMARY_BLUE));
        
        // Card 2: Activos
        panel.add(createMetricCard("✅ Activos", activeDevicesLabel, SECONDARY_GREEN));
        
        // Card 3: Desconectados
        panel.add(createMetricCard("⚠️ Desconectados", disconnectedDevicesLabel, DANGER_RED));
        
        return panel;
    }
    
    private JPanel createMetricCard(String title, JLabel valueLabel, Color accentColor) {
        JPanel card = new JPanel();
        card.setLayout(new BorderLayout(12, 8));
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 24, 20, 24)
        ));
        
        // Título
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        titleLabel.setForeground(TEXT_SECONDARY);
        card.add(titleLabel, BorderLayout.NORTH);
        
        // Valor
        valueLabel.setFont(new Font("Inter", Font.BOLD, 36));
        valueLabel.setForeground(accentColor);
        card.add(valueLabel, BorderLayout.CENTER);
        
        return card;
    }
    
    private JPanel createFiltersPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT, 16, 0));
        panel.setOpaque(false);
        panel.setMaximumSize(new Dimension(Integer.MAX_VALUE, 50));
        
        // Filtro por Care Team
        JLabel careTeamLabel = new JLabel("Care Team:");
        careTeamLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        careTeamLabel.setForeground(TEXT_PRIMARY);
        
        careTeamFilter.setPreferredSize(new Dimension(250, 35));
        careTeamFilter.setFont(new Font("Inter", Font.PLAIN, 13));
        careTeamFilter.addItem("Todos");
        careTeamFilter.addActionListener(e -> applyFilters());
        
        // Checkbox desconectados
        showOnlyDisconnectedFilter.setFont(new Font("Inter", Font.PLAIN, 13));
        showOnlyDisconnectedFilter.setOpaque(false);
        showOnlyDisconnectedFilter.addActionListener(e -> applyFilters());
        
        panel.add(careTeamLabel);
        panel.add(careTeamFilter);
        panel.add(Box.createHorizontalStrut(8));
        panel.add(showOnlyDisconnectedFilter);
        
        return panel;
    }
    
    private JPanel createTableCard() {
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 20, 20, 20)
        ));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 500));
        
        // Header
        JLabel headerLabel = new JLabel("Lista de Dispositivos");
        headerLabel.setFont(new Font("Inter", Font.BOLD, 16));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        card.add(headerLabel, BorderLayout.NORTH);
        
        // Tabla con scroll
        JScrollPane tableScroll = new JScrollPane(devicesTable);
        tableScroll.setBorder(null);
        card.add(tableScroll, BorderLayout.CENTER);
        
        return card;
    }
    
    /**
     * Carga dispositivos de todos los care teams de la organización
     */
    public void loadData() {
        // Paso 1: Obtener lista de care teams
        SwingWorker<JsonArray, Void> worker = new SwingWorker<>() {
            @Override
            protected JsonArray doInBackground() throws Exception {
                JsonObject response = apiClient.getOrganizationCareTeams(accessToken, organization.getOrgId());
                
                // Backend retorna: {data: {organization: {...}, care_teams: [...]}}
                if (response.has("data") && response.get("data").isJsonObject()) {
                    JsonObject data = response.getAsJsonObject("data");
                    if (data.has("care_teams") && data.get("care_teams").isJsonArray()) {
                        return data.getAsJsonArray("care_teams");
                    }
                }
                
                return new JsonArray();
            }
            
            @Override
            protected void done() {
                try {
                    careTeams = get();
                    processCareTeams();
                    loadDevicesForAllTeams();
                } catch (Exception ex) {
                    ex.printStackTrace();
                    exceptionHandler.accept(ex);
                }
            }
        };
        worker.execute();
    }
    
    private void processCareTeams() {
        careTeamsMap.clear();
        careTeamFilter.removeAllItems();
        careTeamFilter.addItem("Todos");
        
        if (careTeams == null) return;
        
        // Extraer care teams únicos
        Map<String, String> uniqueTeams = new HashMap<>();
        
        for (int i = 0; i < careTeams.size(); i++) {
            JsonObject teamObj = careTeams.get(i).getAsJsonObject();
            String teamId = teamObj.has("id") ? teamObj.get("id").getAsString() : "";
            String teamName = teamObj.has("name") ? teamObj.get("name").getAsString() : "Sin nombre";
            
            if (!teamId.isEmpty() && !uniqueTeams.containsKey(teamId)) {
                uniqueTeams.put(teamId, teamName);
                careTeamsMap.put(teamId, teamName);
            }
        }
        
        // Agregar al filtro
        for (String teamName : uniqueTeams.values()) {
            careTeamFilter.addItem(teamName);
        }
    }
    
    /**
     * Carga dispositivos de todos los care teams en paralelo
     */
    private void loadDevicesForAllTeams() {
        allDevices.clear();
        
        if (careTeamsMap.isEmpty()) {
            updateSummaryAndTable();
            snackbarHandler.accept("No hay care teams disponibles", false);
            return;
        }
        
        // Crear lista de futures para cargar en paralelo
        List<CompletableFuture<Void>> futures = new ArrayList<>();
        
        for (Map.Entry<String, String> entry : careTeamsMap.entrySet()) {
            String teamId = entry.getKey();
            String teamName = entry.getValue();
            
            CompletableFuture<Void> future = CompletableFuture.runAsync(() -> {
                try {
                    // Obtener dispositivos del care team
                    JsonObject response = apiClient.getOrganizationCareTeamDevices(
                            accessToken,
                            organization.getOrgId(),
                            teamId
                    );
                    
                    
                    // Backend retorna: {data: {organization, care_team, devices: [...], pagination}}
                    if (response.has("data") && response.get("data").isJsonObject()) {
                        JsonObject data = response.getAsJsonObject("data");
                        if (data.has("devices") && data.get("devices").isJsonArray()) {
                            JsonArray devices = data.getAsJsonArray("devices");
                            
                            synchronized (allDevices) {
                                for (int i = 0; i < devices.size(); i++) {
                                    JsonObject device = devices.get(i).getAsJsonObject();
                                    allDevices.add(new DeviceRow(device, teamId, teamName));
                                }
                            }
                        }
                    }
                } catch (Exception e) {
                    System.err.println("Error cargando dispositivos del team " + teamName + ": " + e.getMessage());
                    e.printStackTrace();
                }
            });
            
            futures.add(future);
        }
        
        // Esperar a que terminen todas las cargas
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
                .thenRun(() -> SwingUtilities.invokeLater(() -> {
                    updateSummaryAndTable();
                    snackbarHandler.accept("Dispositivos cargados: " + allDevices.size(), true);
                }))
                .exceptionally(ex -> {
                    SwingUtilities.invokeLater(() -> {
                        exceptionHandler.accept((Exception) ex);
                    });
                    return null;
                });
    }
    
    private void updateSummaryAndTable() {
        // Calcular resumen
        int total = allDevices.size();
        int active = 0;
        int disconnected = 0;
        
        for (DeviceRow device : allDevices) {
            if (device.isActive) {
                // Un dispositivo está desconectado si tiene última conexión antigua
                if (device.isDisconnected()) {
                    disconnected++;
                } else {
                    active++;
                }
            }
        }
        
        totalDevicesLabel.setText(String.valueOf(total));
        activeDevicesLabel.setText(String.valueOf(active));
        disconnectedDevicesLabel.setText(String.valueOf(disconnected));
        
        // Actualizar tabla
        applyFilters();
    }
    
    private void applyFilters() {
        tableModel.setRowCount(0);
        
        String selectedTeam = (String) careTeamFilter.getSelectedItem();
        boolean onlyDisconnected = showOnlyDisconnectedFilter.isSelected();
        
        // Si no hay selección (ej. durante recarga), no aplicar filtros aún
        if (selectedTeam == null) {
            return;
        }
        
        for (DeviceRow device : allDevices) {
            // Filtro por care team
            if (!selectedTeam.equals("Todos") && !device.careTeamName.equals(selectedTeam)) {
                continue;
            }
            
            // Filtro por desconectados
            if (onlyDisconnected && !device.isDisconnected()) {
                continue;
            }
            
            // Agregar fila
            tableModel.addRow(new Object[]{
                    device.serial,
                    device.brand,
                    device.model,
                    device.careTeamName,
                    device.patientName,
                    device.getStatusText(),
                    device.getLastConnectionText()
            });
        }
    }
    
    /**
     * Clase interna para representar una fila de dispositivo
     */
    private static class DeviceRow {
        String serial;
        String brand;
        String model;
        String careTeamId;
        String careTeamName;
        String patientName;
        boolean isActive;
        String lastStartedAt;
        String lastEndedAt;
        
        DeviceRow(JsonObject device, String teamId, String teamName) {
            this.careTeamId = teamId;
            this.careTeamName = teamName;
            
            this.serial = device.has("serial") && !device.get("serial").isJsonNull()
                    ? device.get("serial").getAsString() : "N/A";
            this.brand = device.has("brand") && !device.get("brand").isJsonNull()
                    ? device.get("brand").getAsString() : "N/A";
            this.model = device.has("model") && !device.get("model").isJsonNull()
                    ? device.get("model").getAsString() : "N/A";
            this.patientName = device.has("patient_name") && !device.get("patient_name").isJsonNull()
                    ? device.get("patient_name").getAsString() : "Sin asignar";
            this.isActive = device.has("active") && device.get("active").getAsBoolean();
            this.lastStartedAt = device.has("last_started_at") && !device.get("last_started_at").isJsonNull()
                    ? device.get("last_started_at").getAsString() : null;
            this.lastEndedAt = device.has("last_ended_at") && !device.get("last_ended_at").isJsonNull()
                    ? device.get("last_ended_at").getAsString() : null;
        }
        
        boolean isDisconnected() {
            // Un dispositivo está desconectado si:
            // 1. No tiene streams (lastStartedAt == null)
            // 2. El último stream terminó (lastEndedAt != null)
            return lastStartedAt == null || lastEndedAt != null;
        }
        
        String getStatusText() {
            if (!isActive) {
                return "❌ Inactivo";
            }
            
            if (isDisconnected()) {
                return "⚠️ Desconectado";
            }
            
            return "✅ Conectado";
        }
        
        String getLastConnectionText() {
            if (lastStartedAt == null) {
                return "Nunca conectado";
            }
            
            if (lastEndedAt != null) {
                // Terminó - mostrar cuándo desconectó
                return "Desconectó: " + formatTimestamp(lastEndedAt);
            }
            
            // Conectado actualmente
            return "Desde: " + formatTimestamp(lastStartedAt);
        }
        
        private String formatTimestamp(String timestamp) {
            // TODO: Implementar formato de fecha relativo
            if (timestamp == null) return "N/A";
            return timestamp.length() > 19 ? timestamp.substring(0, 19).replace('T', ' ') : timestamp;
        }
    }
}
