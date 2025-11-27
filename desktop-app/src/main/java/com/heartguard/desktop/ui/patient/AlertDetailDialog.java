package com.heartguard.desktop.ui.patient;

import com.google.gson.JsonObject;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import javax.swing.border.MatteBorder;
import java.awt.*;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

/**
 * Diálogo para mostrar información detallada de una alerta para pacientes
 * Incluye información de IA y Ground Truth cuando están disponibles
 */
public class AlertDetailDialog extends JDialog {
    private static final Color PRIMARY = new Color(33, 150, 243);
    private static final Color SUCCESS = new Color(46, 204, 113);
    private static final Color WARNING = new Color(255, 179, 0);
    private static final Color DANGER = new Color(231, 76, 60);
    private static final Color INFO = new Color(103, 58, 183);
    private static final Color TEXT_PRIMARY = new Color(35, 52, 70);
    private static final Color TEXT_SECONDARY = new Color(104, 120, 138);
    private static final Color BORDER = new Color(225, 231, 238);
    private static final Color BG_LIGHT = new Color(247, 249, 251);
    
    private final JsonObject alert;
    
    public AlertDetailDialog(Window owner, JsonObject alert) {
        super(owner, "Detalle de Alerta", ModalityType.APPLICATION_MODAL);
        this.alert = alert;
        initUI();
    }
    
    private void initUI() {
        setLayout(new BorderLayout());
        setSize(700, 650);
        setLocationRelativeTo(getOwner());
        
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setBorder(new EmptyBorder(20, 24, 20, 24));
        contentPanel.setBackground(Color.WHITE);
        
        // Header
        contentPanel.add(createHeaderPanel());
        contentPanel.add(Box.createVerticalStrut(20));
        
        // Información principal
        contentPanel.add(createMainInfoPanel());
        contentPanel.add(Box.createVerticalStrut(16));
        
        // Información de IA (si existe)
        if (hasAIInfo()) {
            contentPanel.add(createAIInfoPanel());
            contentPanel.add(Box.createVerticalStrut(16));
        }
        
        // Información de Ground Truth (si existe)
        if (hasGroundTruthInfo()) {
            contentPanel.add(createGroundTruthPanel());
            contentPanel.add(Box.createVerticalStrut(16));
        }
        
        // Ubicación (si existe)
        if (hasLocation()) {
            contentPanel.add(createLocationPanel());
            contentPanel.add(Box.createVerticalStrut(16));
        }
        
        // Envolver en scroll
        JScrollPane scrollPane = new JScrollPane(contentPanel);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        add(scrollPane, BorderLayout.CENTER);
        
        // Botón cerrar
        add(createButtonPanel(), BorderLayout.SOUTH);
    }
    
    private JPanel createHeaderPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setOpaque(false);
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        String type = alert.has("type") && !alert.get("type").isJsonNull()
                ? alert.get("type").getAsString() : "Alerta";
        
        JLabel titleLabel = new JLabel("🚨 " + type.toUpperCase());
        titleLabel.setFont(new Font("Segoe UI", Font.BOLD, 24));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        String level = alert.has("level_label") && !alert.get("level_label").isJsonNull()
                ? alert.get("level_label").getAsString() : "N/A";
        JLabel levelLabel = new JLabel("Nivel: " + level);
        levelLabel.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        levelLabel.setForeground(TEXT_SECONDARY);
        levelLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        panel.add(titleLabel);
        panel.add(Box.createVerticalStrut(4));
        panel.add(levelLabel);
        
        return panel;
    }
    
    private JPanel createMainInfoPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(BG_LIGHT);
        panel.setBorder(new CompoundBorder(
                new LineBorder(BORDER, 1),
                new EmptyBorder(16, 16, 16, 16)
        ));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Descripción
        String description = alert.has("description") && !alert.get("description").isJsonNull()
                ? alert.get("description").getAsString() : "Sin descripción";
        
        JTextArea descArea = new JTextArea(description);
        descArea.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        descArea.setForeground(TEXT_PRIMARY);
        descArea.setBackground(BG_LIGHT);
        descArea.setLineWrap(true);
        descArea.setWrapStyleWord(true);
        descArea.setEditable(false);
        descArea.setBorder(null);
        descArea.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        panel.add(createSectionLabel("📝 Descripción"));
        panel.add(Box.createVerticalStrut(8));
        panel.add(descArea);
        panel.add(Box.createVerticalStrut(16));
        
        // Fecha y Estado
        String createdAt = formatDate(alert.get("created_at").getAsString());
        String status = alert.has("status_label") && !alert.get("status_label").isJsonNull()
                ? alert.get("status_label").getAsString() : "Desconocido";
        
        panel.add(createInfoRow("🕐 Fecha/Hora:", createdAt));
        panel.add(Box.createVerticalStrut(8));
        panel.add(createInfoRow("📍 Estado:", status));
        
        return panel;
    }
    
    private JPanel createAIInfoPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(103, 58, 183, 20));
        panel.setBorder(new CompoundBorder(
                new MatteBorder(2, 2, 2, 2, INFO),
                new EmptyBorder(16, 16, 16, 16)
        ));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel headerLabel = new JLabel("🤖 GENERADA POR INTELIGENCIA ARTIFICIAL");
        headerLabel.setFont(new Font("Segoe UI", Font.BOLD, 14));
        headerLabel.setForeground(INFO);
        headerLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(headerLabel);
        panel.add(Box.createVerticalStrut(12));
        
        String modelName = alert.has("model_name") && !alert.get("model_name").isJsonNull()
                ? alert.get("model_name").getAsString() : "Modelo de IA";
        String modelVersion = alert.has("model_version") && !alert.get("model_version").isJsonNull()
                ? alert.get("model_version").getAsString() : "";
        
        panel.add(createInfoRow("📊 Modelo:", modelName + (modelVersion.isEmpty() ? "" : " v" + modelVersion)));
        panel.add(Box.createVerticalStrut(8));
        
        String modelId = alert.has("created_by_model_id") && !alert.get("created_by_model_id").isJsonNull()
                ? alert.get("created_by_model_id").getAsString() : "N/A";
        JLabel idLabel = new JLabel("ID: " + modelId.substring(0, Math.min(8, modelId.length())) + "...");
        idLabel.setFont(new Font("Segoe UI", Font.ITALIC, 12));
        idLabel.setForeground(TEXT_SECONDARY);
        idLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(idLabel);
        
        return panel;
    }
    
    private JPanel createGroundTruthPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(46, 125, 50, 20));
        panel.setBorder(new CompoundBorder(
                new MatteBorder(2, 2, 2, 2, new Color(46, 125, 50)),
                new EmptyBorder(16, 16, 16, 16)
        ));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel headerLabel = new JLabel("✅ VALIDADA POR PROFESIONAL MÉDICO");
        headerLabel.setFont(new Font("Segoe UI", Font.BOLD, 14));
        headerLabel.setForeground(new Color(46, 125, 50));
        headerLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(headerLabel);
        panel.add(Box.createVerticalStrut(12));
        
        // Obtener el objeto ground_truth
        JsonObject gt = alert.getAsJsonObject("ground_truth");
        
        // Validado por
        String validatedBy = gt.has("validated_by") && !gt.get("validated_by").isJsonNull()
                ? gt.get("validated_by").getAsString() : "Profesional médico";
        panel.add(createInfoRow("👨‍⚕️ Validado por:", validatedBy));
        
        // Tipo de evento validado
        if (gt.has("event_type") && !gt.get("event_type").isJsonNull()) {
            panel.add(Box.createVerticalStrut(8));
            panel.add(createInfoRow("🏥 Tipo de evento:", gt.get("event_type").getAsString()));
        }
        
        // Notas clínicas
        if (gt.has("note") && !gt.get("note").isJsonNull()) {
            panel.add(Box.createVerticalStrut(12));
            String note = gt.get("note").getAsString();
            
            JLabel noteLabel = new JLabel("📋 Notas clínicas:");
            noteLabel.setFont(new Font("Segoe UI", Font.BOLD, 13));
            noteLabel.setForeground(TEXT_PRIMARY);
            noteLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
            panel.add(noteLabel);
            panel.add(Box.createVerticalStrut(4));
            
            JTextArea noteArea = new JTextArea(note);
            noteArea.setFont(new Font("Segoe UI", Font.PLAIN, 13));
            noteArea.setForeground(TEXT_PRIMARY);
            noteArea.setBackground(new Color(46, 125, 50, 20));
            noteArea.setLineWrap(true);
            noteArea.setWrapStyleWord(true);
            noteArea.setEditable(false);
            noteArea.setBorder(null);
            noteArea.setAlignmentX(Component.LEFT_ALIGNMENT);
            panel.add(noteArea);
        }
        
        return panel;
    }
    
    private JPanel createLocationPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(BG_LIGHT);
        panel.setBorder(new CompoundBorder(
                new LineBorder(BORDER, 1),
                new EmptyBorder(16, 16, 16, 16)
        ));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        panel.add(createSectionLabel("🌍 Ubicación GPS"));
        panel.add(Box.createVerticalStrut(8));
        
        JsonObject location = alert.has("location") && alert.get("location").isJsonObject()
                ? alert.getAsJsonObject("location") : null;
        
        if (location != null) {
            Double lat = location.has("lat") && !location.get("lat").isJsonNull() 
                    ? location.get("lat").getAsDouble() : null;
            Double lng = location.has("lng") && !location.get("lng").isJsonNull() 
                    ? location.get("lng").getAsDouble() : null;
            
            if (lat != null && lng != null) {
                panel.add(createInfoRow("Latitud:", String.format("%.6f", lat)));
                panel.add(Box.createVerticalStrut(8));
                panel.add(createInfoRow("Longitud:", String.format("%.6f", lng)));
            }
        }
        
        return panel;
    }
    
    private JPanel createButtonPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 12, 12));
        panel.setBackground(Color.WHITE);
        panel.setBorder(new MatteBorder(1, 0, 0, 0, BORDER));
        
        JButton closeButton = new JButton("Cerrar");
        closeButton.setFont(new Font("Segoe UI", Font.BOLD, 14));
        closeButton.setBackground(PRIMARY);
        closeButton.setForeground(Color.WHITE);
        closeButton.setFocusPainted(false);
        closeButton.setBorder(new EmptyBorder(10, 24, 10, 24));
        closeButton.addActionListener(e -> dispose());
        
        panel.add(closeButton);
        
        return panel;
    }
    
    private JLabel createSectionLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(new Font("Segoe UI", Font.BOLD, 14));
        label.setForeground(TEXT_PRIMARY);
        label.setAlignmentX(Component.LEFT_ALIGNMENT);
        return label;
    }
    
    private JPanel createInfoRow(String label, String value) {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
        panel.setOpaque(false);
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel labelComp = new JLabel(label + " ");
        labelComp.setFont(new Font("Segoe UI", Font.BOLD, 13));
        labelComp.setForeground(TEXT_SECONDARY);
        
        JLabel valueComp = new JLabel(value);
        valueComp.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        valueComp.setForeground(TEXT_PRIMARY);
        
        panel.add(labelComp);
        panel.add(valueComp);
        
        return panel;
    }
    
    private boolean hasAIInfo() {
        return alert.has("created_by_model_id") 
                && !alert.get("created_by_model_id").isJsonNull()
                && !alert.get("created_by_model_id").getAsString().isEmpty();
    }
    
    private boolean hasGroundTruthInfo() {
        return alert.has("ground_truth_id") 
                && !alert.get("ground_truth_id").isJsonNull()
                && !alert.get("ground_truth_id").getAsString().isEmpty();
    }
    
    private boolean hasLocation() {
        if (!alert.has("location") || alert.get("location").isJsonNull()) {
            return false;
        }
        JsonObject location = alert.getAsJsonObject("location");
        return location.has("lat") && !location.get("lat").isJsonNull()
                && location.has("lng") && !location.get("lng").isJsonNull();
    }
    
    private String formatDate(String isoDate) {
        try {
            Instant instant = Instant.parse(isoDate);
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss")
                    .withZone(ZoneId.systemDefault());
            return formatter.format(instant);
        } catch (Exception e) {
            return isoDate;
        }
    }
}
