package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.alert.Alert;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Ventana modal con diseño profesional para mostrar detalles clínicos de un paciente.
 * Bordes redondeados 12px, sombra difusa, paleta médica, tipografía 14-16px.
 */
public class PatientDetailDialog extends JDialog {
    // Paleta médica profesional
    private static final Color GLOBAL_BG = new Color(247, 249, 251);
    private static final Color CARD_BG = Color.WHITE;
    private static final Color PRIMARY_BLUE = new Color(0, 120, 215);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER_LIGHT = new Color(223, 227, 230);
    private static final Color SUCCESS_GREEN = new Color(40, 167, 69);
    private static final Color DANGER_RED = new Color(220, 53, 69);

    private static final Font TITLE_FONT = new Font("Inter", Font.BOLD, 20);
    private static final Font BODY_FONT = new Font("Inter", Font.PLAIN, 14);
    private static final Font CAPTION_FONT = new Font("Inter", Font.PLAIN, 13);

    private final ApiClient apiClient;
    private final String token;
    private final String orgId;
    private final String patientId;
    private final String patientName;

    private final JLabel statusLabel = new JLabel(" ");
    private final JTextArea infoArea = new JTextArea();
    private final DefaultListModel<String> alertsModel = new DefaultListModel<>();
    private final DefaultListModel<String> notesModel = new DefaultListModel<>();
    private VitalSignsChartPanel chartPanel;
    
    // Alertas cargadas con metadata completa
    private JsonArray loadedAlerts = new JsonArray();
    
    // Dispositivos del paciente
    private java.util.List<DeviceInfo> patientDevices = new java.util.ArrayList<>();
    private JPanel chartContainerPanel;
    private JComboBox<String> deviceSelector;
    private JLabel deviceInfoLabel;
    
    // Caché de paneles de gráficas por dispositivo (para evitar reconstrucción)
    private final java.util.Map<String, VitalSignsChartPanel> chartPanelCache = new java.util.HashMap<>();

    public PatientDetailDialog(Frame owner, ApiClient apiClient, String token, String orgId, String patientId, String patientName) {
        super(owner, "Paciente: " + patientName, true);
        this.apiClient = apiClient;
        this.token = token;
        this.orgId = orgId;
        this.patientId = patientId;
        this.patientName = patientName;
        
        System.out.println("Initializing patient detail for: " + patientName + " (ID: " + patientId + ")");
        
        initComponents();
        loadData();
    }

    private void initComponents() {
        // Ventana maximizada para mejor visualización
        Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
        int width = (int) (screenSize.width * 0.9);  // 90% del ancho de pantalla
        int height = (int) (screenSize.height * 0.9); // 90% del alto de pantalla
        setSize(width, height);
        setLocationRelativeTo(getOwner());
        setLayout(new BorderLayout());
        getContentPane().setBackground(GLOBAL_BG);
        setMinimumSize(new Dimension(1400, 900));

        // Encabezado compacto con título y separador
        JPanel header = new JPanel(new BorderLayout());
        header.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, false),
            new EmptyBorder(12, 20, 12, 20)  // Reducido padding
        ));
        header.setBackground(CARD_BG);

        JLabel title = new JLabel("📋 " + patientName);
        title.setFont(new Font("Inter", Font.BOLD, 18));  // Un solo título
        title.setForeground(TEXT_PRIMARY);
        header.add(title, BorderLayout.WEST);

        add(header, BorderLayout.NORTH);

        // Panel principal con scroll para contener tabs y gráficas
        JPanel mainPanel = new JPanel(new BorderLayout(0, 8));
        mainPanel.setOpaque(false);
        mainPanel.setBorder(new EmptyBorder(0, 12, 12, 12));  // Reducido padding

        // Tabs estilizados para métricas, alertas y notas
        JTabbedPane tabs = new JTabbedPane();
        tabs.setFont(new Font("Inter", Font.PLAIN, 14));
        tabs.setBackground(new Color(240, 242, 245));
        tabs.setForeground(TEXT_PRIMARY);
        tabs.setPreferredSize(new Dimension(0, 150)); // Muy reducido para maximizar gráficas

        infoArea.setEditable(false);
        infoArea.setLineWrap(true);
        infoArea.setWrapStyleWord(true);
        infoArea.setFont(BODY_FONT);
        infoArea.setMargin(new Insets(16, 16, 16, 16));
        infoArea.setBackground(CARD_BG);
        infoArea.setBorder(new EmptyBorder(8, 8, 8, 8));
        JScrollPane infoScroll = new JScrollPane(infoArea);
        infoScroll.setBorder(new LineBorder(BORDER_LIGHT, 1));
        tabs.addTab("MÉTRICAS", infoScroll);

        JList<String> alertsList = new JList<>(alertsModel);
        alertsList.setFont(BODY_FONT);
        alertsList.setBackground(CARD_BG);
        alertsList.setBorder(new EmptyBorder(8, 8, 8, 8));
        alertsList.setFixedCellHeight(50);
        
        // Panel para alertas con botón de validación
        JPanel alertsPanel = new JPanel(new BorderLayout(0, 8));
        alertsPanel.setOpaque(false);
        
        JScrollPane alertsScroll = new JScrollPane(alertsList);
        alertsScroll.setBorder(new LineBorder(BORDER_LIGHT, 1));
        alertsPanel.add(alertsScroll, BorderLayout.CENTER);
        
        // Botón para validar alerta seleccionada
        JButton validateAlertButton = new JButton("🔍 Validar Alerta Seleccionada");
        validateAlertButton.setFont(new Font("Inter", Font.BOLD, 13));
        validateAlertButton.setBackground(PRIMARY_BLUE);
        validateAlertButton.setForeground(Color.WHITE);
        validateAlertButton.setFocusPainted(false);
        validateAlertButton.setBorder(new EmptyBorder(10, 16, 10, 16));
        validateAlertButton.addActionListener(e -> validateSelectedAlert(alertsList.getSelectedIndex()));
        alertsPanel.add(validateAlertButton, BorderLayout.SOUTH);
        
        tabs.addTab("ALERTAS", alertsPanel);

        JList<String> notesList = new JList<>(notesModel);
        notesList.setFont(BODY_FONT);
        notesList.setBackground(CARD_BG);
        notesList.setBorder(new EmptyBorder(8, 8, 8, 8));
        JScrollPane notesScroll = new JScrollPane(notesList);
        notesScroll.setBorder(new LineBorder(BORDER_LIGHT, 1));
        tabs.addTab("NOTAS", notesScroll);

        mainPanel.add(tabs, BorderLayout.NORTH);

        // Panel de gráficas en tiempo real
        chartContainerPanel = new JPanel(new BorderLayout());
        chartContainerPanel.setOpaque(false);
        chartContainerPanel.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, true),
            new EmptyBorder(8, 8, 8, 8)
        ));

        // Título y selector de dispositivo
        JPanel headerPanel = new JPanel(new BorderLayout(12, 0));
        headerPanel.setOpaque(false);
        
        JLabel chartTitle = new JLabel("📊 Signos Vitales en Tiempo Real");
        chartTitle.setFont(new Font("Inter", Font.BOLD, 18));
        chartTitle.setForeground(TEXT_PRIMARY);
        chartTitle.setBorder(new EmptyBorder(8, 0, 8, 0));
        headerPanel.add(chartTitle, BorderLayout.WEST);
        
        // Panel para selector de dispositivo e info
        JPanel devicePanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        devicePanel.setOpaque(false);
        
        deviceInfoLabel = new JLabel("");
        deviceInfoLabel.setFont(new Font("Inter", Font.PLAIN, 12));
        deviceInfoLabel.setForeground(TEXT_SECONDARY);
        devicePanel.add(deviceInfoLabel);
        
        deviceSelector = new JComboBox<>();
        deviceSelector.setFont(new Font("Inter", Font.PLAIN, 13));
        deviceSelector.setVisible(false); // Oculto por defecto
        deviceSelector.addActionListener(e -> onDeviceSelected());
        devicePanel.add(deviceSelector);
        
        headerPanel.add(devicePanel, BorderLayout.EAST);
        headerPanel.setBorder(new EmptyBorder(0, 0, 8, 0));
        
        chartContainerPanel.add(headerPanel, BorderLayout.NORTH);

        // Placeholder para gráficas (se carga después de obtener dispositivos)
        JLabel loadingLabel = new JLabel("Cargando información de dispositivos...");
        loadingLabel.setHorizontalAlignment(SwingConstants.CENTER);
        loadingLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        loadingLabel.setForeground(TEXT_SECONDARY);
        chartContainerPanel.add(loadingLabel, BorderLayout.CENTER);

        mainPanel.add(chartContainerPanel, BorderLayout.CENTER);

        add(mainPanel, BorderLayout.CENTER);

        // Footer compacto con estado y botón cerrar
        JPanel footer = new JPanel(new BorderLayout());
        footer.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, false),
            new EmptyBorder(10, 20, 10, 20)  // Reducido padding
        ));
        footer.setBackground(CARD_BG);

        statusLabel.setFont(CAPTION_FONT);
        statusLabel.setForeground(TEXT_SECONDARY);
        footer.add(statusLabel, BorderLayout.WEST);

        JButton closeButton = new JButton("Cerrar");
        closeButton.setFont(new Font("Inter", Font.BOLD, 14));
        closeButton.setForeground(Color.WHITE);
        closeButton.setBackground(PRIMARY_BLUE);
        closeButton.setBorder(new CompoundBorder(
            new LineBorder(PRIMARY_BLUE, 1, true),
            new EmptyBorder(10, 24, 10, 24)
        ));
        closeButton.setFocusPainted(false);
        closeButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        closeButton.addActionListener(e -> {
            cleanup();
            dispose();
        });
        footer.add(closeButton, BorderLayout.EAST);

        add(footer, BorderLayout.SOUTH);
    }

    private void loadData() {
        statusLabel.setText("Recuperando información clínica...");
        statusLabel.setForeground(TEXT_SECONDARY);
        setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));

        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            private JsonObject patient;
            private JsonArray alerts;
            private JsonArray notes;
            private JsonArray devices;
            
            @Override
            protected Void doInBackground() throws Exception {
                // Si orgId es null, el paciente es del caregiver (sin organización)
                // Usar endpoints de caregiver en lugar de endpoints de organización
                if (orgId == null) {
                    // Endpoints para pacientes del caregiver
                    JsonObject detailResponse = apiClient.getCaregiverPatientDetail(token, patientId);
                    JsonObject detailData = detailResponse.getAsJsonObject("data");
                    patient = detailData.getAsJsonObject("patient");

                    JsonObject alertsResponse = apiClient.getCaregiverPatientAlerts(token, patientId, 20);
                    alerts = alertsResponse.getAsJsonObject("data").getAsJsonArray("alerts");

                    JsonObject notesResponse = apiClient.getCaregiverPatientNotes(token, patientId, 20);
                    notes = notesResponse.getAsJsonObject("data").getAsJsonArray("notes");
                    
                    // Cargar dispositivos del paciente
                    JsonObject devicesResponse = apiClient.getCaregiverPatientDevices(token, patientId);
                    devices = devicesResponse.getAsJsonObject("data").getAsJsonArray("devices");
                } else {
                    // Endpoints para pacientes de organización
                    JsonObject detailResponse = apiClient.getOrganizationPatientDetail(token, orgId, patientId);
                    JsonObject detailData = detailResponse.getAsJsonObject("data");
                    patient = detailData.getAsJsonObject("patient");

                    JsonObject alertsResponse = apiClient.getOrganizationPatientAlerts(token, orgId, patientId, 20);
                    alerts = alertsResponse.getAsJsonObject("data").getAsJsonArray("alerts");

                    JsonObject notesResponse = apiClient.getOrganizationPatientNotes(token, orgId, patientId, 20);
                    notes = notesResponse.getAsJsonObject("data").getAsJsonArray("notes");
                    
                    // Cargar dispositivos del paciente
                    JsonObject devicesResponse = apiClient.getOrganizationPatientDevices(token, orgId, patientId);
                    devices = devicesResponse.getAsJsonObject("data").getAsJsonArray("devices");
                }
                return null;
            }

            @Override
            protected void done() {
                setCursor(Cursor.getDefaultCursor());
                try {
                    get();
                    // Actualizar UI en el EDT
                    updateInfoArea(patient);
                    updateAlerts(alerts);
                    updateNotes(notes);
                    loadDevices(devices);
                    
                    statusLabel.setForeground(SUCCESS_GREEN);
                    statusLabel.setText("Información actualizada");
                } catch (Exception ex) {
                    Throwable cause = ex.getCause();
                    statusLabel.setForeground(DANGER_RED);
                    statusLabel.setText((cause != null ? cause.getMessage() : ex.getMessage()));
                }
            }
        };
        worker.execute();
    }

    private void updateInfoArea(JsonObject patient) {
        SwingUtilities.invokeLater(() -> {
            if (patient == null) {
                infoArea.setText("Sin métricas disponibles");
                return;
            }
            List<String> lines = new ArrayList<>();
            lines.add("Nombre: " + safe(patient.get("name")));
            lines.add("Correo: " + safe(patient.get("email")));
            if (patient.has("risk_level") && patient.get("risk_level").isJsonObject()) {
                JsonObject risk = patient.getAsJsonObject("risk_level");
                lines.add("Riesgo actual: " + safe(risk.get("label")));
            }
            if (patient.has("organization") && patient.get("organization").isJsonObject()) {
                JsonObject org = patient.getAsJsonObject("organization");
                lines.add("Organización: " + safe(org.get("name")));
            }
            if (patient.has("created_at")) {
                lines.add("Registrado el: " + safe(patient.get("created_at")));
            }
            infoArea.setText(String.join("\n", lines));
        });
    }

    private void updateAlerts(JsonArray alerts) {
        SwingUtilities.invokeLater(() -> {
            // Guardar las alertas completas para usarlas después
            loadedAlerts = alerts != null ? alerts : new JsonArray();
            
            alertsModel.clear();
            if (alerts == null || alerts.isEmpty()) {
                alertsModel.addElement("Sin alertas registradas");
                return;
            }
            for (JsonElement element : alerts) {
                if (!element.isJsonObject()) continue;
                JsonObject alert = element.getAsJsonObject();

                // Extraer campos correctos: type, level, status, description
                JsonObject typeObj = alert.has("type") && alert.get("type").isJsonObject()
                        ? alert.getAsJsonObject("type")
                        : null;
                JsonObject levelObj = alert.has("level") && alert.get("level").isJsonObject()
                        ? alert.getAsJsonObject("level")
                        : null;
                JsonObject statusObj = alert.has("status") && alert.get("status").isJsonObject()
                        ? alert.getAsJsonObject("status")
                        : null;

                String typeLabel = typeObj != null ? safe(typeObj.get("label")) : "-";
                String description = safe(alert.get("description"));
                String levelLabel = levelObj != null ? safe(levelObj.get("label")) : "-";
                String statusLabel = statusObj != null ? safe(statusObj.get("label")) : "-";
                String created = safe(alert.get("created_at"));

                // Formato mejorado: [fecha] Tipo: descripción | Nivel: X | Estado: Y
                String displayText = String.format("[%s] %s: %s | Nivel: %s | Estado: %s",
                    created, typeLabel, description, levelLabel, statusLabel);
                alertsModel.addElement(displayText);
            }
        });
    }

    private void updateNotes(JsonArray notes) {
        SwingUtilities.invokeLater(() -> {
            notesModel.clear();
            if (notes == null || notes.isEmpty()) {
                notesModel.addElement("Sin notas registradas");
                return;
            }
            for (JsonElement element : notes) {
                if (!element.isJsonObject()) continue;
                JsonObject note = element.getAsJsonObject();
                String onset = safe(note.get("onset"));
                String noteText = safe(note.get("note"));
                notesModel.addElement(String.format("[%s] %s", onset, noteText));
            }
        });
    }

    private String safe(JsonElement element) {
        if (element == null || element.isJsonNull()) {
            return "-";
        }
        return element.getAsString();
    }

    /**
     * Valida una alerta seleccionada abriendo el diálogo de validación
     */
    private void validateSelectedAlert(int selectedIndex) {
        if (selectedIndex < 0 || selectedIndex >= loadedAlerts.size()) {
            JOptionPane.showMessageDialog(this,
                    "Por favor selecciona una alerta de la lista",
                    "Selección requerida",
                    JOptionPane.WARNING_MESSAGE);
            return;
        }
        
        try {
            JsonObject alertJson = loadedAlerts.get(selectedIndex).getAsJsonObject();
            Alert alert = Alert.fromJson(alertJson);
            
            AlertValidationDialog dialog = new AlertValidationDialog(
                    this,
                    alert,
                    orgId,
                    null, // userId lo toma del token
                    token
            );
            dialog.setVisible(true);
            
            // Recargar alertas después de validar
            if (dialog.isValidated()) {
                loadData();
            }
        } catch (Exception ex) {
            ex.printStackTrace();
            JOptionPane.showMessageDialog(this,
                    "<html><body style='width: 300px'>" +
                    "<h3>❌ Error al abrir diálogo</h3>" +
                    "<p>" + ex.getMessage() + "</p>" +
                    "<p><i>Revisa la consola para más detalles</i></p>" +
                    "</body></html>",
                    "Error",
                    JOptionPane.ERROR_MESSAGE);
        }
    }
    
    /**
     * Limpiar recursos al cerrar el diálogo
     */
    private void cleanup() {
        // Limpiar todos los paneles cacheados
        for (VitalSignsChartPanel panel : chartPanelCache.values()) {
            if (panel != null) {
                panel.cleanup();
            }
        }
        chartPanelCache.clear();
    }
    
    /**
     * Clase interna para almacenar información de dispositivos
     */
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
    
    /**
     * Procesa la lista de dispositivos y actualiza la UI
     */
    private void loadDevices(JsonArray devicesArray) {
        patientDevices.clear();
        
        if (devicesArray == null || devicesArray.isEmpty()) {
            SwingUtilities.invokeLater(this::showNoDevicesMessage);
            return;
        }
        
        // Parsear dispositivos
        for (JsonElement element : devicesArray) {
            if (!element.isJsonObject()) continue;
            JsonObject deviceObj = element.getAsJsonObject();
            
            DeviceInfo device = new DeviceInfo();
            device.id = safe(deviceObj.get("id"));
            device.serial = safe(deviceObj.get("serial"));
            device.brand = safe(deviceObj.get("brand"));
            device.model = safe(deviceObj.get("model"));
            
            JsonObject deviceType = deviceObj.has("device_type") && deviceObj.get("device_type").isJsonObject()
                    ? deviceObj.getAsJsonObject("device_type")
                    : null;
            device.typeLabel = deviceType != null ? safe(deviceType.get("label")) : null;
            
            JsonObject stream = deviceObj.has("stream") && deviceObj.get("stream").isJsonObject()
                    ? deviceObj.getAsJsonObject("stream")
                    : null;
            device.hasActiveStream = stream != null && stream.has("is_active") && stream.get("is_active").getAsBoolean();
            
            // Incluir todos los dispositivos del paciente (con o sin stream activo)
            patientDevices.add(device);
        }
        
        SwingUtilities.invokeLater(this::updateDeviceUI);
    }
    
    /**
     * Actualiza la UI según la cantidad de dispositivos disponibles
     */
    private void updateDeviceUI() {
        // Limpiar el centro del chartContainerPanel (excepto el header)
        Component[] components = chartContainerPanel.getComponents();
        for (int i = components.length - 1; i >= 0; i--) {
            if (components[i] != chartContainerPanel.getComponent(0)) { // No remover el header
                chartContainerPanel.remove(components[i]);
            }
        }
        
        if (patientDevices.isEmpty()) {
            showNoDevicesMessage();
            return;
        }
        
        if (patientDevices.size() == 1) {
            // Un solo dispositivo - mostrar info y gráficas directamente
            DeviceInfo device = patientDevices.get(0);
            deviceInfoLabel.setText("📱 " + device.getShortInfo());
            deviceSelector.setVisible(false);
            loadChartsForDevice(device);
        } else {
            // Múltiples dispositivos - configurar selector
            // OPTIMIZACIÓN: Remover listener temporalmente para evitar eventos durante población
            ActionListener[] listeners = deviceSelector.getActionListeners();
            for (ActionListener listener : listeners) {
                deviceSelector.removeActionListener(listener);
            }
            
            deviceSelector.removeAllItems();
            for (DeviceInfo device : patientDevices) {
                deviceSelector.addItem(device.getDisplayName());
            }
            
            // Restaurar listeners
            for (ActionListener listener : listeners) {
                deviceSelector.addActionListener(listener);
            }
            
            deviceSelector.setVisible(true);
            
            // Cargar primer dispositivo directamente
            if (deviceSelector.getItemCount() > 0) {
                DeviceInfo firstDevice = patientDevices.get(0);
                deviceInfoLabel.setText("📱 " + firstDevice.getShortInfo());
                deviceSelector.setSelectedIndex(0);
                loadChartsForDevice(firstDevice);
            }
        }
        
        chartContainerPanel.revalidate();
        chartContainerPanel.repaint();
    }
    
    /**
     * Muestra mensaje cuando no hay dispositivos activos
     */
    private void showNoDevicesMessage() {
        deviceInfoLabel.setText("");
        deviceSelector.setVisible(false);
        
        JLabel noDeviceLabel = new JLabel("<html><div style='text-align:center;padding:40px;'>" +
                "<b>Sin dispositivos activos</b><br><br>" +
                "Este paciente no tiene dispositivos asignados o<br>" +
                "ninguno está generando datos actualmente." +
                "</div></html>");
        noDeviceLabel.setHorizontalAlignment(SwingConstants.CENTER);
        noDeviceLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        noDeviceLabel.setForeground(TEXT_SECONDARY);
        
        chartContainerPanel.add(noDeviceLabel, BorderLayout.CENTER);
        chartContainerPanel.revalidate();
        chartContainerPanel.repaint();
    }
    
    /**
     * Callback cuando se selecciona un dispositivo del combo box
     */
    private void onDeviceSelected() {
        int selectedIndex = deviceSelector.getSelectedIndex();
        if (selectedIndex >= 0 && selectedIndex < patientDevices.size()) {
            DeviceInfo selectedDevice = patientDevices.get(selectedIndex);
            
            // Evitar recarga si ya estamos mostrando este dispositivo
            if (chartPanel != null && chartPanelCache.containsKey(selectedDevice.id)) {
                VitalSignsChartPanel existingPanel = chartPanelCache.get(selectedDevice.id);
                if (existingPanel == chartPanel) {
                    // Ya está mostrando este dispositivo, solo actualizar label
                    deviceInfoLabel.setText("📱 " + selectedDevice.getShortInfo());
                    return;
                }
            }
            
            deviceInfoLabel.setText("📱 " + selectedDevice.getShortInfo());
            loadChartsForDevice(selectedDevice);
        }
    }
    
    /**
     * Carga las gráficas para un dispositivo específico (con caché para rendimiento)
     * OPTIMIZACIÓN: Carga en background para no bloquear la UI
     */
    private void loadChartsForDevice(DeviceInfo device) {
        // Remover panel actual del contenedor (pero NO hacer cleanup todavía)
        if (chartPanel != null) {
            chartContainerPanel.remove(chartPanel);
        }
        
        // Verificar si ya tenemos un panel cacheado para este dispositivo
        VitalSignsChartPanel cachedPanel = chartPanelCache.get(device.id);
        
        if (cachedPanel != null) {
            // Reutilizar panel existente - mucho más rápido
            System.out.println("[PatientDetail] Reusing cached panel for device: " + device.serial);
            chartPanel = cachedPanel;
            chartContainerPanel.add(chartPanel, BorderLayout.CENTER);
            chartContainerPanel.revalidate();
            chartContainerPanel.repaint();
        } else {
            // Mostrar mensaje de carga mientras se crea el panel en background
            JPanel loadingPanel = new JPanel(new BorderLayout());
            loadingPanel.setOpaque(false);
            JLabel loadingLabel = new JLabel("<html><div style='text-align:center;padding:40px;'>" +
                    "<b style='font-size:16px;'>📊 Cargando gráficas...</b><br><br>" +
                    "<span style='color:#64748b;'>Obteniendo datos de " + device.serial + "</span>" +
                    "</div></html>");
            loadingLabel.setHorizontalAlignment(SwingConstants.CENTER);
            loadingLabel.setFont(new Font("Inter", Font.PLAIN, 14));
            loadingPanel.add(loadingLabel, BorderLayout.CENTER);
            chartContainerPanel.add(loadingPanel, BorderLayout.CENTER);
            chartContainerPanel.revalidate();
            chartContainerPanel.repaint();
            
            // Crear panel en background worker para no bloquear UI
            SwingWorker<VitalSignsChartPanel, Void> chartWorker = new SwingWorker<>() {
                @Override
                protected VitalSignsChartPanel doInBackground() throws Exception {
                    System.out.println("[PatientDetail] Creating NEW VitalSignsChartPanel for device: " + device.serial);
                    return new VitalSignsChartPanel(patientId, device.id, apiClient, 10);
                }
                
                @Override
                protected void done() {
                    try {
                        VitalSignsChartPanel newPanel = get();
                        chartContainerPanel.remove(loadingPanel);
                        chartPanel = newPanel;
                        chartPanelCache.put(device.id, chartPanel);
                        chartContainerPanel.add(chartPanel, BorderLayout.CENTER);
                        chartContainerPanel.revalidate();
                        chartContainerPanel.repaint();
                        
                        // OPTIMIZACIÓN: Iniciar carga de datos DESPUÉS de que el panel esté visible
                        SwingUtilities.invokeLater(() -> {
                            chartPanel.startDataLoading();
                        });
                        
                        System.out.println("[PatientDetail] VitalSignsChartPanel created and cached for device " + device.serial);
                    } catch (Exception e) {
                        System.err.println("[PatientDetail] ERROR creating chart panel: " + e.getMessage());
                        e.printStackTrace();
                        chartContainerPanel.remove(loadingPanel);
                        JLabel errorLabel = new JLabel("<html><div style='text-align:center;padding:40px;'>" +
                                "<b style='color:#dc3545;font-size:16px;'>Error al cargar gráficas</b><br><br>" +
                                "<span style='color:#64748b;'>" + e.getMessage() + "</span>" +
                                "</div></html>");
                        errorLabel.setHorizontalAlignment(SwingConstants.CENTER);
                        chartContainerPanel.add(errorLabel, BorderLayout.CENTER);
                        chartContainerPanel.revalidate();
                        chartContainerPanel.repaint();
                    }
                }
            };
            chartWorker.execute();
        }
    }
}
