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
 * Muestra TODOS los dispositivos médicos de la organización.
 * 
 * Estructura:
 * - Dispositivos pertenecen a la org (org_id)
 * - Están asignados a pacientes (owner_patient_id)
 * - Pueden estar conectados actualmente con un paciente (current_connection)
 * 
 * Endpoints:
 * - GET /orgs/{org_id}/devices - Lista TODOS los dispositivos de la org
 * - GET /orgs/{org_id}/devices/{device_id} - Detalle de dispositivo
 * - GET /orgs/{org_id}/devices/{device_id}/streams - Historial de conexiones
 * 
 * Layout:
 * - Panel superior: Resumen (Total, Conectados, Desconectados) + Filtros
 * - Tabla: Serial | Marca | Modelo | Paciente Owner | Paciente Actual | Estado | Última Conexión
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
    private final JLabel connectedDevicesLabel = new JLabel("0");
    private final JLabel disconnectedDevicesLabel = new JLabel("0");
    
    // Filtros
    private final JComboBox<String> statusFilter = new JComboBox<>();
    private final JTextField searchField = new JTextField(20);
    
    // Tabla
    private final DefaultTableModel tableModel;
    private final JTable devicesTable;
    
    // Datos
    private List<DeviceRow> allDevices = new ArrayList<>();
    
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
        String[] columnNames = {"Serial", "Marca", "Modelo", "Tipo", "Paciente Owner", "Conectado Con", "Estado"};
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
        
        // Card 2: Conectados
        panel.add(createMetricCard("✅ Conectados", connectedDevicesLabel, SECONDARY_GREEN));
        
        // Card 3: Desconectados
        panel.add(createMetricCard("⚠️ Desconectados", disconnectedDevicesLabel, WARNING_ORANGE));
        
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
        
        // Filtro por estado
        JLabel statusLabel = new JLabel("Estado:");
        statusLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        statusLabel.setForeground(TEXT_PRIMARY);
        
        statusFilter.setPreferredSize(new Dimension(180, 35));
        statusFilter.setFont(new Font("Inter", Font.PLAIN, 13));
        statusFilter.addItem("Todos");
        statusFilter.addItem("Conectados");
        statusFilter.addItem("Desconectados");
        statusFilter.addItem("Activos");
        statusFilter.addItem("Inactivos");
        statusFilter.addActionListener(e -> applyFilters());
        
        // Campo de búsqueda
        JLabel searchLabel = new JLabel("Buscar:");
        searchLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        searchLabel.setForeground(TEXT_PRIMARY);
        
        searchField.setPreferredSize(new Dimension(250, 35));
        searchField.setFont(new Font("Inter", Font.PLAIN, 13));
        searchField.addActionListener(e -> applyFilters());
        
        JButton searchButton = new JButton("🔍");
        searchButton.setPreferredSize(new Dimension(40, 35));
        searchButton.addActionListener(e -> applyFilters());
        
        panel.add(statusLabel);
        panel.add(statusFilter);
        panel.add(Box.createHorizontalStrut(16));
        panel.add(searchLabel);
        panel.add(searchField);
        panel.add(searchButton);
        
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
     * Carga TODOS los dispositivos de la organización directamente
     */
    public void loadData() {
        SwingWorker<JsonArray, Void> worker = new SwingWorker<>() {
            @Override
            protected JsonArray doInBackground() throws Exception {
                // Usar nuevo endpoint: GET /orgs/{org_id}/devices
                JsonObject response = apiClient.getOrganizationDevices(
                        accessToken,
                        organization.getOrgId(),
                        null,  // active: null = todos (activos e inactivos)
                        null   // connected: null = todos (conectados y desconectados)
                );
                
                // Backend retorna: {data: {organization: {...}, devices: [...], pagination}}
                if (response.has("data") && response.get("data").isJsonObject()) {
                    JsonObject data = response.getAsJsonObject("data");
                    if (data.has("devices") && data.get("devices").isJsonArray()) {
                        return data.getAsJsonArray("devices");
                    }
                }
                
                return new JsonArray();
            }
            
            @Override
            protected void done() {
                try {
                    JsonArray devices = get();
                    processDevices(devices);
                    snackbarHandler.accept("Dispositivos cargados: " + allDevices.size(), true);
                } catch (Exception ex) {
                    ex.printStackTrace();
                    exceptionHandler.accept(ex);
                    snackbarHandler.accept("Error al cargar dispositivos: " + ex.getMessage(), false);
                }
            }
        };
        worker.execute();
    }
    
    private void processDevices(JsonArray devices) {
        allDevices.clear();
        
        for (int i = 0; i < devices.size(); i++) {
            JsonObject device = devices.get(i).getAsJsonObject();
            allDevices.add(new DeviceRow(device));
        }
        
        updateSummaryAndTable();
    }
    
    private void updateSummaryAndTable() {
        // Calcular resumen
        int total = allDevices.size();
        int connected = 0;
        int disconnected = 0;
        
        for (DeviceRow device : allDevices) {
            if (device.isConnected) {
                connected++;
            } else {
                disconnected++;
            }
        }
        
        totalDevicesLabel.setText(String.valueOf(total));
        connectedDevicesLabel.setText(String.valueOf(connected));
        disconnectedDevicesLabel.setText(String.valueOf(disconnected));
        
        // Actualizar tabla
        applyFilters();
    }
    
    private void applyFilters() {
        tableModel.setRowCount(0);
        
        String selectedStatus = (String) statusFilter.getSelectedItem();
        String searchText = searchField.getText().trim().toLowerCase();
        
        // Si no hay selección (ej. durante recarga), no aplicar filtros aún
        if (selectedStatus == null) {
            return;
        }
        
        for (DeviceRow device : allDevices) {
            // Filtro por estado
            if (selectedStatus.equals("Conectados") && !device.isConnected) {
                continue;
            }
            if (selectedStatus.equals("Desconectados") && device.isConnected) {
                continue;
            }
            if (selectedStatus.equals("Activos") && !device.isActive) {
                continue;
            }
            if (selectedStatus.equals("Inactivos") && device.isActive) {
                continue;
            }
            
            // Filtro por búsqueda (serial, marca, modelo, paciente)
            if (!searchText.isEmpty()) {
                boolean matches = device.serial.toLowerCase().contains(searchText) ||
                                device.brand.toLowerCase().contains(searchText) ||
                                device.model.toLowerCase().contains(searchText) ||
                                device.ownerPatientName.toLowerCase().contains(searchText) ||
                                (device.currentPatientName != null && device.currentPatientName.toLowerCase().contains(searchText));
                if (!matches) {
                    continue;
                }
            }
            
            // Agregar fila
            tableModel.addRow(new Object[]{
                    device.serial,
                    device.brand,
                    device.model,
                    device.deviceType,
                    device.ownerPatientName,
                    device.getCurrentPatientText(),
                    device.getStatusText()
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
        String deviceType;
        boolean isActive;
        boolean isConnected;
        
        // Paciente propietario del dispositivo
        String ownerPatientName;
        
        // Paciente con stream activo (puede ser diferente al owner)
        String currentPatientName;
        String connectionStartedAt;
        
        int totalStreams;
        
        DeviceRow(JsonObject device) {
            this.serial = device.has("serial") && !device.get("serial").isJsonNull()
                    ? device.get("serial").getAsString() : "N/A";
            this.brand = device.has("brand") && !device.get("brand").isJsonNull()
                    ? device.get("brand").getAsString() : "N/A";
            this.model = device.has("model") && !device.get("model").isJsonNull()
                    ? device.get("model").getAsString() : "N/A";
            this.isActive = device.has("active") && device.get("active").getAsBoolean();
            this.isConnected = device.has("connected") && device.get("connected").getAsBoolean();
            
            // Tipo de dispositivo
            if (device.has("type") && device.get("type").isJsonObject()) {
                JsonObject type = device.getAsJsonObject("type");
                this.deviceType = type.has("label") && !type.get("label").isJsonNull()
                        ? type.get("label").getAsString() : "N/A";
            } else {
                this.deviceType = "N/A";
            }
            
            // Paciente owner
            if (device.has("owner") && device.get("owner").isJsonObject()) {
                JsonObject owner = device.getAsJsonObject("owner");
                this.ownerPatientName = owner.has("name") && !owner.get("name").isJsonNull()
                        ? owner.get("name").getAsString() : "Sin asignar";
            } else {
                this.ownerPatientName = "Sin asignar";
            }
            
            // Conexión actual
            if (device.has("current_connection") && !device.get("current_connection").isJsonNull()) {
                JsonObject currentConn = device.getAsJsonObject("current_connection");
                this.currentPatientName = currentConn.has("patient_name") && !currentConn.get("patient_name").isJsonNull()
                        ? currentConn.get("patient_name").getAsString() : null;
                this.connectionStartedAt = currentConn.has("started_at") && !currentConn.get("started_at").isJsonNull()
                        ? currentConn.get("started_at").getAsString() : null;
            }
            
            // Streams
            if (device.has("streams") && device.get("streams").isJsonObject()) {
                JsonObject streams = device.getAsJsonObject("streams");
                this.totalStreams = streams.has("total") ? streams.get("total").getAsInt() : 0;
            }
        }
        
        String getCurrentPatientText() {
            if (!isConnected || currentPatientName == null) {
                return "—";
            }
            
            String text = currentPatientName;
            if (connectionStartedAt != null) {
                text += " (desde " + formatTimestamp(connectionStartedAt) + ")";
            }
            return text;
        }
        
        String getStatusText() {
            if (!isActive) {
                return "❌ Inactivo";
            }
            
            if (isConnected) {
                return "✅ Conectado";
            }
            
            return "⚠️ Desconectado";
        }
        
        private String formatTimestamp(String timestamp) {
            if (timestamp == null) return "N/A";
            // Formato simple: 2025-11-23T08:15:00 -> 2025-11-23 08:15
            return timestamp.length() > 19 ? timestamp.substring(0, 19).replace('T', ' ') : timestamp;
        }
    }
}
