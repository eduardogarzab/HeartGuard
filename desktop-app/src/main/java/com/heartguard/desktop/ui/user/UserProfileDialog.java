package com.heartguard.desktop.ui.user;

import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.user.UserProfile;
import com.heartguard.desktop.util.JsonUtils;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;

/**
 * Modal profesional para visualizar y editar información de perfil.
 * Bordes redondeados 12px, sombras sutiles, tipografía clara 14-16px.
 */
public class UserProfileDialog extends JDialog {
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
    private static final Font BODY_BOLD = new Font("Inter", Font.BOLD, 14);
    private static final Font CAPTION_FONT = new Font("Inter", Font.PLAIN, 13);
    
    private final ApiClient apiClient;
    private final String token;
    private final Consumer<UserProfile> onProfileUpdated;

    private final JLabel emailLabel = new JLabel("-");
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
        setSize(600, 480);
        setLocationRelativeTo(getOwner());
        setLayout(new BorderLayout(0, 0));
        getContentPane().setBackground(GLOBAL_BG);

        // Encabezado estilizado
        JPanel header = new JPanel(new BorderLayout());
        header.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, false),
            new EmptyBorder(24, 24, 16, 24)
        ));
        header.setBackground(CARD_BG);
        
        JLabel title = new JLabel("Mi Perfil");
        title.setFont(TITLE_FONT);
        title.setForeground(TEXT_PRIMARY);
        header.add(title, BorderLayout.WEST);
        add(header, BorderLayout.NORTH);

        // Formulario con grilla
        JPanel formPanel = new JPanel(new GridBagLayout());
        formPanel.setBorder(new EmptyBorder(24, 24, 24, 24));
        formPanel.setBackground(CARD_BG);
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(12, 12, 12, 12);
        gbc.anchor = GridBagConstraints.WEST;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.gridx = 0;
        gbc.gridy = 0;

        // Campo Email (read-only)
        JLabel emailFieldLabel = new JLabel("Correo electrónico");
        emailFieldLabel.setFont(BODY_BOLD);
        emailFieldLabel.setForeground(TEXT_PRIMARY);
        formPanel.add(emailFieldLabel, gbc);

        gbc.gridx = 1;
        gbc.weightx = 1.0;
        emailLabel.setFont(BODY_FONT);
        emailLabel.setForeground(TEXT_SECONDARY);
        formPanel.add(emailLabel, gbc);

        // Campo Nombre
        gbc.gridx = 0;
        gbc.gridy++;
        gbc.weightx = 0;
        JLabel nameLabel = new JLabel("Nombre completo");
        nameLabel.setFont(BODY_BOLD);
        nameLabel.setForeground(TEXT_PRIMARY);
        formPanel.add(nameLabel, gbc);

        gbc.gridx = 1;
        gbc.weightx = 1.0;
        nameField.setFont(BODY_FONT);
        nameField.setPreferredSize(new Dimension(300, 36));
        nameField.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1),
            new EmptyBorder(8, 12, 8, 12)
        ));
        formPanel.add(nameField, gbc);

        gbc.gridx = 0;
        gbc.gridy++;
        gbc.weightx = 0;
        JLabel photoLabel = new JLabel("Foto de perfil (URL)");
        photoLabel.setFont(BODY_BOLD);
        photoLabel.setForeground(TEXT_PRIMARY);
        formPanel.add(photoLabel, gbc);

        gbc.gridx = 1;
        gbc.weightx = 1.0;
        photoField.setFont(BODY_FONT);
        photoField.setPreferredSize(new Dimension(300, 36));
        photoField.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1),
            new EmptyBorder(8, 12, 8, 12)
        ));
        formPanel.add(photoField, gbc);

        gbc.gridx = 0;
        gbc.gridy++;
        gbc.gridwidth = 2;
        twoFactorCheck.setFont(BODY_FONT);
        twoFactorCheck.setForeground(TEXT_PRIMARY);
        twoFactorCheck.setBackground(CARD_BG);
        formPanel.add(twoFactorCheck, gbc);

        JPanel formWrapper = new JPanel(new BorderLayout());
        formWrapper.setBorder(new EmptyBorder(0, 16, 16, 16));
        formWrapper.setOpaque(false);
        formWrapper.add(formPanel, BorderLayout.CENTER);
        add(formWrapper, BorderLayout.CENTER);

        // Footer con estado y botones
        JPanel footer = new JPanel(new BorderLayout());
        footer.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, false),
            new EmptyBorder(16, 24, 16, 24)
        ));
        footer.setBackground(CARD_BG);
        
        JPanel statusPanel = new JPanel(new BorderLayout());
        statusPanel.setOpaque(false);
        statusLabel.setForeground(TEXT_SECONDARY);
        statusLabel.setFont(CAPTION_FONT);
        statusPanel.add(statusLabel, BorderLayout.NORTH);
        footer.add(statusPanel, BorderLayout.CENTER);

        JPanel buttons = new JPanel(new FlowLayout(FlowLayout.RIGHT, 12, 0));
        buttons.setOpaque(false);
        
        JButton cancelButton = new JButton("Cancelar");
        cancelButton.setFont(BODY_FONT);
        cancelButton.setForeground(TEXT_PRIMARY);
        cancelButton.setBackground(CARD_BG);
        cancelButton.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1),
            new EmptyBorder(10, 20, 10, 20)
        ));
        cancelButton.setFocusPainted(false);
        cancelButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        cancelButton.addActionListener(e -> dispose());
        
        JButton saveButton = new JButton("Guardar cambios");
        saveButton.setFont(BODY_BOLD);
        saveButton.setForeground(Color.WHITE);
        saveButton.setBackground(PRIMARY_BLUE);
        saveButton.setBorder(new CompoundBorder(
            new LineBorder(PRIMARY_BLUE, 1),
            new EmptyBorder(10, 20, 10, 20)
        ));
        saveButton.setFocusPainted(false);
        saveButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        saveButton.addActionListener(e -> saveChanges(saveButton));
        
        buttons.add(cancelButton);
        buttons.add(saveButton);
        footer.add(buttons, BorderLayout.SOUTH);
        add(footer, BorderLayout.SOUTH);
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
        emailLabel.setText(profile.getEmail() != null ? profile.getEmail() : "-");
        nameField.setText(profile.getName());
        photoField.setText(profile.getProfilePhotoUrl() != null ? profile.getProfilePhotoUrl() : "");
        twoFactorCheck.setSelected(profile.isTwoFactorEnabled());
        statusLabel.setForeground(TEXT_SECONDARY);
        statusLabel.setText("Última actualización: " + (profile.getUpdatedAt() != null ? profile.getUpdatedAt() : "n/d"));
    }

    private void saveChanges(JButton saveButton) {
        String name = nameField.getText().trim();
        if (name.isEmpty()) {
            statusLabel.setForeground(DANGER_RED);
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
            statusLabel.setForeground(SUCCESS_GREEN);
            statusLabel.setText("No hay cambios para guardar");
            return;
        }

        saveButton.setEnabled(false);
        setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
        statusLabel.setForeground(PRIMARY_BLUE);
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
                    statusLabel.setForeground(SUCCESS_GREEN);
                    statusLabel.setText("Perfil actualizado correctamente");
                    if (onProfileUpdated != null) {
                        onProfileUpdated.accept(profile);
                    }
                } catch (Exception ex) {
                    Throwable cause = ex.getCause();
                    statusLabel.setForeground(DANGER_RED);
                    statusLabel.setText((cause instanceof ApiException ? cause.getMessage() : ex.getMessage()));
                }
            }
        };
        worker.execute();
    }
}
