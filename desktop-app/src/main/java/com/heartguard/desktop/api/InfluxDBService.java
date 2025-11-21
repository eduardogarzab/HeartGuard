package com.heartguard.desktop.api;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import com.influxdb.query.FluxRecord;
import com.influxdb.query.FluxTable;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Cliente para consultar datos de series temporales desde InfluxDB.
 * Lee signos vitales de pacientes en tiempo real.
 */
public class InfluxDBService {
    private final String url;
    private final String token;
    private final String org;
    private final String bucket;
    private InfluxDBClient client;

    private static final int CONNECTION_TIMEOUT_SECONDS = 5;
    private static final int READ_TIMEOUT_SECONDS = 10;
    private boolean useMockData = false;
    
    public InfluxDBService(String url, String token, String org, String bucket) {
        this.url = url;
        this.token = token;
        this.org = org;
        this.bucket = bucket;
    }

    /**
     * Conectar al servidor InfluxDB
     */
    public void connect() {
        if (client == null) {
            System.out.println("[InfluxDB] Connecting to: " + url);
            System.out.println("[InfluxDB] Organization: " + org);
            System.out.println("[InfluxDB] Bucket: " + bucket);
            System.out.println("[InfluxDB] Timeout: " + CONNECTION_TIMEOUT_SECONDS + "s");
            
            try {
                // Crear cliente InfluxDB con configuración básica
                client = InfluxDBClientFactory.create(url, token.toCharArray(), org, bucket);
                
                // Verificar conexión con una query simple
                System.out.println("[InfluxDB] Testing connection...");
                try {
                    client.getQueryApi().query("buckets()", org);
                    System.out.println("[InfluxDB] ✓ Connection established and verified successfully");
                    useMockData = false;
                } catch (Exception testEx) {
                    System.err.println("[InfluxDB] ⚠ WARNING: Connection established but cannot query.");
                    System.err.println("[InfluxDB] Error: " + testEx.getMessage());
                    System.err.println("[InfluxDB] Will use mock data for demonstration");
                    useMockData = true;
                }
            } catch (Exception e) {
                System.err.println("[InfluxDB] ✗ ERROR connecting: " + e.getMessage());
                System.err.println("[InfluxDB] Will use mock data for demonstration");
                useMockData = true;
                client = null;
            }
        } else {
            System.out.println("[InfluxDB] Already connected");
        }
    }

    /**
     * Desconectar del servidor InfluxDB
     */
    public void disconnect() {
        if (client != null) {
            client.close();
            client = null;
        }
    }

    /**
     * Obtener los datos de signos vitales de un paciente en las últimas N horas.
     * 
     * @param patientId ID del paciente
     * @param hoursBack Cuántas horas hacia atrás consultar
     * @return Lista de lecturas de signos vitales
     */
    public List<VitalSignsReading> getPatientVitalSigns(String patientId, int hoursBack) {
        List<VitalSignsReading> readings = new ArrayList<>();

        if (client == null) {
            System.out.println("InfluxDB client not connected, connecting now...");
            connect();
        }

        try {
            // Flux query para obtener los datos del paciente
            String flux = String.format("""
                from(bucket: "%s")
                  |> range(start: -%dh)
                  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
                  |> filter(fn: (r) => r["patient_id"] == "%s")
                  |> filter(fn: (r) => 
                      r["_field"] == "heart_rate" or
                      r["_field"] == "spo2" or
                      r["_field"] == "systolic_bp" or
                      r["_field"] == "diastolic_bp" or
                      r["_field"] == "temperature" or
                      r["_field"] == "gps_longitude" or
                      r["_field"] == "gps_latitude"
                  )
                  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                  |> sort(columns: ["_time"], desc: false)
                """, bucket, hoursBack, patientId);

            List<FluxTable> tables = client.getQueryApi().query(flux);

            for (FluxTable table : tables) {
                for (FluxRecord record : table.getRecords()) {
                    VitalSignsReading reading = new VitalSignsReading();
                    reading.timestamp = record.getTime();

                    // Extraer valores de los campos
                    Object heartRate = record.getValueByKey("heart_rate");
                    Object spo2 = record.getValueByKey("spo2");
                    Object systolicBp = record.getValueByKey("systolic_bp");
                    Object diastolicBp = record.getValueByKey("diastolic_bp");
                    Object temperature = record.getValueByKey("temperature");
                    Object gpsLong = record.getValueByKey("gps_longitude");
                    Object gpsLat = record.getValueByKey("gps_latitude");

                    if (heartRate != null) reading.heartRate = ((Number) heartRate).intValue();
                    if (spo2 != null) reading.spo2 = ((Number) spo2).intValue();
                    if (systolicBp != null) reading.systolicBp = ((Number) systolicBp).intValue();
                    if (diastolicBp != null) reading.diastolicBp = ((Number) diastolicBp).intValue();
                    if (temperature != null) reading.temperature = ((Number) temperature).doubleValue();
                    if (gpsLong != null) reading.gpsLongitude = ((Number) gpsLong).doubleValue();
                    if (gpsLat != null) reading.gpsLatitude = ((Number) gpsLat).doubleValue();

                    readings.add(reading);
                }
            }
        } catch (Exception e) {
            System.err.println("Error querying InfluxDB: " + e.getMessage());
            e.printStackTrace();
        }

        return readings;
    }

    /**
     * Obtener los últimos N registros de signos vitales de un paciente.
     * Útil para gráficas en tiempo real con ventana deslizante.
     * 
     * @param patientId ID del paciente
     * @param limit Número de registros a obtener
     * @return Lista de lecturas de signos vitales
     */
    public List<VitalSignsReading> getLatestPatientVitalSigns(String patientId, int limit) {
        List<VitalSignsReading> readings = new ArrayList<>();

        if (client == null) {
            System.out.println("[InfluxDB] Client not connected, connecting now...");
            connect();
        }
        
        // Si debemos usar datos mock, generarlos
        if (useMockData || client == null) {
            System.out.println("[InfluxDB] ⚠ Using mock data (InfluxDB not available)");
            return generateMockData(patientId, limit);
        }
        
        System.out.println("[InfluxDB] Querying for patient: " + patientId + " (last " + limit + " readings)");

        try {
            // Flux query para obtener los últimos N registros
            String flux = String.format("""
                from(bucket: "%s")
                  |> range(start: -24h)
                  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
                  |> filter(fn: (r) => r["patient_id"] == "%s")
                  |> filter(fn: (r) => 
                      r["_field"] == "heart_rate" or
                      r["_field"] == "spo2" or
                      r["_field"] == "systolic_bp" or
                      r["_field"] == "diastolic_bp" or
                      r["_field"] == "temperature" or
                      r["_field"] == "gps_longitude" or
                      r["_field"] == "gps_latitude"
                  )
                  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                  |> sort(columns: ["_time"], desc: true)
                  |> limit(n: %d)
                """, bucket, patientId, limit);

            System.out.println("[InfluxDB] Executing Flux query:");
            System.out.println(flux);
            
            List<FluxTable> tables = client.getQueryApi().query(flux);
            
            System.out.println("[InfluxDB] Query returned " + tables.size() + " tables");

            for (FluxTable table : tables) {
                System.out.println("[InfluxDB] Processing table with " + table.getRecords().size() + " records");
                for (FluxRecord record : table.getRecords()) {
                    VitalSignsReading reading = new VitalSignsReading();
                    reading.timestamp = record.getTime();

                    Object heartRate = record.getValueByKey("heart_rate");
                    Object spo2 = record.getValueByKey("spo2");
                    Object systolicBp = record.getValueByKey("systolic_bp");
                    Object diastolicBp = record.getValueByKey("diastolic_bp");
                    Object temperature = record.getValueByKey("temperature");
                    Object gpsLong = record.getValueByKey("gps_longitude");
                    Object gpsLat = record.getValueByKey("gps_latitude");

                    if (heartRate != null) reading.heartRate = ((Number) heartRate).intValue();
                    if (spo2 != null) reading.spo2 = ((Number) spo2).intValue();
                    if (systolicBp != null) reading.systolicBp = ((Number) systolicBp).intValue();
                    if (diastolicBp != null) reading.diastolicBp = ((Number) diastolicBp).intValue();
                    if (temperature != null) reading.temperature = ((Number) temperature).doubleValue();
                    if (gpsLong != null) reading.gpsLongitude = ((Number) gpsLong).doubleValue();
                    if (gpsLat != null) reading.gpsLatitude = ((Number) gpsLat).doubleValue();

                    readings.add(reading);
                    System.out.println("[InfluxDB] Read: " + reading);
                }
            }

            // Revertir para tener orden cronológico ascendente
            readings.sort((a, b) -> a.timestamp.compareTo(b.timestamp));
            
            System.out.println("[InfluxDB] Successfully retrieved " + readings.size() + " readings for patient " + patientId);
        } catch (Exception e) {
            System.err.println("[InfluxDB] ERROR querying: " + e.getMessage());
            e.printStackTrace();
        }

        return readings;
    }

    /**
     * Generar datos mock para demostración cuando InfluxDB no está disponible
     */
    private List<VitalSignsReading> generateMockData(String patientId, int limit) {
        List<VitalSignsReading> mockReadings = new ArrayList<>();
        Instant now = Instant.now();
        
        System.out.println("[InfluxDB] Generating " + limit + " mock readings for patient " + patientId);
        
        for (int i = limit - 1; i >= 0; i--) {
            VitalSignsReading reading = new VitalSignsReading();
            
            // Timestamp: cada 10 minutos hacia atrás
            reading.timestamp = now.minus(i * 10, java.time.temporal.ChronoUnit.MINUTES);
            
            // Generar valores realistas con pequeñas variaciones
            double variation = Math.sin(i * 0.5) * 5; // Variación sinusoidal
            
            reading.heartRate = (int) (72 + variation + (Math.random() * 6 - 3));
            reading.spo2 = (int) (97 + (Math.random() * 2));
            reading.systolicBp = (int) (120 + variation + (Math.random() * 8 - 4));
            reading.diastolicBp = (int) (80 + variation * 0.5 + (Math.random() * 6 - 3));
            reading.temperature = 36.5 + (Math.random() * 0.6 - 0.3);
            reading.gpsLatitude = 25.6866 + (Math.random() * 0.01 - 0.005);
            reading.gpsLongitude = -100.3161 + (Math.random() * 0.01 - 0.005);
            
            mockReadings.add(reading);
        }
        
        System.out.println("[InfluxDB] Generated " + mockReadings.size() + " mock readings");
        return mockReadings;
    }
    
    /**
     * Clase que representa una lectura de signos vitales
     */
    public static class VitalSignsReading {
        public Instant timestamp;
        public int heartRate;
        public int spo2;
        public int systolicBp;
        public int diastolicBp;
        public double temperature;
        public double gpsLongitude;
        public double gpsLatitude;

        public VitalSignsReading() {
        }

        @Override
        public String toString() {
            return String.format("VitalSigns[time=%s, HR=%d, SpO2=%d, BP=%d/%d, Temp=%.2f°C]",
                    timestamp, heartRate, spo2, systolicBp, diastolicBp, temperature);
        }
    }
}
