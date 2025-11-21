package com.heartguard.desktop.ui.user;

import com.heartguard.desktop.api.InfluxDBService;
import com.heartguard.desktop.api.InfluxDBService.VitalSignsReading;
import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.DateAxis;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.plot.XYPlot;
import org.jfree.chart.renderer.xy.XYLineAndShapeRenderer;
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
import java.util.Date;
import java.util.List;

/**
 * Panel que muestra gráficas de signos vitales en tiempo real.
 * Se actualiza automáticamente cada N segundos.
 */
public class VitalSignsChartPanel extends JPanel {
    private static final Color CARD_BG = Color.WHITE;
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color BORDER_LIGHT = new Color(223, 227, 230);
    private static final Color PRIMARY_BLUE = new Color(0, 120, 215);
    private static final Color SUCCESS_GREEN = new Color(40, 167, 69);
    private static final Color DANGER_RED = new Color(220, 53, 69);
    private static final Color WARNING_ORANGE = new Color(255, 152, 0);

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
        setLayout(new BorderLayout(8, 8));
        setBackground(CARD_BG);
        setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(12, 12, 12, 12)
        ));

        // Panel superior con valores actuales
        JPanel currentValuesPanel = createCurrentValuesPanel();
        add(currentValuesPanel, BorderLayout.NORTH);

        // Panel de gráficas (tabs para diferentes parámetros)
        JTabbedPane chartTabs = createChartTabs();
        add(chartTabs, BorderLayout.CENTER);

        // Panel inferior con estado
        JPanel statusPanel = new JPanel(new BorderLayout());
        statusPanel.setOpaque(false);
        statusPanel.setBorder(new EmptyBorder(8, 0, 0, 0));

        lastUpdateLabel.setFont(new Font("Inter", Font.PLAIN, 12));
        lastUpdateLabel.setForeground(new Color(96, 103, 112));
        statusPanel.add(lastUpdateLabel, BorderLayout.WEST);

        add(statusPanel, BorderLayout.SOUTH);
    }

    private JPanel createCurrentValuesPanel() {
        JPanel panel = new JPanel(new GridLayout(1, 4, 12, 0));
        panel.setOpaque(false);
        panel.setBorder(new EmptyBorder(0, 0, 12, 0));

        // Card de frecuencia cardíaca
        panel.add(createValueCard("❤️ Frecuencia Cardíaca", heartRateLabel, "bpm", DANGER_RED));

        // Card de SpO2
        panel.add(createValueCard("🫁 Oxígeno en Sangre", spo2Label, "%", PRIMARY_BLUE));

        // Card de presión arterial
        panel.add(createValueCard("🩺 Presión Arterial", bloodPressureLabel, "mmHg", SUCCESS_GREEN));

        // Card de temperatura
        panel.add(createValueCard("🌡️ Temperatura", temperatureLabel, "°C", WARNING_ORANGE));

        return panel;
    }

    private JPanel createValueCard(String title, JLabel valueLabel, String unit, Color accentColor) {
        JPanel card = new JPanel(new BorderLayout(4, 4));
        card.setBackground(CARD_BG);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(8, 12, 8, 12)
        ));

        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("Inter", Font.PLAIN, 11));
        titleLabel.setForeground(new Color(96, 103, 112));
        card.add(titleLabel, BorderLayout.NORTH);

        JPanel valuePanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 0));
        valuePanel.setOpaque(false);

        valueLabel.setFont(new Font("Inter", Font.BOLD, 20));
        valueLabel.setForeground(accentColor);
        valuePanel.add(valueLabel);

        JLabel unitLabel = new JLabel(unit);
        unitLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        unitLabel.setForeground(new Color(96, 103, 112));
        valuePanel.add(unitLabel);

        card.add(valuePanel, BorderLayout.CENTER);

        return card;
    }

    private JTabbedPane createChartTabs() {
        JTabbedPane tabs = new JTabbedPane();
        tabs.setFont(new Font("Inter", Font.PLAIN, 13));

        // Crear gráficas individuales para cada parámetro
        tabs.addTab("Frecuencia Cardíaca", createHeartRateChart());
        tabs.addTab("SpO2", createSpo2Chart());
        tabs.addTab("Presión Arterial", createBloodPressureChart());
        tabs.addTab("Temperatura", createTemperatureChart());

        return tabs;
    }

    private ChartPanel createHeartRateChart() {
        TimeSeriesCollection dataset = new TimeSeriesCollection(heartRateSeries);
        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                "Frecuencia Cardíaca en Tiempo Real",
                "Tiempo",
                "Frecuencia (bpm)",
                dataset,
                false,
                true,
                false
        );

        customizeChart(chart, DANGER_RED);
        return new ChartPanel(chart);
    }

    private ChartPanel createSpo2Chart() {
        TimeSeriesCollection dataset = new TimeSeriesCollection(spo2Series);
        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                "Oxígeno en Sangre en Tiempo Real",
                "Tiempo",
                "SpO2 (%)",
                dataset,
                false,
                true,
                false
        );

        customizeChart(chart, PRIMARY_BLUE);
        return new ChartPanel(chart);
    }

    private ChartPanel createBloodPressureChart() {
        TimeSeriesCollection dataset = new TimeSeriesCollection();
        dataset.addSeries(systolicBpSeries);
        dataset.addSeries(diastolicBpSeries);

        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                "Presión Arterial en Tiempo Real",
                "Tiempo",
                "Presión (mmHg)",
                dataset,
                true,
                true,
                false
        );

        XYPlot plot = chart.getXYPlot();
        plot.setBackgroundPaint(Color.WHITE);
        plot.setDomainGridlinePaint(new Color(230, 230, 230));
        plot.setRangeGridlinePaint(new Color(230, 230, 230));

        XYLineAndShapeRenderer renderer = new XYLineAndShapeRenderer();
        renderer.setSeriesPaint(0, SUCCESS_GREEN);
        renderer.setSeriesPaint(1, new Color(76, 175, 80));
        renderer.setSeriesStroke(0, new BasicStroke(2.0f));
        renderer.setSeriesStroke(1, new BasicStroke(2.0f));
        plot.setRenderer(renderer);

        DateAxis axis = (DateAxis) plot.getDomainAxis();
        axis.setDateFormatOverride(new SimpleDateFormat("HH:mm:ss"));

        return new ChartPanel(chart);
    }

    private ChartPanel createTemperatureChart() {
        TimeSeriesCollection dataset = new TimeSeriesCollection(temperatureSeries);
        JFreeChart chart = ChartFactory.createTimeSeriesChart(
                "Temperatura Corporal en Tiempo Real",
                "Tiempo",
                "Temperatura (°C)",
                dataset,
                false,
                true,
                false
        );

        customizeChart(chart, WARNING_ORANGE);

        // Ajustar rango del eje Y para temperatura (normalmente 36-38°C)
        XYPlot plot = chart.getXYPlot();
        NumberAxis rangeAxis = (NumberAxis) plot.getRangeAxis();
        rangeAxis.setRange(35.5, 38.5);

        return new ChartPanel(chart);
    }

    private void customizeChart(JFreeChart chart, Color seriesColor) {
        chart.setBackgroundPaint(CARD_BG);
        chart.getTitle().setFont(new Font("Inter", Font.BOLD, 14));

        XYPlot plot = chart.getXYPlot();
        plot.setBackgroundPaint(Color.WHITE);
        plot.setDomainGridlinePaint(new Color(230, 230, 230));
        plot.setRangeGridlinePaint(new Color(230, 230, 230));

        XYLineAndShapeRenderer renderer = new XYLineAndShapeRenderer();
        renderer.setSeriesPaint(0, seriesColor);
        renderer.setSeriesStroke(0, new BasicStroke(2.0f));
        plot.setRenderer(renderer);

        DateAxis axis = (DateAxis) plot.getDomainAxis();
        axis.setDateFormatOverride(new SimpleDateFormat("HH:mm:ss"));
    }

    private void loadInitialData() {
        SwingWorker<List<VitalSignsReading>, Void> worker = new SwingWorker<>() {
            @Override
            protected List<VitalSignsReading> doInBackground() {
                System.out.println("Loading initial vital signs data for patient: " + patientId);
                try {
                    List<VitalSignsReading> readings = influxService.getLatestPatientVitalSigns(patientId, 50);
                    System.out.println("Loaded " + (readings != null ? readings.size() : 0) + " initial readings");
                    return readings;
                } catch (Exception e) {
                    System.err.println("Error loading initial data: " + e.getMessage());
                    e.printStackTrace();
                    return new ArrayList<>();
                }
            }

            @Override
            protected void done() {
                try {
                    List<VitalSignsReading> readings = get();
                    if (readings != null && !readings.isEmpty()) {
                        updateChartsWithReadings(readings);
                        lastUpdateLabel.setText("Última actualización: " + new SimpleDateFormat("HH:mm:ss").format(new Date()));
                    } else {
                        lastUpdateLabel.setText("No hay datos disponibles para este paciente");
                    }
                } catch (Exception e) {
                    lastUpdateLabel.setText("Error al cargar datos: " + e.getMessage());
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
     * Limpiar recursos al cerrar
     */
    public void cleanup() {
        stopAutoUpdate();
        influxService.disconnect();
    }
}
