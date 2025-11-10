package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.LoginResponse;
import com.heartguard.desktop.models.UserLoginData;
import com.heartguard.desktop.models.user.OrgMembership;
import com.heartguard.desktop.models.user.UserProfile;
import com.heartguard.desktop.util.JsonUtils;
import com.heartguard.desktop.ui.LoginFrame;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.util.ArrayList;
import java.util.List;

/**
 * Ventana principal para usuarios staff con diseño integral profesional.
 * Sistema de grilla fluida de 12 columnas, márgenes 24px, scroll vertical uniforme.
 */
public class UserDashboardFrame extends JFrame {
    // Paleta médica profesional
    private static final Color GLOBAL_BACKGROUND = new Color(247, 249, 251);
    private static final Color CARD_BACKGROUND = Color.WHITE;
    private static final Color PRIMARY_BLUE = new Color(0, 120, 215);
    private static final Color SECONDARY_GREEN = new Color(40, 167, 69);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER_LIGHT = new Color(223, 227, 230);
    private static final Color HEADER_BG = new Color(255, 255, 255);
    private static final Color DANGER_COLOR = new Color(220, 53, 69);
    
    private final ApiClient apiClient;
    private final LoginResponse loginResponse;
    private final String accessToken;

    private UserProfile profile;
    private List<OrgMembership> memberships = new ArrayList<>();
    private OrgMembership selectedMembership;

    private final JLabel nameLabel = new JLabel(" ");
    private final JLabel roleLabel = new JLabel(" ");
    private final JComboBox<OrgMembership> orgSelector = new JComboBox<>();
    private final JButton menuButton = new JButton("⚙");

    private final JPanel centerContainer = new JPanel();
    private final CardLayout centerLayout = new CardLayout();
    private final JPanel emptyStatePanel = new JPanel();
    private final JPanel loadingPanel = new JPanel();
    private final UserDashboardPanel dashboardPanel;
    private final JPanel snackbarPanel = new JPanel(new BorderLayout());
    private Timer snackbarTimer;

    public UserDashboardFrame(ApiClient apiClient, LoginResponse loginResponse) {
        this.apiClient = apiClient;
        this.loginResponse = loginResponse;
        this.accessToken = loginResponse.getAccessToken();
        this.dashboardPanel = new UserDashboardPanel(apiClient, accessToken, this::handleApiException, this::showSnackbar);

        initUI();
        loadInitialData();
    }

    private void initUI() {
        setTitle("HeartGuard - Centro Clínico");
        setSize(1360, 900);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        setMinimumSize(new Dimension(1200, 800));
        getContentPane().setBackground(GLOBAL_BACKGROUND);

        // Encabezado superior fijo
        add(createTopBar(), BorderLayout.NORTH);

        // Contenedor principal con ScrollPane para scroll vertical uniforme
        JPanel mainContentWrapper = new JPanel(new BorderLayout());
        mainContentWrapper.setOpaque(false);
        
        centerContainer.setLayout(centerLayout);
        centerContainer.setOpaque(false);
        
        // Panel de carga
        loadingPanel.setLayout(new BoxLayout(loadingPanel, BoxLayout.Y_AXIS));
        loadingPanel.setOpaque(false);
        loadingPanel.setBorder(new EmptyBorder(80, 0, 0, 0));
        JLabel loadIcon = new JLabel("⏳");
        loadIcon.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 48));
        loadIcon.setAlignmentX(Component.CENTER_ALIGNMENT);
        JLabel loadText = new JLabel("Preparando panel clínico...");
        loadText.setFont(new Font("Inter", Font.PLAIN, 16));
        loadText.setForeground(TEXT_SECONDARY);
        loadText.setAlignmentX(Component.CENTER_ALIGNMENT);
        JProgressBar loadBar = new JProgressBar();
        loadBar.setIndeterminate(true);
        loadBar.setMaximumSize(new Dimension(300, 4));
        loadBar.setAlignmentX(Component.CENTER_ALIGNMENT);
        loadingPanel.add(loadIcon);
        loadingPanel.add(Box.createVerticalStrut(16));
        loadingPanel.add(loadText);
        loadingPanel.add(Box.createVerticalStrut(24));
        loadingPanel.add(loadBar);

        // Estado vacío mejorado
        emptyStatePanel.setLayout(new BoxLayout(emptyStatePanel, BoxLayout.Y_AXIS));
        emptyStatePanel.setBorder(new EmptyBorder(100, 24, 24, 24));
        emptyStatePanel.setOpaque(false);
        JLabel emptyIcon = new JLabel("🩺", SwingConstants.CENTER);
        emptyIcon.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 72));
        emptyIcon.setAlignmentX(Component.CENTER_ALIGNMENT);
        JLabel emptyTitle = new JLabel("Aún no perteneces a una organización");
        emptyTitle.setFont(new Font("Inter", Font.BOLD, 20));
        emptyTitle.setForeground(TEXT_PRIMARY);
        emptyTitle.setAlignmentX(Component.CENTER_ALIGNMENT);
        JLabel emptySubtitle = new JLabel("Solicita acceso o revisa tus invitaciones pendientes");
        emptySubtitle.setFont(new Font("Inter", Font.PLAIN, 15));
        emptySubtitle.setForeground(TEXT_SECONDARY);
        emptySubtitle.setAlignmentX(Component.CENTER_ALIGNMENT);
        JButton invitationsButton = createStyledButton("Ver mis invitaciones", PRIMARY_BLUE);
        invitationsButton.setAlignmentX(Component.CENTER_ALIGNMENT);
        invitationsButton.addActionListener(e -> openInvitationsDialog());
        emptyStatePanel.add(emptyIcon);
        emptyStatePanel.add(Box.createVerticalStrut(24));
        emptyStatePanel.add(emptyTitle);
        emptyStatePanel.add(Box.createVerticalStrut(12));
        emptyStatePanel.add(emptySubtitle);
        emptyStatePanel.add(Box.createVerticalStrut(32));
        emptyStatePanel.add(invitationsButton);
        emptyStatePanel.add(Box.createVerticalGlue());

        centerContainer.add(loadingPanel, "loading");
        centerContainer.add(emptyStatePanel, "empty");
        centerContainer.add(dashboardPanel, "dashboard");
        
        // ScrollPane con fitToWidth para scroll vertical uniforme
        JScrollPane scrollPane = new JScrollPane(centerContainer);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        scrollPane.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        scrollPane.setVerticalScrollBarPolicy(ScrollPaneConstants.VERTICAL_SCROLLBAR_AS_NEEDED);
        scrollPane.getViewport().setBackground(GLOBAL_BACKGROUND);
        
        mainContentWrapper.add(scrollPane, BorderLayout.CENTER);
        add(mainContentWrapper, BorderLayout.CENTER);

        // Snackbar en la parte inferior
        snackbarPanel.setOpaque(false);
        snackbarPanel.setBorder(new EmptyBorder(0, 0, 16, 0));
        add(snackbarPanel, BorderLayout.SOUTH);

        centerLayout.show(centerContainer, "loading");
    }

    private JPanel createTopBar() {
        JPanel topBar = new JPanel(new BorderLayout());
        topBar.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, false),
            new EmptyBorder(24, 24, 24, 24)
        ));
        topBar.setBackground(HEADER_BG);

        // Logo y marca con jerarquía visual
        JPanel brandPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 16, 0));
        brandPanel.setOpaque(false);
        JLabel logoEmoji = new JLabel("💙");
        logoEmoji.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 28));
        JLabel brand = new JLabel("HeartGuard");
        brand.setFont(new Font("Inter", Font.BOLD, 24));
        brand.setForeground(PRIMARY_BLUE);
        JLabel subtitle = new JLabel("Command Center");
        subtitle.setFont(new Font("Inter", Font.PLAIN, 14));
        subtitle.setForeground(TEXT_SECONDARY);
        brandPanel.add(logoEmoji);
        brandPanel.add(brand);
        brandPanel.add(subtitle);
        topBar.add(brandPanel, BorderLayout.WEST);

        // Selector de organización centrado
        JPanel centerPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 12, 0));
        centerPanel.setOpaque(false);
        JLabel orgLabel = new JLabel("Organización:");
        orgLabel.setFont(new Font("Inter", Font.PLAIN, 15));
        orgLabel.setForeground(TEXT_PRIMARY);
        orgSelector.setPreferredSize(new Dimension(280, 36));
        orgSelector.setFont(new Font("Inter", Font.PLAIN, 14));
        orgSelector.addActionListener(this::onOrganizationSelected);
        centerPanel.add(orgLabel);
        centerPanel.add(orgSelector);
        topBar.add(centerPanel, BorderLayout.CENTER);

        // Panel de usuario con rol visible y menú flotante
        JPanel userSection = new JPanel(new FlowLayout(FlowLayout.RIGHT, 16, 0));
        userSection.setOpaque(false);
        
        JPanel userInfo = new JPanel();
        userInfo.setLayout(new BoxLayout(userInfo, BoxLayout.Y_AXIS));
        userInfo.setOpaque(false);
        nameLabel.setFont(new Font("Inter", Font.BOLD, 15));
        nameLabel.setForeground(TEXT_PRIMARY);
        nameLabel.setAlignmentX(Component.RIGHT_ALIGNMENT);
        roleLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        roleLabel.setForeground(TEXT_SECONDARY);
        roleLabel.setAlignmentX(Component.RIGHT_ALIGNMENT);
        userInfo.add(nameLabel);
        userInfo.add(Box.createVerticalStrut(2));
        userInfo.add(roleLabel);

        menuButton.setFont(new Font("Segoe UI Symbol", Font.PLAIN, 24));
        menuButton.setFocusable(false);
        menuButton.setBackground(new Color(245, 247, 250));
        menuButton.setForeground(TEXT_PRIMARY);
        menuButton.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, true),
            new EmptyBorder(8, 14, 8, 14)
        ));
        menuButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        menuButton.addActionListener(e -> showUserMenu());

        userSection.add(userInfo);
        userSection.add(menuButton);
        topBar.add(userSection, BorderLayout.EAST);

        return topBar;
    }

    private void showUserMenu() {
        JPopupMenu menu = new JPopupMenu();
        menu.setBorder(new CompoundBorder(
            new LineBorder(BORDER_LIGHT, 1, true),
            new EmptyBorder(8, 0, 8, 0)
        ));
        
        JMenuItem profileItem = new JMenuItem("Mi perfil");
        profileItem.setFont(new Font("Inter", Font.PLAIN, 14));
        profileItem.setBorder(new EmptyBorder(10, 20, 10, 20));
        profileItem.addActionListener(e -> openProfileDialog());
        
        JMenuItem invitationsItem = new JMenuItem("Mis invitaciones");
        invitationsItem.setFont(new Font("Inter", Font.PLAIN, 14));
        invitationsItem.setBorder(new EmptyBorder(10, 20, 10, 20));
        invitationsItem.addActionListener(e -> openInvitationsDialog());
        
        JMenuItem logoutItem = new JMenuItem("Cerrar sesión");
        logoutItem.setFont(new Font("Inter", Font.PLAIN, 14));
        logoutItem.setBorder(new EmptyBorder(10, 20, 10, 20));
        logoutItem.setForeground(DANGER_COLOR);
        logoutItem.addActionListener(e -> handleLogout());
        
        menu.add(profileItem);
        menu.addSeparator();
        menu.add(invitationsItem);
        menu.addSeparator();
        menu.add(logoutItem);
        menu.show(menuButton, 0, menuButton.getHeight() + 4);
    }

    private JButton createStyledButton(String text, Color bgColor) {
        JButton button = new JButton(text);
        button.setFont(new Font("Inter", Font.BOLD, 14));
        button.setForeground(Color.WHITE);
        button.setBackground(bgColor);
        button.setBorder(new CompoundBorder(
            new LineBorder(bgColor, 1, true),
            new EmptyBorder(10, 24, 10, 24)
        ));
        button.setFocusPainted(false);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        return button;
    }

    private void loadInitialData() {
        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            @Override
            protected Void doInBackground() throws Exception {
                // Log: Iniciando carga de datos
                System.out.println("[DEBUG] Iniciando carga de datos del usuario");
                System.out.println("[DEBUG] Access Token: " + (accessToken != null ? accessToken.substring(0, Math.min(20, accessToken.length())) + "..." : "null"));
                
                // Obtener perfil de usuario
                System.out.println("[DEBUG] Obteniendo perfil de usuario...");
                JsonObject profileResponse = apiClient.getCurrentUserProfile(accessToken);
                System.out.println("[DEBUG] Respuesta de perfil: " + profileResponse.toString());
                
                // Parsear el perfil correctamente: data -> user
                if (profileResponse.has("data") && profileResponse.get("data").isJsonObject()) {
                    JsonObject dataObj = profileResponse.getAsJsonObject("data");
                    
                    // La respuesta tiene estructura: {"data": {"user": {...}}}
                    if (dataObj.has("user") && dataObj.get("user").isJsonObject()) {
                        JsonObject userObj = dataObj.getAsJsonObject("user");
                        profile = JsonUtils.GSON.fromJson(userObj, UserProfile.class);
                        System.out.println("[DEBUG] Perfil parseado correctamente: " + (profile != null ? profile.getName() : "null"));
                    } else {
                        System.out.println("[DEBUG] ADVERTENCIA: No se encontró 'user' dentro de 'data'");
                        System.out.println("[DEBUG] Contenido de 'data': " + dataObj.toString());
                    }
                } else {
                    System.out.println("[DEBUG] ERROR: No se encontró 'data' en la respuesta del perfil");
                }

                // Obtener membresías de organizaciones
                System.out.println("[DEBUG] Obteniendo organizaciones del usuario...");
                JsonArray membershipArray = apiClient.getCurrentUserMemberships(accessToken);
                System.out.println("[DEBUG] Organizaciones recibidas: " + membershipArray.toString());
                System.out.println("[DEBUG] Cantidad de organizaciones: " + membershipArray.size());
                
                memberships = OrgMembership.listFrom(membershipArray);
                System.out.println("[DEBUG] Membresías parseadas: " + memberships.size());
                for (int i = 0; i < memberships.size(); i++) {
                    OrgMembership m = memberships.get(i);
                    System.out.println("[DEBUG]   [" + i + "] " + m.getOrgName() + " (ID: " + m.getOrgId() + ")");
                }
                
                return null;
            }

            @Override
            protected void done() {
                try {
                    get();
                    System.out.println("[DEBUG] Actualizando interfaz...");
                    updateTopBar();
                    refreshOrganizations();
                    System.out.println("[DEBUG] Carga completada exitosamente");
                } catch (Exception ex) {
                    System.out.println("[DEBUG] ERROR durante la carga: " + ex.getMessage());
                    ex.printStackTrace();
                    handleApiException(ex);
                }
            }
        };
        worker.execute();
    }

    private void updateTopBar() {
        if (profile != null) {
            nameLabel.setText(profile.getName());
            // Mostrar rol legible en lugar de código técnico
            String roleDisplay = mapRoleCodeToDisplay(profile.getRoleCode());
            roleLabel.setText(roleDisplay);
        } else {
            UserLoginData userData = loginResponse.getUser();
            if (userData != null) {
                nameLabel.setText(userData.getName());
                String roleDisplay = mapRoleCodeToDisplay(userData.getSystemRole());
                roleLabel.setText(roleDisplay);
            }
        }
    }

    private String mapRoleCodeToDisplay(String roleCode) {
        if (roleCode == null || roleCode.isEmpty()) {
            return "";
        }
        return switch (roleCode.toLowerCase()) {
            case "admin", "administrator" -> "Administrador";
            case "specialist", "especialista" -> "Especialista";
            case "doctor", "medico" -> "Médico";
            case "nurse", "enfermera" -> "Enfermera";
            case "technician", "tecnico" -> "Técnico";
            case "superadmin", "super_admin" -> "Super Administrador";
            default -> roleCode;
        };
    }

    private void refreshOrganizations() {
        orgSelector.removeAllItems();
        if (memberships.isEmpty()) {
            centerLayout.show(centerContainer, "empty");
            return;
        }

        for (OrgMembership membership : memberships) {
            orgSelector.addItem(membership);
        }

        selectedMembership = memberships.get(0);
        orgSelector.setSelectedIndex(0);
        centerLayout.show(centerContainer, "dashboard");
        dashboardPanel.showForOrganization(selectedMembership);
    }

    private void onOrganizationSelected(ActionEvent event) {
        OrgMembership membership = (OrgMembership) orgSelector.getSelectedItem();
        if (membership != null && (selectedMembership == null || !membership.getOrgId().equals(selectedMembership.getOrgId()))) {
            selectedMembership = membership;
            centerLayout.show(centerContainer, "dashboard");
            dashboardPanel.showForOrganization(membership);
        }
    }

    private void openProfileDialog() {
        UserProfileDialog dialog = new UserProfileDialog(this, apiClient, accessToken, profile, updatedProfile -> {
            profile = updatedProfile;
            updateTopBar();
            showSnackbar("Perfil actualizado correctamente", true);
        });
        dialog.setVisible(true);
    }

    private void openInvitationsDialog() {
        InvitationsDialog dialog = new InvitationsDialog(this, apiClient, accessToken, () -> {
            loadMembershipsAgain();
            showSnackbar("Invitaciones actualizadas", true);
        });
        dialog.setVisible(true);
    }

    private void loadMembershipsAgain() {
        SwingWorker<List<OrgMembership>, Void> worker = new SwingWorker<>() {
            @Override
            protected List<OrgMembership> doInBackground() throws Exception {
                JsonArray membershipArray = apiClient.getCurrentUserMemberships(accessToken);
                return OrgMembership.listFrom(membershipArray);
            }

            @Override
            protected void done() {
                try {
                    memberships = get();
                    refreshOrganizations();
                } catch (Exception ex) {
                    handleApiException(ex);
                }
            }
        };
        worker.execute();
    }
    
    private void handleLogout() {
        int option = JOptionPane.showConfirmDialog(
            this,
            "¿Estás seguro de que deseas cerrar sesión?",
            "Cerrar sesión",
            JOptionPane.YES_NO_OPTION,
            JOptionPane.QUESTION_MESSAGE
        );
        
        if (option == JOptionPane.YES_OPTION) {
            // Limpiar datos de la sesión actual
            profile = null;
            memberships.clear();
            selectedMembership = null;
            orgSelector.removeAllItems();
            
            // Detener cualquier timer activo
            if (snackbarTimer != null && snackbarTimer.isRunning()) {
                snackbarTimer.stop();
            }
            
            // Nota: No llamamos a dashboardPanel.removeAll() porque puede causar
            // problemas con componentes JavaFX embebidos. En su lugar, simplemente
            // cerramos la ventana y creamos un nuevo LoginFrame limpio.
            
            // Cerrar ventana actual
            dispose();
            
            // Mostrar pantalla de login con un nuevo frame limpio
            SwingUtilities.invokeLater(() -> {
                LoginFrame loginFrame = new LoginFrame();
                loginFrame.setVisible(true);
            });
        }
    }

    void showSnackbar(String message, boolean success) {
        snackbarPanel.removeAll();
        JPanel snackbar = new JPanel(new BorderLayout());
        snackbar.setBorder(new CompoundBorder(
            new LineBorder(success ? SECONDARY_GREEN : DANGER_COLOR, 1, true),
            new EmptyBorder(14, 24, 14, 24)
        ));
        snackbar.setBackground(success ? new Color(212, 237, 218) : new Color(248, 215, 218));
        JLabel messageLabel = new JLabel(message);
        messageLabel.setForeground(success ? new Color(21, 87, 36) : new Color(114, 28, 36));
        messageLabel.setFont(new Font("Inter", Font.BOLD, 14));
        snackbar.add(messageLabel, BorderLayout.CENTER);
        snackbarPanel.add(snackbar, BorderLayout.SOUTH);
        snackbarPanel.revalidate();
        snackbarPanel.repaint();

        if (snackbarTimer != null && snackbarTimer.isRunning()) {
            snackbarTimer.stop();
        }
        snackbarTimer = new Timer(3500, e -> {
            snackbarPanel.removeAll();
            snackbarPanel.revalidate();
            snackbarPanel.repaint();
        });
        snackbarTimer.setRepeats(false);
        snackbarTimer.start();
    }

    private void handleApiException(Exception ex) {
        System.out.println("[DEBUG] handleApiException llamado con: " + ex.getClass().getName());
        System.out.println("[DEBUG] Mensaje: " + ex.getMessage());
        ex.printStackTrace();
        
        Throwable cause = ex instanceof ApiException ? ex : ex.getCause();
        if (cause instanceof ApiException apiException && apiException.getStatusCode() == 401) {
            showSnackbar(apiException.getMessage(), false);
            dispose();
            SwingUtilities.invokeLater(() -> {
                LoginFrame loginFrame = new LoginFrame();
                loginFrame.setVisible(true);
            });
            return;
        }
        
        // Mostrar mensaje de error detallado
        String errorMessage = ex.getMessage();
        if (cause instanceof ApiException apiException) {
            errorMessage = "Error " + apiException.getStatusCode() + ": " + apiException.getMessage();
        }
        showSnackbar(errorMessage, false);
    }

    void handleApiException(ApiException apiException) {
        System.out.println("[DEBUG] handleApiException(ApiException) llamado");
        System.out.println("[DEBUG] Status Code: " + apiException.getStatusCode());
        System.out.println("[DEBUG] Mensaje: " + apiException.getMessage());
        
        if (apiException.getStatusCode() == 401) {
            showSnackbar(apiException.getMessage(), false);
            dispose();
            SwingUtilities.invokeLater(() -> {
                LoginFrame loginFrame = new LoginFrame();
                loginFrame.setVisible(true);
            });
        } else {
            showSnackbar("Error " + apiException.getStatusCode() + ": " + apiException.getMessage(), false);
        }
    }
}
