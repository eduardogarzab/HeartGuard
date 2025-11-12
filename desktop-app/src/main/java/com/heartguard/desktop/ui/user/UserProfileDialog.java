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
    private UserProfilePhotoPanel profilePhotoPanel;
    private final JCheckBox twoFactorCheck = new JCheckBox("Habilitar segundo factor de autenticación");
    private final JLabel statusLabel = new JLabel(" ");

    private UserProfile profile;
    private JPanel formPanel;
    private JPanel photoPlaceholder;

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
        setSize(700, 600);
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

        // Panel principal con dos columnas
        JPanel mainPanel = new JPanel(new BorderLayout(20, 0));
        mainPanel.setBorder(new EmptyBorder(24, 24, 24, 24));
        mainPanel.setBackground(CARD_BG);

        // Columna izquierda: Foto de perfil
        JPanel leftPanel = new JPanel(new BorderLayout(0, 12));
        leftPanel.setOpaque(false);
        leftPanel.setBorder(new EmptyBorder(0, 0, 0, 20));
        
        JLabel photoSectionLabel = new JLabel("Foto de perfil", SwingConstants.CENTER);
        photoSectionLabel.setFont(BODY_BOLD);
        photoSectionLabel.setForeground(TEXT_PRIMARY);
        leftPanel.add(photoSectionLabel, BorderLayout.NORTH);
        
        // El panel de foto se creará después de cargar el perfil
        photoPlaceholder = new JPanel();
        photoPlaceholder.setOpaque(false);
        photoPlaceholder.setPreferredSize(new Dimension(150, 200));
        leftPanel.add(photoPlaceholder, BorderLayout.CENTER);

        // Columna derecha: Formulario
        formPanel = new JPanel(new GridBagLayout());
        formPanel.setOpaque(false);
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(8, 0, 8, 0);
        gbc.anchor = GridBagConstraints.NORTHWEST;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.weightx = 1.0;

        // Título de sección
        JLabel infoSectionLabel = new JLabel("Información personal");
        infoSectionLabel.setFont(new Font("Inter", Font.BOLD, 16));
        infoSectionLabel.setForeground(TEXT_PRIMARY);
        infoSectionLabel.setBorder(new EmptyBorder(0, 0, 12, 0));
        formPanel.add(infoSectionLabel, gbc);

        // Campo Email (read-only)
        gbc.gridy++;
        JLabel emailFieldLabel = new JLabel("Correo electrónico");
        emailFieldLabel.setFont(CAPTION_FONT);
        emailFieldLabel.setForeground(TEXT_SECONDARY);
        formPanel.add(emailFieldLabel, gbc);

        gbc.gridy++;
        emailLabel.setFont(BODY_FONT);
        emailLabel.setForeground(TEXT_PRIMARY);
        emailLabel.setBorder(new EmptyBorder(0, 0, 12, 0));
        formPanel.add(emailLabel, gbc);

        // Campo Nombre
        gbc.gridy++;
        JLabel nameLabel = new JLabel("Nombre completo");
        nameLabel.setFont(CAPTION_FONT);
        nameLabel.setForeground(TEXT_SECONDARY);
        formPanel.add(nameLabel, gbc);

        gbc.gridy++;
        nameField.setFont(BODY_FONT);
        nameField.setPreferredSize(new Dimension(300, 40));
        nameField.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, true),
            new EmptyBorder(8, 12, 8, 12)
        ));
        formPanel.add(nameField, gbc);

        // Espacio
        gbc.gridy++;
        JPanel spacer = new JPanel();
        spacer.setOpaque(false);
        spacer.setPreferredSize(new Dimension(1, 20));
        formPanel.add(spacer, gbc);

        // Título de seguridad
        gbc.gridy++;
        JLabel securitySectionLabel = new JLabel("Seguridad");
        securitySectionLabel.setFont(new Font("Inter", Font.BOLD, 16));
        securitySectionLabel.setForeground(TEXT_PRIMARY);
        securitySectionLabel.setBorder(new EmptyBorder(0, 0, 12, 0));
        formPanel.add(securitySectionLabel, gbc);

        // Checkbox 2FA
        gbc.gridy++;
        twoFactorCheck.setFont(BODY_FONT);
        twoFactorCheck.setForeground(TEXT_PRIMARY);
        twoFactorCheck.setOpaque(false);
        formPanel.add(twoFactorCheck, gbc);

        // Empujar todo hacia arriba
        gbc.gridy++;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.BOTH;
        JPanel filler = new JPanel();
        filler.setOpaque(false);
        formPanel.add(filler, gbc);

        // Agregar columnas al panel principal
        mainPanel.add(leftPanel, BorderLayout.WEST);
        mainPanel.add(formPanel, BorderLayout.CENTER);

        JPanel formWrapper = new JPanel(new BorderLayout());
        formWrapper.setBorder(new EmptyBorder(0, 16, 16, 16));
        formWrapper.setOpaque(false);
        formWrapper.add(mainPanel, BorderLayout.CENTER);
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
        
        // Crear o actualizar el panel de foto de perfil
        if (profilePhotoPanel == null && profile.getId() != null) {
            // Primera vez: crear el panel
            profilePhotoPanel = new UserProfilePhotoPanel(apiClient, token, profile.getId());
            profilePhotoPanel.setOnPhotoChangedCallback(() -> {
                // Recargar el perfil cuando cambia la foto
                loadProfile();
            });
            
            // Reemplazar el placeholder con el panel real
            if (photoPlaceholder != null && photoPlaceholder.getParent() != null) {
                Container parent = photoPlaceholder.getParent();
                int index = -1;
                for (int i = 0; i < parent.getComponentCount(); i++) {
                    if (parent.getComponent(i) == photoPlaceholder) {
                        index = i;
                        break;
                    }
                }
                if (index != -1) {
                    parent.remove(photoPlaceholder);
                    parent.add(profilePhotoPanel, index);
                    parent.revalidate();
                    parent.repaint();
                }
            }
        }
        
        // Cargar foto en el panel si existe
        if (profilePhotoPanel != null) {
            String photoUrl = profile.getProfilePhotoUrl();
            profilePhotoPanel.setPhotoUrl(photoUrl);
        }
        
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
        // La foto de perfil se maneja directamente en UserProfilePhotoPanel
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
