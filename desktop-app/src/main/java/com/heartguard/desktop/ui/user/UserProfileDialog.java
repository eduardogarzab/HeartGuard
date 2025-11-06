package com.heartguard.desktop.ui.user;

import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.user.UserProfile;
import com.heartguard.desktop.util.JsonUtils;

import javax.swing.*;
import java.awt.*;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;

/**
 * Modal que permite visualizar y editar información básica del perfil.
 */
public class UserProfileDialog extends JDialog {
    private final ApiClient apiClient;
    private final String token;
    private final Consumer<UserProfile> onProfileUpdated;

    private final JTextField nameField = new JTextField(28);
    private final JTextField photoField = new JTextField(28);
    private final JCheckBox twoFactorCheck = new JCheckBox("Habilitar segundo factor de autenticación");
    private final JLabel statusLabel = new JLabel(" ");

    private UserProfile profile;

    public UserProfileDialog(Frame owner, ApiClient apiClient, String token, UserProfile profile,
                             Consumer<UserProfile> onProfileUpdated) {
        super(owner, "Mi información de perfil", true);
        this.apiClient = apiClient;
        this.token = token;
        this.profile = profile;
        this.onProfileUpdated = onProfileUpdated;
        initComponents();
        loadProfile();
    }

    private void initComponents() {
        setSize(520, 360);
        setLocationRelativeTo(getOwner());
        setLayout(new BorderLayout(0, 12));

        JPanel header = new JPanel(new BorderLayout());
        header.setBorder(BorderFactory.createEmptyBorder(16, 20, 0, 20));
        JLabel title = new JLabel("Mi información de perfil");
        title.setFont(new Font("Segoe UI", Font.BOLD, 20));
        header.add(title, BorderLayout.WEST);
        add(header, BorderLayout.NORTH);

        JPanel formPanel = new JPanel(new GridBagLayout());
        formPanel.setBorder(BorderFactory.createEmptyBorder(8, 24, 8, 24));
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(8, 8, 8, 8);
        gbc.anchor = GridBagConstraints.WEST;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.gridx = 0;
        gbc.gridy = 0;

        JLabel nameLabel = new JLabel("Nombre completo");
        nameLabel.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        formPanel.add(nameLabel, gbc);

        gbc.gridx = 1;
        nameField.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        formPanel.add(nameField, gbc);

        gbc.gridx = 0;
        gbc.gridy++;
        JLabel photoLabel = new JLabel("Foto (URL opcional)");
        photoLabel.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        formPanel.add(photoLabel, gbc);

        gbc.gridx = 1;
        formPanel.add(photoField, gbc);

        gbc.gridx = 0;
        gbc.gridy++;
        gbc.gridwidth = 2;
        formPanel.add(twoFactorCheck, gbc);

        add(formPanel, BorderLayout.CENTER);

        JPanel footer = new JPanel(new BorderLayout());
        footer.setBorder(BorderFactory.createEmptyBorder(0, 24, 16, 24));
        statusLabel.setForeground(new Color(100, 110, 120));
        statusLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        footer.add(statusLabel, BorderLayout.NORTH);

        JPanel buttons = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        JButton cancelButton = new JButton("Cerrar");
        JButton saveButton = new JButton("Guardar cambios");
        buttons.add(cancelButton);
        buttons.add(saveButton);
        footer.add(buttons, BorderLayout.SOUTH);
        add(footer, BorderLayout.SOUTH);

        cancelButton.addActionListener(e -> dispose());
        saveButton.addActionListener(e -> saveChanges(saveButton));
    }

    private void loadProfile() {
        if (profile != null) {
            fillForm(profile);
            return;
        }

        setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
        statusLabel.setText("Cargando perfil...");
        SwingWorker<UserProfile, Void> worker = new SwingWorker<>() {
            @Override
            protected UserProfile doInBackground() throws Exception {
                JsonObject response = apiClient.getCurrentUserProfile(token);
                JsonObject data = response.getAsJsonObject("data");
                return JsonUtils.GSON.fromJson(data, UserProfile.class);
            }

            @Override
            protected void done() {
                setCursor(Cursor.getDefaultCursor());
                try {
                    profile = get();
                    fillForm(profile);
                    statusLabel.setText("Perfil cargado correctamente");
                } catch (Exception ex) {
                    statusLabel.setForeground(Color.RED.darker());
                    statusLabel.setText("No fue posible obtener el perfil: " + ex.getMessage());
                }
            }
        };
        worker.execute();
    }

    private void fillForm(UserProfile profile) {
        nameField.setText(profile.getName());
        photoField.setText(profile.getProfilePhotoUrl() != null ? profile.getProfilePhotoUrl() : "");
        twoFactorCheck.setSelected(profile.isTwoFactorEnabled());
        statusLabel.setForeground(new Color(100, 110, 120));
        statusLabel.setText("Última actualización: " + (profile.getUpdatedAt() != null ? profile.getUpdatedAt() : "n/d"));
    }

    private void saveChanges(JButton saveButton) {
        String name = nameField.getText().trim();
        if (name.isEmpty()) {
            statusLabel.setForeground(Color.RED.darker());
            statusLabel.setText("El nombre no puede estar vacío");
            return;
        }

        Map<String, Object> updates = new HashMap<>();
        if (!name.equals(profile != null ? profile.getName() : "")) {
            updates.put("name", name);
        }
        String photo = photoField.getText().trim();
        updates.put("profile_photo_url", photo.isEmpty() ? null : photo);
        updates.put("two_factor_enabled", twoFactorCheck.isSelected());

        if (updates.isEmpty()) {
            statusLabel.setForeground(new Color(76, 175, 80));
            statusLabel.setText("No hay cambios para guardar");
            return;
        }

        saveButton.setEnabled(false);
        setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
        statusLabel.setForeground(new Color(33, 150, 243));
        statusLabel.setText("Guardando cambios...");

        SwingWorker<UserProfile, Void> worker = new SwingWorker<>() {
            @Override
            protected UserProfile doInBackground() throws Exception {
                JsonObject response = apiClient.updateCurrentUserProfile(token, updates);
                JsonObject data = response.getAsJsonObject("data");
                return JsonUtils.GSON.fromJson(data, UserProfile.class);
            }

            @Override
            protected void done() {
                setCursor(Cursor.getDefaultCursor());
                saveButton.setEnabled(true);
                try {
                    profile = get();
                    fillForm(profile);
                    statusLabel.setForeground(new Color(76, 175, 80));
                    statusLabel.setText("Perfil actualizado correctamente");
                    if (onProfileUpdated != null) {
                        onProfileUpdated.accept(profile);
                    }
                } catch (Exception ex) {
                    Throwable cause = ex.getCause();
                    statusLabel.setForeground(Color.RED.darker());
                    statusLabel.setText(cause instanceof ApiException ? cause.getMessage() : ex.getMessage());
                }
            }
        };
        worker.execute();
    }
}
