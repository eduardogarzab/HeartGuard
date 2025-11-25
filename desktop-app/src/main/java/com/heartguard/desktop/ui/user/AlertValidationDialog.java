package com.heartguard.desktop.ui.user;

import com.heartguard.desktop.api.AlertService;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.api.GroundTruthService;
import com.heartguard.desktop.config.AppConfig;
import com.heartguard.desktop.models.alert.*;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.CompletableFuture;

/**
 * Diálogo para validar alertas como verdadero/falso positivo
 * Permite crear registros de ground truth
 */
public class AlertValidationDialog extends JDialog {
    private static final Color PRIMARY = new Color(0, 120, 215);
    private static final Color SUCCESS = new Color(40, 167, 69);
    private static final Color DANGER = new Color(220, 53, 69);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER = new Color(223, 227, 230);
    
    private final Alert alert;
    private final String organizationId;
    private final String userId;
    private final String accessToken;
    
    private final AlertService alertService;
    private final GroundTruthService groundTruthService;
    
    private final JTextArea notesArea;
    private final JRadioButton truePositiveRadio;
    private final JRadioButton falsePositiveRadio;
    private final JButton submitButton;
    private final JButton cancelButton;
    
    private boolean validated = false;
    
    public AlertValidationDialog(Window owner, Alert alert, String organizationId, String userId, String accessToken) {
        super(owner, "Validar Alerta", ModalityType.APPLICATION_MODAL);
        
        this.alert = alert;
        this.organizationId = organizationId;
        this.userId = userId;
        this.accessToken = accessToken;
        
        String gatewayUrl = AppConfig.getInstance().getGatewayBaseUrl();
        this.alertService = new AlertService(gatewayUrl);
        this.alertService.setAccessToken(accessToken);
        this.groundTruthService = new GroundTruthService(gatewayUrl);
        this.groundTruthService.setAccessToken(accessToken);
        
        this.notesArea = new JTextArea(5, 40);
        this.truePositiveRadio = new JRadioButton("Verdadero Positivo - El evento es REAL");
        this.falsePositiveRadio = new JRadioButton("Falso Positivo - La IA se equivocó");
        this.submitButton = new JButton("✓ Validar y Resolver");
        this.cancelButton = new JButton("Cancelar");
        
        initUI();
    }
    
    private void initUI() {
        setLayout(new BorderLayout(16, 16));
        setSize(700, 600);
        setLocationRelativeTo(getOwner());
        
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setBorder(new EmptyBorder(24, 24, 24, 24));
        contentPanel.setBackground(Color.WHITE);
        
        // Título
        JLabel titleLabel = new JLabel("🔍 Validación de Alerta de IA");
        titleLabel.setFont(new Font("Inter", Font.BOLD, 20));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        contentPanel.add(titleLabel);
        contentPanel.add(Box.createVerticalStrut(20));
        
        // Información de la alerta
        contentPanel.add(createAlertInfoPanel());
        contentPanel.add(Box.createVerticalStrut(20));
        
        // Opciones de validación
        contentPanel.add(createValidationOptionsPanel());
        contentPanel.add(Box.createVerticalStrut(20));
        
        // Notas
        contentPanel.add(createNotesPanel());
        contentPanel.add(Box.createVerticalStrut(20));
        
        // Explicación de Ground Truth
        contentPanel.add(createGroundTruthExplanation());
        
        add(contentPanel, BorderLayout.CENTER);
        
        // Botones
        add(createButtonsPanel(), BorderLayout.SOUTH);
    }
    
    private JPanel createAlertInfoPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(247, 249, 251));
        panel.setBorder(new EmptyBorder(16, 16, 16, 16));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss")
                .withZone(ZoneId.systemDefault());
        
        addInfoRow(panel, "Paciente:", alert.getPatientName() != null ? alert.getPatientName() : "Desconocido");
        addInfoRow(panel, "Tipo de Alerta:", alert.getType().getEmoji() + " " + alert.getType().getDisplayName());
        addInfoRow(panel, "Nivel de Severidad:", alert.getAlertLevel().getDisplayName(), alert.getAlertLevel().getColor());
        addInfoRow(panel, "Descripción:", alert.getDescription());
        addInfoRow(panel, "Fecha y Hora:", formatter.format(alert.getCreatedAt()));
        
        if (alert.hasLocation()) {
            addInfoRow(panel, "Ubicación GPS:", 
                String.format("%.4f, %.4f", alert.getLatitude(), alert.getLongitude()));
        }
        
        if (alert.isCreatedByAI()) {
            JLabel aiLabel = new JLabel("🤖 Esta alerta fue generada por el modelo de IA");
            aiLabel.setFont(new Font("Inter", Font.ITALIC, 12));
            aiLabel.setForeground(PRIMARY);
            aiLabel.setBorder(new EmptyBorder(8, 0, 0, 0));
            panel.add(aiLabel);
        }
        
        return panel;
    }
    
    private void addInfoRow(JPanel panel, String label, String value) {
        addInfoRow(panel, label, value, TEXT_PRIMARY);
    }
    
    private void addInfoRow(JPanel panel, String label, String value, Color valueColor) {
        JPanel row = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 4));
        row.setOpaque(false);
        
        JLabel labelComp = new JLabel(label);
        labelComp.setFont(new Font("Inter", Font.BOLD, 13));
        labelComp.setForeground(TEXT_SECONDARY);
        labelComp.setPreferredSize(new Dimension(160, 20));
        
        JLabel valueComp = new JLabel(value);
        valueComp.setFont(new Font("Inter", Font.PLAIN, 13));
        valueComp.setForeground(valueColor);
        
        row.add(labelComp);
        row.add(valueComp);
        panel.add(row);
    }
    
    private JPanel createValidationOptionsPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(Color.WHITE);
        panel.setBorder(new LineBorder(BORDER, 1));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel title = new JLabel("¿El evento detectado por la IA fue real?");
        title.setFont(new Font("Inter", Font.BOLD, 14));
        title.setForeground(TEXT_PRIMARY);
        title.setBorder(new EmptyBorder(12, 12, 8, 12));
        title.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(title);
        
        ButtonGroup group = new ButtonGroup();
        group.add(truePositiveRadio);
        group.add(falsePositiveRadio);
        
        truePositiveRadio.setFont(new Font("Inter", Font.PLAIN, 13));
        truePositiveRadio.setForeground(SUCCESS);
        truePositiveRadio.setBackground(Color.WHITE);
        truePositiveRadio.setBorder(new EmptyBorder(8, 12, 8, 12));
        truePositiveRadio.setSelected(true);
        panel.add(truePositiveRadio);
        
        JLabel trueDesc = new JLabel("Se creará un registro de ground truth confirmando el evento");
        trueDesc.setFont(new Font("Inter", Font.ITALIC, 11));
        trueDesc.setForeground(TEXT_SECONDARY);
        trueDesc.setBorder(new EmptyBorder(0, 40, 12, 12));
        panel.add(trueDesc);
        
        falsePositiveRadio.setFont(new Font("Inter", Font.PLAIN, 13));
        falsePositiveRadio.setForeground(DANGER);
        falsePositiveRadio.setBackground(Color.WHITE);
        falsePositiveRadio.setBorder(new EmptyBorder(8, 12, 8, 12));
        panel.add(falsePositiveRadio);
        
        JLabel falseDesc = new JLabel("Se marcará la alerta como falso positivo para mejorar el modelo");
        falseDesc.setFont(new Font("Inter", Font.ITALIC, 11));
        falseDesc.setForeground(TEXT_SECONDARY);
        falseDesc.setBorder(new EmptyBorder(0, 40, 12, 12));
        panel.add(falseDesc);
        
        return panel;
    }
    
    private JPanel createNotesPanel() {
        JPanel panel = new JPanel(new BorderLayout(8, 8));
        panel.setBackground(Color.WHITE);
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel label = new JLabel("Notas clínicas (opcional):");
        label.setFont(new Font("Inter", Font.BOLD, 13));
        label.setForeground(TEXT_PRIMARY);
        
        notesArea.setFont(new Font("Inter", Font.PLAIN, 12));
        notesArea.setLineWrap(true);
        notesArea.setWrapStyleWord(true);
        notesArea.setBorder(new EmptyBorder(8, 8, 8, 8));
        
        JScrollPane scrollPane = new JScrollPane(notesArea);
        scrollPane.setBorder(new LineBorder(BORDER, 1));
        
        panel.add(label, BorderLayout.NORTH);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createGroundTruthExplanation() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(232, 244, 253));
        panel.setBorder(new EmptyBorder(12, 12, 12, 12));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel title = new JLabel("ℹ️ ¿Qué es Ground Truth?");
        title.setFont(new Font("Inter", Font.BOLD, 12));
        title.setForeground(TEXT_PRIMARY);
        panel.add(title);
        
        JLabel desc1 = new JLabel("<html><body style='width: 580px'>" +
            "Ground Truth son etiquetas validadas por personal médico que confirman si un evento fue real o no. " +
            "Esta información es crítica para:" +
            "</body></html>");
        desc1.setFont(new Font("Inter", Font.PLAIN, 11));
        desc1.setForeground(TEXT_SECONDARY);
        desc1.setBorder(new EmptyBorder(4, 0, 4, 0));
        panel.add(desc1);
        
        String[] points = {
            "✅ Medir la precisión del modelo de IA (% de aciertos)",
            "✅ Reentrenar el modelo con datos validados",
            "✅ Auditoría médica y legal",
            "✅ Estadísticas de calidad del servicio"
        };
        
        for (String point : points) {
            JLabel pointLabel = new JLabel(point);
            pointLabel.setFont(new Font("Inter", Font.PLAIN, 11));
            pointLabel.setForeground(TEXT_PRIMARY);
            pointLabel.setBorder(new EmptyBorder(2, 16, 2, 0));
            panel.add(pointLabel);
        }
        
        return panel;
    }
    
    private JPanel createButtonsPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 12, 12));
        panel.setBackground(Color.WHITE);
        panel.setBorder(new LineBorder(BORDER, 1, false));
        
        cancelButton.setFont(new Font("Inter", Font.PLAIN, 13));
        cancelButton.setForeground(TEXT_PRIMARY);
        cancelButton.setBackground(Color.WHITE);
        cancelButton.setBorder(new LineBorder(BORDER, 1));
        cancelButton.setFocusPainted(false);
        cancelButton.setPreferredSize(new Dimension(100, 36));
        cancelButton.addActionListener(e -> dispose());
        
        submitButton.setFont(new Font("Inter", Font.BOLD, 13));
        submitButton.setForeground(Color.WHITE);
        submitButton.setBackground(SUCCESS);
        submitButton.setFocusPainted(false);
        submitButton.setBorderPainted(false);
        submitButton.setPreferredSize(new Dimension(180, 36));
        submitButton.addActionListener(e -> submitValidation());
        
        panel.add(cancelButton);
        panel.add(submitButton);
        
        return panel;
    }
    
    private void submitValidation() {
        submitButton.setEnabled(false);
        submitButton.setText("⏳ Procesando...");
        
        boolean isTruePositive = truePositiveRadio.isSelected();
        String notes = notesArea.getText().trim();
        
        CompletableFuture.runAsync(() -> {
            try {
                if (isTruePositive) {
                    // Crear registro de ground truth (verdadero positivo)
                    EventType eventType = alert.getType().getCode().equals("GENERAL_RISK") 
                        ? EventType.GENERAL_RISK 
                        : EventType.fromCode(alert.getType().getCode());
                    
                    groundTruthService.validateAsTruePositive(
                        organizationId,
                        alert.getId(),
                        alert.getPatientId(),
                        eventType,
                        alert.getCreatedAt(),
                        null, // offset_at (fin del evento) - puede ser null
                        userId,
                        notes.isEmpty() ? "Evento confirmado por personal médico" : notes
                    );
                } else {
                    // Marcar como falso positivo
                    groundTruthService.validateAsFalsePositive(
                        alert.getId(),
                        userId,
                        notes.isEmpty() ? "Falso positivo confirmado por personal médico" : notes
                    );
                }
                
                // Resolver la alerta
                alertService.resolveAlert(alert.getId(), userId, notes);
                
                SwingUtilities.invokeLater(() -> {
                    validated = true;
                    JOptionPane.showMessageDialog(
                        this,
                        "Alerta validada y resuelta correctamente",
                        "Éxito",
                        JOptionPane.INFORMATION_MESSAGE
                    );
                    dispose();
                });
                
            } catch (ApiException e) {
                SwingUtilities.invokeLater(() -> {
                    submitButton.setEnabled(true);
                    submitButton.setText("✓ Validar y Resolver");
                    JOptionPane.showMessageDialog(
                        this,
                        "Error al validar: " + e.getMessage(),
                        "Error",
                        JOptionPane.ERROR_MESSAGE
                    );
                });
            }
        });
    }
    
    public boolean isValidated() {
        return validated;
    }
}
