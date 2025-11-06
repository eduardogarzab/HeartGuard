package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.user.OrgMembership;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutionException;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Panel central del dashboard de usuario staff con diseño moderno mejorado.
 */
public class UserDashboardPanel extends JPanel {
    // Paleta de colores moderna (misma que PatientDashboard)
    private static final Color BACKGROUND_COLOR = new Color(240, 244, 249);
    private static final Color CARD_BACKGROUND = Color.WHITE;
    private static final Color PRIMARY_COLOR = new Color(33, 150, 243);
    private static final Color PRIMARY_DARK = new Color(25, 118, 210);
    private static final Color ACCENT_COLOR = new Color(0, 188, 212);
    private static final Color TEXT_PRIMARY_COLOR = new Color(35, 52, 70);
    private static final Color TEXT_SECONDARY_COLOR = new Color(104, 120, 138);
    private static final Color NEUTRAL_BORDER_COLOR = new Color(225, 231, 238);
    private static final Color SUCCESS_COLOR = new Color(46, 204, 113);
    private static final Color WARNING_COLOR = new Color(255, 179, 0);
    private static final Color INFO_COLOR = new Color(155, 89, 182);
    private static final Color DANGER_COLOR = new Color(231, 76, 60);
    
    // Tipografía consistente
    private static final Font SECTION_TITLE_FONT = new Font("Segoe UI", Font.BOLD, 18);
    private static final Font BODY_FONT = new Font("Segoe UI", Font.PLAIN, 14);
    private static final Font CAPTION_FONT = new Font("Segoe UI", Font.PLAIN, 12);
    private static final Font METRIC_VALUE_FONT = new Font("Segoe UI", Font.BOLD, 28);
    private static final Font METRIC_DESC_FONT = new Font("Segoe UI", Font.PLAIN, 13);
    
    private final ApiClient apiClient;
    private final String token;
    private final Consumer<ApiException> apiErrorHandler;
    private final BiConsumer<String, Boolean> snackbar;

    private OrgMembership currentOrg;

    private final JPanel metricsPanel = new JPanel(new GridLayout(1, 4, 16, 0));
    private final MetricCard patientsCard = new MetricCard("Pacientes activos", PRIMARY_COLOR);
    private final MetricCard alertsCard = new MetricCard("Alertas abiertas", DANGER_COLOR);
    private final MetricCard devicesCard = new MetricCard("Dispositivos activos", ACCENT_COLOR);
    private final MetricCard caregiversCard = new MetricCard("Caregivers activos", SUCCESS_COLOR);

    private final UserMapPanel mapPanel = new UserMapPanel();
    private final JComboBox<TeamOption> teamFilter = new JComboBox<>();
    private final JButton refreshMapButton = new JButton("Actualizar");
    private final JLabel mapStatusLabel = new JLabel(" ");

    private final JTabbedPane modulesTabs = new JTabbedPane();
    private final CardLayout patientsCardLayout = new CardLayout();
    private final JPanel patientsContainer = new JPanel(patientsCardLayout);
    private final JPanel myPatientsPanel = new JPanel();
    private final JPanel teamPatientsPanel = new JPanel();
    private final JLabel patientsStatusLabel = new JLabel(" ");
    private final ButtonGroup patientsToggleGroup = new ButtonGroup();

    private final DefaultListModel<TeamOption> teamListModel = new DefaultListModel<>();
    private final JList<TeamOption> careTeamList = new JList<>(teamListModel);
    private final JPanel careTeamDetailPanel = new JPanel(new BorderLayout());
    private final JLabel careTeamStatusLabel = new JLabel("Selecciona un equipo para ver detalles");
    private final JPanel membersListPanel = new JPanel();
    private final JPanel activeDevicesPanel = new JPanel();
    private final JPanel disconnectedDevicesPanel = new JPanel();

    private final JPanel devicesSummaryPanel = new JPanel();
    private final JLabel devicesSummaryLabel = new JLabel(" ");

    private final JPanel alertsPanel = new JPanel();
    private final JLabel alertsStatusLabel = new JLabel(" ");

    private JsonArray mapPatientsData = new JsonArray();
    private JsonArray mapMembersData = new JsonArray();
    private JsonArray careTeamsArray = new JsonArray();
    private final Map<String, JsonArray> devicesCache = new HashMap<>();
    private final Map<String, JsonArray> disconnectedDevicesCache = new HashMap<>();

    public UserDashboardPanel(ApiClient apiClient, String token,
                              Consumer<ApiException> apiErrorHandler,
                              BiConsumer<String, Boolean> snackbar) {
        this.apiClient = apiClient;
        this.token = token;
        this.apiErrorHandler = apiErrorHandler;
        this.snackbar = snackbar;
        initUI();
    }

    private void initUI() {
        setLayout(new BorderLayout(0, 16));
        setBackground(BACKGROUND_COLOR);
        setBorder(new EmptyBorder(20, 24, 24, 24));

        // Panel de métricas en la parte superior
        metricsPanel.setOpaque(false);
        metricsPanel.add(patientsCard);
        metricsPanel.add(alertsCard);
        metricsPanel.add(devicesCard);
        metricsPanel.add(caregiversCard);
        add(metricsPanel, BorderLayout.NORTH);

        // Panel central con mapa y módulos
        JPanel centerPanel = new JPanel(new BorderLayout(0, 16));
        centerPanel.setOpaque(false);
        centerPanel.add(createMapSection(), BorderLayout.CENTER);
        centerPanel.add(createModulesSection(), BorderLayout.SOUTH);
        add(centerPanel, BorderLayout.CENTER);
    }

    private JPanel createMapSection() {
        JPanel wrapper = new JPanel(new BorderLayout(0, 12));
        wrapper.setOpaque(false);

        // Encabezado del mapa con filtros
        JPanel header = new JPanel(new BorderLayout());
        header.setOpaque(false);
        header.setBorder(new EmptyBorder(0, 0, 8, 0));
        
        JLabel mapTitle = new JLabel("Mapa de Ubicaciones en Tiempo Real");
        mapTitle.setFont(SECTION_TITLE_FONT);
        mapTitle.setForeground(TEXT_PRIMARY_COLOR);
        header.add(mapTitle, BorderLayout.WEST);

        JPanel filters = new JPanel(new FlowLayout(FlowLayout.RIGHT, 12, 0));
        filters.setOpaque(false);
        
        JLabel filterLabel = new JLabel("Filtrar por equipo:");
        filterLabel.setFont(CAPTION_FONT);
        filterLabel.setForeground(TEXT_SECONDARY_COLOR);
        filters.add(filterLabel);
        
        teamFilter.setPreferredSize(new Dimension(220, 32));
        teamFilter.setFont(BODY_FONT);
        teamFilter.setBackground(CARD_BACKGROUND);
        teamFilter.addActionListener(e -> applyMapFilter());
        filters.add(teamFilter);

        styleButton(refreshMapButton, ACCENT_COLOR);
        refreshMapButton.setToolTipText("Recargar ubicaciones");
        refreshMapButton.setPreferredSize(new Dimension(44, 32));
        refreshMapButton.addActionListener(e -> fetchMapData());
        filters.add(refreshMapButton);
        
        mapStatusLabel.setFont(CAPTION_FONT);
        mapStatusLabel.setForeground(TEXT_SECONDARY_COLOR);
        filters.add(mapStatusLabel);

        header.add(filters, BorderLayout.EAST);
        wrapper.add(header, BorderLayout.NORTH);

        // Contenedor del mapa con sombra
        JPanel mapContainer = createStyledCard();
        mapContainer.setLayout(new BorderLayout());
        mapContainer.add(mapPanel, BorderLayout.CENTER);
        mapContainer.setPreferredSize(new Dimension(0, 400));
        wrapper.add(mapContainer, BorderLayout.CENTER);

        return wrapper;
    }

    private JPanel createModulesSection() {
        JPanel wrapper = new JPanel(new BorderLayout());
        wrapper.setOpaque(false);
        
        // Estilizar las tabs
        modulesTabs.setFont(BODY_FONT);
        modulesTabs.setBackground(CARD_BACKGROUND);
        modulesTabs.setForeground(TEXT_PRIMARY_COLOR);
        
        modulesTabs.addTab("Pacientes", createPatientsTab());
        modulesTabs.addTab("Care-teams", createCareTeamsTab());
        modulesTabs.addTab("Dispositivos", createDevicesTab());
        modulesTabs.addTab("Alertas", createAlertsTab());

        JPanel tabsCard = createStyledCard();
        tabsCard.setLayout(new BorderLayout());
        tabsCard.add(modulesTabs, BorderLayout.CENTER);
        tabsCard.setPreferredSize(new Dimension(0, 500));
        
        wrapper.add(tabsCard, BorderLayout.CENTER);
        return wrapper;
    }
    
    /**
     * Crea un panel con estilo de tarjeta moderna (sombra y bordes redondeados)
     */
    private JPanel createStyledCard() {
        JPanel card = new JPanel();
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(NEUTRAL_BORDER_COLOR, 1),
            new EmptyBorder(16, 16, 16, 16)
        ));
        return card;
    }
    
    /**
     * Aplica estilo moderno a un botón
     */
    private void styleButton(JButton button, Color color) {
        button.setBackground(color);
        button.setForeground(Color.WHITE);
        button.setFont(new Font("Segoe UI", Font.BOLD, 13));
        button.setFocusPainted(false);
        button.setBorderPainted(false);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        button.setBorder(new EmptyBorder(8, 16, 8, 16));
    }
    
    /**
     * Aplica estilo moderno a un toggle button
     */
    private void styleToggleButton(JToggleButton button) {
        button.setFont(BODY_FONT);
        button.setFocusPainted(false);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        button.setBorder(new EmptyBorder(8, 16, 8, 16));
        button.setBackground(CARD_BACKGROUND);
        button.setForeground(TEXT_PRIMARY_COLOR);
        
        // Cambiar estilo cuando esté seleccionado
        button.addItemListener(e -> {
            if (button.isSelected()) {
                button.setBackground(PRIMARY_COLOR);
                button.setForeground(Color.WHITE);
            } else {
                button.setBackground(CARD_BACKGROUND);
                button.setForeground(TEXT_PRIMARY_COLOR);
            }
        });
    }

    private JPanel createPatientsTab() {
        JPanel container = new JPanel(new BorderLayout(0, 12));
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(12, 12, 12, 12));

        // Header con toggles estilizados
        JPanel header = new JPanel(new BorderLayout());
        header.setOpaque(false);
        
        JLabel title = new JLabel("Pacientes en Seguimiento");
        title.setFont(SECTION_TITLE_FONT);
        title.setForeground(TEXT_PRIMARY_COLOR);
        header.add(title, BorderLayout.WEST);
        
        JPanel togglePanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 0));
        togglePanel.setOpaque(false);
        
        JToggleButton myPatientsToggle = new JToggleButton("Mis pacientes");
        JToggleButton teamPatientsToggle = new JToggleButton("Por equipos");
        styleToggleButton(myPatientsToggle);
        styleToggleButton(teamPatientsToggle);
        
        myPatientsToggle.setSelected(true);
        patientsToggleGroup.add(myPatientsToggle);
        patientsToggleGroup.add(teamPatientsToggle);
        myPatientsToggle.addActionListener(e -> patientsCardLayout.show(patientsContainer, "mine"));
        teamPatientsToggle.addActionListener(e -> patientsCardLayout.show(patientsContainer, "teams"));
        
        togglePanel.add(myPatientsToggle);
        togglePanel.add(teamPatientsToggle);
        
        patientsStatusLabel.setFont(CAPTION_FONT);
        patientsStatusLabel.setForeground(TEXT_SECONDARY_COLOR);
        togglePanel.add(patientsStatusLabel);
        
        header.add(togglePanel, BorderLayout.EAST);
        container.add(header, BorderLayout.NORTH);

        // Paneles de pacientes con fondo y scroll
        myPatientsPanel.setLayout(new BoxLayout(myPatientsPanel, BoxLayout.Y_AXIS));
        myPatientsPanel.setOpaque(false);
        myPatientsPanel.setBorder(new EmptyBorder(8, 0, 8, 0));
        
        teamPatientsPanel.setLayout(new BoxLayout(teamPatientsPanel, BoxLayout.Y_AXIS));
        teamPatientsPanel.setOpaque(false);
        teamPatientsPanel.setBorder(new EmptyBorder(8, 0, 8, 0));

        JScrollPane myScroll = new JScrollPane(myPatientsPanel);
        configureStyledScroll(myScroll);
        JScrollPane teamScroll = new JScrollPane(teamPatientsPanel);
        configureStyledScroll(teamScroll);

        patientsContainer.add(myScroll, "mine");
        patientsContainer.add(teamScroll, "teams");
        container.add(patientsContainer, BorderLayout.CENTER);
        patientsCardLayout.show(patientsContainer, "mine");
        return container;
    }

    private JPanel createCareTeamsTab() {
        JPanel container = new JPanel(new BorderLayout(12, 0));
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(12, 12, 12, 12));

        // Lista de equipos con estilo
        JPanel listPanel = new JPanel(new BorderLayout(0, 8));
        listPanel.setOpaque(false);
        listPanel.setPreferredSize(new Dimension(280, 0));
        
        JLabel listTitle = new JLabel("Equipos de Cuidado");
        listTitle.setFont(new Font("Segoe UI", Font.BOLD, 15));
        listTitle.setForeground(TEXT_PRIMARY_COLOR);
        listTitle.setBorder(new EmptyBorder(0, 8, 0, 0));
        listPanel.add(listTitle, BorderLayout.NORTH);
        
        careTeamList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        careTeamList.setFont(BODY_FONT);
        careTeamList.setBackground(CARD_BACKGROUND);
        careTeamList.setBorder(new EmptyBorder(8, 8, 8, 8));
        careTeamList.addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                TeamOption option = careTeamList.getSelectedValue();
                if (option != null) {
                    loadCareTeamDetail(option);
                }
            }
        });
        
        JScrollPane listScroll = new JScrollPane(careTeamList);
        configureStyledScroll(listScroll);
        listPanel.add(listScroll, BorderLayout.CENTER);

        // Panel de detalles con estilo
        careTeamDetailPanel.setOpaque(false);
        careTeamDetailPanel.setBorder(new EmptyBorder(0, 12, 0, 0));
        
        JPanel detailHeader = new JPanel(new BorderLayout());
        detailHeader.setOpaque(false);
        detailHeader.setBorder(new EmptyBorder(0, 0, 12, 0));
        
        careTeamStatusLabel.setFont(SECTION_TITLE_FONT);
        careTeamStatusLabel.setForeground(TEXT_PRIMARY_COLOR);
        detailHeader.add(careTeamStatusLabel, BorderLayout.WEST);
        careTeamDetailPanel.add(detailHeader, BorderLayout.NORTH);

        // Contenido de detalles
        JPanel detailBody = new JPanel();
        detailBody.setLayout(new BoxLayout(detailBody, BoxLayout.Y_AXIS));
        detailBody.setOpaque(false);
        
        // Panel de miembros
        JPanel membersCard = createStyledCard();
        membersCard.setLayout(new BorderLayout(0, 8));
        JLabel membersTitle = new JLabel("Miembros del Equipo");
        membersTitle.setFont(new Font("Segoe UI", Font.BOLD, 14));
        membersTitle.setForeground(TEXT_PRIMARY_COLOR);
        membersCard.add(membersTitle, BorderLayout.NORTH);
        
        membersListPanel.setLayout(new BoxLayout(membersListPanel, BoxLayout.Y_AXIS));
        membersListPanel.setOpaque(false);
        JScrollPane membersScroll = new JScrollPane(membersListPanel);
        configureStyledScroll(membersScroll);
        membersScroll.setPreferredSize(new Dimension(0, 200));
        membersCard.add(membersScroll, BorderLayout.CENTER);
        
        detailBody.add(membersCard);
        detailBody.add(Box.createVerticalStrut(12));

        // Tabs de dispositivos con estilo
        JTabbedPane deviceTabs = new JTabbedPane();
        deviceTabs.setFont(BODY_FONT);
        
        activeDevicesPanel.setLayout(new BoxLayout(activeDevicesPanel, BoxLayout.Y_AXIS));
        activeDevicesPanel.setOpaque(false);
        activeDevicesPanel.setBorder(new EmptyBorder(8, 8, 8, 8));
        
        disconnectedDevicesPanel.setLayout(new BoxLayout(disconnectedDevicesPanel, BoxLayout.Y_AXIS));
        disconnectedDevicesPanel.setOpaque(false);
        disconnectedDevicesPanel.setBorder(new EmptyBorder(8, 8, 8, 8));
        
        JScrollPane activeScroll = new JScrollPane(activeDevicesPanel);
        JScrollPane disconnectedScroll = new JScrollPane(disconnectedDevicesPanel);
        configureStyledScroll(activeScroll);
        configureStyledScroll(disconnectedScroll);
        
        deviceTabs.addTab("Activos", activeScroll);
        deviceTabs.addTab("Desconectados", disconnectedScroll);
        
        JPanel devicesCard = createStyledCard();
        devicesCard.setLayout(new BorderLayout());
        devicesCard.add(deviceTabs, BorderLayout.CENTER);
        devicesCard.setPreferredSize(new Dimension(0, 300));
        
        detailBody.add(devicesCard);
        careTeamDetailPanel.add(detailBody, BorderLayout.CENTER);

        // Split pane
        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, listPanel, careTeamDetailPanel);
        splitPane.setDividerLocation(280);
        splitPane.setOpaque(false);
        splitPane.setBorder(null);
        container.add(splitPane, BorderLayout.CENTER);
        return container;
    }

    private JPanel createDevicesTab() {
        JPanel container = new JPanel(new BorderLayout());
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(12, 12, 12, 12));
        
        devicesSummaryPanel.setLayout(new BoxLayout(devicesSummaryPanel, BoxLayout.Y_AXIS));
        devicesSummaryPanel.setOpaque(false);
        
        devicesSummaryLabel.setFont(BODY_FONT);
        devicesSummaryLabel.setForeground(TEXT_SECONDARY_COLOR);
        devicesSummaryPanel.add(devicesSummaryLabel);
        
        JScrollPane scroll = new JScrollPane(devicesSummaryPanel);
        configureStyledScroll(scroll);
        container.add(scroll, BorderLayout.CENTER);
        return container;
    }

    private JPanel createAlertsTab() {
        JPanel container = new JPanel(new BorderLayout(0, 12));
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(12, 12, 12, 12));
        
        alertsStatusLabel.setFont(CAPTION_FONT);
        alertsStatusLabel.setForeground(TEXT_SECONDARY_COLOR);
        container.add(alertsStatusLabel, BorderLayout.NORTH);
        
        alertsPanel.setLayout(new BoxLayout(alertsPanel, BoxLayout.Y_AXIS));
        alertsPanel.setOpaque(false);
        alertsPanel.setBorder(new EmptyBorder(8, 0, 8, 0));
        
        JScrollPane scrollPane = new JScrollPane(alertsPanel);
        configureStyledScroll(scrollPane);
        container.add(scrollPane, BorderLayout.CENTER);
        return container;
    }

    /**
     * Configura el estilo del scroll pane para que sea consistente
     */
    private void configureStyledScroll(JScrollPane scrollPane) {
        scrollPane.setBorder(BorderFactory.createLineBorder(NEUTRAL_BORDER_COLOR, 1));
        scrollPane.getViewport().setBackground(CARD_BACKGROUND);
        scrollPane.setBackground(CARD_BACKGROUND);
    }
    
    // Mantener el método antiguo para compatibilidad
    private void configureScroll(JScrollPane scrollPane) {
        configureStyledScroll(scrollPane);
    }

    public void showForOrganization(OrgMembership membership) {
        this.currentOrg = membership;
        resetPanels();
        loadDashboardData();
    }

    private void resetPanels() {
        patientsStatusLabel.setText("Actualizando pacientes...");
        myPatientsPanel.removeAll();
        teamPatientsPanel.removeAll();
        mapStatusLabel.setText("Actualizando mapa...");
        mapPanel.reset();
        teamFilter.removeAllItems();
        teamListModel.clear();
        membersListPanel.removeAll();
        activeDevicesPanel.removeAll();
        disconnectedDevicesPanel.removeAll();
        devicesSummaryPanel.removeAll();
        devicesSummaryPanel.add(devicesSummaryLabel);
        devicesSummaryLabel.setText("Analizando dispositivos...");
        alertsPanel.removeAll();
        alertsStatusLabel.setText("Cargando alertas recientes...");
        revalidate();
        repaint();
    }

    private void loadDashboardData() {
        if (currentOrg == null) {
            return;
        }
        String orgId = currentOrg.getOrgId();

        CompletableFuture<JsonObject> dashboardFuture = apiClient.getOrganizationDashboardAsync(token, orgId);
        CompletableFuture<JsonObject> metricsFuture = apiClient.getOrganizationMetricsAsync(token, orgId);
        CompletableFuture<JsonObject> careTeamsFuture = apiClient.getOrganizationCareTeamsAsync(token, orgId);
        CompletableFuture<JsonObject> careTeamPatientsFuture = apiClient.getOrganizationCareTeamPatientsAsync(token, orgId)
                .exceptionally(this::handleCareTeamPatientsFallback);
        CompletableFuture<JsonObject> caregiverPatientsFuture = apiClient.getCaregiverPatientsAsync(token);

        Map<String, String> locationParams = Map.of("org_id", orgId);
        CompletableFuture<JsonObject> careTeamLocationsFuture = apiClient.getCareTeamLocationsAsync(token, locationParams);
        CompletableFuture<JsonObject> caregiverLocationsFuture = apiClient.getCaregiverPatientLocationsAsync(token, locationParams);

        CompletableFuture<DashboardBundle> bundleFuture = CompletableFuture.allOf(
                        dashboardFuture,
                        metricsFuture,
                        careTeamsFuture,
                        careTeamPatientsFuture,
                        caregiverPatientsFuture,
                        careTeamLocationsFuture,
                        caregiverLocationsFuture
                )
                .thenApplyAsync(ignored -> {
                    DashboardBundle bundle = new DashboardBundle();
                    bundle.dashboard = dashboardFuture.join();
                    bundle.metrics = metricsFuture.join();
                    bundle.careTeams = careTeamsFuture.join();
                    bundle.careTeamPatients = careTeamPatientsFuture.join();
                    bundle.caregiverPatients = caregiverPatientsFuture.join();
                    bundle.careTeamLocations = careTeamLocationsFuture.join();
                    bundle.caregiverLocations = caregiverLocationsFuture.join();
                    return bundle;
                });

        bundleFuture.thenAccept(bundle ->
                SwingUtilities.invokeLater(() -> renderDashboard(bundle))
        ).exceptionally(ex -> {
            handleAsyncException(ex, "Error al actualizar dashboard");
            return null;
        });
    }

    private JsonObject handleCareTeamPatientsFallback(Throwable throwable) {
        Throwable cause = unwrapCompletionException(throwable);
        if (cause instanceof ApiException apiException && apiException.getStatusCode() == 403) {
            System.out.println("[INFO] Usuario no pertenece a ningún equipo de cuidado en esta organización");
            return createEmptyResponse();
        }
        throw new CompletionException(cause);
    }

    private void renderDashboard(DashboardBundle bundle) {
        // Limpiar todos los datos de la organización anterior
        mapPatientsData = new JsonArray();
        mapMembersData = new JsonArray();
        careTeamsArray = new JsonArray();
        devicesCache.clear();
        disconnectedDevicesCache.clear();
        
        JsonObject dashboardData = getData(bundle.dashboard);
        JsonObject metricsData = getData(bundle.metrics);
        JsonObject overview = dashboardData.has("overview") && dashboardData.get("overview").isJsonObject()
                ? dashboardData.getAsJsonObject("overview")
                : new JsonObject();
        JsonObject metrics = metricsData.has("metrics") && metricsData.get("metrics").isJsonObject()
                ? metricsData.getAsJsonObject("metrics")
                : new JsonObject();
        updateMetrics(overview, metrics);

        teamListModel.clear();
        teamFilter.removeAllItems();
        List<TeamOption> teamOptions = new ArrayList<>();
        TeamOption all = new TeamOption("all", "Todos los equipos");
        teamFilter.addItem(all);
        
        // Usar care_team_patients en lugar de care_teams para filtrar por membresía
        JsonObject careTeamPatientsData = getData(bundle.careTeamPatients);
        careTeamsArray = getArray(careTeamPatientsData, "care_teams");
        JsonArray careTeams = careTeamsArray;
        
        if (careTeams != null) {
            Set<String> addedTeamIds = new HashSet<>();
            for (JsonElement element : careTeams) {
                if (!element.isJsonObject()) continue;
                JsonObject team = element.getAsJsonObject();
                String id = team.has("id") && !team.get("id").isJsonNull() ? team.get("id").getAsString() : null;
                if (id == null || addedTeamIds.contains(id)) {
                    continue;
                }
                String name = team.has("name") && !team.get("name").isJsonNull() ? team.get("name").getAsString() : "Equipo";
                TeamOption option = new TeamOption(id, name);
                teamOptions.add(option);
                teamFilter.addItem(option);
                teamListModel.addElement(option);
                addedTeamIds.add(id);
            }
        }
        if (!teamOptions.isEmpty()) {
            careTeamList.setSelectedIndex(0);
        }

        mapPatientsData = getArray(getData(bundle.caregiverLocations), "patients");
        mapMembersData = getArray(getData(bundle.careTeamLocations), "members");
        applyMapFilter();
        mapStatusLabel.setText(mapPatientsData.size() == 0 && mapMembersData.size() == 0
                ? "Sin ubicaciones registradas actualmente"
                : "Actualizado hace unos segundos");

        renderPatients(bundle);
        renderAlerts(bundle);
        loadDevicesSummary(teamOptions);
    }

    private void renderPatients(DashboardBundle bundle) {
        myPatientsPanel.removeAll();
        teamPatientsPanel.removeAll();

        JsonArray caregiverPatients = getArray(getData(bundle.caregiverPatients), "patients");
        if (caregiverPatients == null || caregiverPatients.size() == 0) {
            myPatientsPanel.add(createEmptyState(
                    "No tienes pacientes asignados por ahora",
                    "Actualizar pacientes",
                    this::loadDashboardData
            ));
        } else {
            for (JsonElement element : caregiverPatients) {
                if (!element.isJsonObject()) continue;
                myPatientsPanel.add(createPatientCard(element.getAsJsonObject(), true));
                myPatientsPanel.add(Box.createVerticalStrut(10));
            }
        }

        JsonArray teamPatients = getArray(getData(bundle.careTeamPatients), "care_teams");
        if (teamPatients == null || teamPatients.size() == 0) {
            teamPatientsPanel.add(createEmptyState(
                    "No hay pacientes registrados en los equipos",
                    "Actualizar equipos",
                    this::loadDashboardData
            ));
        } else {
            for (JsonElement element : teamPatients) {
                if (!element.isJsonObject()) continue;
                JsonObject team = element.getAsJsonObject();
                String teamName = team.has("name") && !team.get("name").isJsonNull() ? team.get("name").getAsString() : "Equipo";
                JLabel teamLabel = new JLabel(teamName);
                teamLabel.setFont(new Font("Segoe UI", Font.BOLD, 14));
                teamPatientsPanel.add(teamLabel);
                teamPatientsPanel.add(Box.createVerticalStrut(6));
                JsonArray patients = team.getAsJsonArray("patients");
                if (patients != null) {
                    for (JsonElement patientElement : patients) {
                        if (!patientElement.isJsonObject()) continue;
                        teamPatientsPanel.add(createPatientCard(patientElement.getAsJsonObject(), false));
                        teamPatientsPanel.add(Box.createVerticalStrut(6));
                    }
                }
                teamPatientsPanel.add(Box.createVerticalStrut(12));
            }
        }
        patientsStatusLabel.setText("Última actualización sincronizada");
        myPatientsPanel.revalidate();
        teamPatientsPanel.revalidate();
    }

    private JPanel createPatientCard(JsonObject patient, boolean caregiverContext) {
        JPanel card = new JPanel(new BorderLayout(12, 0));
        card.setBackground(Color.WHITE);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(229, 234, 243)),
                new EmptyBorder(16, 16, 16, 16)
        ));

        // Información del paciente
        JLabel name = new JLabel(patient.get("name").getAsString());
        name.setFont(new Font("Segoe UI", Font.BOLD, 15));
        name.setForeground(TEXT_PRIMARY_COLOR);
        
        JLabel org = new JLabel("Organización: " + safe(patient.get("organization"), "name"));
        org.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        org.setForeground(TEXT_SECONDARY_COLOR);
        
        // Badge de riesgo con color
        String riskLabel = safe(patient.get("risk_level"), "label");
        JLabel risk = new JLabel(riskLabel);
        risk.setFont(new Font("Segoe UI", Font.BOLD, 12));
        risk.setOpaque(true);
        risk.setBorder(new EmptyBorder(4, 10, 4, 10));
        
        // Colorear badge según nivel de riesgo
        if (riskLabel.toLowerCase().contains("alto") || riskLabel.toLowerCase().contains("high")) {
            risk.setBackground(new Color(254, 226, 226));
            risk.setForeground(new Color(185, 28, 28));
        } else if (riskLabel.toLowerCase().contains("medio") || riskLabel.toLowerCase().contains("medium")) {
            risk.setBackground(new Color(254, 243, 199));
            risk.setForeground(new Color(146, 64, 14));
        } else {
            risk.setBackground(new Color(220, 252, 231));
            risk.setForeground(new Color(22, 101, 52));
        }

        JPanel info = new JPanel();
        info.setOpaque(false);
        info.setLayout(new BoxLayout(info, BoxLayout.Y_AXIS));
        info.add(name);
        info.add(Box.createVerticalStrut(6));
        info.add(org);
        info.add(Box.createVerticalStrut(8));
        info.add(risk);

        // Botón con mejor estilo
        JButton details = new JButton("Ver detalle");
        details.setFont(new Font("Segoe UI", Font.BOLD, 13));
        details.setForeground(Color.WHITE);
        details.setBackground(PRIMARY_COLOR);
        details.setBorderPainted(false);
        details.setFocusPainted(false);
        details.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        details.setPreferredSize(new Dimension(120, 36));
        details.addActionListener(e -> openPatientDetail(patient));

        card.add(info, BorderLayout.CENTER);
        card.add(details, BorderLayout.EAST);
        return card;
    }

    private void openPatientDetail(JsonObject patient) {
        if (currentOrg == null) return;
        String patientId = patient.get("id").getAsString();
        String name = patient.get("name").getAsString();
        Window window = SwingUtilities.getWindowAncestor(this);
        Frame frame = window instanceof Frame ? (Frame) window : null;
        PatientDetailDialog dialog = new PatientDetailDialog(
                frame,
                apiClient,
                token,
                currentOrg.getOrgId(),
                patientId,
                name
        );
        dialog.setVisible(true);
    }

    private void renderAlerts(DashboardBundle bundle) {
        alertsPanel.removeAll();
        JsonArray patients = mapPatientsData;
        int count = 0;
        for (JsonElement element : patients) {
            if (!element.isJsonObject()) continue;
            JsonObject patient = element.getAsJsonObject();
            if (!patient.has("alert") || patient.get("alert").isJsonNull()) continue;
            JsonObject alert = patient.getAsJsonObject("alert");
            JPanel alertCard = new JPanel(new BorderLayout());
            alertCard.setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(new Color(245, 203, 92)),
                    new EmptyBorder(12, 14, 12, 14)
            ));
            alertCard.setBackground(new Color(255, 248, 230));
            JLabel title = new JLabel(patient.get("name").getAsString() + " · " + safe(alert, "label"));
            title.setFont(new Font("Segoe UI", Font.BOLD, 13));
            JLabel subtitle = new JLabel("Última actualización: " + safe(alert, "created_at"));
            subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            subtitle.setForeground(new Color(120, 130, 140));
            alertCard.add(title, BorderLayout.NORTH);
            alertCard.add(subtitle, BorderLayout.SOUTH);
            alertsPanel.add(alertCard);
            alertsPanel.add(Box.createVerticalStrut(10));
            count++;
        }
        alertsStatusLabel.setText(count == 0 ? "Sin alertas recientes" : count + " alertas en seguimiento");
    }

    private void loadDevicesSummary(List<TeamOption> teamOptions) {
        if (currentOrg == null) {
            return;
        }
        SwingWorker<DeviceSummary, Void> worker = new SwingWorker<>() {
            @Override
            protected DeviceSummary doInBackground() throws Exception {
                DeviceSummary summary = new DeviceSummary();
                for (TeamOption option : teamOptions) {
                    JsonObject response = apiClient.getCareTeamDevices(token, currentOrg.getOrgId(), option.id);
                    JsonArray devices = getArray(getData(response), "devices");
                    devicesCache.put(option.id, devices);
                    TeamDeviceStats stats = summary.teams.computeIfAbsent(option.id, id -> new TeamDeviceStats(option.id, option.name));
                    stats.total = 0;
                    stats.active = 0;
                    for (JsonElement element : devices) {
                        if (!element.isJsonObject()) continue;
                        JsonObject device = element.getAsJsonObject();
                        summary.total++;
                        stats.total++;
                        if (device.has("active") && device.get("active").getAsBoolean()) {
                            summary.active++;
                            stats.active++;
                        }
                    }
                    JsonObject disconnectedResponse = apiClient.getCareTeamDisconnectedDevices(token, currentOrg.getOrgId(), option.id);
                    JsonArray disconnected = getArray(getData(disconnectedResponse), "devices");
                    stats.disconnected = disconnected.size();
                    disconnectedDevicesCache.put(option.id, disconnected);
                }
                return summary;
            }

            @Override
            protected void done() {
                try {
                    DeviceSummary summary = get();
                    devicesCard.updateValue(String.valueOf(summary.active), "Total instalados: " + summary.total,
                            new double[]{summary.active, Math.max(0, summary.total - summary.active)});
                    devicesSummaryLabel.setText("Hay " + summary.total + " dispositivos registrados en la organización");
                    renderDeviceSummary(summary);
                } catch (Exception ex) {
                    devicesSummaryLabel.setText("No fue posible obtener los dispositivos");
                    if (ex.getCause() instanceof ApiException apiException) {
                        apiErrorHandler.accept(apiException);
                    }
                }
            }
        };
        worker.execute();
    }

    private void renderDeviceSummary(DeviceSummary summary) {
        devicesSummaryPanel.removeAll();
        devicesSummaryPanel.add(devicesSummaryLabel);
        devicesSummaryPanel.add(Box.createVerticalStrut(12));
        for (TeamDeviceStats stats : summary.teams.values()) {
            JPanel card = new JPanel(new BorderLayout());
            card.setBackground(Color.WHITE);
            card.setBorder(new EmptyBorder(10, 12, 10, 12));

            JLabel title = new JLabel(stats.teamName);
            title.setFont(new Font("Segoe UI", Font.BOLD, 13));

            JLabel status = new JLabel(stats.active + " activos · " + stats.disconnected + " desconectados");
            status.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            status.setForeground(new Color(120, 130, 140));

            JLabel total = new JLabel("Total: " + stats.total);
            total.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            total.setForeground(new Color(120, 130, 140));

            JPanel text = new JPanel();
            text.setOpaque(false);
            text.setLayout(new BoxLayout(text, BoxLayout.Y_AXIS));
            text.add(title);
            text.add(Box.createVerticalStrut(4));
            text.add(status);
            text.add(total);

            card.add(text, BorderLayout.CENTER);
            devicesSummaryPanel.add(card);
            devicesSummaryPanel.add(Box.createVerticalStrut(10));
        }
        devicesSummaryPanel.revalidate();
        devicesSummaryPanel.repaint();
    }

    private void loadCareTeamDetail(TeamOption option) {
        membersListPanel.removeAll();
        activeDevicesPanel.removeAll();
        disconnectedDevicesPanel.removeAll();
        careTeamStatusLabel.setText("Cargando datos del equipo...");

        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            JsonArray members;
            JsonArray activeDevices;
            JsonArray disconnectedDevices;

            @Override
            protected Void doInBackground() throws Exception {
                JsonArray careTeams = careTeamsArray;
                if (careTeams != null) {
                    for (JsonElement element : careTeams) {
                        if (!element.isJsonObject()) continue;
                        JsonObject team = element.getAsJsonObject();
                        if (team.get("id").getAsString().equals(option.id)) {
                            members = team.getAsJsonArray("members");
                            break;
                        }
                    }
                }
                activeDevices = devicesCache.computeIfAbsent(option.id, key -> new JsonArray());
                disconnectedDevices = disconnectedDevicesCache.computeIfAbsent(option.id, key -> new JsonArray());
                return null;
            }

            @Override
            protected void done() {
                try {
                    get();
                    renderCareTeamDetail(option, members, activeDevices, disconnectedDevices);
                } catch (Exception ex) {
                    if (ex.getCause() instanceof ApiException apiException) {
                        apiErrorHandler.accept(apiException);
                    }
                }
            }
        };
        worker.execute();
    }

    private void renderCareTeamDetail(TeamOption option, JsonArray members, JsonArray activeDevices, JsonArray disconnected) {
        careTeamStatusLabel.setText("Equipo " + option.name);
        membersListPanel.removeAll();
        if (members == null || members.size() == 0) {
            membersListPanel.add(createEmptyState("No hay miembros registrados", null, null));
        } else {
            for (JsonElement element : members) {
                if (!element.isJsonObject()) continue;
                JsonObject member = element.getAsJsonObject();
                
                // Crear tarjeta de miembro con mejor diseño
                JPanel memberCard = new JPanel(new BorderLayout(10, 0));
                memberCard.setBackground(new Color(249, 250, 251));
                memberCard.setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(new Color(229, 234, 243)),
                    new EmptyBorder(10, 12, 10, 12)
                ));
                
                JLabel nameLabel = new JLabel(member.get("name").getAsString());
                nameLabel.setFont(new Font("Segoe UI", Font.BOLD, 13));
                nameLabel.setForeground(TEXT_PRIMARY_COLOR);
                
                // Badge de rol
                String roleLabel = safe(member.get("role"), "label");
                JLabel roleBadge = new JLabel(roleLabel);
                roleBadge.setFont(new Font("Segoe UI", Font.BOLD, 11));
                roleBadge.setForeground(PRIMARY_COLOR);
                roleBadge.setOpaque(true);
                roleBadge.setBackground(new Color(219, 234, 254));
                roleBadge.setBorder(new EmptyBorder(3, 8, 3, 8));
                
                memberCard.add(nameLabel, BorderLayout.CENTER);
                memberCard.add(roleBadge, BorderLayout.EAST);
                
                membersListPanel.add(memberCard);
                membersListPanel.add(Box.createVerticalStrut(6));
            }
        }

        fillDevicePanel(activeDevicesPanel, activeDevices, true, option);
        fillDevicePanel(disconnectedDevicesPanel, disconnected, false, option);
        membersListPanel.revalidate();
        activeDevicesPanel.revalidate();
        disconnectedDevicesPanel.revalidate();
    }

    private void fillDevicePanel(JPanel panel, JsonArray devices, boolean active, TeamOption option) {
        panel.removeAll();
        if (devices == null || devices.size() == 0) {
            panel.add(createEmptyState(
                    active ? "Sin dispositivos activos" : "Sin dispositivos desconectados",
                    active ? "Refrescar activos" : "Refrescar desconectados",
                    () -> reloadDevices(option)
            ));
            return;
        }
        for (JsonElement element : devices) {
            if (!element.isJsonObject()) continue;
            JsonObject device = element.getAsJsonObject();
            
            // Card con mejor diseño
            JPanel card = new JPanel(new BorderLayout(12, 8));
            card.setBackground(Color.WHITE);
            card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(active ? new Color(209, 231, 221) : new Color(252, 213, 207)),
                new EmptyBorder(14, 14, 14, 14)
            ));
            
            // Información del dispositivo
            JPanel infoPanel = new JPanel();
            infoPanel.setOpaque(false);
            infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));
            
            JLabel title = new JLabel(device.get("serial").getAsString());
            title.setFont(new Font("Segoe UI", Font.BOLD, 14));
            title.setForeground(TEXT_PRIMARY_COLOR);
            
            JLabel typeLabel = new JLabel("Tipo: " + safe(device.get("type"), "label"));
            typeLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            typeLabel.setForeground(TEXT_SECONDARY_COLOR);
            
            JLabel subtitle = new JLabel("Paciente: " + safe(device.get("owner"), "name"));
            subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            subtitle.setForeground(TEXT_SECONDARY_COLOR);
            
            // Badge de estado
            JLabel status = new JLabel(active ? "● Activo" : "● Desconectado");
            status.setFont(new Font("Segoe UI", Font.BOLD, 12));
            status.setForeground(active ? new Color(40, 167, 69) : new Color(220, 53, 69));
            
            infoPanel.add(title);
            infoPanel.add(Box.createVerticalStrut(4));
            infoPanel.add(typeLabel);
            infoPanel.add(Box.createVerticalStrut(2));
            infoPanel.add(subtitle);
            infoPanel.add(Box.createVerticalStrut(6));
            infoPanel.add(status);
            
            // Botón mejorado
            JButton streamsButton = new JButton("Ver streams");
            streamsButton.setFont(new Font("Segoe UI", Font.BOLD, 12));
            streamsButton.setForeground(PRIMARY_COLOR);
            streamsButton.setBackground(new Color(239, 246, 255));
            streamsButton.setBorderPainted(false);
            streamsButton.setFocusPainted(false);
            streamsButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            streamsButton.setPreferredSize(new Dimension(110, 32));
            streamsButton.addActionListener(e -> openDeviceStreams(option, device));
            
            card.add(infoPanel, BorderLayout.CENTER);
            card.add(streamsButton, BorderLayout.EAST);
            panel.add(card);
            panel.add(Box.createVerticalStrut(10));
        }
    }

    private void reloadDevices(TeamOption option) {
        if (currentOrg == null) {
            return;
        }

        CompletableFuture<JsonObject> devicesFuture = apiClient.getCareTeamDevicesAsync(token, currentOrg.getOrgId(), option.id);
        CompletableFuture<JsonObject> disconnectedFuture = apiClient.getCareTeamDisconnectedDevicesAsync(token, currentOrg.getOrgId(), option.id);

        CompletableFuture.allOf(devicesFuture, disconnectedFuture)
                .thenApplyAsync(ignored -> {
                    JsonArray devices = getArray(getData(devicesFuture.join()), "devices");
                    JsonArray disconnected = getArray(getData(disconnectedFuture.join()), "devices");
                    devicesCache.put(option.id, devices);
                    disconnectedDevicesCache.put(option.id, disconnected);
                    return new DeviceReloadResult(devices, disconnected);
                })
                .thenAccept(result -> SwingUtilities.invokeLater(() -> {
                    fillDevicePanel(activeDevicesPanel, result.activeDevices, true, option);
                    fillDevicePanel(disconnectedDevicesPanel, result.disconnectedDevices, false, option);
                }))
                .exceptionally(ex -> {
                    handleAsyncException(ex, "Error al recargar dispositivos");
                    return null;
                });
    }

    private void openDeviceStreams(TeamOption option, JsonObject device) {
        if (currentOrg == null) {
            return;
        }

        String deviceId = device.get("id").getAsString();
        apiClient.getCareTeamDeviceStreamsAsync(token, currentOrg.getOrgId(), option.id, deviceId)
                .thenApplyAsync(response -> getArray(getData(response), "streams"))
                .thenAccept(streams -> SwingUtilities.invokeLater(() -> showStreamsDialog(device, streams)))
                .exceptionally(ex -> {
                    handleAsyncException(ex, "Error al cargar streams");
                    return null;
                });
    }

    private void showStreamsDialog(JsonObject device, JsonArray streams) {
        String deviceSerial = device.get("serial").getAsString();

        JDialog dialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(UserDashboardPanel.this), "Streams · " + deviceSerial, true);
        dialog.setSize(600, 450);
        dialog.setLocationRelativeTo(UserDashboardPanel.this);
        dialog.setLayout(new BorderLayout());
        dialog.getContentPane().setBackground(BACKGROUND_COLOR);

        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(Color.WHITE);
        header.setBorder(new EmptyBorder(20, 24, 16, 24));

        JLabel title = new JLabel("Historial de Streams");
        title.setFont(new Font("Segoe UI", Font.BOLD, 18));
        title.setForeground(TEXT_PRIMARY_COLOR);

        JLabel subtitle = new JLabel("Dispositivo: " + deviceSerial);
        subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        subtitle.setForeground(TEXT_SECONDARY_COLOR);

        JPanel headerText = new JPanel();
        headerText.setOpaque(false);
        headerText.setLayout(new BoxLayout(headerText, BoxLayout.Y_AXIS));
        headerText.add(title);
        headerText.add(Box.createVerticalStrut(4));
        headerText.add(subtitle);

        header.add(headerText, BorderLayout.WEST);
        dialog.add(header, BorderLayout.NORTH);

        JPanel streamsPanel = new JPanel();
        streamsPanel.setLayout(new BoxLayout(streamsPanel, BoxLayout.Y_AXIS));
        streamsPanel.setOpaque(false);
        streamsPanel.setBorder(new EmptyBorder(12, 12, 12, 12));

        if (streams == null || streams.size() == 0) {
            JLabel empty = new JLabel("No hay streams registrados para este dispositivo");
            empty.setFont(new Font("Segoe UI", Font.PLAIN, 14));
            empty.setForeground(TEXT_SECONDARY_COLOR);
            empty.setBorder(new EmptyBorder(40, 20, 40, 20));
            streamsPanel.add(empty);
        } else {
            for (JsonElement element : streams) {
                if (!element.isJsonObject()) continue;
                JsonObject stream = element.getAsJsonObject();

                JPanel streamCard = new JPanel(new BorderLayout(10, 6));
                streamCard.setBackground(Color.WHITE);
                streamCard.setBorder(BorderFactory.createCompoundBorder(
                        BorderFactory.createLineBorder(new Color(229, 234, 243)),
                        new EmptyBorder(12, 14, 12, 14)
                ));

                JLabel startLabel = new JLabel("Inicio: " + safe(stream, "started_at"));
                startLabel.setFont(new Font("Segoe UI", Font.PLAIN, 13));
                startLabel.setForeground(TEXT_PRIMARY_COLOR);

                JLabel endLabel = new JLabel("Fin: " + safe(stream, "ended_at"));
                endLabel.setFont(new Font("Segoe UI", Font.PLAIN, 13));
                endLabel.setForeground(TEXT_SECONDARY_COLOR);

                JPanel info = new JPanel();
                info.setOpaque(false);
                info.setLayout(new BoxLayout(info, BoxLayout.Y_AXIS));
                info.add(startLabel);
                info.add(Box.createVerticalStrut(4));
                info.add(endLabel);

                streamCard.add(info, BorderLayout.CENTER);
                streamsPanel.add(streamCard);
                streamsPanel.add(Box.createVerticalStrut(8));
            }
        }

        JScrollPane scrollPane = new JScrollPane(streamsPanel);
        configureStyledScroll(scrollPane);
        scrollPane.setBorder(null);
        dialog.add(scrollPane, BorderLayout.CENTER);

        JPanel footer = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        footer.setBackground(Color.WHITE);
        footer.setBorder(new EmptyBorder(12, 24, 16, 24));

        JButton closeButton = new JButton("Cerrar");
        closeButton.setFont(new Font("Segoe UI", Font.BOLD, 13));
        closeButton.setForeground(Color.WHITE);
        closeButton.setBackground(PRIMARY_COLOR);
        closeButton.setBorderPainted(false);
        closeButton.setFocusPainted(false);
        closeButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        closeButton.setPreferredSize(new Dimension(100, 36));
        closeButton.addActionListener(e -> dialog.dispose());

        footer.add(closeButton);
        dialog.add(footer, BorderLayout.SOUTH);

        dialog.setVisible(true);
    }

    private void updateMetrics(JsonObject overview, JsonObject metrics) {
        int patients = overview != null && overview.has("total_patients") ? overview.get("total_patients").getAsInt() : 0;
        int careTeams = overview != null && overview.has("total_care_teams") ? overview.get("total_care_teams").getAsInt() : 0;
        int caregivers = overview != null && overview.has("total_caregivers") ? overview.get("total_caregivers").getAsInt() : 0;
        int alerts7d = overview != null && overview.has("alerts_last_7d") ? overview.get("alerts_last_7d").getAsInt() : 0;
        int openAlerts = overview != null && overview.has("open_alerts") ? overview.get("open_alerts").getAsInt() : 0;
        double avgAlerts = metrics != null && metrics.has("avg_alerts_per_patient") ? metrics.get("avg_alerts_per_patient").getAsDouble() : 0.0;

        patientsCard.updateValue(String.valueOf(patients), careTeams + " equipos activos", new double[]{patients, careTeams});
        alertsCard.updateValue(String.valueOf(openAlerts), alerts7d + " alertas en 7d", new double[]{openAlerts, alerts7d, avgAlerts});
        caregiversCard.updateValue(String.valueOf(caregivers), "Promedio alertas/paciente: " + String.format("%.2f", avgAlerts), new double[]{caregivers, alerts7d});
    }

    private void applyMapFilter() {
        TeamOption option = (TeamOption) teamFilter.getSelectedItem();
        if (option == null) {
            mapPanel.updateLocations(mapPatientsData, mapMembersData);
            return;
        }
        if (option.id.equals("all")) {
            mapPanel.updateLocations(mapPatientsData, mapMembersData);
            return;
        }
        JsonArray filteredPatients = new JsonArray();
        for (JsonElement element : mapPatientsData) {
            if (!element.isJsonObject()) continue;
            JsonObject patient = element.getAsJsonObject();
            if (patient.has("care_team") && patient.get("care_team").isJsonObject()) {
                JsonObject team = patient.getAsJsonObject("care_team");
                if (team.has("id") && !team.get("id").isJsonNull() && team.get("id").getAsString().equals(option.id)) {
                    filteredPatients.add(patient);
                }
            }
        }
        JsonArray filteredMembers = new JsonArray();
        for (JsonElement element : mapMembersData) {
            if (!element.isJsonObject()) continue;
            JsonObject member = element.getAsJsonObject();
            if (member.has("care_team") && member.get("care_team").isJsonObject()) {
                JsonObject team = member.getAsJsonObject("care_team");
                if (team.has("id") && !team.get("id").isJsonNull() && team.get("id").getAsString().equals(option.id)) {
                    filteredMembers.add(member);
                }
            }
        }
        mapPanel.updateLocations(filteredPatients, filteredMembers);
    }

    private void fetchMapData() {
        if (currentOrg == null) return;
        mapStatusLabel.setText("Recargando ubicaciones...");

        Map<String, String> params = Map.of("org_id", currentOrg.getOrgId());
        CompletableFuture<JsonObject> caregiverFuture = apiClient.getCaregiverPatientLocationsAsync(token, params);
        CompletableFuture<JsonObject> careTeamFuture = apiClient.getCareTeamLocationsAsync(token, params);

        CompletableFuture.allOf(caregiverFuture, careTeamFuture)
                .thenApplyAsync(ignored -> {
                    JsonArray patients = getArray(getData(caregiverFuture.join()), "patients");
                    JsonArray members = getArray(getData(careTeamFuture.join()), "members");
                    return new MapPayload(patients, members);
                })
                .thenAccept(payload -> SwingUtilities.invokeLater(() -> {
                    mapPatientsData = payload.patients != null ? payload.patients : new JsonArray();
                    mapMembersData = payload.members != null ? payload.members : new JsonArray();
                    applyMapFilter();
                    snackbar.accept("Mapa actualizado", true);
                    mapStatusLabel.setText("Datos sincronizados");
                }))
                .exceptionally(ex -> {
                    SwingUtilities.invokeLater(() -> mapStatusLabel.setText("Error al recargar"));
                    handleAsyncException(ex, "Error al recargar mapa");
                    return null;
                });
    }

    private void handleAsyncException(Throwable throwable, String fallbackMessage) {
        Throwable cause = unwrapCompletionException(throwable);
        if (cause instanceof ApiException apiException) {
            SwingUtilities.invokeLater(() -> apiErrorHandler.accept(apiException));
            return;
        }
        String message = (cause != null && cause.getMessage() != null && !cause.getMessage().isBlank())
                ? cause.getMessage()
                : fallbackMessage;
        SwingUtilities.invokeLater(() -> snackbar.accept(message, false));
    }

    private Throwable unwrapCompletionException(Throwable throwable) {
        if (throwable instanceof CompletionException completion && completion.getCause() != null) {
            return completion.getCause();
        }
        if (throwable instanceof ExecutionException execution && execution.getCause() != null) {
            return execution.getCause();
        }
        return throwable;
    }

    private JPanel createEmptyState(String message, String actionLabel, Runnable action) {
        JPanel panel = new JPanel();
        panel.setOpaque(false);
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        JLabel label = new JLabel(message);
        label.setAlignmentX(Component.CENTER_ALIGNMENT);
        label.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        label.setForeground(new Color(120, 130, 140));
        panel.add(label);
        if (action != null) {
            String buttonLabel = actionLabel != null && !actionLabel.isBlank() ? actionLabel : "Actualizar";
            JButton button = new JButton(buttonLabel);
            button.setAlignmentX(Component.CENTER_ALIGNMENT);
            button.addActionListener(e -> action.run());
            panel.add(Box.createVerticalStrut(8));
            panel.add(button);
        }
        return panel;
    }

    private String safe(JsonElement parent, String property) {
        if (parent == null || parent.isJsonNull()) {
            return "-";
        }
        JsonObject object = parent.getAsJsonObject();
        JsonElement element = object.get(property);
        return element == null || element.isJsonNull() ? "-" : element.getAsString();
    }

    private JsonObject getData(JsonObject response) {
        if (response == null || response.isJsonNull()) {
            return new JsonObject();
        }
        JsonElement data = response.get("data");
        return data != null && data.isJsonObject() ? data.getAsJsonObject() : new JsonObject();
    }
    
    private JsonObject createEmptyResponse() {
        JsonObject response = new JsonObject();
        JsonObject data = new JsonObject();
        data.add("care_teams", new JsonArray());
        response.add("data", data);
        response.addProperty("status", "success");
        response.addProperty("message", "Sin datos");
        return response;
    }

    private String safe(JsonObject object, String property) {
        if (object == null || object.isJsonNull()) {
            return "-";
        }
        JsonElement element = object.get(property);
        return element == null || element.isJsonNull() ? "-" : element.getAsString();
    }

    private JsonArray getArray(JsonObject object, String property) {
        if (object == null || object.isJsonNull()) {
            return new JsonArray();
        }
        JsonElement element = object.get(property);
        return element != null && element.isJsonArray() ? element.getAsJsonArray() : new JsonArray();
    }

    private static class MapPayload {
        final JsonArray patients;
        final JsonArray members;

        MapPayload(JsonArray patients, JsonArray members) {
            this.patients = patients;
            this.members = members;
        }
    }

    private static class DeviceReloadResult {
        final JsonArray activeDevices;
        final JsonArray disconnectedDevices;

        DeviceReloadResult(JsonArray activeDevices, JsonArray disconnectedDevices) {
            this.activeDevices = activeDevices;
            this.disconnectedDevices = disconnectedDevices;
        }
    }

    private static class TeamOption {
        private final String id;
        private final String name;

        TeamOption(String id, String name) {
            this.id = id;
            this.name = name;
        }

        @Override
        public String toString() {
            return name;
        }
    }

    private static class DeviceSummary {
        int total = 0;
        int active = 0;
        final Map<String, TeamDeviceStats> teams = new LinkedHashMap<>();
    }

    private static class TeamDeviceStats {
        final String teamId;
        final String teamName;
        int total;
        int active;
        int disconnected;

        TeamDeviceStats(String teamId, String teamName) {
            this.teamId = teamId;
            this.teamName = teamName;
        }
    }

    private static class DashboardBundle {
        JsonObject dashboard;
        JsonObject metrics;
        JsonObject careTeams;
        JsonObject careTeamPatients;
        JsonObject caregiverPatients;
        JsonObject careTeamLocations;
        JsonObject caregiverLocations;
    }

    private static class MetricCard extends JPanel {
        private final JLabel valueLabel = new JLabel("--");
        private final JLabel subtitleLabel = new JLabel(" ");
        private final MiniSparklinePanel sparklinePanel = new MiniSparklinePanel();

        MetricCard(String title, Color accent) {
            setLayout(new BorderLayout(8, 8));
            setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(NEUTRAL_BORDER_COLOR, 1),
                new EmptyBorder(16, 20, 16, 20)
            ));
            setBackground(CARD_BACKGROUND);
            
            // Título de la métrica
            JLabel titleLabel = new JLabel(title);
            titleLabel.setFont(METRIC_DESC_FONT);
            titleLabel.setForeground(TEXT_SECONDARY_COLOR);
            add(titleLabel, BorderLayout.NORTH);

            // Valor principal grande
            valueLabel.setFont(METRIC_VALUE_FONT);
            valueLabel.setForeground(accent);
            add(valueLabel, BorderLayout.CENTER);

            // Panel inferior con subtítulo y sparkline
            JPanel bottomPanel = new JPanel(new BorderLayout());
            bottomPanel.setOpaque(false);
            
            subtitleLabel.setFont(CAPTION_FONT);
            subtitleLabel.setForeground(TEXT_SECONDARY_COLOR);
            bottomPanel.add(subtitleLabel, BorderLayout.WEST);
            
            sparklinePanel.setPreferredSize(new Dimension(100, 40));
            sparklinePanel.setOpaque(false);
            bottomPanel.add(sparklinePanel, BorderLayout.EAST);
            
            add(bottomPanel, BorderLayout.SOUTH);
        }

        void updateValue(String value, String subtitle, double[] trend) {
            valueLabel.setText(value);
            subtitleLabel.setText(subtitle != null && !subtitle.isBlank() ? subtitle : " ");
            sparklinePanel.setValues(trend);
        }
    }

    private static class MiniSparklinePanel extends JPanel {
        private double[] values = new double[0];

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            if (values.length < 2) {
                return;
            }
            
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            
            int width = getWidth();
            int height = getHeight();
            
            // Calcular min/max para normalización
            double max = Double.MIN_VALUE;
            double min = Double.MAX_VALUE;
            for (double v : values) {
                max = Math.max(max, v);
                min = Math.min(min, v);
            }
            double diff = Math.max(1, max - min);
            
            int padding = 2;
            int graphWidth = width - padding * 2;
            int graphHeight = height - padding * 2;
            int points = values.length;
            
            // Calcular puntos
            int[] xPoints = new int[points];
            int[] yPoints = new int[points];
            for (int i = 0; i < points; i++) {
                xPoints[i] = padding + (i * graphWidth) / (points - 1);
                double normalized = (values[i] - min) / diff;
                yPoints[i] = padding + graphHeight - (int) (normalized * graphHeight);
            }

            // Área bajo la curva con gradiente
            g2.setColor(new Color(PRIMARY_COLOR.getRed(), PRIMARY_COLOR.getGreen(), PRIMARY_COLOR.getBlue(), 40));
            int[] areaXPoints = new int[points + 2];
            int[] areaYPoints = new int[points + 2];
            System.arraycopy(xPoints, 0, areaXPoints, 0, points);
            areaXPoints[points] = xPoints[points - 1];
            areaXPoints[points + 1] = xPoints[0];
            System.arraycopy(yPoints, 0, areaYPoints, 0, points);
            areaYPoints[points] = height - padding;
            areaYPoints[points + 1] = height - padding;
            g2.fillPolygon(areaXPoints, areaYPoints, points + 2);
            
            // Línea de tendencia
            g2.setStroke(new BasicStroke(2.5f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            g2.setColor(PRIMARY_COLOR);
            for (int i = 0; i < points - 1; i++) {
                g2.drawLine(xPoints[i], yPoints[i], xPoints[i + 1], yPoints[i + 1]);
            }
            
            // Puntos en la línea
            g2.setColor(PRIMARY_COLOR);
            for (int i = 0; i < points; i++) {
                g2.fillOval(xPoints[i] - 3, yPoints[i] - 3, 6, 6);
            }
            
            g2.dispose();
        }

        void setValues(double[] values) {
            this.values = values != null ? values : new double[0];
            repaint();
        }
    }
}
