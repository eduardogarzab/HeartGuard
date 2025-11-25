package com.heartguard.desktop.ui.user;

import com.heartguard.desktop.api.AlertService;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.config.AppConfig;
import com.heartguard.desktop.models.alert.*;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.CompletableFuture;

/**
 * Diálogo para gestionar alertas: Reconocer o Resolver
 * Sigue el flujo: pending → acknowledged → resolved (con ground truth automático)
 */
public class AlertValidationDialog extends JDialog {
    private static final Color PRIMARY = new Color(0, 120, 215);
    private static final Color SUCCESS = new Color(40, 167, 69);
    private static final Color WARNING = new Color(255, 193, 7);
    private static final Color DANGER = new Color(220, 53, 69);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER = new Color(223, 227, 230);
    private static final Color BG_LIGHT = new Color(247, 249, 251);
    
    private final Alert alert;
    private final String organizationId;
    private final String userId;
    private final String accessToken;
    private final String patientName;
    
    private final AlertService alertService;
    
    private final JTextArea notesArea;
    private final JRadioButton acknowledgeRadio;
    private final JRadioButton resolveRadio;
    private final JRadioButton truePositiveRadio;
    private final JRadioButton falsePositiveRadio;
    private final JPanel resolveOptionsPanel;
    private final JButton submitButton;
    private final JButton cancelButton;
    
    private boolean validated = false;
    
    public AlertValidationDialog(Window owner, Alert alert, String organizationId, String userId, String accessToken, String patientName) {
        super(owner, "Gestionar Alerta", ModalityType.APPLICATION_MODAL);
        
        this.alert = alert;
        this.organizationId = organizationId;
        this.userId = userId;
        this.accessToken = accessToken;
        this.patientName = patientName;
        
        String gatewayUrl = AppConfig.getInstance().getGatewayBaseUrl();
        this.alertService = new AlertService(gatewayUrl);
        this.alertService.setAccessToken(accessToken);
        
        this.notesArea = new JTextArea(6, 50);
        this.acknowledgeRadio = new JRadioButton("<html><b>Reconocer</b> - Confirmo que vi la alerta y la estoy revisando</html>");
        this.resolveRadio = new JRadioButton("<html><b>Resolver</b> - Ya atendí el caso y quiero cerrarlo</html>");
        this.truePositiveRadio = new JRadioButton("✅ Verdadero Positivo - El evento fue REAL");
        this.falsePositiveRadio = new JRadioButton("❌ Falso Positivo - La IA se equivocó");
        this.resolveOptionsPanel = createResolveOptionsPanel();
        this.submitButton = new JButton("Enviar");
        this.cancelButton = new JButton("Cancelar");
        
        initUI();
    }
    
    private void initUI() {
        setLayout(new BorderLayout(0, 0));
        setSize(900, 750);
        setLocationRelativeTo(getOwner());
        
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setBorder(new EmptyBorder(28, 32, 28, 32));
        contentPanel.setBackground(Color.WHITE);
        
        // Header con título grande
        JLabel titleLabel = new JLabel("🚨 Gestión de Alerta");
        titleLabel.setFont(new Font("Inter", Font.BOLD, 26));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        contentPanel.add(titleLabel);
        
        JLabel subtitleLabel = new JLabel("Reconoce o resuelve esta alerta generada por IA");
        subtitleLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        subtitleLabel.setForeground(TEXT_SECONDARY);
        subtitleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        contentPanel.add(subtitleLabel);
        contentPanel.add(Box.createVerticalStrut(24));
        
        // Información de la alerta (más grande y prominente)
        contentPanel.add(createAlertInfoPanel());
        contentPanel.add(Box.createVerticalStrut(24));
        
        // Selector de acción: Reconocer vs Resolver
        contentPanel.add(createActionSelectorPanel());
        contentPanel.add(Box.createVerticalStrut(20));
        
        // Notas
        contentPanel.add(createNotesPanel());
        
        // Envolver contentPanel en JScrollPane para permitir scroll
        JScrollPane scrollPane = new JScrollPane(contentPanel);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        add(scrollPane, BorderLayout.CENTER);
        
        // Botones
        add(createButtonsPanel(), BorderLayout.SOUTH);
    }
    
    private JPanel createAlertInfoPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(BG_LIGHT);
        panel.setBorder(new EmptyBorder(20, 20, 20, 20));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss")
                .withZone(ZoneId.systemDefault());
        
        // Tipo de alerta grande y prominente
        JLabel typeLabel = new JLabel(alert.getType().getEmoji() + " " + alert.getType().getDisplayName());
        typeLabel.setFont(new Font("Inter", Font.BOLD, 22));
        typeLabel.setForeground(alert.getType().getColor());
        panel.add(typeLabel);
        panel.add(Box.createVerticalStrut(8));
        
        // Descripción
        JLabel descLabel = new JLabel("<html><body style='width: 750px'><b>Descripción:</b> " + alert.getDescription() + "</body></html>");
        descLabel.setFont(new Font("Inter", Font.PLAIN, 15));
        descLabel.setForeground(TEXT_PRIMARY);
        panel.add(descLabel);
        panel.add(Box.createVerticalStrut(16));
        
        // Grid con información
        JPanel gridPanel = new JPanel(new GridLayout(0, 2, 24, 12));
        gridPanel.setOpaque(false);
        
        addInfoField(gridPanel, "👤 Paciente", patientName != null ? patientName : "Desconocido");
        addInfoField(gridPanel, "📊 Nivel", alert.getAlertLevel().getDisplayName());
        addInfoField(gridPanel, "🕐 Fecha/Hora", formatter.format(alert.getCreatedAt()));
        addInfoField(gridPanel, "📍 Estado", alert.getStatus().getDisplayName());
        
        if (alert.hasLocation()) {
            addInfoField(gridPanel, "🌍 Ubicación GPS", 
                String.format("%.4f, %.4f", alert.getLatitude(), alert.getLongitude()));
        }
        
        if (alert.isCreatedByAI()) {
            addInfoField(gridPanel, "🤖 Origen", "Generada por Inteligencia Artificial");
        }
        
        panel.add(gridPanel);
        
        return panel;
    }
    
    private void addInfoField(JPanel panel, String label, String value) {
        JPanel fieldPanel = new JPanel(new BorderLayout(8, 0));
        fieldPanel.setOpaque(false);
        
        JLabel labelComp = new JLabel(label);
        labelComp.setFont(new Font("Inter", Font.BOLD, 14));
        labelComp.setForeground(TEXT_SECONDARY);
        
        JLabel valueComp = new JLabel(value);
        valueComp.setFont(new Font("Inter", Font.PLAIN, 14));
        valueComp.setForeground(TEXT_PRIMARY);
        
        fieldPanel.add(labelComp, BorderLayout.WEST);
        fieldPanel.add(valueComp, BorderLayout.CENTER);
        
        panel.add(fieldPanel);
    }
    
    private JPanel createActionSelectorPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel title = new JLabel("Selecciona una acción:");
        title.setFont(new Font("Inter", Font.BOLD, 16));
        title.setForeground(TEXT_PRIMARY);
        title.setAlignmentX(Component.LEFT_ALIGNMENT);
        panel.add(title);
        panel.add(Box.createVerticalStrut(12));
        
        ButtonGroup actionGroup = new ButtonGroup();
        actionGroup.add(acknowledgeRadio);
        actionGroup.add(resolveRadio);
        
        // Reconocer
        acknowledgeRadio.setFont(new Font("Inter", Font.PLAIN, 15));
        acknowledgeRadio.setForeground(TEXT_PRIMARY);
        acknowledgeRadio.setBackground(Color.WHITE);
        acknowledgeRadio.setBorder(new EmptyBorder(12, 16, 12, 16));
        acknowledgeRadio.setAlignmentX(Component.LEFT_ALIGNMENT);
        acknowledgeRadio.addActionListener(e -> {
            resolveOptionsPanel.setVisible(false);
            submitButton.setText("✓ Reconocer Alerta");
            submitButton.setBackground(WARNING);
            revalidate();
        });
        
        JPanel ackPanel = new JPanel(new BorderLayout());
        ackPanel.setBackground(Color.WHITE);
        ackPanel.setBorder(new LineBorder(BORDER, 2));
        ackPanel.add(acknowledgeRadio, BorderLayout.CENTER);
        
        JLabel ackDesc = new JLabel("Estado pasará de 'pendiente' → 'reconocida'");
        ackDesc.setFont(new Font("Inter", Font.ITALIC, 13));
        ackDesc.setForeground(TEXT_SECONDARY);
        ackDesc.setBorder(new EmptyBorder(0, 52, 12, 16));
        ackPanel.add(ackDesc, BorderLayout.SOUTH);
        
        panel.add(ackPanel);
        panel.add(Box.createVerticalStrut(12));
        
        // Resolver
        resolveRadio.setFont(new Font("Inter", Font.PLAIN, 15));
        resolveRadio.setForeground(TEXT_PRIMARY);
        resolveRadio.setBackground(Color.WHITE);
        resolveRadio.setBorder(new EmptyBorder(12, 16, 12, 16));
        resolveRadio.setAlignmentX(Component.LEFT_ALIGNMENT);
        resolveRadio.setSelected(true);
        resolveRadio.addActionListener(e -> {
            resolveOptionsPanel.setVisible(true);
            submitButton.setText("✓ Resolver y Crear Ground Truth");
            submitButton.setBackground(SUCCESS);
            revalidate();
        });
        
        JPanel resolvePanel = new JPanel(new BorderLayout());
        resolvePanel.setBackground(Color.WHITE);
        resolvePanel.setBorder(new LineBorder(PRIMARY, 2));
        resolvePanel.add(resolveRadio, BorderLayout.CENTER);
        
        JLabel resolveDesc = new JLabel("Cerrará el caso y creará registro de Ground Truth automáticamente");
        resolveDesc.setFont(new Font("Inter", Font.ITALIC, 13));
        resolveDesc.setForeground(TEXT_SECONDARY);
        resolveDesc.setBorder(new EmptyBorder(0, 52, 12, 16));
        resolvePanel.add(resolveDesc, BorderLayout.SOUTH);
        
        panel.add(resolvePanel);
        panel.add(Box.createVerticalStrut(16));
        panel.add(resolveOptionsPanel);
        
        return panel;
    }
    
    private JPanel createResolveOptionsPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(new Color(240, 248, 255));
        panel.setBorder(new EmptyBorder(16, 20, 16, 20));
        
        JLabel title = new JLabel("¿El evento detectado por la IA fue real?");
        title.setFont(new Font("Inter", Font.BOLD, 16));
        title.setForeground(TEXT_PRIMARY);
        panel.add(title, BorderLayout.NORTH);
        
        // Panel con 2 columnas para las opciones
        JPanel optionsPanel = new JPanel(new GridLayout(1, 2, 16, 0));
        optionsPanel.setBackground(new Color(240, 248, 255));
        optionsPanel.setBorder(new EmptyBorder(16, 0, 0, 0));
        
        ButtonGroup group = new ButtonGroup();
        group.add(truePositiveRadio);
        group.add(falsePositiveRadio);
        
        // Panel Verdadero Positivo
        JPanel truePanel = new JPanel();
        truePanel.setLayout(new BoxLayout(truePanel, BoxLayout.Y_AXIS));
        truePanel.setBackground(Color.WHITE);
        truePanel.setBorder(new CompoundBorder(
            new LineBorder(SUCCESS, 2, true),
            new EmptyBorder(16, 16, 16, 16)
        ));
        
        truePositiveRadio.setFont(new Font("Inter", Font.BOLD, 15));
        truePositiveRadio.setForeground(SUCCESS);
        truePositiveRadio.setBackground(Color.WHITE);
        truePositiveRadio.setSelected(true);
        truePanel.add(truePositiveRadio);
        truePanel.add(Box.createVerticalStrut(8));
        
        JLabel trueDesc = new JLabel("<html><div style='width:200px'>Se guardará como verdadero positivo en Ground Truth</div></html>");
        trueDesc.setFont(new Font("Inter", Font.PLAIN, 13));
        trueDesc.setForeground(TEXT_SECONDARY);
        truePanel.add(trueDesc);
        
        // Panel Falso Positivo
        JPanel falsePanel = new JPanel();
        falsePanel.setLayout(new BoxLayout(falsePanel, BoxLayout.Y_AXIS));
        falsePanel.setBackground(Color.WHITE);
        falsePanel.setBorder(new CompoundBorder(
            new LineBorder(DANGER, 2, true),
            new EmptyBorder(16, 16, 16, 16)
        ));
        
        falsePositiveRadio.setFont(new Font("Inter", Font.BOLD, 15));
        falsePositiveRadio.setForeground(DANGER);
        falsePositiveRadio.setBackground(Color.WHITE);
        falsePanel.add(falsePositiveRadio);
        falsePanel.add(Box.createVerticalStrut(8));
        
        JLabel falseDesc = new JLabel("<html><div style='width:200px'>Se marcará como error de IA para reentrenamiento</div></html>");
        falseDesc.setFont(new Font("Inter", Font.PLAIN, 13));
        falseDesc.setForeground(TEXT_SECONDARY);
        falsePanel.add(falseDesc);
        
        optionsPanel.add(truePanel);
        optionsPanel.add(falsePanel);
        
        panel.add(optionsPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createNotesPanel() {
        JPanel panel = new JPanel(new BorderLayout(8, 8));
        panel.setBackground(Color.WHITE);
        panel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel label = new JLabel("📝 Notas clínicas:");
        label.setFont(new Font("Inter", Font.BOLD, 15));
        label.setForeground(TEXT_PRIMARY);
        
        notesArea.setFont(new Font("Inter", Font.PLAIN, 14));
        notesArea.setLineWrap(true);
        notesArea.setWrapStyleWord(true);
        notesArea.setBorder(new EmptyBorder(12, 12, 12, 12));
        notesArea.setBackground(BG_LIGHT);
        
        JScrollPane scrollPane = new JScrollPane(notesArea);
        scrollPane.setBorder(new LineBorder(BORDER, 1));
        scrollPane.setPreferredSize(new Dimension(800, 120));
        
        panel.add(label, BorderLayout.NORTH);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createButtonsPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 16, 16));
        panel.setBackground(Color.WHITE);
        panel.setBorder(new LineBorder(BORDER, 1, false));
        
        cancelButton.setFont(new Font("Inter", Font.PLAIN, 14));
        cancelButton.setForeground(TEXT_PRIMARY);
        cancelButton.setBackground(Color.WHITE);
        cancelButton.setBorder(new LineBorder(BORDER, 2));
        cancelButton.setFocusPainted(false);
        cancelButton.setPreferredSize(new Dimension(120, 42));
        cancelButton.addActionListener(e -> dispose());
        
        submitButton.setFont(new Font("Inter", Font.BOLD, 14));
        submitButton.setForeground(Color.WHITE);
        submitButton.setBackground(SUCCESS);
        submitButton.setFocusPainted(false);
        submitButton.setBorderPainted(false);
        submitButton.setPreferredSize(new Dimension(280, 42));
        submitButton.setText("✓ Resolver y Crear Ground Truth");
        submitButton.addActionListener(e -> submitAction());
        
        panel.add(cancelButton);
        panel.add(submitButton);
        
        return panel;
    }
    
    private void submitAction() {
        submitButton.setEnabled(false);
        cancelButton.setEnabled(false);
        submitButton.setText("⏳ Procesando...");
        
        String notes = notesArea.getText().trim();
        boolean isResolve = resolveRadio.isSelected();
        
        CompletableFuture.runAsync(() -> {
            try {
                if (isResolve) {
                    // RESOLVER: Cambia estado a resolved y crea Ground Truth automáticamente
                    String outcome = truePositiveRadio.isSelected() ? "TRUE_POSITIVE" : "FALSE_POSITIVE";
                    
                    alertService.resolveAlert(
                        organizationId,
                        alert.getPatientId(),
                        alert.getId(),
                        userId,
                        outcome,
                        notes.isEmpty() ? null : notes
                    );
                    
                    SwingUtilities.invokeLater(() -> {
                        validated = true;
                        JOptionPane.showMessageDialog(
                            this,
                            "<html><body style='width: 350px'>" +
                            "<h3>✅ Alerta Resuelta</h3>" +
                            "<p>La alerta ha sido marcada como <b>" + outcome + "</b></p>" +
                            "<p>El registro de Ground Truth se creó automáticamente en la base de datos.</p>" +
                            "<p><i>Este dato se usará para mejorar el modelo de IA.</i></p>" +
                            "</body></html>",
                            "Éxito",
                            JOptionPane.INFORMATION_MESSAGE
                        );
                        dispose();
                    });
                } else {
                    // RECONOCER: Solo cambia estado a acknowledged
                    alertService.acknowledgeAlert(
                        organizationId,
                        alert.getPatientId(),
                        alert.getId(),
                        userId,
                        notes.isEmpty() ? null : notes
                    );
                    
                    SwingUtilities.invokeLater(() -> {
                        validated = true;
                        JOptionPane.showMessageDialog(
                            this,
                            "<html><body style='width: 350px'>" +
                            "<h3>✅ Alerta Reconocida</h3>" +
                            "<p>La alerta cambió de estado <b>pendiente → reconocida</b></p>" +
                            "<p>Recuerda resolverla una vez que hayas atendido el caso.</p>" +
                            "</body></html>",
                            "Éxito",
                            JOptionPane.INFORMATION_MESSAGE
                        );
                        dispose();
                    });
                }
                
            } catch (ApiException e) {
                SwingUtilities.invokeLater(() -> {
                    submitButton.setEnabled(true);
                    cancelButton.setEnabled(true);
                    submitButton.setText(isResolve ? "✓ Resolver y Crear Ground Truth" : "✓ Reconocer Alerta");
                    JOptionPane.showMessageDialog(
                        this,
                        "<html><body style='width: 300px'>" +
                        "<h3>❌ Error</h3>" +
                        "<p>" + e.getMessage() + "</p>" +
                        "</body></html>",
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
