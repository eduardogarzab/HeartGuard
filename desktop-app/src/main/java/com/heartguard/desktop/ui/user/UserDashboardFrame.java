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
import com.heartguard.desktop.util.ResponsiveUtils;
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

    private final JLabel nameLabel = new JLabel(" ");
    private final JLabel roleLabel = new JLabel(" ");
    private final JButton menuButton = new JButton("⚙");

    private final JPanel centerContainer = new JPanel();
    private final CardLayout centerLayout = new CardLayout();
    private final JPanel emptyStatePanel = new JPanel();
    private final JPanel loadingPanel = new JPanel();
    private MainDashboardPanel mainDashboardPanel;
    private final JPanel snackbarPanel = new JPanel(new BorderLayout());
    private Timer snackbarTimer;

    public UserDashboardFrame(ApiClient apiClient, LoginResponse loginResponse) {
        this.apiClient = apiClient;
        this.loginResponse = loginResponse;
        this.accessToken = loginResponse.getAccessToken();

        initUI();
        loadInitialData();
    }

    private void initUI() {
        setTitle("HeartGuard - Centro Clínico");
        
        // Usar utilidad responsive para calcular tamaño
        Dimension windowSize = ResponsiveUtils.getResponsiveSize(0.9, 0.9, 1200, 800);
        setSize(windowSize);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        setMinimumSize(new Dimension(1200, 800));
        getContentPane().setBackground(GLOBAL_BACKGROUND);
        
        // Agregar listener para limpiar recursos al cerrar
        addWindowListener(new java.awt.event.WindowAdapter() {
            @Override
            public void windowClosing(java.awt.event.WindowEvent windowEvent) {
                cleanup();
            }
        });

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
        // mainDashboardPanel se agregará dinámicamente después de cargar datos
        
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

        // Panel central vacío (el MainDashboardPanel maneja organizaciones internamente)
        JPanel centerPanel = new JPanel();
        centerPanel.setOpaque(false);
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
                // Obtener perfil de usuario
                JsonObject profileResponse = apiClient.getCurrentUserProfile(accessToken);
                
                // Parsear el perfil correctamente: data -> user
                if (profileResponse.has("data") && profileResponse.get("data").isJsonObject()) {
                    JsonObject dataObj = profileResponse.getAsJsonObject("data");
                    
                    // La respuesta tiene estructura: {"data": {"user": {...}}}
                    if (dataObj.has("user") && dataObj.get("user").isJsonObject()) {
                        JsonObject userObj = dataObj.getAsJsonObject("user");
                        profile = JsonUtils.GSON.fromJson(userObj, UserProfile.class);
                    }
                }

                // Obtener membresías de organizaciones
                JsonArray membershipArray = apiClient.getCurrentUserMemberships(accessToken);
                
                memberships = OrgMembership.listFrom(membershipArray);
                
                return null;
            }

            @Override
            protected void done() {
                try {
                    get();
                    updateTopBar();
                    refreshOrganizations();
                } catch (Exception ex) {
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
        if (memberships.isEmpty()) {
            centerLayout.show(centerContainer, "empty");
            return;
        }

        // Crear MainDashboardPanel con datos cargados
        if (mainDashboardPanel == null && profile != null) {
            mainDashboardPanel = new MainDashboardPanel(
                    apiClient,
                    accessToken,
                    profile,
                    memberships,
                    this::handleApiException,
                    this::showSnackbar
            );
            centerContainer.add(mainDashboardPanel, "dashboard");
        }
        
        centerLayout.show(centerContainer, "dashboard");
        
        // Cargar datos
        if (mainDashboardPanel != null) {
            mainDashboardPanel.loadCaregiverData();
            mainDashboardPanel.updateMemberships(memberships);
        }
    }

    private void onOrganizationSelected(ActionEvent event) {
        // Ya no se usa - el MainDashboardPanel maneja organizaciones internamente
    }

    private void openProfileDialog() {
        UserProfileDialog dialog = new UserProfileDialog(this, apiClient, accessToken, profile, updatedProfile -> {
            profile = updatedProfile;
            updateTopBar();
            
            // Actualizar el perfil en MainDashboardPanel si existe y refrescar TODOS los datos
            if (mainDashboardPanel != null) {
                mainDashboardPanel.updateUserProfile(updatedProfile);
                // Refrescar TODOS los tabs (no solo el actual) porque la foto puede aparecer en cualquier tab
                mainDashboardPanel.refreshAllTabs();
            }
            
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

            protected void done() {
                try {
                    memberships = get();
                    refreshOrganizations();
                    
                    // Actualizar memberships en MainDashboardPanel si existe
                    if (mainDashboardPanel != null) {
                        mainDashboardPanel.updateMemberships(memberships);
                    }
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
            
            // Detener cualquier timer activo
            if (snackbarTimer != null && snackbarTimer.isRunning()) {
                snackbarTimer.stop();
            }
            
            // Limpiar MainDashboardPanel
            if (mainDashboardPanel != null) {
                centerContainer.remove(mainDashboardPanel);
                mainDashboardPanel = null;
            }
            
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
    
    /**
     * Limpia recursos antes de cerrar la ventana
     */
    private void cleanup() {
        // MainDashboardPanel ya no tiene recursos que limpiar
        // (AlertsPanel fue eliminado)
    }
}
