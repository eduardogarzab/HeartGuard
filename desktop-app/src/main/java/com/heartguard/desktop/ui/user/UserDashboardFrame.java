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
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.util.ArrayList;
import java.util.List;

/**
 * Ventana principal para usuarios staff.
 */
public class UserDashboardFrame extends JFrame {
    private final ApiClient apiClient;
    private final LoginResponse loginResponse;
    private final String accessToken;

    private UserProfile profile;
    private List<OrgMembership> memberships = new ArrayList<>();
    private OrgMembership selectedMembership;

    private final JLabel nameLabel = new JLabel(" ");
    private final JLabel roleLabel = new JLabel(" ");
    private final JComboBox<OrgMembership> orgSelector = new JComboBox<>();
    private final JButton menuButton = new JButton("⚙️");

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
        setSize(1280, 860);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        setMinimumSize(new Dimension(1100, 760));

        add(createTopBar(), BorderLayout.NORTH);

        centerContainer.setLayout(centerLayout);
        loadingPanel.setLayout(new FlowLayout(FlowLayout.CENTER, 10, 30));
        loadingPanel.add(new JLabel("Preparando panel clínico..."));
        loadingPanel.add(new JProgressBar());

        emptyStatePanel.setLayout(new BoxLayout(emptyStatePanel, BoxLayout.Y_AXIS));
        emptyStatePanel.setBorder(new EmptyBorder(60, 0, 0, 0));
        JLabel icon = new JLabel("🏥", SwingConstants.CENTER);
        icon.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 56));
        icon.setAlignmentX(Component.CENTER_ALIGNMENT);
        JLabel title = new JLabel("Aún no perteneces a ninguna organización");
        title.setFont(new Font("Segoe UI", Font.BOLD, 18));
        title.setAlignmentX(Component.CENTER_ALIGNMENT);
        JLabel subtitle = new JLabel("Solicita acceso o revisa tus invitaciones pendientes");
        subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        subtitle.setForeground(new Color(120, 130, 140));
        subtitle.setAlignmentX(Component.CENTER_ALIGNMENT);
        JButton invitationsButton = new JButton("Ver mis invitaciones");
        invitationsButton.setAlignmentX(Component.CENTER_ALIGNMENT);
        invitationsButton.addActionListener(e -> openInvitationsDialog());
        emptyStatePanel.add(icon);
        emptyStatePanel.add(Box.createVerticalStrut(16));
        emptyStatePanel.add(title);
        emptyStatePanel.add(Box.createVerticalStrut(8));
        emptyStatePanel.add(subtitle);
        emptyStatePanel.add(Box.createVerticalStrut(18));
        emptyStatePanel.add(invitationsButton);
        emptyStatePanel.add(Box.createVerticalGlue());

        centerContainer.add(loadingPanel, "loading");
        centerContainer.add(emptyStatePanel, "empty");
        centerContainer.add(dashboardPanel, "dashboard");
        add(centerContainer, BorderLayout.CENTER);

        snackbarPanel.setOpaque(false);
        snackbarPanel.setBorder(new EmptyBorder(0, 0, 16, 0));
        add(snackbarPanel, BorderLayout.SOUTH);

        centerLayout.show(centerContainer, "loading");
    }

    private JPanel createTopBar() {
        JPanel topBar = new JPanel(new BorderLayout());
        topBar.setBorder(new EmptyBorder(18, 24, 18, 24));
        topBar.setBackground(new Color(246, 249, 253));

        JLabel brand = new JLabel("HeartGuard Command Center");
        brand.setFont(new Font("Segoe UI", Font.BOLD, 22));
        brand.setForeground(new Color(30, 64, 98));

        JPanel brandPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        brandPanel.setOpaque(false);
        brandPanel.add(new JLabel("💙"));
        brandPanel.add(brand);
        topBar.add(brandPanel, BorderLayout.WEST);

        JPanel centerPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 12, 0));
        centerPanel.setOpaque(false);
        JLabel orgLabel = new JLabel("Organización:");
        orgLabel.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        orgSelector.setPreferredSize(new Dimension(260, 32));
        orgSelector.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        orgSelector.addActionListener(this::onOrganizationSelected);
        centerPanel.add(orgLabel);
        centerPanel.add(orgSelector);
        topBar.add(centerPanel, BorderLayout.CENTER);

        JPanel userPanel = new JPanel();
        userPanel.setOpaque(false);
        userPanel.setLayout(new BoxLayout(userPanel, BoxLayout.Y_AXIS));
        nameLabel.setFont(new Font("Segoe UI", Font.BOLD, 14));
        roleLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        roleLabel.setForeground(new Color(110, 120, 130));
        userPanel.add(nameLabel);
        userPanel.add(roleLabel);

        JPanel right = new JPanel(new FlowLayout(FlowLayout.RIGHT, 12, 0));
        right.setOpaque(false);
        styleMenuButton(menuButton);
        right.add(userPanel);
        right.add(menuButton);
        topBar.add(right, BorderLayout.EAST);

        menuButton.addActionListener(e -> showUserMenu());
        return topBar;
    }

    private void styleMenuButton(JButton button) {
        button.setFont(new Font("Segoe UI Symbol", Font.PLAIN, 22));
        button.setFocusable(false);
        button.setBackground(new Color(234, 238, 246));
        button.setBorder(BorderFactory.createEmptyBorder(6, 12, 6, 12));
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
    }

    private void showUserMenu() {
        JPopupMenu menu = new JPopupMenu();
        JMenuItem profileItem = new JMenuItem("Mi información de perfil");
        JMenuItem invitationsItem = new JMenuItem("Mis invitaciones");
        profileItem.addActionListener(e -> openProfileDialog());
        invitationsItem.addActionListener(e -> openInvitationsDialog());
        menu.add(profileItem);
        menu.add(invitationsItem);
        menu.show(menuButton, 0, menuButton.getHeight());
    }

    private void loadInitialData() {
        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            @Override
            protected Void doInBackground() throws Exception {
                JsonObject profileResponse = apiClient.getCurrentUserProfile(accessToken);
                JsonObject profileData = profileResponse.getAsJsonObject("data");
                profile = JsonUtils.GSON.fromJson(profileData, UserProfile.class);

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
                    handleApiException(ex);
                }
            }
        };
        worker.execute();
    }

    private void updateTopBar() {
        if (profile != null) {
            nameLabel.setText(profile.getName());
            roleLabel.setText(profile.getRoleCode());
        } else {
            UserLoginData userData = loginResponse.getUser();
            if (userData != null) {
                nameLabel.setText(userData.getName());
                roleLabel.setText(userData.getSystemRole());
            }
        }
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

    void showSnackbar(String message, boolean success) {
        snackbarPanel.removeAll();
        JPanel snackbar = new JPanel(new BorderLayout());
        snackbar.setBorder(new EmptyBorder(12, 24, 12, 24));
        snackbar.setBackground(success ? new Color(46, 204, 113) : new Color(231, 76, 60));
        JLabel messageLabel = new JLabel(message);
        messageLabel.setForeground(Color.WHITE);
        messageLabel.setFont(new Font("Segoe UI", Font.BOLD, 13));
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
        showSnackbar(ex.getMessage(), false);
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
            showSnackbar(apiException.getMessage(), false);
        }
    }
}
