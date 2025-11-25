package com.heartguard.desktop.ui.user;

import com.heartguard.desktop.api.AlertService;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.alert.*;
import com.heartguard.desktop.config.AppConfig;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import javax.swing.table.AbstractTableModel;
import javax.swing.table.DefaultTableCellRenderer;
import javax.swing.table.TableRowSorter;
import java.awt.*;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Panel para mostrar alertas de pacientes en tiempo real
 * Incluye filtros, búsqueda y acciones de validación
 */
public class AlertsPanel extends JPanel {
    // Colores
    private static final Color BACKGROUND = new Color(247, 249, 251);
    private static final Color CARD_BG = Color.WHITE;
    private static final Color PRIMARY = new Color(0, 120, 215);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER = new Color(223, 227, 230);
    
    private final AlertService alertService;
    private final String organizationId;
    private final String userId;
    private final String accessToken;
    
    private final AlertTableModel tableModel;
    private final JTable alertsTable;
    private final TableRowSorter<AlertTableModel> sorter;
    
    private final JComboBox<String> statusFilter;
    private final JComboBox<String> levelFilter;
    private final JTextField searchField;
    private final JLabel statsLabel;
    private final JButton refreshButton;
    
    private Timer autoRefreshTimer;
    
    public AlertsPanel(String organizationId, String userId, String accessToken) {
        this.organizationId = organizationId;
        this.userId = userId;
        this.accessToken = accessToken;
        
        this.alertService = new AlertService(AppConfig.getInstance().getGatewayBaseUrl());
        this.alertService.setAccessToken(accessToken);
        
        this.tableModel = new AlertTableModel();
        this.alertsTable = new JTable(tableModel);
        this.sorter = new TableRowSorter<>(tableModel);
        
        this.statusFilter = new JComboBox<>(new String[]{"Todos", "Creada", "Notificada", "Reconocida", "Resuelta"});
        this.levelFilter = new JComboBox<>(new String[]{"Todos", "Crítico", "Alto", "Medio", "Bajo"});
        this.searchField = new JTextField(20);
        this.statsLabel = new JLabel("0 alertas");
        this.refreshButton = new JButton("🔄 Actualizar");
        
        initUI();
        loadAlerts();
        startAutoRefresh();
    }
    
    private void initUI() {
        setLayout(new BorderLayout(0, 16));
        setBackground(BACKGROUND);
        setBorder(new EmptyBorder(24, 24, 24, 24));
        
        // Header
        add(createHeader(), BorderLayout.NORTH);
        
        // Tabla de alertas
        add(createAlertsTable(), BorderLayout.CENTER);
        
        // Panel de acciones
        add(createActionsPanel(), BorderLayout.SOUTH);
    }
    
    private JPanel createHeader() {
        JPanel header = new JPanel(new BorderLayout());
        header.setOpaque(false);
        
        // Título
        JLabel title = new JLabel("🚨 Alertas Activas");
        title.setFont(new Font("Inter", Font.BOLD, 24));
        title.setForeground(TEXT_PRIMARY);
        
        // Panel de filtros
        JPanel filtersPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        filtersPanel.setOpaque(false);
        
        filtersPanel.add(new JLabel("Estado:"));
        statusFilter.setPreferredSize(new Dimension(140, 32));
        statusFilter.addActionListener(e -> applyFilters());
        filtersPanel.add(statusFilter);
        
        filtersPanel.add(new JLabel("Nivel:"));
        levelFilter.setPreferredSize(new Dimension(120, 32));
        levelFilter.addActionListener(e -> applyFilters());
        filtersPanel.add(levelFilter);
        
        searchField.setPreferredSize(new Dimension(200, 32));
        searchField.putClientProperty("JTextField.placeholderText", "Buscar paciente...");
        searchField.getDocument().addDocumentListener(new javax.swing.event.DocumentListener() {
            public void insertUpdate(javax.swing.event.DocumentEvent e) { applyFilters(); }
            public void removeUpdate(javax.swing.event.DocumentEvent e) { applyFilters(); }
            public void changedUpdate(javax.swing.event.DocumentEvent e) { applyFilters(); }
        });
        filtersPanel.add(searchField);
        
        refreshButton.setBackground(PRIMARY);
        refreshButton.setForeground(Color.WHITE);
        refreshButton.setFocusPainted(false);
        refreshButton.setBorderPainted(false);
        refreshButton.setPreferredSize(new Dimension(130, 32));
        refreshButton.addActionListener(e -> loadAlerts());
        filtersPanel.add(refreshButton);
        
        header.add(title, BorderLayout.WEST);
        header.add(filtersPanel, BorderLayout.EAST);
        
        return header;
    }
    
    private JScrollPane createAlertsTable() {
        // Configurar tabla
        alertsTable.setRowSorter(sorter);
        alertsTable.setRowHeight(60);
        alertsTable.setShowGrid(false);
        alertsTable.setIntercellSpacing(new Dimension(0, 4));
        alertsTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        alertsTable.setBackground(CARD_BG);
        alertsTable.getTableHeader().setBackground(CARD_BG);
        alertsTable.getTableHeader().setForeground(TEXT_SECONDARY);
        alertsTable.getTableHeader().setFont(new Font("Inter", Font.BOLD, 12));
        alertsTable.getTableHeader().setBorder(new LineBorder(BORDER, 1));
        
        // Configurar anchos de columnas
        alertsTable.getColumnModel().getColumn(0).setPreferredWidth(50);  // Emoji
        alertsTable.getColumnModel().getColumn(1).setPreferredWidth(150); // Paciente
        alertsTable.getColumnModel().getColumn(2).setPreferredWidth(120); // Tipo
        alertsTable.getColumnModel().getColumn(3).setPreferredWidth(80);  // Nivel
        alertsTable.getColumnModel().getColumn(4).setPreferredWidth(250); // Descripción
        alertsTable.getColumnModel().getColumn(5).setPreferredWidth(150); // Fecha
        alertsTable.getColumnModel().getColumn(6).setPreferredWidth(100); // Estado
        alertsTable.getColumnModel().getColumn(7).setPreferredWidth(100); // Acciones
        
        // Renderizadores personalizados
        alertsTable.setDefaultRenderer(Object.class, new AlertCellRenderer());
        alertsTable.getColumnModel().getColumn(7).setCellRenderer(new ActionButtonRenderer());
        alertsTable.getColumnModel().getColumn(7).setCellEditor(new ActionButtonEditor(new JCheckBox()));
        
        // Ordenamiento inicial: por fecha descendente
        List<RowSorter.SortKey> sortKeys = new ArrayList<>();
        sortKeys.add(new RowSorter.SortKey(5, SortOrder.DESCENDING));
        sorter.setSortKeys(sortKeys);
        
        JScrollPane scrollPane = new JScrollPane(alertsTable);
        scrollPane.setBorder(new LineBorder(BORDER, 1));
        scrollPane.setBackground(CARD_BG);
        
        return scrollPane;
    }
    
    private JPanel createActionsPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setOpaque(false);
        panel.setBorder(new EmptyBorder(16, 0, 0, 0));
        
        // Estadísticas
        statsLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        statsLabel.setForeground(TEXT_SECONDARY);
        panel.add(statsLabel, BorderLayout.WEST);
        
        // Botones de acción
        JPanel buttonsPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 10, 0));
        buttonsPanel.setOpaque(false);
        
        JButton acknowledgeAllBtn = new JButton("✓ Reconocer Seleccionadas");
        acknowledgeAllBtn.setBackground(new Color(40, 167, 69));
        acknowledgeAllBtn.setForeground(Color.WHITE);
        acknowledgeAllBtn.setFocusPainted(false);
        acknowledgeAllBtn.setBorderPainted(false);
        acknowledgeAllBtn.addActionListener(e -> acknowledgeSelectedAlerts());
        buttonsPanel.add(acknowledgeAllBtn);
        
        panel.add(buttonsPanel, BorderLayout.EAST);
        
        return panel;
    }
    
    private void loadAlerts() {
        refreshButton.setEnabled(false);
        refreshButton.setText("⏳ Cargando...");
        
        System.out.println("[AlertsPanel] Cargando alertas para org: " + organizationId);
        
        // Cargar TODAS las alertas (sin filtro de status inicial)
        // El usuario puede filtrar después usando el dropdown
        CompletableFuture.supplyAsync(() -> {
            try {
                List<Alert> alerts = alertService.getOrganizationAlerts(organizationId, null, null);
                System.out.println("[AlertsPanel] ✅ Cargadas " + alerts.size() + " alertas");
                return alerts;
            } catch (ApiException e) {
                System.err.println("[AlertsPanel] ❌ Error al cargar alertas: " + e.getMessage());
                e.printStackTrace();
                SwingUtilities.invokeLater(() -> {
                    JOptionPane.showMessageDialog(
                        this,
                        "Error al cargar alertas: " + e.getMessage(),
                        "Error",
                        JOptionPane.ERROR_MESSAGE
                    );
                });
                return new ArrayList<Alert>();
            }
        }).thenAccept(alerts -> {
            SwingUtilities.invokeLater(() -> {
                tableModel.setAlerts(alerts);
                updateStats();
                refreshButton.setEnabled(true);
                refreshButton.setText("🔄 Actualizar");
                System.out.println("[AlertsPanel] Tabla actualizada con " + tableModel.getRowCount() + " filas");
            });
        });
    }
    
    private void applyFilters() {
        RowFilter<AlertTableModel, Object> rf = new RowFilter<AlertTableModel, Object>() {
            public boolean include(Entry<? extends AlertTableModel, ? extends Object> entry) {
                // Filtro de estado
                String statusText = (String) entry.getValue(6);
                String selectedStatus = (String) statusFilter.getSelectedItem();
                if (selectedStatus != null && !selectedStatus.equals("Todos")) {
                    if (!statusText.contains(selectedStatus)) {
                        return false;
                    }
                }
                
                // Filtro de nivel
                String levelText = (String) entry.getValue(3);
                String selectedLevel = (String) levelFilter.getSelectedItem();
                if (selectedLevel != null && !selectedLevel.equals("Todos")) {
                    if (!levelText.contains(selectedLevel)) {
                        return false;
                    }
                }
                
                // Búsqueda por nombre de paciente
                String search = searchField.getText().toLowerCase();
                if (!search.isEmpty()) {
                    String patientName = ((String) entry.getValue(1)).toLowerCase();
                    if (!patientName.contains(search)) {
                        return false;
                    }
                }
                
                return true;
            }
        };
        
        sorter.setRowFilter(rf);
        updateStats();
    }
    
    private void updateStats() {
        int total = tableModel.getRowCount();
        int visible = alertsTable.getRowCount();
        
        if (visible == total) {
            statsLabel.setText(String.format("%d alertas activas", total));
        } else {
            statsLabel.setText(String.format("%d de %d alertas", visible, total));
        }
    }
    
    private void acknowledgeSelectedAlerts() {
        int selectedRow = alertsTable.getSelectedRow();
        if (selectedRow == -1) {
            JOptionPane.showMessageDialog(this, "Seleccione una alerta primero", "Aviso", JOptionPane.WARNING_MESSAGE);
            return;
        }
        
        int modelRow = alertsTable.convertRowIndexToModel(selectedRow);
        Alert alert = tableModel.getAlert(modelRow);
        
        acknowledgeAlert(alert);
    }
    
    private void acknowledgeAlert(Alert alert) {
        int confirm = JOptionPane.showConfirmDialog(
            this,
            "¿Reconocer la alerta de " + alert.getPatientName() + "?",
            "Confirmar",
            JOptionPane.YES_NO_OPTION
        );
        
        if (confirm == JOptionPane.YES_OPTION) {
            CompletableFuture.runAsync(() -> {
                try {
                    alertService.acknowledgeAlert(alert.getId(), userId);
                    SwingUtilities.invokeLater(() -> {
                        JOptionPane.showMessageDialog(this, "Alerta reconocida", "Éxito", JOptionPane.INFORMATION_MESSAGE);
                        loadAlerts();
                    });
                } catch (ApiException e) {
                    SwingUtilities.invokeLater(() -> {
                        JOptionPane.showMessageDialog(this, "Error: " + e.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
                    });
                }
            });
        }
    }
    
    void validateAlert(Alert alert) {
        // Este método será llamado desde AlertValidationDialog
        AlertValidationDialog dialog = new AlertValidationDialog(
            SwingUtilities.getWindowAncestor(this),
            alert,
            organizationId,
            userId,
            accessToken
        );
        dialog.setVisible(true);
        
        if (dialog.isValidated()) {
            loadAlerts(); // Recargar después de validar
        }
    }
    
    private void startAutoRefresh() {
        // Auto-refresh cada 30 segundos
        autoRefreshTimer = new Timer(30000, e -> loadAlerts());
        autoRefreshTimer.start();
    }
    
    public void stopAutoRefresh() {
        if (autoRefreshTimer != null) {
            autoRefreshTimer.stop();
        }
    }
    
    // ========== TABLA MODEL ==========
    
    private static class AlertTableModel extends AbstractTableModel {
        private final String[] columns = {"", "Paciente", "Tipo", "Nivel", "Descripción", "Fecha", "Estado", "Acciones"};
        private List<Alert> alerts = new ArrayList<>();
        
        public void setAlerts(List<Alert> alerts) {
            this.alerts = alerts;
            fireTableDataChanged();
        }
        
        public Alert getAlert(int row) {
            return alerts.get(row);
        }
        
        @Override
        public int getRowCount() {
            return alerts.size();
        }
        
        @Override
        public int getColumnCount() {
            return columns.length;
        }
        
        @Override
        public String getColumnName(int column) {
            return columns[column];
        }
        
        @Override
        public Object getValueAt(int row, int column) {
            Alert alert = alerts.get(row);
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm")
                    .withZone(ZoneId.systemDefault());
            
            switch (column) {
                case 0: return alert.getType().getEmoji();
                case 1: return alert.getPatientName() != null ? alert.getPatientName() : "Paciente";
                case 2: return alert.getType().getDisplayName();
                case 3: return alert.getAlertLevel().getDisplayName();
                case 4: return alert.getDescription();
                case 5: return formatter.format(alert.getCreatedAt());
                case 6: return alert.getStatus().getDisplayName();
                case 7: return "Acciones";
                default: return "";
            }
        }
        
        @Override
        public boolean isCellEditable(int row, int column) {
            return column == 7; // Solo columna de acciones es editable
        }
    }
    
    // ========== RENDERIZADORES ==========
    
    private class AlertCellRenderer extends DefaultTableCellRenderer {
        @Override
        public Component getTableCellRendererComponent(JTable table, Object value,
                boolean isSelected, boolean hasFocus, int row, int column) {
            Component c = super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column);
            
            int modelRow = table.convertRowIndexToModel(row);
            Alert alert = tableModel.getAlert(modelRow);
            
            // Color de fondo según nivel de alerta
            if (!isSelected) {
                Color bgColor = alert.getAlertLevel().getColor();
                c.setBackground(new Color(bgColor.getRed(), bgColor.getGreen(), bgColor.getBlue(), 30));
            }
            
            // Color de texto según columna
            if (column == 3) { // Nivel
                c.setForeground(alert.getAlertLevel().getColor());
                setFont(getFont().deriveFont(Font.BOLD));
            } else if (column == 6) { // Estado
                c.setForeground(alert.getStatus().getColor());
            } else {
                c.setForeground(TEXT_PRIMARY);
            }
            
            setBorder(new EmptyBorder(8, 8, 8, 8));
            
            return c;
        }
    }
    
    private class ActionButtonRenderer extends JPanel implements javax.swing.table.TableCellRenderer {
        private final JButton validateBtn = new JButton("Validar");
        
        public ActionButtonRenderer() {
            setLayout(new FlowLayout(FlowLayout.CENTER, 4, 4));
            validateBtn.setFont(new Font("Inter", Font.PLAIN, 11));
            validateBtn.setBackground(PRIMARY);
            validateBtn.setForeground(Color.WHITE);
            validateBtn.setFocusPainted(false);
            validateBtn.setBorderPainted(false);
            validateBtn.setPreferredSize(new Dimension(70, 28));
            add(validateBtn);
        }
        
        @Override
        public Component getTableCellRendererComponent(JTable table, Object value,
                boolean isSelected, boolean hasFocus, int row, int column) {
            return this;
        }
    }
    
    private class ActionButtonEditor extends DefaultCellEditor {
        private final JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER, 4, 4));
        private final JButton validateBtn = new JButton("Validar");
        private Alert currentAlert;
        
        public ActionButtonEditor(JCheckBox checkBox) {
            super(checkBox);
            
            validateBtn.setFont(new Font("Inter", Font.PLAIN, 11));
            validateBtn.setBackground(PRIMARY);
            validateBtn.setForeground(Color.WHITE);
            validateBtn.setFocusPainted(false);
            validateBtn.setBorderPainted(false);
            validateBtn.setPreferredSize(new Dimension(70, 28));
            
            validateBtn.addActionListener(e -> {
                fireEditingStopped();
                validateAlert(currentAlert);
            });
            
            panel.add(validateBtn);
        }
        
        @Override
        public Component getTableCellEditorComponent(JTable table, Object value,
                boolean isSelected, int row, int column) {
            int modelRow = table.convertRowIndexToModel(row);
            currentAlert = tableModel.getAlert(modelRow);
            return panel;
        }
        
        @Override
        public Object getCellEditorValue() {
            return "Acciones";
        }
    }
}
