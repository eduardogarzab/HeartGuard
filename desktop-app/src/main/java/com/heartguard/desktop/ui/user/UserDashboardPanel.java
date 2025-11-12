package com.heartguard.desktop.ui.user;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.user.OrgMembership;
import com.heartguard.desktop.ui.components.AvatarPanel;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
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
    private static final Color BORDER_COLOR = new Color(226, 232, 240);
    private static final Color NEUTRAL_BORDER_COLOR = new Color(225, 231, 238);
    private static final Color SUCCESS_COLOR = new Color(46, 204, 113);
    private static final Color WARNING_COLOR = new Color(255, 179, 0);
    private static final Color INFO_COLOR = new Color(155, 89, 182);
    private static final Color DANGER_COLOR = new Color(231, 76, 60);

    // Instancia de Gson para serialización JSON
    private static final Gson GSON = new GsonBuilder().create();

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

    private final EmbeddedMapPanel mapPanel = new EmbeddedMapPanel();
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
        setLayout(new BorderLayout(0, 24));
        setBackground(BACKGROUND_COLOR);
        setBorder(new EmptyBorder(32, 32, 32, 32));

        // Panel principal con ancho máximo y centrado
        JPanel mainPanel = new JPanel();
        mainPanel.setOpaque(false);
        mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
        mainPanel.setMaximumSize(new Dimension(1400, Integer.MAX_VALUE)); // Ancho máximo de 1400px
        mainPanel.setAlignmentX(Component.CENTER_ALIGNMENT);

        // Panel de métricas superior con ancho máximo
        JPanel metricsWrapper = new JPanel(new BorderLayout());
        metricsWrapper.setOpaque(false);
        metricsWrapper.setMaximumSize(new Dimension(1400, Integer.MAX_VALUE));
        metricsWrapper.setAlignmentX(Component.CENTER_ALIGNMENT);
        metricsWrapper.add(createMetricsPanel(), BorderLayout.CENTER);

        mainPanel.add(metricsWrapper);
        mainPanel.add(Box.createVerticalStrut(24));

        // Panel central con mapa y módulos con ancho máximo
        JPanel contentPanel = new JPanel();
        contentPanel.setOpaque(false);
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setMaximumSize(new Dimension(1400, Integer.MAX_VALUE));
        contentPanel.setAlignmentX(Component.CENTER_ALIGNMENT);

        contentPanel.add(createMapSection());
        contentPanel.add(Box.createVerticalStrut(20));
        contentPanel.add(createModulesSection());

        mainPanel.add(contentPanel);

        // Wrapper para centrar el panel principal
        JPanel centerWrapper = new JPanel(new GridBagLayout());
        centerWrapper.setOpaque(false);
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.NONE;
        centerWrapper.add(mainPanel, gbc);

        add(centerWrapper, BorderLayout.CENTER);
    }

    private JPanel createMetricsPanel() {
        JPanel wrapper = new JPanel(new BorderLayout());
        wrapper.setOpaque(false);
        wrapper.setBorder(new EmptyBorder(0, 0, 16, 0));
        wrapper.setMaximumSize(new Dimension(1400, Integer.MAX_VALUE));

        // Header de métricas
        JPanel header = new JPanel(new BorderLayout());
        header.setOpaque(false);
        header.setBorder(new EmptyBorder(0, 0, 16, 0));

        JLabel metricsTitle = new JLabel("Resumen General");
        metricsTitle.setFont(new Font("Segoe UI", Font.BOLD, 20));
        metricsTitle.setForeground(TEXT_PRIMARY_COLOR);
        header.add(metricsTitle, BorderLayout.WEST);

        wrapper.add(header, BorderLayout.NORTH);

        // Panel de métricas con ancho máximo y centrado
        JPanel metricsContainer = new JPanel();
        metricsContainer.setOpaque(false);
        metricsContainer.setLayout(new BoxLayout(metricsContainer, BoxLayout.X_AXIS));
        metricsContainer.setMaximumSize(new Dimension(1400, Integer.MAX_VALUE));

        // Crear tarjetas de métricas con mejor estilo
        metricsContainer.add(createModernMetricCard("Pacientes activos", PRIMARY_COLOR, patientsCard));
        metricsContainer.add(Box.createHorizontalStrut(20));
        metricsContainer.add(createModernMetricCard("Alertas abiertas", DANGER_COLOR, alertsCard));
        metricsContainer.add(Box.createHorizontalStrut(20));
        metricsContainer.add(createModernMetricCard("Dispositivos activos", ACCENT_COLOR, devicesCard));
        metricsContainer.add(Box.createHorizontalStrut(20));
        metricsContainer.add(createModernMetricCard("Caregivers activos", SUCCESS_COLOR, caregiversCard));

        // Wrapper para centrar las métricas
        JPanel centerMetrics = new JPanel(new GridBagLayout());
        centerMetrics.setOpaque(false);
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.weightx = 1.0;
        gbc.fill = GridBagConstraints.NONE;
        centerMetrics.add(metricsContainer, gbc);

        wrapper.add(centerMetrics, BorderLayout.CENTER);
        return wrapper;
    }

    private JPanel createModernMetricCard(String title, Color accentColor, MetricCard metricCard) {
        JPanel wrapper = new JPanel(new BorderLayout());
        wrapper.setBackground(CARD_BACKGROUND);
        wrapper.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(BORDER_COLOR, 1),
            new EmptyBorder(24, 24, 24, 24)
        ));

        // Título de la métrica
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Segoe UI", Font.BOLD, 14));
        titleLabel.setForeground(TEXT_SECONDARY_COLOR);
        wrapper.add(titleLabel, BorderLayout.NORTH);

        // Valor principal
        wrapper.add(metricCard, BorderLayout.CENTER);

        return wrapper;
    }

    private JPanel createMapSection() {
        JPanel wrapper = new JPanel(new BorderLayout(0, 16));
        wrapper.setOpaque(false);

        // Header moderno del mapa
        JPanel header = new JPanel();
        header.setOpaque(false);
        header.setLayout(new BoxLayout(header, BoxLayout.Y_AXIS));
        header.setBorder(new EmptyBorder(0, 0, 16, 0));

        // Título del mapa
        JLabel mapTitle = new JLabel("Mapa de Ubicaciones en Tiempo Real");
        mapTitle.setFont(new Font("Segoe UI", Font.BOLD, 18));
        mapTitle.setForeground(TEXT_PRIMARY_COLOR);
        mapTitle.setAlignmentX(Component.CENTER_ALIGNMENT);
        header.add(mapTitle);
        header.add(Box.createVerticalStrut(12));

        // Toolbar moderno con todos los controles
        JPanel toolbar = createModernToolbar();
        toolbar.setAlignmentX(Component.CENTER_ALIGNMENT);
        header.add(toolbar);

        wrapper.add(header, BorderLayout.NORTH);

        // Contenedor del mapa incrustado con mejor diseño
        JPanel mapContainer = createStyledCard();
        mapContainer.setLayout(new BorderLayout());
        mapContainer.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(BORDER_COLOR, 1),
            new EmptyBorder(8, 8, 8, 8)
        ));

        // Agregar el mapa incrustado directamente
        mapContainer.add(mapPanel, BorderLayout.CENTER);
        mapContainer.setPreferredSize(new Dimension(0, 500)); // Altura generosa para el mapa

        wrapper.add(mapContainer, BorderLayout.CENTER);

        return wrapper;
    }

    private JPanel createModernToolbar() {
        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.RIGHT, 12, 0));
        toolbar.setOpaque(false);

        // Etiqueta del filtro
        JLabel filterLabel = new JLabel("Equipo:");
        filterLabel.setFont(new Font("Segoe UI", Font.BOLD, 13));
        filterLabel.setForeground(TEXT_SECONDARY_COLOR);
        toolbar.add(filterLabel);

        // ComboBox del filtro con mejor estilo
        teamFilter.setPreferredSize(new Dimension(200, 36));
        teamFilter.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        teamFilter.setBackground(CARD_BACKGROUND);
        teamFilter.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(BORDER_COLOR, 1),
            new EmptyBorder(6, 12, 6, 12)
        ));
        teamFilter.addActionListener(e -> applyMapFilter());
        toolbar.add(teamFilter);

        // Botón de actualizar con mejor estilo
        JButton refreshButton = createModernSecondaryButton("↻", "Recargar ubicaciones");
        refreshButton.addActionListener(e -> fetchMapData());
        toolbar.add(refreshButton);

        // Label de estado
        mapStatusLabel.setFont(new Font("Segoe UI", Font.ITALIC, 12));
        mapStatusLabel.setForeground(TEXT_SECONDARY_COLOR);
        toolbar.add(mapStatusLabel);

        return toolbar;
    }

    private JButton createModernPrimaryButton(String text, String tooltip) {
        JButton button = new JButton(text);
        button.setFont(new Font("Segoe UI", Font.BOLD, 14));
        button.setForeground(Color.WHITE);
        button.setBackground(PRIMARY_COLOR);
        button.setBorderPainted(false);
        button.setFocusPainted(false);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        button.setBorder(new EmptyBorder(12, 24, 12, 24));
        button.setPreferredSize(new Dimension(140, 44));

        // Efectos hover
        button.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                button.setBackground(PRIMARY_DARK);
            }
            public void mouseExited(java.awt.event.MouseEvent evt) {
                button.setBackground(PRIMARY_COLOR);
            }
        });

        if (tooltip != null) {
            button.setToolTipText(tooltip);
        }

        return button;
    }

    private JButton createModernSecondaryButton(String text, String tooltip) {
        JButton button = new JButton(text);
        button.setFont(new Font("Segoe UI", Font.BOLD, 14));
        button.setForeground(PRIMARY_COLOR);
        button.setBackground(CARD_BACKGROUND);
        button.setBorderPainted(true);
        button.setBorder(BorderFactory.createLineBorder(PRIMARY_COLOR, 1));
        button.setFocusPainted(false);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        button.setPreferredSize(new Dimension(44, 36));

        // Efectos hover
        button.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                button.setBackground(new Color(239, 246, 255));
            }
            public void mouseExited(java.awt.event.MouseEvent evt) {
                button.setBackground(CARD_BACKGROUND);
            }
        });

        if (tooltip != null) {
            button.setToolTipText(tooltip);
        }

        return button;
    }

    private JPanel createModulesSection() {
        JPanel wrapper = new JPanel(new BorderLayout());
        wrapper.setOpaque(false);
        wrapper.setMaximumSize(new Dimension(1400, Integer.MAX_VALUE));

        // Header de módulos
        JPanel header = new JPanel(new BorderLayout());
        header.setOpaque(false);
        header.setBorder(new EmptyBorder(0, 0, 16, 0));

        JLabel modulesTitle = new JLabel("Gestión de Datos");
        modulesTitle.setFont(new Font("Segoe UI", Font.BOLD, 18));
        modulesTitle.setForeground(TEXT_PRIMARY_COLOR);
        header.add(modulesTitle, BorderLayout.WEST);

        wrapper.add(header, BorderLayout.NORTH);

        // Tabs con mejor estilo
        modulesTabs.setFont(new Font("Segoe UI", Font.BOLD, 13));
        modulesTabs.setBackground(CARD_BACKGROUND);
        modulesTabs.setForeground(TEXT_PRIMARY_COLOR);
        modulesTabs.setBorder(BorderFactory.createLineBorder(BORDER_COLOR, 1));

        // Personalizar apariencia de las tabs
        modulesTabs.setUI(new javax.swing.plaf.basic.BasicTabbedPaneUI() {
            @Override
            protected void paintTabBackground(Graphics g, int tabPlacement, int tabIndex, int x, int y, int w, int h, boolean isSelected) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                if (isSelected) {
                    g2.setColor(PRIMARY_COLOR);
                    g2.fillRoundRect(x, y, w, h, 8, 8);
                } else {
                    g2.setColor(CARD_BACKGROUND);
                    g2.fillRoundRect(x, y, w, h, 8, 8);
                    g2.setColor(BORDER_COLOR);
                    g2.drawRoundRect(x, y, w, h, 8, 8);
                }
                g2.dispose();
            }

            @Override
            protected void paintTabBorder(Graphics g, int tabPlacement, int tabIndex, int x, int y, int w, int h, boolean isSelected) {
                // No pintar borde adicional
            }

            @Override
            protected void paintContentBorder(Graphics g, int tabPlacement, int selectedIndex) {
                // No pintar borde del contenido
            }
        });

        modulesTabs.addTab("👥 Pacientes", createPatientsTab());
        modulesTabs.addTab("🏥 Care-teams", createCareTeamsTab());
        modulesTabs.addTab("📱 Dispositivos", createDevicesTab());
        modulesTabs.addTab("🚨 Alertas", createAlertsTab());

        JPanel tabsCard = createStyledCard();
        tabsCard.setLayout(new BorderLayout());
        tabsCard.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(BORDER_COLOR, 1),
            new EmptyBorder(24, 24, 24, 24)
        ));
        tabsCard.add(modulesTabs, BorderLayout.CENTER);
        tabsCard.setPreferredSize(new Dimension(0, 550));

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

    /**
     * Crea un header consistente para las tabs de gestión de datos
     * siguiendo principios de usabilidad: agrupación lógica, jerarquía visual y consistencia
     */
    private JPanel createDataTabHeader(String title, JComponent[] controls, JLabel statusLabel) {
        JPanel header = new JPanel();
        header.setOpaque(false);
        header.setLayout(new BoxLayout(header, BoxLayout.Y_AXIS));
        header.setBorder(new EmptyBorder(0, 0, 16, 0)); // Espacio inferior para separación

        // Título a la izquierda con jerarquía visual clara
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Segoe UI", Font.BOLD, 16));
        titleLabel.setForeground(TEXT_PRIMARY_COLOR);
        titleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        header.add(titleLabel);
        header.add(Box.createVerticalStrut(12));

        // Panel de controles agrupados centrados
        JPanel controlsPanel = new JPanel();
        controlsPanel.setOpaque(false);
        controlsPanel.setLayout(new BoxLayout(controlsPanel, BoxLayout.X_AXIS));
        controlsPanel.setAlignmentX(Component.CENTER_ALIGNMENT);

        // Agregar controles principales (botones, toggles)
        for (JComponent control : controls) {
            controlsPanel.add(control);
            controlsPanel.add(Box.createHorizontalStrut(8)); // Espacio entre controles
        }

        // Agregar status label integrado si existe
        if (statusLabel != null) {
            statusLabel.setFont(new Font("Segoe UI", Font.ITALIC, 12));
            statusLabel.setForeground(TEXT_SECONDARY_COLOR);
            controlsPanel.add(Box.createHorizontalStrut(16)); // Más espacio antes del status
            controlsPanel.add(statusLabel);
        }

        header.add(controlsPanel);
        return header;
    }

    private JPanel createPatientsTab() {
        JPanel container = new JPanel(new BorderLayout(0, 20));
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(16, 16, 16, 16));

        // Crear header consistente con controles agrupados
        JToggleButton myPatientsToggle = createModernToggleButton("👥 Míos", true);
        JToggleButton teamPatientsToggle = createModernToggleButton("🏥 Equipos", false);

        myPatientsToggle.setSelected(true);
        patientsToggleGroup.add(myPatientsToggle);
        patientsToggleGroup.add(teamPatientsToggle);
        myPatientsToggle.addActionListener(e -> patientsCardLayout.show(patientsContainer, "mine"));
        teamPatientsToggle.addActionListener(e -> patientsCardLayout.show(patientsContainer, "teams"));

        // Usar header consistente con controles agrupados
        JPanel header = createDataTabHeader("Pacientes en Seguimiento",
                                          new JComponent[]{myPatientsToggle, teamPatientsToggle},
                                          patientsStatusLabel);
        container.add(header, BorderLayout.NORTH);

        // Paneles de pacientes con mejor organización
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

    private JToggleButton createModernToggleButton(String text, boolean isPrimary) {
        JToggleButton button = new JToggleButton(text);
        button.setFont(new Font("Segoe UI", Font.BOLD, 13));
        button.setFocusPainted(false);
        button.setBorderPainted(true);
        button.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        button.setBorder(new EmptyBorder(10, 12, 10, 12)); // Padding reducido
        button.setPreferredSize(new Dimension(110, 36)); // Ancho reducido de 130 a 110

        // Estilo inicial
        if (isPrimary) {
            button.setBackground(PRIMARY_COLOR);
            button.setForeground(Color.WHITE);
            button.setBorder(BorderFactory.createLineBorder(PRIMARY_COLOR, 1));
        } else {
            button.setBackground(CARD_BACKGROUND);
            button.setForeground(TEXT_SECONDARY_COLOR);
            button.setBorder(BorderFactory.createLineBorder(BORDER_COLOR, 1));
        }

        // Cambiar estilo cuando esté seleccionado
        button.addItemListener(e -> {
            if (button.isSelected()) {
                button.setBackground(PRIMARY_COLOR);
                button.setForeground(Color.WHITE);
                button.setBorder(BorderFactory.createLineBorder(PRIMARY_COLOR, 1));
            } else {
                button.setBackground(CARD_BACKGROUND);
                button.setForeground(TEXT_SECONDARY_COLOR);
                button.setBorder(BorderFactory.createLineBorder(BORDER_COLOR, 1));
            }
        });

        // Efectos hover
        button.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                if (!button.isSelected()) {
                    button.setBackground(new Color(249, 250, 252));
                    button.setForeground(TEXT_PRIMARY_COLOR);
                }
            }
            public void mouseExited(java.awt.event.MouseEvent evt) {
                if (!button.isSelected()) {
                    button.setBackground(CARD_BACKGROUND);
                    button.setForeground(TEXT_SECONDARY_COLOR);
                }
            }
        });

        return button;
    }

    private JPanel createCareTeamsTab() {
        JPanel container = new JPanel(new BorderLayout(0, 20));
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(16, 16, 16, 16));

        // Header consistente con información de estado
        JPanel header = createDataTabHeader("Equipos de Cuidado", new JComponent[]{}, careTeamStatusLabel);
        container.add(header, BorderLayout.NORTH);

        // Panel de lista de equipos mejorado
        JPanel listPanel = new JPanel(new BorderLayout(0, 12));
        listPanel.setOpaque(false);
        listPanel.setPreferredSize(new Dimension(300, 0)); // Ancho más generoso para mejor usabilidad
        listPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(BORDER_COLOR, 1),
            new EmptyBorder(16, 16, 16, 16)
        ));
        listPanel.setBackground(CARD_BACKGROUND);

        // Título de la lista
        JLabel listTitle = new JLabel("Seleccionar Equipo");
        listTitle.setFont(new Font("Segoe UI", Font.BOLD, 14));
        listTitle.setForeground(TEXT_PRIMARY_COLOR);
        listTitle.setBorder(new EmptyBorder(0, 0, 8, 0));
        listPanel.add(listTitle, BorderLayout.NORTH);

        // Lista con mejor configuración
        careTeamList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        careTeamList.setFont(BODY_FONT);
        careTeamList.setBackground(CARD_BACKGROUND);
        careTeamList.setBorder(new EmptyBorder(4, 4, 4, 4));
        careTeamList.setFixedCellHeight(40); // Altura consistente para mejor usabilidad
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
        listScroll.setBorder(null); // Remover borde para mejor integración
        listPanel.add(listScroll, BorderLayout.CENTER);

        // Panel de detalles mejorado
        careTeamDetailPanel.setOpaque(false);
        careTeamDetailPanel.setBorder(new EmptyBorder(0, 20, 0, 0));

        // Layout más organizado para detalles
        careTeamDetailPanel.setLayout(new BoxLayout(careTeamDetailPanel, BoxLayout.Y_AXIS));

        // Panel de miembros con mejor diseño
        JPanel membersCard = createStyledCard();
        membersCard.setLayout(new BorderLayout(0, 12));
        membersCard.setBorder(new EmptyBorder(16, 16, 16, 16));

        JLabel membersTitle = new JLabel("👥 Miembros del Equipo");
        membersTitle.setFont(new Font("Segoe UI", Font.BOLD, 15));
        membersTitle.setForeground(TEXT_PRIMARY_COLOR);
        membersCard.add(membersTitle, BorderLayout.NORTH);

        membersListPanel.setLayout(new BoxLayout(membersListPanel, BoxLayout.Y_AXIS));
        membersListPanel.setOpaque(false);

        JScrollPane membersScroll = new JScrollPane(membersListPanel);
        configureStyledScroll(membersScroll);
        membersScroll.setPreferredSize(new Dimension(0, 200));
        membersCard.add(membersScroll, BorderLayout.CENTER);

        careTeamDetailPanel.add(membersCard);
        careTeamDetailPanel.add(Box.createVerticalStrut(16));

        // Tabs de dispositivos con mejor organización
        JTabbedPane deviceTabs = new JTabbedPane();
        deviceTabs.setFont(BODY_FONT);
        deviceTabs.setBorder(new EmptyBorder(8, 0, 0, 0));

        activeDevicesPanel.setLayout(new BoxLayout(activeDevicesPanel, BoxLayout.Y_AXIS));
        activeDevicesPanel.setOpaque(false);
        activeDevicesPanel.setBorder(new EmptyBorder(12, 12, 12, 12));

        disconnectedDevicesPanel.setLayout(new BoxLayout(disconnectedDevicesPanel, BoxLayout.Y_AXIS));
        disconnectedDevicesPanel.setOpaque(false);
        disconnectedDevicesPanel.setBorder(new EmptyBorder(12, 12, 12, 12));

        JScrollPane activeScroll = new JScrollPane(activeDevicesPanel);
        JScrollPane disconnectedScroll = new JScrollPane(disconnectedDevicesPanel);
        configureStyledScroll(activeScroll);
        configureStyledScroll(disconnectedScroll);
        activeScroll.setBorder(null);
        disconnectedScroll.setBorder(null);

        deviceTabs.addTab("🟢 Activos", activeScroll);
        deviceTabs.addTab("🔴 Desconectados", disconnectedScroll);

        JPanel devicesCard = createStyledCard();
        devicesCard.setLayout(new BorderLayout());
        devicesCard.setBorder(new EmptyBorder(16, 16, 16, 16));
        devicesCard.add(deviceTabs, BorderLayout.CENTER);
        devicesCard.setPreferredSize(new Dimension(0, 350));

        careTeamDetailPanel.add(devicesCard);

        // Split pane mejorado con proporciones más usables
        JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, listPanel, careTeamDetailPanel);
        splitPane.setDividerLocation(320); // Posición más generosa
        splitPane.setDividerSize(8); // Divider más grueso para mejor agarre
        splitPane.setOpaque(false);
        splitPane.setBorder(null);
        splitPane.setResizeWeight(0.35); // Permitir redimensionamiento manteniendo proporción

        container.add(splitPane, BorderLayout.CENTER);
        return container;
    }

    private JPanel createDevicesTab() {
        JPanel container = new JPanel(new BorderLayout(0, 20));
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(16, 16, 16, 16));

        // Header consistente con información de resumen
        JPanel header = createDataTabHeader("Dispositivos", new JComponent[]{}, devicesSummaryLabel);
        container.add(header, BorderLayout.NORTH);

        // Panel de resumen mejorado con mejor organización
        devicesSummaryPanel.setLayout(new BoxLayout(devicesSummaryPanel, BoxLayout.Y_AXIS));
        devicesSummaryPanel.setOpaque(false);
        devicesSummaryPanel.setBorder(new EmptyBorder(8, 0, 8, 0));

        JScrollPane scroll = new JScrollPane(devicesSummaryPanel);
        configureStyledScroll(scroll);
        scroll.setBorder(null); // Mejor integración visual
        container.add(scroll, BorderLayout.CENTER);
        return container;
    }

    private JPanel createAlertsTab() {
        JPanel container = new JPanel(new BorderLayout(0, 20));
        container.setOpaque(false);
        container.setBorder(new EmptyBorder(16, 16, 16, 16));

        // Header consistente con información de estado
        JPanel header = createDataTabHeader("Alertas Activas", new JComponent[]{}, alertsStatusLabel);
        container.add(header, BorderLayout.NORTH);

        // Panel de alertas con mejor organización
        alertsPanel.setLayout(new BoxLayout(alertsPanel, BoxLayout.Y_AXIS));
        alertsPanel.setOpaque(false);
        alertsPanel.setBorder(new EmptyBorder(8, 0, 8, 0));

        JScrollPane scrollPane = new JScrollPane(alertsPanel);
        configureStyledScroll(scrollPane);
        scrollPane.setBorder(null); // Mejor integración visual
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
        CompletableFuture<JsonObject> careTeamPatientsLocationsFuture = apiClient.getOrganizationCareTeamPatientsLocationsAsync(token, orgId)
                .exceptionally(this::handleCareTeamPatientsFallback);

        CompletableFuture<DashboardBundle> bundleFuture = CompletableFuture.allOf(
                        dashboardFuture,
                        metricsFuture,
                        careTeamsFuture,
                        careTeamPatientsFuture,
                        caregiverPatientsFuture,
                        careTeamLocationsFuture,
                        caregiverLocationsFuture,
                        careTeamPatientsLocationsFuture
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
                    bundle.careTeamPatientsLocations = careTeamPatientsLocationsFuture.join();
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

        // Combinar pacientes de care teams CON UBICACIONES + pacientes del caregiver
        JsonArray careTeamPatientsWithLocations = processCareTeamPatients(bundle.careTeamPatientsLocations);
        JsonArray caregiverPatients = getArray(getData(bundle.caregiverLocations), "patients");
        
        JsonArray allPatients = new JsonArray();
        if (careTeamPatientsWithLocations != null) {
            System.out.println("[RENDER] Agregando " + careTeamPatientsWithLocations.size() + " pacientes de care teams CON ubicaciones");
            careTeamPatientsWithLocations.forEach(allPatients::add);
        }
        if (caregiverPatients != null) {
            System.out.println("[RENDER] Agregando " + caregiverPatients.size() + " pacientes de caregiver");
            caregiverPatients.forEach(allPatients::add);
        }
        
        mapPatientsData = allPatients;
        mapMembersData = getArray(getData(bundle.careTeamLocations), "members");
        
        System.out.println("[RENDER] Total pacientes en mapa: " + mapPatientsData.size());
        System.out.println("[RENDER] Total miembros en mapa: " + (mapMembersData != null ? mapMembersData.size() : 0));
        
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
        JPanel card = new JPanel();
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(BORDER_COLOR, 1),
                new EmptyBorder(20, 20, 20, 20)
        ));
        card.setLayout(new BoxLayout(card, BoxLayout.Y_AXIS));

        // Fila superior: Nombre y Organización en línea horizontal
        JPanel headerRow = new JPanel();
        headerRow.setOpaque(false);
        headerRow.setLayout(new BoxLayout(headerRow, BoxLayout.X_AXIS));

        // Nombre del paciente
        JLabel name = new JLabel(patient.get("name").getAsString());
        name.setFont(new Font("Segoe UI", Font.BOLD, 16));
        name.setForeground(TEXT_PRIMARY_COLOR);
        headerRow.add(name);

        headerRow.add(Box.createHorizontalStrut(16));

        // Organización
        JLabel org = new JLabel("🏥 " + safe(patient.get("organization"), "name"));
        org.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        org.setForeground(TEXT_SECONDARY_COLOR);
        headerRow.add(org);

        headerRow.add(Box.createHorizontalGlue()); // Empujar contenido a la izquierda

        card.add(headerRow);
        card.add(Box.createVerticalStrut(12));

        // Fila inferior: Badge de riesgo y botón de detalles
        JPanel actionRow = new JPanel();
        actionRow.setOpaque(false);
        actionRow.setLayout(new BoxLayout(actionRow, BoxLayout.X_AXIS));

        // Badge de riesgo con mejor diseño
        String riskLabel = safe(patient.get("risk_level"), "label");
        JLabel risk = new JLabel("⚠️ " + riskLabel);
        risk.setFont(new Font("Segoe UI", Font.BOLD, 12));
        risk.setOpaque(true);
        risk.setBorder(new EmptyBorder(6, 12, 6, 12));

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

        actionRow.add(risk);
        actionRow.add(Box.createHorizontalStrut(16)); // Espaciado entre badge y botón

        // Botón de detalles con tamaño fijo y compacto
        JButton details = new JButton("👁️ Ver detalles");
        details.setFont(new Font("Segoe UI", Font.BOLD, 13));
        details.setForeground(PRIMARY_COLOR);
        details.setBackground(new Color(239, 246, 255));
        details.setBorderPainted(true);
        details.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(PRIMARY_COLOR, 1),
            new EmptyBorder(8, 16, 8, 16)
        ));
        details.setFocusPainted(false);
        details.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        details.setMaximumSize(new Dimension(150, 36)); // Tamaño máximo fijo
        details.setPreferredSize(new Dimension(150, 36));
        details.setToolTipText("Ver detalles del paciente");

        // Efectos hover
        details.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                details.setBackground(PRIMARY_COLOR);
                details.setForeground(Color.WHITE);
            }
            public void mouseExited(java.awt.event.MouseEvent evt) {
                details.setBackground(new Color(239, 246, 255));
                details.setForeground(PRIMARY_COLOR);
            }
        });

        details.addActionListener(e -> openPatientDetail(patient, caregiverContext));

        actionRow.add(details);
        actionRow.add(Box.createHorizontalGlue()); // Mantener el botón cerca del badge

        card.add(actionRow);

        // Establecer altura máxima para evitar que las tarjetas se estiren
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 120));

        return card;
    }

    private void openPatientDetail(JsonObject patient, boolean isCaregiverPatient) {
        String patientId = patient.get("id").getAsString();
        String name = patient.get("name").getAsString();

        // Determinar el orgId basado en el contexto:
        // - Si es paciente de caregiver (mis pacientes propios): orgId = null (usar endpoints de caregiver)
        // - Si es paciente de care-team (organización): usar currentOrg.getOrgId() (usar endpoints de organización)
        String orgId = isCaregiverPatient ? null : (currentOrg != null ? currentOrg.getOrgId() : null);

        Window window = SwingUtilities.getWindowAncestor(this);
        Frame frame = window instanceof Frame ? (Frame) window : null;
        PatientDetailDialog dialog = new PatientDetailDialog(
                frame,
                apiClient,
                token,
                orgId,  // null para caregiver, orgId para care-team
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
                JPanel memberCard = new JPanel();
                memberCard.setBackground(new Color(249, 250, 251));
                memberCard.setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(new Color(229, 234, 243)),
                    new EmptyBorder(10, 12, 10, 12)
                ));
                memberCard.setLayout(new BorderLayout(12, 0));

                // Avatar circular con foto o iniciales
                String memberName = member.get("name").getAsString();
                String photoUrl = member.has("profile_photo_url") && !member.get("profile_photo_url").isJsonNull()
                        ? member.get("profile_photo_url").getAsString() : null;
                AvatarPanel avatar = new AvatarPanel(memberName, photoUrl, 40);
                memberCard.add(avatar, BorderLayout.WEST);

                // Panel central con información
                JPanel infoPanel = new JPanel();
                infoPanel.setOpaque(false);
                infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));

                // Fila superior: Nombre y badge de rol
                JPanel headerRow = new JPanel();
                headerRow.setOpaque(false);
                headerRow.setLayout(new BoxLayout(headerRow, BoxLayout.X_AXIS));

                // Nombre del miembro
                JLabel nameLabel = new JLabel(memberName);
                nameLabel.setFont(new Font("Segoe UI", Font.BOLD, 13));
                nameLabel.setForeground(TEXT_PRIMARY_COLOR);
                headerRow.add(nameLabel);

                headerRow.add(Box.createHorizontalStrut(12));

                // Badge de rol
                String roleLabel = safe(member.get("role"), "label");
                JLabel roleBadge = new JLabel(roleLabel);
                roleBadge.setFont(new Font("Segoe UI", Font.BOLD, 11));
                roleBadge.setForeground(PRIMARY_COLOR);
                roleBadge.setOpaque(true);
                roleBadge.setBackground(new Color(219, 234, 254));
                roleBadge.setBorder(new EmptyBorder(3, 8, 3, 8));
                headerRow.add(roleBadge);

                headerRow.add(Box.createHorizontalGlue());

                infoPanel.add(headerRow);

                // Email (si está disponible)
                if (member.has("email") && !member.get("email").isJsonNull()) {
                    String email = member.get("email").getAsString();
                    JLabel emailLabel = new JLabel(email);
                    emailLabel.setFont(new Font("Segoe UI", Font.PLAIN, 11));
                    emailLabel.setForeground(TEXT_SECONDARY_COLOR);
                    infoPanel.add(Box.createVerticalStrut(2));
                    infoPanel.add(emailLabel);
                }

                memberCard.add(infoPanel, BorderLayout.CENTER);

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
            JPanel card = new JPanel();
            card.setBackground(Color.WHITE);
            card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(active ? new Color(209, 231, 221) : new Color(252, 213, 207)),
                new EmptyBorder(14, 14, 14, 14)
            ));
            card.setLayout(new BoxLayout(card, BoxLayout.Y_AXIS));

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

            card.add(infoPanel);
            card.add(Box.createVerticalStrut(12));

            // Botón mejorado con tamaño fijo
            JButton streamsButton = new JButton("Ver streams");
            streamsButton.setFont(new Font("Segoe UI", Font.BOLD, 12));
            streamsButton.setForeground(PRIMARY_COLOR);
            streamsButton.setBackground(new Color(239, 246, 255));
            streamsButton.setBorderPainted(false);
            streamsButton.setFocusPainted(false);
            streamsButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
            streamsButton.setMaximumSize(new Dimension(120, 32));
            streamsButton.setPreferredSize(new Dimension(120, 32));
            streamsButton.setAlignmentX(Component.LEFT_ALIGNMENT);
            streamsButton.addActionListener(e -> openDeviceStreams(option, device));

            card.add(streamsButton);

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
            mapPanel.updateLocations(mapPatientsData);
            return;
        }
        if (option.id.equals("all")) {
            mapPanel.updateLocations(mapPatientsData);
            return;
        }
        
        System.out.println("[FILTRO] Filtrando por equipo: " + option.name + " (ID: " + option.id + ")");
        System.out.println("[FILTRO] Total pacientes sin filtrar: " + mapPatientsData.size());
        
        JsonArray filteredPatients = new JsonArray();
        for (JsonElement element : mapPatientsData) {
            if (!element.isJsonObject()) continue;
            JsonObject patient = element.getAsJsonObject();
            
            System.out.println("[FILTRO] Paciente: " + patient);
            
            if (patient.has("care_team") && patient.get("care_team").isJsonObject()) {
                JsonObject team = patient.getAsJsonObject("care_team");
                System.out.println("[FILTRO]   - Tiene care_team: " + team);
                if (team.has("id") && !team.get("id").isJsonNull() && team.get("id").getAsString().equals(option.id)) {
                    filteredPatients.add(patient);
                    System.out.println("[FILTRO]   - ✓ INCLUIDO");
                } else {
                    System.out.println("[FILTRO]   - ✗ No coincide el ID");
                }
            } else {
                System.out.println("[FILTRO]   - ✗ No tiene care_team");
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
        mapPanel.updateLocations(filteredPatients);
    }

    /**
     * Procesa la respuesta de /orgs/{org_id}/care-team-patients para convertirla
     * al formato esperado por el mapa (con care_team incluido en cada paciente)
     */
    private JsonArray processCareTeamPatients(JsonObject response) {
        JsonArray result = new JsonArray();
        JsonObject data = getData(response);
        if (data == null) return result;
        
        JsonArray careTeams = getArray(data, "care_teams");
        if (careTeams == null) return result;
        
        // Iterar sobre cada care team
        for (JsonElement teamElement : careTeams) {
            if (!teamElement.isJsonObject()) continue;
            JsonObject team = teamElement.getAsJsonObject();
            
            String teamId = team.has("id") ? team.get("id").getAsString() : null;
            String teamName = team.has("name") ? team.get("name").getAsString() : null;
            
            if (teamId == null) continue;
            
            // Obtener los pacientes de este team
            JsonArray patients = getArray(team, "patients");
            if (patients == null) continue;
            
            // Agregar la referencia del care team a cada paciente
            for (JsonElement patientElement : patients) {
                if (!patientElement.isJsonObject()) continue;
                JsonObject patient = patientElement.getAsJsonObject();
                
                // Crear objeto care_team para agregar al paciente
                JsonObject careTeamRef = new JsonObject();
                careTeamRef.addProperty("id", teamId);
                careTeamRef.addProperty("name", teamName);
                
                // Agregar care_team al paciente
                patient.add("care_team", careTeamRef);
                
                result.add(patient);
            }
        }
        
        System.out.println("[DASHBOARD] Procesados " + result.size() + " pacientes de care teams");
        return result;
    }

    private void fetchMapData() {
        if (currentOrg == null) return;
        mapStatusLabel.setText("Recargando ubicaciones...");

        System.out.println("[DASHBOARD] Obteniendo datos de ubicaciones para org: " + currentOrg.getOrgId());
        
        Map<String, String> params = Map.of("org_id", currentOrg.getOrgId());
        
        // Obtener pacientes de care teams (con toda su info) y miembros del care team con ubicaciones
        CompletableFuture<JsonObject> careTeamPatientsFuture = CompletableFuture.supplyAsync(() -> {
            try {
                return apiClient.getOrganizationCareTeamPatients(token, currentOrg.getOrgId());
            } catch (Exception e) {
                System.err.println("[DASHBOARD] Error obteniendo care team patients: " + e.getMessage());
                return new JsonObject();
            }
        });
        
        CompletableFuture<JsonObject> caregiverPatientsFuture = apiClient.getCaregiverPatientLocationsAsync(token, params);
        CompletableFuture<JsonObject> careTeamMembersFuture = apiClient.getCareTeamLocationsAsync(token, params);

        CompletableFuture.allOf(careTeamPatientsFuture, caregiverPatientsFuture, careTeamMembersFuture)
                .thenApplyAsync(ignored -> {
                    JsonObject careTeamPatientsResponse = careTeamPatientsFuture.join();
                    JsonObject caregiverPatientsResponse = caregiverPatientsFuture.join();
                    JsonObject careTeamMembersResponse = careTeamMembersFuture.join();
                    
                    System.out.println("[DASHBOARD] Respuesta care team patients: " + careTeamPatientsResponse);
                    System.out.println("[DASHBOARD] Respuesta caregiver patients: " + caregiverPatientsResponse);
                    System.out.println("[DASHBOARD] Respuesta care team members: " + careTeamMembersResponse);
                    
                    // Procesar pacientes de care teams
                    JsonArray careTeamPatients = processCareTeamPatients(careTeamPatientsResponse);
                    
                    // Obtener pacientes del caregiver individual (con ubicaciones)
                    JsonArray caregiverPatients = getArray(getData(caregiverPatientsResponse), "patients");
                    
                    // Combinar ambos arrays de pacientes
                    JsonArray allPatients = new JsonArray();
                    if (careTeamPatients != null) {
                        careTeamPatients.forEach(allPatients::add);
                    }
                    if (caregiverPatients != null) {
                        caregiverPatients.forEach(allPatients::add);
                    }
                    
                    // Obtener miembros del care team
                    JsonArray members = getArray(getData(careTeamMembersResponse), "members");
                    
                    System.out.println("[DASHBOARD] Total pacientes combinados: " + allPatients.size());
                    System.out.println("[DASHBOARD] Miembros obtenidos: " + (members != null ? members.size() : 0));
                    
                    return new MapPayload(allPatients, members);
                })
                .thenAccept(payload -> SwingUtilities.invokeLater(() -> {
                    mapPatientsData = payload.patients != null ? payload.patients : new JsonArray();
                    mapMembersData = payload.members != null ? payload.members : new JsonArray();
                    
                    System.out.println("[DASHBOARD] Datos actualizados - Pacientes: " + mapPatientsData.size() + ", Miembros: " + mapMembersData.size());
                    
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
        JsonObject careTeamPatientsLocations;
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

            // Panel inferior con subtítulo y sparkline agrupados
            JPanel bottomPanel = new JPanel();
            bottomPanel.setOpaque(false);
            bottomPanel.setLayout(new BoxLayout(bottomPanel, BoxLayout.X_AXIS));
            bottomPanel.setAlignmentX(Component.CENTER_ALIGNMENT);

            subtitleLabel.setFont(CAPTION_FONT);
            subtitleLabel.setForeground(TEXT_SECONDARY_COLOR);
            bottomPanel.add(subtitleLabel);

            // Espacio flexible entre subtítulo y sparkline
            bottomPanel.add(Box.createHorizontalGlue());

            sparklinePanel.setPreferredSize(new Dimension(100, 40));
            sparklinePanel.setMaximumSize(new Dimension(100, 40));
            sparklinePanel.setOpaque(false);
            bottomPanel.add(sparklinePanel);

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
    
    /**
     * Limpia recursos del panel, especialmente el mapa incrustado
     */
    public void cleanup() {
        if (mapPanel != null) {
            mapPanel.dispose();
        }
    }
}

