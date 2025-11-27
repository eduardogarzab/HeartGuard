package com.heartguard.desktop.ui.user;

import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.models.user.OrgMembership;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.util.List;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Contenedor para vista organizacional.
 * Incluye:
 * - Selector de organización (JComboBox)
 * - OrganizationDashboardPanel dinámico
 */
public class OrganizationsContainerPanel extends JPanel {
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
    
    private List<OrgMembership> memberships;
    private OrgMembership selectedOrg;
    
    private final JComboBox<OrgMembership> orgSelector;
    private final JPanel dashboardContainer;
    private final CardLayout dashboardLayout;
    
    private OrganizationDashboardPanel currentDashboard;
    
    public OrganizationsContainerPanel(
            ApiClient apiClient,
            String accessToken,
            List<OrgMembership> memberships,
            Consumer<Exception> exceptionHandler,
            BiConsumer<String, Boolean> snackbarHandler
    ) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.memberships = memberships;
        this.exceptionHandler = exceptionHandler;
        this.snackbarHandler = snackbarHandler;
        
        setLayout(new BorderLayout());
        setOpaque(false);
        setBorder(new EmptyBorder(16, 16, 16, 16));
        
        // Panel header con selector
        JPanel headerPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 16, 0));
        headerPanel.setOpaque(false);
        headerPanel.setBorder(new EmptyBorder(0, 0, 24, 0));
        
        JLabel selectorLabel = new JLabel("Seleccionar Organización:");
        selectorLabel.setFont(new Font("Inter", Font.BOLD, 16));
        selectorLabel.setForeground(TEXT_PRIMARY);
        
        orgSelector = new JComboBox<>();
        orgSelector.setPreferredSize(new Dimension(350, 40));
        orgSelector.setFont(new Font("Inter", Font.PLAIN, 14));
        orgSelector.addActionListener(e -> onOrganizationChanged());
        
        headerPanel.add(selectorLabel);
        headerPanel.add(orgSelector);
        
        add(headerPanel, BorderLayout.NORTH);
        
        // Contenedor para dashboard con CardLayout
        dashboardLayout = new CardLayout();
        dashboardContainer = new JPanel(dashboardLayout);
        dashboardContainer.setOpaque(false);
        
        // Panel estado vacío
        JPanel emptyPanel = createEmptyPanel();
        dashboardContainer.add(emptyPanel, "empty");
        
        add(dashboardContainer, BorderLayout.CENTER);
        
        // Cargar organizaciones
        loadOrganizations();
    }
    
    private JPanel createEmptyPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setOpaque(false);
        panel.setBorder(new EmptyBorder(80, 0, 0, 0));
        
        JLabel icon = new JLabel("🏥", SwingConstants.CENTER);
        icon.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 64));
        icon.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel title = new JLabel("Selecciona una Organización");
        title.setFont(new Font("Inter", Font.BOLD, 24));
        title.setForeground(TEXT_PRIMARY);
        title.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel subtitle = new JLabel("Elige una organización del menú superior");
        subtitle.setFont(new Font("Inter", Font.PLAIN, 15));
        subtitle.setForeground(TEXT_SECONDARY);
        subtitle.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        panel.add(icon);
        panel.add(Box.createVerticalStrut(24));
        panel.add(title);
        panel.add(Box.createVerticalStrut(12));
        panel.add(subtitle);
        panel.add(Box.createVerticalGlue());
        
        return panel;
    }
    
    private void loadOrganizations() {
        orgSelector.removeAllItems();
        
        if (memberships == null || memberships.isEmpty()) {
            dashboardLayout.show(dashboardContainer, "empty");
            return;
        }
        
        // Agregar organizaciones al selector
        for (OrgMembership membership : memberships) {
            orgSelector.addItem(membership);
        }
        
        // Seleccionar la primera por defecto
        if (!memberships.isEmpty()) {
            selectedOrg = memberships.get(0);
            orgSelector.setSelectedIndex(0);
            loadDashboardForOrg(selectedOrg);
        }
    }
    
    private void onOrganizationChanged() {
        OrgMembership selected = (OrgMembership) orgSelector.getSelectedItem();
        if (selected != null && (selectedOrg == null || !selected.getOrgId().equals(selectedOrg.getOrgId()))) {
            selectedOrg = selected;
            loadDashboardForOrg(selected);
        }
    }
    
    private void loadDashboardForOrg(OrgMembership org) {
        // Remover dashboard anterior si existe
        if (currentDashboard != null) {
            dashboardContainer.remove(currentDashboard);
        }
        
        // Crear nuevo dashboard para la organización
        currentDashboard = new OrganizationDashboardPanel(
                apiClient,
                accessToken,
                org,
                exceptionHandler,
                snackbarHandler
        );
        
        dashboardContainer.add(currentDashboard, "dashboard");
        dashboardLayout.show(dashboardContainer, "dashboard");
        
        // Cargar datos
        currentDashboard.loadData();
    }
    
    /**
     * Actualiza lista de organizaciones disponibles
     */
    public void updateMemberships(List<OrgMembership> newMemberships) {
        this.memberships = newMemberships;
        loadOrganizations();
    }
    
    /**
     * Refresca los datos de la organización actual
     */
    public void refreshCurrentOrganization() {
        if (currentDashboard != null) {
            currentDashboard.loadData();
        }
    }
}
