package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.user.OrgMembership;
import com.heartguard.desktop.models.user.UserProfile;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.util.List;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Panel principal de dashboard con navegación de tabs:
 * - Tab 1: 👤 Mis Pacientes (vista personal/caregiver)
 * - Tab 2: 🏥 Organizaciones (vista organizacional con care teams)
 */
public class MainDashboardPanel extends JPanel {
    // Paleta de colores
    private static final Color GLOBAL_BACKGROUND = new Color(247, 249, 251);
    private static final Color CARD_BACKGROUND = Color.WHITE;
    private static final Color PRIMARY_BLUE = new Color(0, 120, 215);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER_LIGHT = new Color(223, 227, 230);
    
    private final ApiClient apiClient;
    private final String accessToken;
    private final Consumer<Exception> exceptionHandler;
    private final BiConsumer<String, Boolean> snackbarHandler;
    
    private UserProfile userProfile;
    private List<OrgMembership> memberships;
    
    private final JTabbedPane mainTabs;
    private CaregiverDashboardPanel caregiverPanel;
    private OrganizationsContainerPanel organizationsPanel;
    
    public MainDashboardPanel(
            ApiClient apiClient,
            String accessToken,
            UserProfile userProfile,
            List<OrgMembership> memberships,
            Consumer<Exception> exceptionHandler,
            BiConsumer<String, Boolean> snackbarHandler
    ) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.userProfile = userProfile;
        this.memberships = memberships;
        this.exceptionHandler = exceptionHandler;
        this.snackbarHandler = snackbarHandler;
        
        setLayout(new BorderLayout());
        setOpaque(false);
        setBorder(new EmptyBorder(24, 24, 24, 24));
        
        // Crear tabs principal
        mainTabs = new JTabbedPane();
        mainTabs.setFont(new Font("Inter", Font.BOLD, 15));
        mainTabs.setBackground(GLOBAL_BACKGROUND);
        mainTabs.setOpaque(false);
        
        // Tab 1: Mis Pacientes (Caregiver)
        caregiverPanel = new CaregiverDashboardPanel(
                apiClient,
                accessToken,
                exceptionHandler,
                snackbarHandler
        );
        mainTabs.addTab("👤 Mis Pacientes", caregiverPanel);
        
        // Tab 2: Organizaciones
        organizationsPanel = new OrganizationsContainerPanel(
                apiClient,
                accessToken,
                memberships,
                exceptionHandler,
                snackbarHandler
        );
        mainTabs.addTab("🏥 Organizaciones", organizationsPanel);
        
        add(mainTabs, BorderLayout.CENTER);
        
        // Cargar datos iniciales
        loadCaregiverData();
    }
    
    /**
     * Carga datos de la vista personal (caregiver)
     */
    public void loadCaregiverData() {
        caregiverPanel.loadData();
    }
    
    /**
     * Actualiza las organizaciones disponibles
     */
    public void updateMemberships(List<OrgMembership> newMemberships) {
        this.memberships = newMemberships;
        organizationsPanel.updateMemberships(newMemberships);
    }
    
    /**
     * Actualiza el perfil del usuario
     */
    public void updateUserProfile(UserProfile profile) {
        this.userProfile = profile;
    }
    
    /**
     * Refresca los datos del tab actualmente visible
     */
    public void refreshCurrentTab() {
        int selectedIndex = mainTabs.getSelectedIndex();
        if (selectedIndex == 0) {
            // Tab Caregiver
            caregiverPanel.loadData();
        } else if (selectedIndex == 1) {
            // Tab Organizaciones
            organizationsPanel.refreshCurrentOrganization();
        }
    }
    
    /**
     * Cambia al tab de organizaciones
     */
    public void switchToOrganizations() {
        mainTabs.setSelectedIndex(1);
    }
    
    /**
     * Cambia al tab de caregiver
     */
    public void switchToCaregiver() {
        mainTabs.setSelectedIndex(0);
    }
}
