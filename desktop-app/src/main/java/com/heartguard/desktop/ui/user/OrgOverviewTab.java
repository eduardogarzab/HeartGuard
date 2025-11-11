package com.heartguard.desktop.ui.user;

import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.models.user.OrgMembership;
import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.plot.PiePlot;
import org.jfree.chart.plot.CategoryPlot;
import org.jfree.chart.renderer.category.StackedBarRenderer;
import org.jfree.data.category.DefaultCategoryDataset;
import org.jfree.data.general.DefaultPieDataset;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Tab Overview de una organización.
 * Muestra:
 * - Cards de métricas (pacientes, care teams, caregivers, dispositivos)
 * - Pie Chart: Distribución de pacientes por nivel de riesgo
 * - Stacked Bar Chart: Alertas últimos 7 días por nivel
 * - Progress Ring: Porcentaje de dispositivos activos
 */
public class OrgOverviewTab extends JPanel {
    // Colores
    private static final Color GLOBAL_BACKGROUND = new Color(247, 249, 251);
    private static final Color CARD_BACKGROUND = Color.WHITE;
    private static final Color PRIMARY_BLUE = new Color(0, 120, 215);
    private static final Color SECONDARY_GREEN = new Color(40, 167, 69);
    private static final Color WARNING_ORANGE = new Color(255, 152, 0);
    private static final Color DANGER_RED = new Color(220, 53, 69);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER_LIGHT = new Color(223, 227, 230);
    
    private final ApiClient apiClient;
    private final String accessToken;
    private final OrgMembership organization;
    private final Consumer<Exception> exceptionHandler;
    private final BiConsumer<String, Boolean> snackbarHandler;
    
    // Componentes de métricas
    private final JLabel totalPatientsLabel = new JLabel("--");
    private final JLabel totalCareTeamsLabel = new JLabel("--");
    private final JLabel totalCaregiversLabel = new JLabel("--");
    private final JLabel alertsLast7DaysLabel = new JLabel("--");
    private final JLabel openAlertsLabel = new JLabel("--");
    private final JLabel devicesActiveLabel = new JLabel("--");
    
    // Paneles para gráficos
    private JPanel riskDistributionPanel;
    private JPanel alertsChartPanel;
    private JPanel devicesGaugePanel;
    
    public OrgOverviewTab(
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
        
        initUI();
    }
    
    private void initUI() {
        JPanel mainContent = new JPanel();
        mainContent.setLayout(new BoxLayout(mainContent, BoxLayout.Y_AXIS));
        mainContent.setOpaque(false);
        mainContent.setBorder(new EmptyBorder(24, 24, 24, 24));
        
        // Título
        JLabel titleLabel = new JLabel("📊 Vista General - " + organization.getOrgName());
        titleLabel.setFont(new Font("Inter", Font.BOLD, 24));
        titleLabel.setForeground(TEXT_PRIMARY);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(titleLabel);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Grid de métricas (2 filas x 3 columnas)
        JPanel metricsGrid = createMetricsGrid();
        metricsGrid.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(metricsGrid);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Grid de gráficos (2 columnas)
        JPanel chartsGrid = new JPanel(new GridLayout(1, 2, 16, 0));
        chartsGrid.setOpaque(false);
        chartsGrid.setMaximumSize(new Dimension(Integer.MAX_VALUE, 400));
        chartsGrid.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Gráfico 1: Distribución de Pacientes por Riesgo (Pie Chart)
        riskDistributionPanel = createChartCard("Pacientes por Nivel de Riesgo");
        chartsGrid.add(riskDistributionPanel);
        
        // Gráfico 2: Alertas Últimos 7 Días (Stacked Bar Chart)
        alertsChartPanel = createChartCard("Alertas Últimos 7 Días");
        chartsGrid.add(alertsChartPanel);
        
        mainContent.add(chartsGrid);
        mainContent.add(Box.createVerticalStrut(24));
        
        // Dispositivos activos (Progress Ring)
        devicesGaugePanel = createChartCard("Estado de Dispositivos");
        devicesGaugePanel.setMaximumSize(new Dimension(Integer.MAX_VALUE, 250));
        devicesGaugePanel.setAlignmentX(Component.LEFT_ALIGNMENT);
        mainContent.add(devicesGaugePanel);
        
        mainContent.add(Box.createVerticalGlue());
        
        // ScrollPane
        JScrollPane scrollPane = new JScrollPane(mainContent);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        scrollPane.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        scrollPane.getViewport().setBackground(GLOBAL_BACKGROUND);
        
        add(scrollPane, BorderLayout.CENTER);
    }
    
    private JPanel createMetricsGrid() {
        JPanel grid = new JPanel(new GridLayout(2, 3, 16, 16));
        grid.setOpaque(false);
        grid.setMaximumSize(new Dimension(Integer.MAX_VALUE, 260));
        
        // Fila 1
        grid.add(createMetricCard("👥 Pacientes", totalPatientsLabel, PRIMARY_BLUE));
        grid.add(createMetricCard("🏥 Care Teams", totalCareTeamsLabel, SECONDARY_GREEN));
        grid.add(createMetricCard("👨‍⚕️ Caregivers", totalCaregiversLabel, new Color(103, 58, 183)));
        
        // Fila 2
        grid.add(createMetricCard("📊 Alertas (7d)", alertsLast7DaysLabel, WARNING_ORANGE));
        grid.add(createMetricCard("🚨 Alertas Abiertas", openAlertsLabel, DANGER_RED));
        grid.add(createMetricCard("📱 Dispositivos Activos", devicesActiveLabel, new Color(0, 150, 136)));
        
        return grid;
    }
    
    private JPanel createMetricCard(String title, JLabel valueLabel, Color accentColor) {
        JPanel card = new JPanel();
        card.setLayout(new BorderLayout(12, 8));
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 24, 20, 24)
        ));
        
        // Título
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        titleLabel.setForeground(TEXT_SECONDARY);
        card.add(titleLabel, BorderLayout.NORTH);
        
        // Valor grande
        valueLabel.setFont(new Font("Inter", Font.BOLD, 36));
        valueLabel.setForeground(accentColor);
        card.add(valueLabel, BorderLayout.CENTER);
        
        return card;
    }
    
    private JPanel createChartCard(String title) {
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 24, 20, 24)
        ));
        
        // Header
        JLabel headerLabel = new JLabel(title);
        headerLabel.setFont(new Font("Inter", Font.BOLD, 16));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        card.add(headerLabel, BorderLayout.NORTH);
        
        // Placeholder para gráfico
        JLabel placeholderLabel = new JLabel("Cargando datos...", SwingConstants.CENTER);
        placeholderLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        placeholderLabel.setForeground(TEXT_SECONDARY);
        card.add(placeholderLabel, BorderLayout.CENTER);
        
        return card;
    }
    
    /**
     * Carga datos del dashboard de la organización
     */
    public void loadData() {
        SwingWorker<JsonObject, Void> worker = new SwingWorker<>() {
            @Override
            protected JsonObject doInBackground() throws Exception {
                System.out.println("[OrgOverviewTab] Cargando dashboard para org: " + organization.getOrgName());
                return apiClient.getOrganizationDashboard(accessToken, organization.getOrgId());
            }
            
            @Override
            protected void done() {
                try {
                    JsonObject response = get();
                    System.out.println("[OrgOverviewTab] Respuesta recibida: " + response.toString());
                    
                    // La respuesta tiene estructura: {data: {organization, overview, metrics}}
                    JsonObject data = response.has("data") ? response.getAsJsonObject("data") : new JsonObject();
                    System.out.println("[OrgOverviewTab] Data extraída: " + data.toString());
                    
                    // Extraer overview y metrics
                    JsonObject overview = data.has("overview") ? data.getAsJsonObject("overview") : new JsonObject();
                    JsonObject metrics = data.has("metrics") ? data.getAsJsonObject("metrics") : new JsonObject();
                    
                    System.out.println("[OrgOverviewTab] Overview: " + overview.toString());
                    System.out.println("[OrgOverviewTab] Metrics: " + metrics.toString());
                    
                    updateMetrics(overview, metrics);
                    updateCharts(overview, metrics);
                    
                    System.out.println("[OrgOverviewTab] Datos actualizados correctamente");
                } catch (Exception ex) {
                    System.err.println("[OrgOverviewTab] ERROR: " + ex.getMessage());
                    ex.printStackTrace();
                    exceptionHandler.accept(ex);
                }
            }
        };
        worker.execute();
    }
    
    private void updateMetrics(JsonObject overview, JsonObject metrics) {
        // Actualizar cards de métricas desde overview
        totalPatientsLabel.setText(String.valueOf(overview.has("total_patients") ? overview.get("total_patients").getAsInt() : 0));
        totalCareTeamsLabel.setText(String.valueOf(overview.has("total_care_teams") ? overview.get("total_care_teams").getAsInt() : 0));
        totalCaregiversLabel.setText(String.valueOf(overview.has("total_caregivers") ? overview.get("total_caregivers").getAsInt() : 0));
        alertsLast7DaysLabel.setText(String.valueOf(overview.has("alerts_last_7d") ? overview.get("alerts_last_7d").getAsInt() : 0));
        openAlertsLabel.setText(String.valueOf(overview.has("open_alerts") ? overview.get("open_alerts").getAsInt() : 0));
        
        // Dispositivos activos (si está disponible)
        if (overview.has("devices_active") && overview.has("devices_total")) {
            int active = overview.get("devices_active").getAsInt();
            int total = overview.get("devices_total").getAsInt();
            devicesActiveLabel.setText(active + " / " + total);
        } else {
            devicesActiveLabel.setText("N/A");
        }
    }
    
    private void updateCharts(JsonObject overview, JsonObject metrics) {
        // 1. Pie Chart: Pacientes por Riesgo
        updateRiskDistributionChart(overview);
        
        // 2. Stacked Bar Chart: Alertas por día
        updateAlertsChart(overview);
        
        // 3. Gauge: Dispositivos activos
        updateDevicesGauge(overview);
    }
    
    private void updateRiskDistributionChart(JsonObject overview) {
        // Crear dataset para Pie Chart
        DefaultPieDataset<String> dataset = new DefaultPieDataset<>();
        
        // TODO: Obtener datos reales de distribución por riesgo
        // Por ahora, datos de ejemplo
        if (overview.has("risk_distribution")) {
            JsonObject riskDist = overview.getAsJsonObject("risk_distribution");
            if (riskDist.has("high")) dataset.setValue("Alto Riesgo", riskDist.get("high").getAsInt());
            if (riskDist.has("medium")) dataset.setValue("Riesgo Medio", riskDist.get("medium").getAsInt());
            if (riskDist.has("low")) dataset.setValue("Bajo Riesgo", riskDist.get("low").getAsInt());
        } else {
            // Datos de ejemplo
            dataset.setValue("Alto Riesgo", 12);
            dataset.setValue("Riesgo Medio", 25);
            dataset.setValue("Bajo Riesgo", 8);
        }
        
        // Crear gráfico
        JFreeChart chart = ChartFactory.createPieChart(
                null, // Sin título (ya está en el card)
                dataset,
                true, // Leyenda
                true, // Tooltips
                false // URLs
        );
        
        // Personalizar colores
        PiePlot plot = (PiePlot) chart.getPlot();
        plot.setSectionPaint("Alto Riesgo", DANGER_RED);
        plot.setSectionPaint("Riesgo Medio", WARNING_ORANGE);
        plot.setSectionPaint("Bajo Riesgo", SECONDARY_GREEN);
        plot.setBackgroundPaint(CARD_BACKGROUND);
        plot.setOutlineVisible(false);
        chart.setBackgroundPaint(CARD_BACKGROUND);
        
        // Agregar al panel
        ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setBackground(CARD_BACKGROUND);
        chartPanel.setPreferredSize(new Dimension(400, 300));
        
        riskDistributionPanel.removeAll();
        JLabel headerLabel = new JLabel("Pacientes por Nivel de Riesgo");
        headerLabel.setFont(new Font("Inter", Font.BOLD, 16));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        riskDistributionPanel.add(headerLabel, BorderLayout.NORTH);
        riskDistributionPanel.add(chartPanel, BorderLayout.CENTER);
        riskDistributionPanel.revalidate();
        riskDistributionPanel.repaint();
    }
    
    private void updateAlertsChart(JsonObject overview) {
        // Crear dataset para Stacked Bar Chart
        DefaultCategoryDataset dataset = new DefaultCategoryDataset();
        
        // TODO: Obtener datos reales de alertas por día
        // Por ahora, datos de ejemplo
        String[] days = {"Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"};
        
        if (overview.has("alerts_by_day")) {
            // Parsear datos reales cuando estén disponibles
            // JsonArray alertsByDay = overview.getAsJsonArray("alerts_by_day");
        } else {
            // Datos de ejemplo
            for (String day : days) {
                dataset.addValue(Math.random() * 5, "Crítica", day);
                dataset.addValue(Math.random() * 8, "Alta", day);
                dataset.addValue(Math.random() * 12, "Media", day);
                dataset.addValue(Math.random() * 6, "Baja", day);
            }
        }
        
        // Crear gráfico
        JFreeChart chart = ChartFactory.createStackedBarChart(
                null, // Sin título
                null, // Sin label eje X
                "Cantidad", // Label eje Y
                dataset
        );
        
        // Personalizar colores
        CategoryPlot plot = chart.getCategoryPlot();
        StackedBarRenderer renderer = (StackedBarRenderer) plot.getRenderer();
        renderer.setSeriesPaint(0, DANGER_RED);
        renderer.setSeriesPaint(1, WARNING_ORANGE);
        renderer.setSeriesPaint(2, new Color(255, 193, 7));
        renderer.setSeriesPaint(3, SECONDARY_GREEN);
        plot.setBackgroundPaint(CARD_BACKGROUND);
        plot.setOutlineVisible(false);
        chart.setBackgroundPaint(CARD_BACKGROUND);
        
        // Agregar al panel
        ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setBackground(CARD_BACKGROUND);
        chartPanel.setPreferredSize(new Dimension(400, 300));
        
        alertsChartPanel.removeAll();
        JLabel headerLabel = new JLabel("Alertas Últimos 7 Días");
        headerLabel.setFont(new Font("Inter", Font.BOLD, 16));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        alertsChartPanel.add(headerLabel, BorderLayout.NORTH);
        alertsChartPanel.add(chartPanel, BorderLayout.CENTER);
        alertsChartPanel.revalidate();
        alertsChartPanel.repaint();
    }
    
    private void updateDevicesGauge(JsonObject overview) {
        // Crear un gráfico de anillo (Donut) para simular gauge
        DefaultPieDataset<String> dataset = new DefaultPieDataset<>();
        
        int active = 0;
        int total = 100;
        
        if (overview.has("devices_active") && overview.has("devices_total")) {
            active = overview.get("devices_active").getAsInt();
            total = overview.get("devices_total").getAsInt();
        }
        
        int inactive = total - active;
        double percentage = total > 0 ? (active * 100.0 / total) : 0;
        
        dataset.setValue("Activos", active);
        dataset.setValue("Inactivos", inactive);
        
        JFreeChart chart = ChartFactory.createPieChart(
                String.format("%.1f%% Activos (%d / %d)", percentage, active, total),
                dataset,
                true,
                true,
                false
        );
        
        PiePlot plot = (PiePlot) chart.getPlot();
        plot.setSectionPaint("Activos", SECONDARY_GREEN);
        plot.setSectionPaint("Inactivos", new Color(220, 220, 220));
        plot.setBackgroundPaint(CARD_BACKGROUND);
        plot.setOutlineVisible(false);
        chart.setBackgroundPaint(CARD_BACKGROUND);
        chart.getTitle().setFont(new Font("Inter", Font.BOLD, 18));
        
        ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setBackground(CARD_BACKGROUND);
        chartPanel.setPreferredSize(new Dimension(800, 180));
        
        devicesGaugePanel.removeAll();
        JLabel headerLabel = new JLabel("Estado de Dispositivos");
        headerLabel.setFont(new Font("Inter", Font.BOLD, 16));
        headerLabel.setForeground(TEXT_PRIMARY);
        headerLabel.setBorder(new EmptyBorder(0, 0, 16, 0));
        devicesGaugePanel.add(headerLabel, BorderLayout.NORTH);
        devicesGaugePanel.add(chartPanel, BorderLayout.CENTER);
        devicesGaugePanel.revalidate();
        devicesGaugePanel.repaint();
    }
}
