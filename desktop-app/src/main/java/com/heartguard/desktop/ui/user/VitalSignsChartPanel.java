package com.heartguard.desktop.ui.user;

import com.heartguard.desktop.api.InfluxDBService;
import com.heartguard.desktop.api.InfluxDBService.VitalSignsReading;
import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.DateAxis;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.labels.StandardXYToolTipGenerator;
import org.jfree.chart.plot.IntervalMarker;
import org.jfree.chart.plot.ValueMarker;
import org.jfree.chart.plot.XYPlot;
import org.jfree.chart.renderer.xy.XYAreaRenderer;
import org.jfree.chart.renderer.xy.XYLineAndShapeRenderer;
import org.jfree.chart.ui.Layer;
import org.jfree.chart.ui.RectangleAnchor;
import org.jfree.chart.ui.TextAnchor;
import org.jfree.data.time.Second;
import org.jfree.data.time.TimeSeries;
import org.jfree.data.time.TimeSeriesCollection;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * Panel que muestra gráficas de signos vitales en tiempo real.
 * Se actualiza automáticamente cada N segundos.
 */
public class VitalSignsChartPanel extends JPanel {
    // Modern color palette
    private static final Color CARD_BG = new Color(250, 251, 252);
    private static final Color CHART_BG = Color.WHITE;
    private static final Color TEXT_PRIMARY = new Color(30, 41, 59);
    private static final Color TEXT_SECONDARY = new Color(100, 116, 139);
    private static final Color BORDER_LIGHT = new Color(226, 232, 240);
    
    // Vibrant accent colors
    private static final Color HEART_COLOR = new Color(239, 68, 68);      // Red
    private static final Color SPO2_COLOR = new Color(59, 130, 246);      // Blue
    private static final Color BP_SYSTOLIC_COLOR = new Color(34, 197, 94); // Green
    private static final Color BP_DIASTOLIC_COLOR = new Color(16, 185, 129); // Teal
    private static final Color TEMP_COLOR = new Color(249, 115, 22);      // Orange
    
    // Grid and background
    private static final Color GRID_COLOR = new Color(241, 245, 249);
    private static final Color PLOT_BG = new Color(248, 250, 252);
    
    // Range indicators (semi-transparent zones)
    private static final Color ZONE_NORMAL = new Color(34, 197, 94, 25);    // Green zone
    private static final Color ZONE_WARNING = new Color(251, 191, 36, 25);  // Yellow zone
    private static final Color ZONE_DANGER = new Color(239, 68, 68, 25);    // Red zone
    
    // Shadow and depth
    private static final Color SHADOW_COLOR = new Color(0, 0, 0, 8);

    private final String patientId;
    private final InfluxDBService influxService;
    private Timer updateTimer;
    private final int updateIntervalSeconds;

    // Series de datos para cada parámetro
    private final TimeSeries heartRateSeries;
    private final TimeSeries spo2Series;
    private final TimeSeries systolicBpSeries;
    private final TimeSeries diastolicBpSeries;
    private final TimeSeries temperatureSeries;

    // Labels para mostrar valores actuales
    private final JLabel heartRateLabel;
    private final JLabel spo2Label;
    private final JLabel bloodPressureLabel;
    private final JLabel temperatureLabel;
    private final JLabel lastUpdateLabel;

    /**
     * Constructor
     * 
     * @param patientId ID del paciente
     * @param influxService Servicio de InfluxDB
     * @param updateIntervalSeconds Intervalo de actualización en segundos
     */
    public VitalSignsChartPanel(String patientId, InfluxDBService influxService, int updateIntervalSeconds) {
        this.patientId = patientId;
        this.influxService = influxService;
        this.updateIntervalSeconds = updateIntervalSeconds;

        // Crear series de tiempo
        heartRateSeries = new TimeSeries("Frecuencia Cardíaca (bpm)");
        spo2Series = new TimeSeries("SpO2 (%)");
        systolicBpSeries = new TimeSeries("Presión Sistólica (mmHg)");
        diastolicBpSeries = new TimeSeries("Presión Diastólica (mmHg)");
        temperatureSeries = new TimeSeries("Temperatura (°C)");

        // Limitar el número de puntos en la serie (ventana deslizante)
        heartRateSeries.setMaximumItemCount(50);
        spo2Series.setMaximumItemCount(50);
        systolicBpSeries.setMaximumItemCount(50);
        diastolicBpSeries.setMaximumItemCount(50);
        temperatureSeries.setMaximumItemCount(50);

        // Labels para valores actuales
        heartRateLabel = new JLabel("--");
        spo2Label = new JLabel("--");
        bloodPressureLabel = new JLabel("--/--");
        temperatureLabel = new JLabel("--");
        lastUpdateLabel = new JLabel("Cargando...");

        initComponents();
        loadInitialData();
        startAutoUpdate();
    }

    private void initComponents() {
        setLayout(new BorderLayout(16, 16));
        setBackground(CARD_BG);
        setBorder(new EmptyBorder(20, 20, 20, 20));

        // Panel superior con valores actuales
        JPanel currentValuesPanel = createCurrentValuesPanel();
        add(currentValuesPanel, BorderLayout.NORTH);

        // Panel de gráficas (tabs para diferentes parámetros)
        JTabbedPane chartTabs = createChartTabs();
        add(chartTabs, BorderLayout.CENTER);

        // Panel inferior con estado
        JPanel statusPanel = new JPanel(new BorderLayout());
        statusPanel.setOpaque(false);
        statusPanel.setBorder(new EmptyBorder(12, 0, 0, 0));

        lastUpdateLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        lastUpdateLabel.setForeground(TEXT_SECONDARY);
        statusPanel.add(lastUpdateLabel, BorderLayout.WEST);

        add(statusPanel, BorderLayout.SOUTH);
    }

    private JPanel createCurrentValuesPanel() {
        JPanel panel = new JPanel(new GridLayout(1, 4, 16, 0));
        panel.setOpaque(false);
        panel.setBorder(new EmptyBorder(0, 0, 20, 0));

        // Card de frecuencia cardíaca
        panel.add(createValueCard("❤️  Frecuencia Cardíaca", heartRateLabel, "bpm", HEART_COLOR));

        // Card de SpO2
        panel.add(createValueCard("🫁  Saturación O₂", spo2Label, "%", SPO2_COLOR));

        // Card de presión arterial
        panel.add(createValueCard("🩺  Presión Arterial", bloodPressureLabel, "mmHg", BP_SYSTOLIC_COLOR));

        // Card de temperatura
        panel.add(createValueCard("🌡️  Temperatura", temperatureLabel, "°C", TEMP_COLOR));

        return panel;
    }

    private JPanel createValueCard(String title, JLabel valueLabel, String unit, Color accentColor) {
        JPanel card = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2d = (Graphics2D) g.create();
                g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                
                // Subtle gradient background
                GradientPaint gradient = new GradientPaint(
                    0, 0, Color.WHITE,
                    0, getHeight(), new Color(252, 252, 253)
                );
                g2d.setPaint(gradient);
                g2d.fillRoundRect(0, 0, getWidth(), getHeight(), 16, 16);
                
                // Subtle border
                g2d.setColor(BORDER_LIGHT);
                g2d.setStroke(new BasicStroke(1.5f));
                g2d.drawRoundRect(0, 0, getWidth() - 1, getHeight() - 1, 16, 16);
                
                // Accent bar at top
                g2d.setColor(accentColor);
                g2d.fillRoundRect(0, 0, getWidth(), 4, 16, 16);
                
                g2d.dispose();
            }
        };
        
        card.setLayout(new BorderLayout(0, 8));
        card.setOpaque(false);
        card.setBorder(new EmptyBorder(16, 16, 16, 16));

        // Title label
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        titleLabel.setForeground(TEXT_SECONDARY);
        card.add(titleLabel, BorderLayout.NORTH);

        // Value panel with large number
        JPanel valuePanel = new JPanel(new BorderLayout(8, 0));
        valuePanel.setOpaque(false);

        valueLabel.setFont(new Font("Segoe UI", Font.BOLD, 32));
        valueLabel.setForeground(accentColor);
        valuePanel.add(valueLabel, BorderLayout.CENTER);

        JLabel unitLabel = new JLabel(unit);
        unitLabel.setFont(new Font("Segoe UI", Font.PLAIN, 16));
        unitLabel.setForeground(TEXT_SECONDARY);
        unitLabel.setBorder(new EmptyBorder(10, 0, 0, 0));
        valuePanel.add(unitLabel, BorderLayout.EAST);

        card.add(valuePanel, BorderLayout.CENTER);

        return card;
    }

    private JTabbedPane createChartTabs() {
        JTabbedPane tabs = new JTabbedPane();
        tabs.setFont(new Font("Segoe UI", Font.BOLD, 13));
        tabs.setBackground(CARD_BG);
        tabs.setBorder(new EmptyBorder(8, 0, 0, 0));

        // Crear gráficas individuales para cada parámetro
        tabs.addTab("❤️ Frecuencia Cardíaca", createHeartRateChart());
        tabs.addTab("🫁 Saturación O₂", createSpo2Chart());
        tabs.addTab("🩺 Presión Arterial", createBloodPressureChart());
        tabs.addTab("🌡️ Temperatura", createTemperatureChart());

        return tabs;
    }

    private ChartPanel createHeartRateChart() {
        TimeSeriesCollection dataset = new TimeSeriesCollection(heartRateSeries);
        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                null,
                "Tiempo",
                "Frecuencia Cardíaca (bpm)",
                dataset,
                false,
                true,
                false
        );

        customizeChart(chart, HEART_COLOR);
        XYPlot plot = chart.getXYPlot();
        
        // Add area renderer with gradient fill
        XYAreaRenderer areaRenderer = new XYAreaRenderer();
        areaRenderer.setSeriesPaint(0, new GradientPaint(
            0, 0, new Color(239, 68, 68, 60),
            0, 300, new Color(239, 68, 68, 10)
        ));
        areaRenderer.setOutline(true);
        areaRenderer.setSeriesOutlinePaint(0, HEART_COLOR);
        areaRenderer.setSeriesOutlineStroke(0, new BasicStroke(
            3.5f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND
        ));
        plot.setRenderer(areaRenderer);
        
        // Add normal range indicator (60-100 bpm)
        IntervalMarker normalZone = new IntervalMarker(60, 100, ZONE_NORMAL);
        normalZone.setLabel("Rango Normal");
        normalZone.setLabelFont(new Font("Segoe UI", Font.PLAIN, 10));
        normalZone.setLabelPaint(new Color(34, 197, 94, 150));
        normalZone.setLabelAnchor(RectangleAnchor.TOP_RIGHT);
        normalZone.setLabelTextAnchor(TextAnchor.TOP_RIGHT);
        plot.addRangeMarker(normalZone, Layer.BACKGROUND);
        
        // Professional tooltip
        areaRenderer.setDefaultToolTipGenerator(new StandardXYToolTipGenerator(
            "<html><b>Frecuencia Cardíaca</b><br>Valor: {2} bpm<br>Hora: {1}</html>",
            new SimpleDateFormat("HH:mm:ss"),
            new java.text.DecimalFormat("0")
        ));
        
        ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setBackground(CHART_BG);
        chartPanel.setBorder(createChartBorder());
        return chartPanel;
    }

    private ChartPanel createSpo2Chart() {
        TimeSeriesCollection dataset = new TimeSeriesCollection(spo2Series);
        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                null,
                "Tiempo",
                "Saturación de Oxígeno (%)",
                dataset,
                false,
                true,
                false
        );

        customizeChart(chart, SPO2_COLOR);
        XYPlot plot = chart.getXYPlot();
        
        // Add area renderer with gradient fill
        XYAreaRenderer areaRenderer = new XYAreaRenderer();
        areaRenderer.setSeriesPaint(0, new GradientPaint(
            0, 0, new Color(59, 130, 246, 70),
            0, 300, new Color(59, 130, 246, 15)
        ));
        areaRenderer.setOutline(true);
        areaRenderer.setSeriesOutlinePaint(0, SPO2_COLOR);
        areaRenderer.setSeriesOutlineStroke(0, new BasicStroke(
            3.5f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND
        ));
        plot.setRenderer(areaRenderer);
        
        // Set Y-axis range for SpO2 (90-100%)
        NumberAxis rangeAxis = (NumberAxis) plot.getRangeAxis();
        rangeAxis.setRange(88, 101);
        
        // Add critical zone (< 92%)
        IntervalMarker criticalZone = new IntervalMarker(88, 92, ZONE_DANGER);
        criticalZone.setLabel("Crítico");
        criticalZone.setLabelFont(new Font("Segoe UI", Font.PLAIN, 10));
        criticalZone.setLabelPaint(new Color(239, 68, 68, 150));
        criticalZone.setLabelAnchor(RectangleAnchor.BOTTOM_RIGHT);
        criticalZone.setLabelTextAnchor(TextAnchor.BOTTOM_RIGHT);
        plot.addRangeMarker(criticalZone, Layer.BACKGROUND);
        
        // Add normal zone (95-100%)
        IntervalMarker normalZone = new IntervalMarker(95, 101, ZONE_NORMAL);
        normalZone.setLabel("Normal");
        normalZone.setLabelFont(new Font("Segoe UI", Font.PLAIN, 10));
        normalZone.setLabelPaint(new Color(34, 197, 94, 150));
        normalZone.setLabelAnchor(RectangleAnchor.TOP_RIGHT);
        normalZone.setLabelTextAnchor(TextAnchor.TOP_RIGHT);
        plot.addRangeMarker(normalZone, Layer.BACKGROUND);
        
        // Professional tooltip
        areaRenderer.setDefaultToolTipGenerator(new StandardXYToolTipGenerator(
            "<html><b>Saturación O₂</b><br>Valor: {2}%<br>Hora: {1}</html>",
            new SimpleDateFormat("HH:mm:ss"),
            new java.text.DecimalFormat("0.0")
        ));
        
        ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setBackground(CHART_BG);
        chartPanel.setBorder(createChartBorder());
        return chartPanel;
    }

    private ChartPanel createBloodPressureChart() {
        TimeSeriesCollection dataset = new TimeSeriesCollection();
        dataset.addSeries(systolicBpSeries);
        dataset.addSeries(diastolicBpSeries);

        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                null,
                "Tiempo",
                "Presión Arterial (mmHg)",
                dataset,
                true,
                true,
                false
        );

        chart.setBackgroundPaint(CHART_BG);
        chart.setAntiAlias(true);
        
        XYPlot plot = chart.getXYPlot();
        plot.setBackgroundPaint(PLOT_BG);
        plot.setDomainGridlinePaint(GRID_COLOR);
        plot.setRangeGridlinePaint(GRID_COLOR);
        plot.setOutlineVisible(false);

        // Use area renderer with gradient fills
        XYAreaRenderer areaRenderer = new XYAreaRenderer();
        
        // Systolic (top line) - Green gradient
        areaRenderer.setSeriesPaint(0, new GradientPaint(
            0, 0, new Color(34, 197, 94, 50),
            0, 300, new Color(34, 197, 94, 10)
        ));
        areaRenderer.setSeriesOutlinePaint(0, BP_SYSTOLIC_COLOR);
        areaRenderer.setSeriesOutlineStroke(0, new BasicStroke(
            3.5f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND
        ));
        
        // Diastolic (bottom line) - Teal gradient
        areaRenderer.setSeriesPaint(1, new GradientPaint(
            0, 0, new Color(16, 185, 129, 40),
            0, 300, new Color(16, 185, 129, 5)
        ));
        areaRenderer.setSeriesOutlinePaint(1, BP_DIASTOLIC_COLOR);
        areaRenderer.setSeriesOutlineStroke(1, new BasicStroke(
            3.5f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND
        ));
        
        areaRenderer.setOutline(true);
        plot.setRenderer(areaRenderer);
        
        // Add hypertension zones
        // Normal systolic: 90-120
        IntervalMarker normalSystolic = new IntervalMarker(90, 120, new Color(34, 197, 94, 20));
        normalSystolic.setLabel("Presión Normal");
        normalSystolic.setLabelFont(new Font("Segoe UI", Font.PLAIN, 10));
        normalSystolic.setLabelPaint(new Color(34, 197, 94, 150));
        normalSystolic.setLabelAnchor(RectangleAnchor.TOP_LEFT);
        normalSystolic.setLabelTextAnchor(TextAnchor.TOP_LEFT);
        plot.addRangeMarker(normalSystolic, Layer.BACKGROUND);
        
        // High blood pressure marker at 140
        ValueMarker highBpLine = new ValueMarker(140);
        highBpLine.setPaint(new Color(239, 68, 68, 100));
        highBpLine.setStroke(new BasicStroke(1.5f, BasicStroke.CAP_BUTT, BasicStroke.JOIN_MITER, 10.0f, new float[]{5.0f, 5.0f}, 0.0f));
        highBpLine.setLabel("Hipertensión");
        highBpLine.setLabelFont(new Font("Segoe UI", Font.PLAIN, 10));
        highBpLine.setLabelPaint(new Color(239, 68, 68, 180));
        highBpLine.setLabelAnchor(RectangleAnchor.TOP_RIGHT);
        highBpLine.setLabelTextAnchor(TextAnchor.BOTTOM_RIGHT);
        plot.addRangeMarker(highBpLine, Layer.BACKGROUND);
        
        // Professional tooltips
        areaRenderer.setDefaultToolTipGenerator(new StandardXYToolTipGenerator(
            "<html><b>{0}</b><br>Valor: {2} mmHg<br>Hora: {1}</html>",
            new SimpleDateFormat("HH:mm:ss"),
            new java.text.DecimalFormat("0")
        ));
        
        // Style axes
        DateAxis domainAxis = (DateAxis) plot.getDomainAxis();
        domainAxis.setDateFormatOverride(new SimpleDateFormat("HH:mm:ss"));
        domainAxis.setLabelFont(new Font("Segoe UI", Font.PLAIN, 12));
        domainAxis.setTickLabelFont(new Font("Segoe UI", Font.PLAIN, 11));
        domainAxis.setLabelPaint(TEXT_SECONDARY);
        domainAxis.setTickLabelPaint(TEXT_SECONDARY);
        
        NumberAxis rangeAxis = (NumberAxis) plot.getRangeAxis();
        rangeAxis.setLabelFont(new Font("Segoe UI", Font.PLAIN, 12));
        rangeAxis.setTickLabelFont(new Font("Segoe UI", Font.PLAIN, 11));
        rangeAxis.setLabelPaint(TEXT_SECONDARY);
        rangeAxis.setTickLabelPaint(TEXT_SECONDARY);
        
        // Modern legend styling
        if (chart.getLegend() != null) {
            chart.getLegend().setItemFont(new Font("Segoe UI", Font.BOLD, 11));
            chart.getLegend().setBackgroundPaint(new Color(255, 255, 255, 200));
        }

        ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setBackground(CHART_BG);
        chartPanel.setBorder(createChartBorder());
        return chartPanel;
    }

    private ChartPanel createTemperatureChart() {
        TimeSeriesCollection dataset = new TimeSeriesCollection(temperatureSeries);
        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                null,
                "Tiempo",
                "Temperatura Corporal (°C)",
                dataset,
                false,
                true,
                false
        );

        customizeChart(chart, TEMP_COLOR);
        XYPlot plot = chart.getXYPlot();
        
        // Add area renderer with warm gradient fill
        XYAreaRenderer areaRenderer = new XYAreaRenderer();
        areaRenderer.setSeriesPaint(0, new GradientPaint(
            0, 0, new Color(249, 115, 22, 65),
            0, 300, new Color(249, 115, 22, 12)
        ));
        areaRenderer.setOutline(true);
        areaRenderer.setSeriesOutlinePaint(0, TEMP_COLOR);
        areaRenderer.setSeriesOutlineStroke(0, new BasicStroke(
            3.5f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND
        ));
        plot.setRenderer(areaRenderer);

        // Set Y-axis range
        NumberAxis rangeAxis = (NumberAxis) plot.getRangeAxis();
        rangeAxis.setRange(35.0, 39.5);
        
        // Hypothermia zone (< 36°C)
        IntervalMarker hypothermia = new IntervalMarker(35.0, 36.0, new Color(59, 130, 246, 25));
        hypothermia.setLabel("Hipotermia");
        hypothermia.setLabelFont(new Font("Segoe UI", Font.PLAIN, 10));
        hypothermia.setLabelPaint(new Color(59, 130, 246, 150));
        hypothermia.setLabelAnchor(RectangleAnchor.BOTTOM_LEFT);
        hypothermia.setLabelTextAnchor(TextAnchor.BOTTOM_LEFT);
        plot.addRangeMarker(hypothermia, Layer.BACKGROUND);
        
        // Normal zone (36.1 - 37.2°C)
        IntervalMarker normalTemp = new IntervalMarker(36.1, 37.2, ZONE_NORMAL);
        normalTemp.setLabel("Temperatura Normal");
        normalTemp.setLabelFont(new Font("Segoe UI", Font.PLAIN, 10));
        normalTemp.setLabelPaint(new Color(34, 197, 94, 150));
        normalTemp.setLabelAnchor(RectangleAnchor.TOP_LEFT);
        normalTemp.setLabelTextAnchor(TextAnchor.TOP_LEFT);
        plot.addRangeMarker(normalTemp, Layer.BACKGROUND);
        
        // Fever marker at 38°C
        ValueMarker feverLine = new ValueMarker(38.0);
        feverLine.setPaint(new Color(239, 68, 68, 120));
        feverLine.setStroke(new BasicStroke(1.5f, BasicStroke.CAP_BUTT, BasicStroke.JOIN_MITER, 10.0f, new float[]{5.0f, 5.0f}, 0.0f));
        feverLine.setLabel("Fiebre");
        feverLine.setLabelFont(new Font("Segoe UI", Font.PLAIN, 10));
        feverLine.setLabelPaint(new Color(239, 68, 68, 180));
        feverLine.setLabelAnchor(RectangleAnchor.TOP_RIGHT);
        feverLine.setLabelTextAnchor(TextAnchor.BOTTOM_RIGHT);
        plot.addRangeMarker(feverLine, Layer.BACKGROUND);
        
        // Professional tooltip
        areaRenderer.setDefaultToolTipGenerator(new StandardXYToolTipGenerator(
            "<html><b>Temperatura</b><br>Valor: {2}°C<br>Hora: {1}</html>",
            new SimpleDateFormat("HH:mm:ss"),
            new java.text.DecimalFormat("0.00")
        ));

        ChartPanel chartPanel = new ChartPanel(chart);
        chartPanel.setBackground(CHART_BG);
        chartPanel.setBorder(createChartBorder());
        return chartPanel;
    }

    /**
     * Creates a professional border for chart panels with subtle shadow effect
     */
    private CompoundBorder createChartBorder() {
        return new CompoundBorder(
            new CompoundBorder(
                new EmptyBorder(2, 2, 4, 4), // Outer shadow space
                new LineBorder(SHADOW_COLOR, 2, true)
            ),
            new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(16, 16, 16, 16)
            )
        );
    }
    
    private void customizeChart(JFreeChart chart, Color seriesColor) {
        // Enable anti-aliasing for smooth rendering
        chart.setAntiAlias(true);
        chart.setBackgroundPaint(CHART_BG);
        chart.setBorderVisible(false);
        
        // Remove or style title if present
        if (chart.getTitle() != null) {
            chart.getTitle().setFont(new Font("Segoe UI", Font.BOLD, 16));
            chart.getTitle().setPaint(TEXT_PRIMARY);
        }

        XYPlot plot = chart.getXYPlot();
        plot.setBackgroundPaint(PLOT_BG);
        plot.setDomainGridlinePaint(GRID_COLOR);
        plot.setRangeGridlinePaint(GRID_COLOR);
        plot.setDomainGridlinesVisible(true);
        plot.setRangeGridlinesVisible(true);
        plot.setOutlineVisible(false);
        
        // Modern renderer with smooth, thick lines
        XYLineAndShapeRenderer renderer = new XYLineAndShapeRenderer();
        renderer.setSeriesPaint(0, seriesColor);
        renderer.setSeriesStroke(0, new BasicStroke(
            3.5f,                      // Line width
            BasicStroke.CAP_ROUND,     // Rounded ends
            BasicStroke.JOIN_ROUND     // Rounded joins
        ));
        renderer.setDefaultShapesVisible(false); // Hide data point markers for cleaner look
        plot.setRenderer(renderer);

        // Style domain axis (time)
        DateAxis domainAxis = (DateAxis) plot.getDomainAxis();
        domainAxis.setDateFormatOverride(new SimpleDateFormat("HH:mm:ss"));
        domainAxis.setLabelFont(new Font("Segoe UI", Font.PLAIN, 12));
        domainAxis.setTickLabelFont(new Font("Segoe UI", Font.PLAIN, 11));
        domainAxis.setLabelPaint(TEXT_SECONDARY);
        domainAxis.setTickLabelPaint(TEXT_SECONDARY);
        domainAxis.setAxisLinePaint(BORDER_LIGHT);
        domainAxis.setTickMarkPaint(BORDER_LIGHT);
        
        // Style range axis (values)
        NumberAxis rangeAxis = (NumberAxis) plot.getRangeAxis();
        rangeAxis.setLabelFont(new Font("Segoe UI", Font.PLAIN, 12));
        rangeAxis.setTickLabelFont(new Font("Segoe UI", Font.PLAIN, 11));
        rangeAxis.setLabelPaint(TEXT_SECONDARY);
        rangeAxis.setTickLabelPaint(TEXT_SECONDARY);
        rangeAxis.setAxisLinePaint(BORDER_LIGHT);
        rangeAxis.setTickMarkPaint(BORDER_LIGHT);
    }

    private void loadInitialData() {
        SwingWorker<List<VitalSignsReading>, Void> worker = new SwingWorker<>() {
            @Override
            protected List<VitalSignsReading> doInBackground() {
                System.out.println("[VitalSignsChart] Loading initial vital signs data for patient: " + patientId);
                try {
                    // Asegurar conexión a InfluxDB
                    influxService.connect();
                    System.out.println("[VitalSignsChart] InfluxDB connected successfully");
                    
                    List<VitalSignsReading> readings = influxService.getLatestPatientVitalSigns(patientId, 50);
                    System.out.println("[VitalSignsChart] Loaded " + (readings != null ? readings.size() : 0) + " initial readings");
                    return readings != null ? readings : new ArrayList<>();
                } catch (Exception e) {
                    System.err.println("[VitalSignsChart] ERROR loading initial data: " + e.getMessage());
                    e.printStackTrace();
                    return new ArrayList<>();
                }
            }

            @Override
            protected void done() {
                try {
                    List<VitalSignsReading> readings = get();
                    System.out.println("[VitalSignsChart] done() called with " + (readings != null ? readings.size() : 0) + " readings");
                    
                    if (readings != null && !readings.isEmpty()) {
                        System.out.println("[VitalSignsChart] Updating charts with " + readings.size() + " readings");
                        updateChartsWithReadings(readings);
                        
                        // Verificar si son datos de prueba (todos tienen el mismo patrón)
                        boolean isMockData = checkIfMockData(readings);
                        if (isMockData) {
                            lastUpdateLabel.setText("⚠ Datos de demostración (InfluxDB no accesible) - " + new SimpleDateFormat("HH:mm:ss").format(new Date()));
                            lastUpdateLabel.setForeground(new Color(255, 152, 0)); // Naranja
                        } else {
                            lastUpdateLabel.setText("✓ Última actualización: " + new SimpleDateFormat("HH:mm:ss").format(new Date()));
                            lastUpdateLabel.setForeground(new Color(40, 167, 69));
                        }
                    } else {
                        System.out.println("[VitalSignsChart] No data available for patient " + patientId);
                        lastUpdateLabel.setText("⚠ No hay datos de signos vitales para este paciente");
                        lastUpdateLabel.setForeground(new Color(255, 152, 0));
                        showNoDataMessage();
                    }
                } catch (Exception e) {
                    System.err.println("[VitalSignsChart] ERROR in done(): " + e.getMessage());
                    lastUpdateLabel.setText("✗ Error al cargar datos: " + e.getMessage());
                    lastUpdateLabel.setForeground(new Color(220, 53, 69));
                    e.printStackTrace();
                }
            }
        };
        worker.execute();
    }

    private void updateChartsWithReadings(List<VitalSignsReading> readings) {
        if (readings == null || readings.isEmpty()) {
            System.out.println("No readings to update charts");
            return;
        }

        System.out.println("Updating charts with " + readings.size() + " readings");
        
        for (VitalSignsReading reading : readings) {
            Date timestamp = Date.from(reading.timestamp);
            Second second = new Second(timestamp);

            heartRateSeries.addOrUpdate(second, reading.heartRate);
            spo2Series.addOrUpdate(second, reading.spo2);
            systolicBpSeries.addOrUpdate(second, reading.systolicBp);
            diastolicBpSeries.addOrUpdate(second, reading.diastolicBp);
            temperatureSeries.addOrUpdate(second, reading.temperature);
        }

        // Actualizar valores actuales con la última lectura
        VitalSignsReading latest = readings.get(readings.size() - 1);
        updateCurrentValues(latest);
        System.out.println("Charts updated successfully. Latest reading: " + latest);
    }

    private void updateCurrentValues(VitalSignsReading reading) {
        heartRateLabel.setText(String.valueOf(reading.heartRate));
        spo2Label.setText(String.valueOf(reading.spo2));
        bloodPressureLabel.setText(reading.systolicBp + "/" + reading.diastolicBp);
        temperatureLabel.setText(String.format("%.2f", reading.temperature));
    }

    private void startAutoUpdate() {
        updateTimer = new Timer(updateIntervalSeconds * 1000, e -> {
            SwingWorker<List<VitalSignsReading>, Void> worker = new SwingWorker<>() {
                @Override
                protected List<VitalSignsReading> doInBackground() {
                    // Obtener solo los últimos 10 registros para actualización incremental
                    return influxService.getLatestPatientVitalSigns(patientId, 10);
                }

                @Override
                protected void done() {
                    try {
                        List<VitalSignsReading> readings = get();
                        updateChartsWithReadings(readings);
                        lastUpdateLabel.setText("Última actualización: " + new SimpleDateFormat("HH:mm:ss").format(new Date()));
                    } catch (Exception ex) {
                        lastUpdateLabel.setText("Error en actualización automática");
                    }
                }
            };
            worker.execute();
        });
        updateTimer.start();
    }

    /**
     * Detener la actualización automática
     */
    public void stopAutoUpdate() {
        if (updateTimer != null) {
            updateTimer.stop();
        }
    }

    /**
     * Verificar si los datos son mock (de prueba)
     */
    private boolean checkIfMockData(List<VitalSignsReading> readings) {
        if (readings == null || readings.isEmpty()) return false;
        // Si los datos tienen valores muy uniformes, probablemente son mock
        // Esta es una heurística simple
        return readings.size() >= 5 && readings.get(0).heartRate >= 65 && readings.get(0).heartRate <= 80;
    }
    
    /**
     * Mostrar mensaje cuando no hay datos disponibles
     */
    private void showNoDataMessage() {
        SwingUtilities.invokeLater(() -> {
            heartRateLabel.setText("--");
            spo2Label.setText("--");
            bloodPressureLabel.setText("--/--");
            temperatureLabel.setText("--");
        });
    }

    /**
     * Limpiar recursos al cerrar
     */
    public void cleanup() {
        System.out.println("[VitalSignsChart] Cleaning up resources for patient " + patientId);
        stopAutoUpdate();
        influxService.disconnect();
    }
}
