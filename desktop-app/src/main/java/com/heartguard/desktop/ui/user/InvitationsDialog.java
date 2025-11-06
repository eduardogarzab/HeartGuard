package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.user.Invitation;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.util.List;
import java.util.function.Consumer;

/**
 * Modal que muestra las invitaciones pendientes del usuario y permite aceptarlas o rechazarlas.
 */
public class InvitationsDialog extends JDialog {
    private final ApiClient apiClient;
    private final String token;
    private final Runnable onMembershipChanged;

    private final JPanel listPanel = new JPanel();
    private final JLabel statusLabel = new JLabel(" ");

    public InvitationsDialog(Frame owner, ApiClient apiClient, String token, Runnable onMembershipChanged) {
        super(owner, "Mis invitaciones", true);
        this.apiClient = apiClient;
        this.token = token;
        this.onMembershipChanged = onMembershipChanged;
        initComponents();
        loadInvitations();
    }

    private void initComponents() {
        setSize(560, 420);
        setLocationRelativeTo(getOwner());
        setLayout(new BorderLayout());

        JLabel title = new JLabel("Invitaciones pendientes");
        title.setFont(new Font("Segoe UI", Font.BOLD, 20));
        JPanel header = new JPanel(new BorderLayout());
        header.setBorder(new EmptyBorder(16, 20, 0, 20));
        header.add(title, BorderLayout.WEST);
        add(header, BorderLayout.NORTH);

        listPanel.setLayout(new BoxLayout(listPanel, BoxLayout.Y_AXIS));
        listPanel.setBorder(new EmptyBorder(12, 20, 12, 20));
        listPanel.setOpaque(false);

        JScrollPane scrollPane = new JScrollPane(listPanel);
        scrollPane.setBorder(BorderFactory.createEmptyBorder());
        scrollPane.getViewport().setBackground(Color.WHITE);
        add(scrollPane, BorderLayout.CENTER);

        JPanel footer = new JPanel(new BorderLayout());
        footer.setBorder(new EmptyBorder(8, 20, 16, 20));
        statusLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        statusLabel.setForeground(new Color(100, 110, 120));
        footer.add(statusLabel, BorderLayout.WEST);

        JButton closeButton = new JButton("Cerrar");
        closeButton.addActionListener(e -> dispose());
        footer.add(closeButton, BorderLayout.EAST);

        add(footer, BorderLayout.SOUTH);
    }

    private void loadInvitations() {
        statusLabel.setForeground(new Color(100, 110, 120));
        statusLabel.setText("Cargando invitaciones...");
        listPanel.removeAll();
        listPanel.add(createLoadingPanel());
        listPanel.revalidate();
        listPanel.repaint();

        SwingWorker<List<Invitation>, Void> worker = new SwingWorker<>() {
            @Override
            protected List<Invitation> doInBackground() throws Exception {
                JsonArray array = apiClient.getPendingInvitations(token);
                return Invitation.listFrom(array);
            }

            @Override
            protected void done() {
                try {
                    List<Invitation> invitations = get();
                    renderInvitations(invitations);
                } catch (Exception ex) {
                    statusLabel.setForeground(Color.RED.darker());
                    statusLabel.setText("No fue posible obtener las invitaciones: " + ex.getMessage());
                    listPanel.removeAll();
                    listPanel.add(createEmptyState("No pudimos recuperar las invitaciones"));
                    listPanel.revalidate();
                    listPanel.repaint();
                }
            }
        };
        worker.execute();
    }

    private JPanel createLoadingPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER));
        panel.setOpaque(false);
        JLabel label = new JLabel("Conectando con el servicio...");
        label.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        panel.add(new JProgressBar());
        panel.add(label);
        return panel;
    }

    private JPanel createEmptyState(String message) {
        JPanel panel = new JPanel();
        panel.setOpaque(false);
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        JLabel icon = new JLabel("📭", SwingConstants.CENTER);
        icon.setAlignmentX(Component.CENTER_ALIGNMENT);
        icon.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 42));
        JLabel label = new JLabel(message);
        label.setAlignmentX(Component.CENTER_ALIGNMENT);
        label.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        label.setForeground(new Color(110, 120, 130));
        panel.add(Box.createVerticalStrut(24));
        panel.add(icon);
        panel.add(Box.createVerticalStrut(12));
        panel.add(label);
        panel.add(Box.createVerticalGlue());
        return panel;
    }

    private void renderInvitations(List<Invitation> invitations) {
        listPanel.removeAll();
        if (invitations.isEmpty()) {
            statusLabel.setForeground(new Color(76, 175, 80));
            statusLabel.setText("No tienes invitaciones pendientes");
            listPanel.add(createEmptyState("No hay invitaciones por ahora"));
        } else {
            statusLabel.setForeground(new Color(100, 110, 120));
            statusLabel.setText(invitations.size() + " invitaciones disponibles");
            for (Invitation invitation : invitations) {
                listPanel.add(createInvitationCard(invitation));
                listPanel.add(Box.createVerticalStrut(10));
            }
        }
        listPanel.revalidate();
        listPanel.repaint();
    }

    private JPanel createInvitationCard(Invitation invitation) {
        JPanel card = new JPanel(new BorderLayout());
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(229, 234, 243)),
                new EmptyBorder(16, 18, 16, 18)
        ));
        card.setBackground(Color.WHITE);

        JLabel title = new JLabel(invitation.getOrganizationLabel());
        title.setFont(new Font("Segoe UI", Font.BOLD, 16));
        JLabel subtitle = new JLabel("Rol propuesto: " + (invitation.getRoleLabel() != null ? invitation.getRoleLabel() : "Miembro"));
        subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        subtitle.setForeground(new Color(100, 110, 120));

        JPanel textPanel = new JPanel();
        textPanel.setOpaque(false);
        textPanel.setLayout(new BoxLayout(textPanel, BoxLayout.Y_AXIS));
        textPanel.add(title);
        textPanel.add(Box.createVerticalStrut(4));
        textPanel.add(subtitle);

        JLabel datesLabel = new JLabel();
        datesLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        datesLabel.setForeground(new Color(120, 130, 140));
        StringBuilder dateText = new StringBuilder();
        if (invitation.getSentAt() != null) {
            dateText.append("Enviada: ").append(invitation.getSentAt());
        }
        if (invitation.getExpiresAt() != null) {
            if (dateText.length() > 0) {
                dateText.append(" · ");
            }
            dateText.append("Expira: ").append(invitation.getExpiresAt());
        }
        datesLabel.setText(dateText.toString());
        textPanel.add(Box.createVerticalStrut(6));
        textPanel.add(datesLabel);

        JPanel actions = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        JButton acceptButton = new JButton("Aceptar");
        acceptButton.setBackground(new Color(46, 204, 113));
        acceptButton.setForeground(Color.WHITE);
        acceptButton.setFocusPainted(false);

        JButton rejectButton = new JButton("Rechazar");
        rejectButton.setBackground(new Color(231, 76, 60));
        rejectButton.setForeground(Color.WHITE);
        rejectButton.setFocusPainted(false);

        actions.add(acceptButton);
        actions.add(rejectButton);

        card.add(textPanel, BorderLayout.CENTER);
        card.add(actions, BorderLayout.EAST);

        Consumer<Boolean> refreshHandler = accepted -> handleInvitationAction(invitation, accepted, acceptButton, rejectButton);
        acceptButton.addActionListener(e -> refreshHandler.accept(true));
        rejectButton.addActionListener(e -> refreshHandler.accept(false));
        return card;
    }

    private void handleInvitationAction(Invitation invitation, boolean accept, JButton acceptButton, JButton rejectButton) {
        acceptButton.setEnabled(false);
        rejectButton.setEnabled(false);
        statusLabel.setForeground(new Color(33, 150, 243));
        statusLabel.setText("Procesando invitación...");

        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            @Override
            protected Void doInBackground() throws Exception {
                if (accept) {
                    JsonObject response = apiClient.acceptInvitation(token, invitation.getId());
                    if (response.has("error")) {
                        throw new ApiException(response.get("message").getAsString());
                    }
                } else {
                    JsonObject response = apiClient.rejectInvitation(token, invitation.getId());
                    if (response.has("error")) {
                        throw new ApiException(response.get("message").getAsString());
                    }
                }
                return null;
            }

            @Override
            protected void done() {
                try {
                    get();
                    statusLabel.setForeground(new Color(76, 175, 80));
                    statusLabel.setText(accept ? "Invitación aceptada con éxito" : "Invitación rechazada");
                    loadInvitations();
                    if (onMembershipChanged != null) {
                        onMembershipChanged.run();
                    }
                } catch (Exception ex) {
                    Throwable cause = ex.getCause();
                    statusLabel.setForeground(Color.RED.darker());
                    statusLabel.setText(cause != null ? cause.getMessage() : ex.getMessage());
                    acceptButton.setEnabled(true);
                    rejectButton.setEnabled(true);
                }
            }
        };
        worker.execute();
    }
}
