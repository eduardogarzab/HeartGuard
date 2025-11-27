package com.heartguard.desktop.ui.user;

import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.models.user.OrgMembership;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Dashboard de una organización específica.
 * Incluye 4 tabs:
 * - 📊 Overview (métricas + gráficos)
 * - 👥 Care Teams (lista + detalle)
 * - 📱 Dispositivos (todos los dispositivos de la org)
 * - 🗺️ Pacientes (todos los pacientes + mapa)
 */
public class OrganizationDashboardPanel extends JPanel {
    private static final Color GLOBAL_BACKGROUND = new Color(247, 249, 251);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    
    private final ApiClient apiClient;
    private final String accessToken;
    private final OrgMembership organization;
    private final Consumer<Exception> exceptionHandler;
    private final BiConsumer<String, Boolean> snackbarHandler;
    
    private final JTabbedPane tabs;
    private OrgOverviewTab overviewTab;
    private OrgCareTeamsTab careTeamsTab;
    private OrgDevicesTab devicesTab;
    private OrgPatientsTab patientsTab;
    
    public OrganizationDashboardPanel(
            ApiClient apiClient,
            String accessToken,
            OrgMembership organization,
            Consumer<Exception> exceptionHandler,
            BiConsumer<String, Boolean> snackbarHandler
    ) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.organization = organization;
        this.exceptionHandler = exceptionHandler;
        this.snackbarHandler = snackbarHandler;
        
        setLayout(new BorderLayout());
        setOpaque(false);
        setBorder(new EmptyBorder(16, 0, 0, 0));
        
        // Título de organización
        JPanel headerPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        headerPanel.setOpaque(false);
        headerPanel.setBorder(new EmptyBorder(0, 16, 16, 16));
        
        JLabel orgLabel = new JLabel("🏥 " + organization.getOrgName());
        orgLabel.setFont(new Font("Inter", Font.BOLD, 24));
        orgLabel.setForeground(TEXT_PRIMARY);
        headerPanel.add(orgLabel);
        
        add(headerPanel, BorderLayout.NORTH);
        
        // Tabs secundarios
        tabs = new JTabbedPane();
        tabs.setFont(new Font("Inter", Font.BOLD, 14));
        tabs.setBackground(GLOBAL_BACKGROUND);
        
        // Tab 1: Overview con métricas y gráficos
        overviewTab = new OrgOverviewTab(
                apiClient,
                accessToken,
                organization,
                exceptionHandler,
                snackbarHandler
        );
        tabs.addTab("📊 Overview", overviewTab);
        
        // Tab 2: Care Teams con sidebar
        careTeamsTab = new OrgCareTeamsTab(
                apiClient,
                accessToken,
                organization,
                exceptionHandler,
                snackbarHandler
        );
        tabs.addTab("👥 Care Teams", careTeamsTab);
        
        // Tab 3: Dispositivos
        devicesTab = new OrgDevicesTab(
                apiClient,
                accessToken,
                organization,
                exceptionHandler,
                snackbarHandler
        );
        tabs.addTab("📱 Dispositivos", devicesTab);
        
        // Tab 4: Pacientes de todos los care teams
        patientsTab = new OrgPatientsTab(
                apiClient,
                accessToken,
                organization,
                exceptionHandler,
                snackbarHandler
        );
        tabs.addTab("🗺️ Pacientes", patientsTab);
        
        add(tabs, BorderLayout.CENTER);
    }
    
    private JPanel createPlaceholderTab(String title, String subtitle) {
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setOpaque(false);
        panel.setBorder(new EmptyBorder(80, 0, 0, 0));
        
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Inter", Font.BOLD, 28));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel subtitleLabel = new JLabel(subtitle);
        subtitleLabel.setFont(new Font("Inter", Font.PLAIN, 16));
        subtitleLabel.setForeground(new Color(96, 103, 112));
        subtitleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel statusLabel = new JLabel("🚧 En construcción");
        statusLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        statusLabel.setForeground(new Color(255, 152, 0));
        statusLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        panel.add(titleLabel);
        panel.add(Box.createVerticalStrut(12));
        panel.add(subtitleLabel);
        panel.add(Box.createVerticalStrut(24));
        panel.add(statusLabel);
        panel.add(Box.createVerticalGlue());
        
        return panel;
    }
    
    /**
     * Carga datos de la organización
     */
    public void loadData() {
        // Cargar datos del tab Overview
        if (overviewTab != null) {
            overviewTab.loadData();
        }
        
        // Cargar datos del tab Care Teams
        if (careTeamsTab != null) {
            careTeamsTab.loadData();
        }
        
        // Cargar datos del tab Dispositivos
        if (devicesTab != null) {
            devicesTab.loadData();
        }
        
        // Cargar datos del tab Pacientes
        if (patientsTab != null) {
            patientsTab.loadData();
        }
        
        snackbarHandler.accept("Cargando datos de " + organization.getOrgName(), true);
    }
}
