package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

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

    public PatientDetailDialog(Frame owner, ApiClient apiClient, String token, String orgId, String patientId, String patientName) {
        super(owner, "Paciente: " + patientName, true);
        this.apiClient = apiClient;
        this.token = token;
        this.orgId = orgId;
        this.patientId = patientId;
        this.patientName = patientName;
        initComponents();
        loadData();
    }

    private void initComponents() {
        setSize(820, 680);
        setLocationRelativeTo(getOwner());
        setLayout(new BorderLayout());
        getContentPane().setBackground(GLOBAL_BG);

        // Encabezado con título y separador
        JPanel header = new JPanel(new BorderLayout());
        header.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, false),
            new EmptyBorder(24, 24, 16, 24)
        ));
        header.setBackground(CARD_BG);
        
        JLabel title = new JLabel("Resumen Clínico");
        title.setFont(TITLE_FONT);
        title.setForeground(TEXT_PRIMARY);
        header.add(title, BorderLayout.WEST);
        
        JLabel patientNameLabel = new JLabel(patientName);
        patientNameLabel.setFont(new Font("Inter", Font.BOLD, 16));
        patientNameLabel.setForeground(PRIMARY_BLUE);
        header.add(patientNameLabel, BorderLayout.EAST);
        
        add(header, BorderLayout.NORTH);

        // Tabs estilizados
        JTabbedPane tabs = new JTabbedPane();
        tabs.setFont(new Font("Inter", Font.PLAIN, 15));
        tabs.setBackground(new Color(240, 242, 245));
        tabs.setForeground(TEXT_PRIMARY);

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
        JScrollPane alertsScroll = new JScrollPane(alertsList);
        alertsScroll.setBorder(new LineBorder(BORDER_LIGHT, 1));
        alertsScroll.setPreferredSize(new Dimension(0, 400));
        tabs.addTab("ALERTAS", alertsScroll);

        JList<String> notesList = new JList<>(notesModel);
        notesList.setFont(BODY_FONT);
        notesList.setBackground(CARD_BG);
        notesList.setBorder(new EmptyBorder(8, 8, 8, 8));
        JScrollPane notesScroll = new JScrollPane(notesList);
        notesScroll.setBorder(new LineBorder(BORDER_LIGHT, 1));
        tabs.addTab("NOTAS", notesScroll);

        JPanel tabsWrapper = new JPanel(new BorderLayout());
        tabsWrapper.setBorder(new EmptyBorder(0, 16, 16, 16));
        tabsWrapper.setOpaque(false);
        tabsWrapper.add(tabs, BorderLayout.CENTER);
        add(tabsWrapper, BorderLayout.CENTER);

        // Footer con estado y botón cerrar
        JPanel footer = new JPanel(new BorderLayout());
        footer.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, false),
            new EmptyBorder(16, 24, 16, 24)
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
        closeButton.addActionListener(e -> dispose());
        footer.add(closeButton, BorderLayout.EAST);
        
        add(footer, BorderLayout.SOUTH);
    }

    private void loadData() {
        statusLabel.setText("Recuperando información clínica...");
        statusLabel.setForeground(TEXT_SECONDARY);
        setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));

        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            @Override
            protected Void doInBackground() throws Exception {
                JsonObject detailResponse = apiClient.getOrganizationPatientDetail(token, orgId, patientId);
                JsonObject detailData = detailResponse.getAsJsonObject("data");
                JsonObject patient = detailData.getAsJsonObject("patient");
                updateInfoArea(patient);

                JsonObject alertsResponse = apiClient.getOrganizationPatientAlerts(token, orgId, patientId, 20);
                JsonArray alerts = alertsResponse.getAsJsonObject("data").getAsJsonArray("alerts");
                updateAlerts(alerts);

                JsonObject notesResponse = apiClient.getOrganizationPatientNotes(token, orgId, patientId, 20);
                JsonArray notes = notesResponse.getAsJsonObject("data").getAsJsonArray("notes");
                updateNotes(notes);
                return null;
            }

            @Override
            protected void done() {
                setCursor(Cursor.getDefaultCursor());
                try {
                    get();
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
}
