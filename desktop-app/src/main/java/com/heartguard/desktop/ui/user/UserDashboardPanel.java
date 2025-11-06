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
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Panel central del dashboard de usuario staff.
 */
public class UserDashboardPanel extends JPanel {
    private final ApiClient apiClient;
    private final String token;
    private final Consumer<ApiException> apiErrorHandler;
    private final BiConsumer<String, Boolean> snackbar;

    private OrgMembership currentOrg;

    private final JPanel metricsPanel = new JPanel(new GridLayout(1, 4, 16, 0));
    private final MetricCard patientsCard = new MetricCard("Pacientes activos", new Color(30, 136, 229));
    private final MetricCard alertsCard = new MetricCard("Alertas abiertas", new Color(239, 83, 80));
    private final MetricCard devicesCard = new MetricCard("Dispositivos conectados", new Color(0, 172, 193));
    private final MetricCard caregiversCard = new MetricCard("Caregivers disponibles", new Color(76, 175, 80));

    private final UserMapPanel mapPanel = new UserMapPanel();
    private final JComboBox<TeamOption> teamFilter = new JComboBox<>();
    private final JButton refreshMapButton = new JButton("🔄");
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
        setLayout(new BorderLayout());
        setBackground(new Color(247, 250, 253));
        setBorder(new EmptyBorder(16, 24, 24, 24));

        metricsPanel.setOpaque(false);
        metricsPanel.add(patientsCard);
        metricsPanel.add(alertsCard);
        metricsPanel.add(devicesCard);
        metricsPanel.add(caregiversCard);
        add(metricsPanel, BorderLayout.NORTH);

        JPanel centerPanel = new JPanel(new BorderLayout(0, 16));
        centerPanel.setOpaque(false);
        centerPanel.add(createMapSection(), BorderLayout.CENTER);
        centerPanel.add(createModulesSection(), BorderLayout.SOUTH);
        add(centerPanel, BorderLayout.CENTER);
    }

    private JPanel createMapSection() {
        JPanel wrapper = new JPanel(new BorderLayout(0, 8));
        wrapper.setOpaque(false);

        JPanel filters = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        filters.setOpaque(false);
        JLabel mapTitle = new JLabel("Mapa de ubicaciones clínicas");
        mapTitle.setFont(new Font("Segoe UI", Font.BOLD, 16));
        filters.add(mapTitle);

        teamFilter.setPreferredSize(new Dimension(240, 28));
        teamFilter.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        teamFilter.addActionListener(e -> applyMapFilter());
        filters.add(new JLabel("Equipo:"));
        filters.add(teamFilter);

        refreshMapButton.setToolTipText("Recargar ubicaciones");
        refreshMapButton.setBorder(BorderFactory.createEmptyBorder(4, 10, 4, 10));
        refreshMapButton.setFocusable(false);
        refreshMapButton.addActionListener(e -> fetchMapData());
        filters.add(refreshMapButton);
        filters.add(mapStatusLabel);
        mapStatusLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        mapStatusLabel.setForeground(new Color(120, 130, 140));

        wrapper.add(filters, BorderLayout.NORTH);

        JPanel mapContainer = new JPanel(new BorderLayout());
        mapContainer.setBorder(new EmptyBorder(12, 12, 12, 12));
        mapContainer.setBackground(Color.WHITE);
        mapContainer.add(mapPanel, BorderLayout.CENTER);
        wrapper.add(mapContainer, BorderLayout.CENTER);

        return wrapper;
    }

    private JPanel createModulesSection() {
        modulesTabs.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        modulesTabs.addTab("Pacientes", createPatientsTab());
        modulesTabs.addTab("Care-teams", createCareTeamsTab());
        modulesTabs.addTab("Dispositivos", createDevicesTab());
        modulesTabs.addTab("Alertas", createAlertsTab());

        JPanel panel = new JPanel(new BorderLayout());
        panel.setOpaque(false);
        panel.add(modulesTabs, BorderLayout.CENTER);
        return panel;
    }

    private JPanel createPatientsTab() {
        JPanel container = new JPanel(new BorderLayout());
        container.setOpaque(false);

        JPanel header = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 8));
        header.setOpaque(false);
        JLabel title = new JLabel("Pacientes en seguimiento");
        title.setFont(new Font("Segoe UI", Font.BOLD, 15));
        header.add(title);

        JToggleButton myPatientsToggle = new JToggleButton("Mis pacientes");
        JToggleButton teamPatientsToggle = new JToggleButton("Pacientes por equipos");
        myPatientsToggle.setSelected(true);
        patientsToggleGroup.add(myPatientsToggle);
        patientsToggleGroup.add(teamPatientsToggle);
        myPatientsToggle.addActionListener(e -> patientsCardLayout.show(patientsContainer, "mine"));
        teamPatientsToggle.addActionListener(e -> patientsCardLayout.show(patientsContainer, "teams"));
        header.add(myPatientsToggle);
        header.add(teamPatientsToggle);
        header.add(patientsStatusLabel);
        patientsStatusLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        patientsStatusLabel.setForeground(new Color(120, 130, 140));

        container.add(header, BorderLayout.NORTH);

        myPatientsPanel.setLayout(new BoxLayout(myPatientsPanel, BoxLayout.Y_AXIS));
        myPatientsPanel.setOpaque(false);
        teamPatientsPanel.setLayout(new BoxLayout(teamPatientsPanel, BoxLayout.Y_AXIS));
        teamPatientsPanel.setOpaque(false);

        JScrollPane myScroll = new JScrollPane(myPatientsPanel);
        configureScroll(myScroll);
        JScrollPane teamScroll = new JScrollPane(teamPatientsPanel);
        configureScroll(teamScroll);

        patientsContainer.add(myScroll, "mine");
        patientsContainer.add(teamScroll, "teams");
        container.add(patientsContainer, BorderLayout.CENTER);
        patientsCardLayout.show(patientsContainer, "mine");
        return container;
    }

    private JPanel createCareTeamsTab() {
        JPanel container = new JPanel(new BorderLayout());
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(8, 8, 8, 8));

        careTeamList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        careTeamList.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        careTeamList.addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                TeamOption option = careTeamList.getSelectedValue();
                if (option != null) {
                    loadCareTeamDetail(option);
                }
            }
        });
        JScrollPane listScroll = new JScrollPane(careTeamList);
        listScroll.setPreferredSize(new Dimension(260, 0));
        configureScroll(listScroll);

        careTeamDetailPanel.setOpaque(false);
        careTeamDetailPanel.setBorder(new EmptyBorder(12, 16, 12, 16));
        careTeamStatusLabel.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        careTeamStatusLabel.setForeground(new Color(120, 130, 140));
        careTeamDetailPanel.add(careTeamStatusLabel, BorderLayout.NORTH);

        membersListPanel.setLayout(new BoxLayout(membersListPanel, BoxLayout.Y_AXIS));
        membersListPanel.setOpaque(false);
        JScrollPane membersScroll = new JScrollPane(membersListPanel);
        configureScroll(membersScroll);
        membersScroll.setBorder(BorderFactory.createTitledBorder("Miembros del equipo"));

        JTabbedPane deviceTabs = new JTabbedPane();
        activeDevicesPanel.setLayout(new BoxLayout(activeDevicesPanel, BoxLayout.Y_AXIS));
        activeDevicesPanel.setOpaque(false);
        disconnectedDevicesPanel.setLayout(new BoxLayout(disconnectedDevicesPanel, BoxLayout.Y_AXIS));
        disconnectedDevicesPanel.setOpaque(false);
        JScrollPane activeScroll = new JScrollPane(activeDevicesPanel);
        JScrollPane disconnectedScroll = new JScrollPane(disconnectedDevicesPanel);
        configureScroll(activeScroll);
        configureScroll(disconnectedScroll);
        deviceTabs.addTab("Activos", activeScroll);
        deviceTabs.addTab("Desconectados", disconnectedScroll);

        JPanel detailBody = new JPanel();
        detailBody.setOpaque(false);
        detailBody.setLayout(new BoxLayout(detailBody, BoxLayout.Y_AXIS));
        detailBody.add(membersScroll);
        detailBody.add(Box.createVerticalStrut(12));
        detailBody.add(deviceTabs);
        careTeamDetailPanel.add(detailBody, BorderLayout.CENTER);

        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, listScroll, careTeamDetailPanel);
        splitPane.setDividerLocation(260);
        container.add(splitPane, BorderLayout.CENTER);
        return container;
    }

    private JPanel createDevicesTab() {
        JPanel container = new JPanel(new BorderLayout());
        container.setOpaque(false);
        devicesSummaryPanel.setLayout(new BoxLayout(devicesSummaryPanel, BoxLayout.Y_AXIS));
        devicesSummaryPanel.setOpaque(false);
        devicesSummaryLabel.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        devicesSummaryLabel.setForeground(new Color(120, 130, 140));
        devicesSummaryPanel.add(devicesSummaryLabel);
        container.add(devicesSummaryPanel, BorderLayout.CENTER);
        return container;
    }

    private JPanel createAlertsTab() {
        JPanel container = new JPanel(new BorderLayout());
        container.setOpaque(false);
        alertsPanel.setLayout(new BoxLayout(alertsPanel, BoxLayout.Y_AXIS));
        alertsPanel.setOpaque(false);
        JScrollPane scrollPane = new JScrollPane(alertsPanel);
        configureScroll(scrollPane);
        container.add(scrollPane, BorderLayout.CENTER);
        alertsStatusLabel.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        alertsStatusLabel.setForeground(new Color(120, 130, 140));
        container.add(alertsStatusLabel, BorderLayout.NORTH);
        return container;
    }

    private void configureScroll(JScrollPane scrollPane) {
        scrollPane.setBorder(BorderFactory.createEmptyBorder());
        scrollPane.getViewport().setBackground(Color.WHITE);
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
        mapPanel.clear();
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
        SwingWorker<DashboardBundle, Void> worker = new SwingWorker<>() {
            @Override
            protected DashboardBundle doInBackground() throws Exception {
                DashboardBundle bundle = new DashboardBundle();
                bundle.dashboard = apiClient.getOrganizationDashboard(token, currentOrg.getOrgId());
                bundle.metrics = apiClient.getOrganizationMetrics(token, currentOrg.getOrgId());
                bundle.careTeams = apiClient.getOrganizationCareTeams(token, currentOrg.getOrgId());
                bundle.careTeamPatients = apiClient.getOrganizationCareTeamPatients(token, currentOrg.getOrgId());
                bundle.caregiverPatients = apiClient.getCaregiverPatients(token);

                Map<String, String> mapParams = new HashMap<>();
                mapParams.put("org_id", currentOrg.getOrgId());
                bundle.careTeamLocations = apiClient.getCareTeamLocations(token, mapParams);

                Map<String, String> caregiverParams = new HashMap<>();
                caregiverParams.put("org_id", currentOrg.getOrgId());
                bundle.caregiverLocations = apiClient.getCaregiverPatientLocations(token, caregiverParams);
                return bundle;
            }

            @Override
            protected void done() {
                try {
                    DashboardBundle bundle = get();
                    renderDashboard(bundle);
                } catch (Exception ex) {
                    if (ex.getCause() instanceof ApiException apiException) {
                        apiErrorHandler.accept(apiException);
                    } else {
                        snackbar.accept(ex.getMessage(), false);
                    }
                }
            }
        };
        worker.execute();
    }

    private void renderDashboard(DashboardBundle bundle) {
        JsonObject dashboardData = getData(bundle.dashboard);
        JsonObject metricsData = getData(bundle.metrics);
        JsonObject overview = dashboardData.has("overview") && dashboardData.get("overview").isJsonObject()
                ? dashboardData.getAsJsonObject("overview")
                : new JsonObject();
        JsonObject metrics = metricsData.has("metrics") && metricsData.get("metrics").isJsonObject()
                ? metricsData.getAsJsonObject("metrics")
                : new JsonObject();
        updateMetrics(overview, metrics);

        careTeamListModel.clear();
        teamFilter.removeAllItems();
        List<TeamOption> teamOptions = new ArrayList<>();
        TeamOption all = new TeamOption("all", "Todos los equipos");
        teamFilter.addItem(all);
        careTeamsArray = getData(bundle.careTeams).getAsJsonArray("care_teams");
        JsonArray careTeams = careTeamsArray;
        if (careTeams != null) {
            for (JsonElement element : careTeams) {
                if (!element.isJsonObject()) continue;
                JsonObject team = element.getAsJsonObject();
                String id = team.has("id") && !team.get("id").isJsonNull() ? team.get("id").getAsString() : null;
                if (id == null) {
                    continue;
                }
                String name = team.has("name") && !team.get("name").isJsonNull() ? team.get("name").getAsString() : "Equipo";
                TeamOption option = new TeamOption(id, name);
                teamOptions.add(option);
                teamFilter.addItem(option);
                teamListModel.addElement(option);
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
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(Color.WHITE);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(229, 234, 243)),
                new EmptyBorder(12, 14, 12, 14)
        ));

        JLabel name = new JLabel(patient.get("name").getAsString());
        name.setFont(new Font("Segoe UI", Font.BOLD, 14));
        JLabel org = new JLabel("Organización: " + safe(patient.get("organization"), "name"));
        org.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        org.setForeground(new Color(120, 130, 140));
        JLabel risk = new JLabel("Riesgo: " + safe(patient.get("risk_level"), "label"));
        risk.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        risk.setForeground(new Color(120, 130, 140));

        JPanel info = new JPanel();
        info.setOpaque(false);
        info.setLayout(new BoxLayout(info, BoxLayout.Y_AXIS));
        info.add(name);
        info.add(Box.createVerticalStrut(4));
        info.add(org);
        info.add(risk);

        JButton details = new JButton("Ver detalle");
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

            JLabel status = new JLabel("🟢 " + stats.active + " activos · 🔴 " + stats.disconnected + " desconectados");
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
                JLabel label = new JLabel(member.get("name").getAsString() + " · " + safe(member.get("role"), "label"));
                label.setFont(new Font("Segoe UI", Font.PLAIN, 13));
                membersListPanel.add(label);
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
            JPanel card = new JPanel(new BorderLayout());
            card.setBackground(active ? new Color(236, 248, 240) : new Color(253, 236, 234));
            card.setBorder(new EmptyBorder(10, 12, 10, 12));
            JLabel title = new JLabel(device.get("serial").getAsString() + " · " + safe(device.get("type"), "label"));
            title.setFont(new Font("Segoe UI", Font.BOLD, 13));
            JLabel subtitle = new JLabel("Paciente: " + safe(device.get("owner"), "name"));
            subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            subtitle.setForeground(new Color(120, 130, 140));
            JLabel status = new JLabel(active ? "🟢 Activo" : "🔴 Desconectado");
            status.setFont(new Font("Segoe UI", Font.BOLD, 12));
            JPanel info = new JPanel();
            info.setOpaque(false);
            info.setLayout(new BoxLayout(info, BoxLayout.Y_AXIS));
            info.add(title);
            info.add(subtitle);
            info.add(status);
            JButton streamsButton = new JButton("Ver streams");
            streamsButton.addActionListener(e -> openDeviceStreams(option, device));
            card.add(info, BorderLayout.CENTER);
            card.add(streamsButton, BorderLayout.EAST);
            panel.add(card);
            panel.add(Box.createVerticalStrut(8));
        }
    }

    private void reloadDevices(TeamOption option) {
        SwingWorker<JsonArray, Void> worker = new SwingWorker<>() {
            @Override
            protected JsonArray doInBackground() throws Exception {
                JsonObject response = apiClient.getCareTeamDevices(token, currentOrg.getOrgId(), option.id);
                JsonArray devices = getArray(getData(response), "devices");
                devicesCache.put(option.id, devices);
                JsonObject disconnectedResponse = apiClient.getCareTeamDisconnectedDevices(token, currentOrg.getOrgId(), option.id);
                JsonArray disconnected = getArray(getData(disconnectedResponse), "devices");
                disconnectedDevicesCache.put(option.id, disconnected);
                return devices;
            }

            @Override
            protected void done() {
                try {
                    JsonArray devices = get();
                    fillDevicePanel(activeDevicesPanel, devices, true, option);
                    fillDevicePanel(disconnectedDevicesPanel, disconnectedDevicesCache.get(option.id), false, option);
                } catch (Exception ex) {
                    if (ex.getCause() instanceof ApiException apiException) {
                        apiErrorHandler.accept(apiException);
                    }
                }
            }
        };
        worker.execute();
    }

    private void openDeviceStreams(TeamOption option, JsonObject device) {
        SwingWorker<JsonArray, Void> worker = new SwingWorker<>() {
            @Override
            protected JsonArray doInBackground() throws Exception {
                JsonObject response = apiClient.getCareTeamDeviceStreams(token, currentOrg.getOrgId(), option.id, device.get("id").getAsString());
                return getArray(getData(response), "streams");
            }

            @Override
            protected void done() {
                try {
                    JsonArray streams = get();
                    JDialog dialog = new JDialog((Frame) SwingUtilities.getWindowAncestor(UserDashboardPanel.this), "Streams del dispositivo", true);
                    dialog.setSize(480, 360);
                    dialog.setLocationRelativeTo(UserDashboardPanel.this);
                    JPanel panel = new JPanel();
                    panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
                    if (streams == null || streams.size() == 0) {
                        panel.add(new JLabel("No hay streams registrados"));
                    } else {
                        for (JsonElement element : streams) {
                            if (!element.isJsonObject()) continue;
                            JsonObject stream = element.getAsJsonObject();
                            JLabel label = new JLabel("Inicio: " + safe(stream, "started_at") + " · Fin: " + safe(stream, "ended_at"));
                            label.setBorder(new EmptyBorder(6, 6, 6, 6));
                            panel.add(label);
                        }
                    }
                    JScrollPane scrollPane = new JScrollPane(panel);
                    configureScroll(scrollPane);
                    dialog.add(scrollPane);
                    dialog.setVisible(true);
                } catch (Exception ex) {
                    if (ex.getCause() instanceof ApiException apiException) {
                        apiErrorHandler.accept(apiException);
                    }
                }
            }
        };
        worker.execute();
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
                if (team.get("id").getAsString().equals(option.id)) {
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
                if (team.get("id").getAsString().equals(option.id)) {
                    filteredMembers.add(member);
                }
            }
        }
        mapPanel.updateLocations(filteredPatients, filteredMembers);
    }

    private void fetchMapData() {
        if (currentOrg == null) return;
        mapStatusLabel.setText("Recargando ubicaciones...");
        SwingWorker<Void, Void> worker = new SwingWorker<>() {
            JsonArray patients;
            JsonArray members;

            @Override
            protected Void doInBackground() throws Exception {
                Map<String, String> params = new HashMap<>();
                params.put("org_id", currentOrg.getOrgId());
                JsonObject caregiver = apiClient.getCaregiverPatientLocations(token, params);
                patients = getArray(getData(caregiver), "patients");
                JsonObject careTeam = apiClient.getCareTeamLocations(token, params);
                members = getArray(getData(careTeam), "members");
                return null;
            }

            @Override
            protected void done() {
                try {
                    get();
                    mapPatientsData = patients != null ? patients : new JsonArray();
                    mapMembersData = members != null ? members : new JsonArray();
                    applyMapFilter();
                    snackbar.accept("Mapa actualizado", true);
                    mapStatusLabel.setText("Datos sincronizados");
                } catch (Exception ex) {
                    mapStatusLabel.setText("Error al recargar");
                    if (ex.getCause() instanceof ApiException apiException) {
                        apiErrorHandler.accept(apiException);
                    }
                }
            }
        };
        worker.execute();
    }

    private JPanel createEmptyState(String message, String actionLabel, Runnable action) {
        JPanel panel = new JPanel();
        panel.setOpaque(false);
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        JLabel icon = new JLabel("✨");
        icon.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 28));
        icon.setAlignmentX(Component.CENTER_ALIGNMENT);
        JLabel label = new JLabel(message);
        label.setAlignmentX(Component.CENTER_ALIGNMENT);
        label.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        label.setForeground(new Color(120, 130, 140));
        panel.add(icon);
        panel.add(Box.createVerticalStrut(8));
        panel.add(label);
        if (action != null) {
            String label = actionLabel != null && !actionLabel.isBlank() ? actionLabel : "Actualizar";
            JButton button = new JButton(label);
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
            setLayout(new BorderLayout());
            setBorder(BorderFactory.createEmptyBorder(12, 18, 12, 18));
            setBackground(Color.WHITE);
            JLabel titleLabel = new JLabel(title);
            titleLabel.setFont(new Font("Segoe UI", Font.PLAIN, 13));
            titleLabel.setForeground(new Color(110, 120, 130));
            add(titleLabel, BorderLayout.NORTH);

            valueLabel.setFont(new Font("Segoe UI", Font.BOLD, 24));
            valueLabel.setForeground(accent);
            add(valueLabel, BorderLayout.CENTER);

            subtitleLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
            subtitleLabel.setForeground(new Color(120, 130, 140));
            add(subtitleLabel, BorderLayout.SOUTH);

            add(sparklinePanel, BorderLayout.EAST);
            sparklinePanel.setPreferredSize(new Dimension(90, 48));
        }

        void updateValue(String value, String subtitle, double[] trend) {
            valueLabel.setText(value);
            subtitleLabel.setText(subtitle);
            sparklinePanel.setValues(trend);
        }
    }

    private static class MiniSparklinePanel extends JPanel {
        private double[] values = new double[0];

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            int width = getWidth();
            int height = getHeight();
            g2.setColor(new Color(230, 240, 250));
            g2.fillRoundRect(0, 0, width, height, 16, 16);

            if (values.length < 2) {
                g2.dispose();
                return;
            }
            double max = Double.MIN_VALUE;
            double min = Double.MAX_VALUE;
            for (double v : values) {
                max = Math.max(max, v);
                min = Math.min(min, v);
            }
            double diff = Math.max(1, max - min);
            int padding = 8;
            int graphWidth = width - padding * 2;
            int graphHeight = height - padding * 2;
            int points = values.length;
            int step = graphWidth / (points - 1);

            int[] xPoints = new int[points];
            int[] yPoints = new int[points];
            for (int i = 0; i < points; i++) {
                xPoints[i] = padding + i * step;
                double normalized = (values[i] - min) / diff;
                yPoints[i] = padding + graphHeight - (int) (normalized * graphHeight);
            }

            g2.setColor(new Color(33, 150, 243, 120));
            for (int i = 0; i < points - 1; i++) {
                g2.fillPolygon(new int[]{xPoints[i], xPoints[i + 1], xPoints[i + 1], xPoints[i]},
                        new int[]{yPoints[i], yPoints[i + 1], padding + graphHeight, padding + graphHeight}, 4);
            }
            g2.setStroke(new BasicStroke(2f));
            g2.setColor(new Color(33, 150, 243));
            for (int i = 0; i < points - 1; i++) {
                g2.drawLine(xPoints[i], yPoints[i], xPoints[i + 1], yPoints[i + 1]);
            }
            g2.dispose();
        }

        void setValues(double[] values) {
            this.values = values != null ? values : new double[0];
            repaint();
        }
    }
}
