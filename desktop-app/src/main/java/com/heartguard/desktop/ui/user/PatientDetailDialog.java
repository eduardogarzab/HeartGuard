package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Ventana modal con pestañas para mostrar detalles de un paciente desde perspectiva organizacional.
 */
public class PatientDetailDialog extends JDialog {
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
        setSize(680, 520);
        setLocationRelativeTo(getOwner());
        setLayout(new BorderLayout());

        JPanel header = new JPanel(new BorderLayout());
        header.setBorder(new EmptyBorder(18, 24, 0, 24));
        JLabel title = new JLabel("Resumen clínico de " + patientName);
        title.setFont(new Font("Segoe UI", Font.BOLD, 18));
        header.add(title, BorderLayout.WEST);
        add(header, BorderLayout.NORTH);

        JTabbedPane tabs = new JTabbedPane();
        tabs.setFont(new Font("Segoe UI", Font.PLAIN, 14));

        infoArea.setEditable(false);
        infoArea.setLineWrap(true);
        infoArea.setWrapStyleWord(true);
        infoArea.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        infoArea.setMargin(new Insets(12, 12, 12, 12));
        JScrollPane infoScroll = new JScrollPane(infoArea);
        infoScroll.setBorder(new EmptyBorder(0, 0, 0, 0));
        tabs.addTab("Métricas", infoScroll);

        JList<String> alertsList = new JList<>(alertsModel);
        alertsList.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        JScrollPane alertsScroll = new JScrollPane(alertsList);
        alertsScroll.setBorder(new EmptyBorder(0, 0, 0, 0));
        tabs.addTab("Alertas", alertsScroll);

        JList<String> notesList = new JList<>(notesModel);
        notesList.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        JScrollPane notesScroll = new JScrollPane(notesList);
        notesScroll.setBorder(new EmptyBorder(0, 0, 0, 0));
        tabs.addTab("Notas", notesScroll);

        add(tabs, BorderLayout.CENTER);

        JPanel footer = new JPanel(new BorderLayout());
        footer.setBorder(new EmptyBorder(8, 24, 16, 24));
        statusLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        statusLabel.setForeground(new Color(120, 130, 140));
        footer.add(statusLabel, BorderLayout.WEST);
        JButton closeButton = new JButton("Cerrar");
        closeButton.addActionListener(e -> dispose());
        footer.add(closeButton, BorderLayout.EAST);
        add(footer, BorderLayout.SOUTH);
    }

    private void loadData() {
        statusLabel.setText("Recuperando información clínica...");
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
                    statusLabel.setForeground(new Color(76, 175, 80));
                    statusLabel.setText("Información actualizada");
                } catch (Exception ex) {
                    Throwable cause = ex.getCause();
                    statusLabel.setForeground(Color.RED.darker());
                    statusLabel.setText(cause != null ? cause.getMessage() : ex.getMessage());
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
                JsonObject event = alert.has("event") && alert.get("event").isJsonObject()
                        ? alert.getAsJsonObject("event")
                        : null;
                JsonObject levelObj = alert.has("level") && alert.get("level").isJsonObject()
                        ? alert.getAsJsonObject("level")
                        : null;
                String label = event != null ? safe(event.get("label")) : safe(alert.get("label"));
                String created = safe(alert.get("created_at"));
                String level = levelObj != null ? safe(levelObj.get("label")) : "-";
                alertsModel.addElement(String.format("[%s] %s · %s", created, label, level));
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
