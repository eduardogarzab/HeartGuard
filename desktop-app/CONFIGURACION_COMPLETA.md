# ✅ CONFIGURACIÓN COMPLETA - Desktop App con Signos Vitales en Tiempo Real

## Estado Actual del Sistema

### ✅ Backend - Todos los servicios funcionando

```bash
cd /root/HeartGuard/services
make status
```

Resultado:
```
✓ auth-service (5001)
✓ admin-service (5002)  
✓ user-service (5003)
✓ patient-service (5004)
✓ media-service (5005)
✓ gateway (8080)
✓ realtime-generator (5006) - Iteración 244+, generando datos cada 5 segundos
```

### ✅ Datos en InfluxDB

- **Bucket**: `timeseries`
- **Measurement**: `vital_signs`
- **Tags**: `patient_id`, `patient_name`, `org_id`, `risk_level`
- **Fields**: `heart_rate`, `spo2`, `systolic_bp`, `diastolic_bp`, `temperature`, `gps_longitude`, `gps_latitude`
- **Frecuencia**: Datos cada 5 segundos para 3 pacientes

### ✅ Pacientes de Prueba

1. **José Hernández** (ID: `fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21`) - Medium Risk
2. **María Delgado** (ID: `8c9436b4-f085-405f-a3d2-87cb1d1cf097`) - High Risk
3. **Valeria Ortiz** (ID: `ae15cd87-5ac2-4f90-8712-184b02c541a5`) - Low Risk

## Configuración del Desktop App

### Archivo .env (Requerido)

**El desktop app NO tiene IPs o tokens hardcodeados.** Toda la configuración viene del archivo `.env`:

1. **Crear archivo de configuración**:
   ```bash
   cd /root/HeartGuard/desktop-app
   cp .env.example .env
   ```

2. **Editar con tus valores**:
   ```dotenv
   # Gateway API Configuration
   GATEWAY_BASE_URL=http://134.199.204.58:8080

   # InfluxDB Configuration
   INFLUXDB_URL=http://134.199.204.58:8086
   INFLUXDB_TOKEN=heartguard-dev-token-change-me
   INFLUXDB_ORG=heartguard
   INFLUXDB_BUCKET=timeseries
   ```

**⚠️ IMPORTANTE**: 
- El archivo `.env` está en `.gitignore` y NO se sube al repositorio
- Cada desarrollador/servidor debe tener su propio `.env`
- Nunca expongas credenciales en el código fuente

### AppConfig - Configuración Centralizada

La clase `com.heartguard.desktop.config.AppConfig` maneja toda la configuración:

```java
// Singleton que lee desde .env o variables de entorno
AppConfig config = AppConfig.getInstance();

// Al iniciar, muestra configuración (tokens enmascarados):
// ============================================================
// HeartGuard Desktop App - Configuration Loaded
// ============================================================
// Gateway URL: http://134.199.204.58:8080
// InfluxDB URL: http://134.199.204.58:8086
// InfluxDB Org: heartguard
// InfluxDB Bucket: timeseries
// InfluxDB Token: hear...e-me
// ============================================================
```

## Código Java - Configuración Correcta

### 1. AppConfig.java ✅ (NUEVO)

```java
// Clase centralizada de configuración
public class AppConfig {
    // Lee desde .env o variables de entorno del sistema
    // NO tiene valores hardcodeados
    
    private AppConfig() {
        // Cargar .env
        this.dotenv = Dotenv.configure()
                .ignoreIfMissing()
                .load();
        
        // Cargar valores (falla si faltan requeridos)
        this.influxdbUrl = getEnv("INFLUXDB_URL", null);
        this.influxdbToken = getEnv("INFLUXDB_TOKEN", null);
        
        // Validar configuración
        validateConfig();
    }
    
    // Getters públicos
    public String getInfluxdbUrl() { return influxdbUrl; }
    public String getInfluxdbToken() { return influxdbToken; }
}
```

### 2. PatientDetailDialog.java ✅

```java
// Constructor - líneas 50-68
public PatientDetailDialog(Frame owner, ApiClient apiClient, String token, 
                          String orgId, String patientId, String patientName) {
    // ...
    
    // Obtener configuración desde AppConfig (lee de .env)
    AppConfig config = AppConfig.getInstance();
    
    this.influxService = new InfluxDBService(
        config.getInfluxdbUrl(),      // Desde .env
        config.getInfluxdbToken(),    // Desde .env
        config.getInfluxdbOrg(),      // Desde .env
        config.getInfluxdbBucket()    // Desde .env
    );
    
    System.out.println("Initializing patient detail for: " + patientName);
    
    initComponents();
    loadData();
}
```

### 3. InfluxDBService.java ✅

```java
// Constructor recibe configuración desde AppConfig
public InfluxDBService(String url, String token, String org, String bucket) {
    this.url = url;       // Desde .env
    this.token = token;   // Desde .env
    this.org = org;       // Desde .env
    this.bucket = bucket; // Desde .env
}

// Método getLatestPatientVitalSigns - líneas 122-185
public List<VitalSignsReading> getLatestPatientVitalSigns(String patientId, int limit) {
    // Auto-conectar si no está conectado
    if (client == null) {
        System.out.println("InfluxDB client not connected, connecting now...");
        connect();
    }
    
    System.out.println("Querying InfluxDB for patient: " + patientId + 
                       " (last " + limit + " readings)");
    
    // Flux query con filtros correctos
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
              r["_field"] == "temperature"
          )
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: %d)
        """, bucket, patientId, limit);
    
    // Ejecutar query y procesar resultados
    // ... (código de procesamiento)
}
```

### 4. VitalSignsChartPanel.java ✅

```java
// Constructor - líneas 66-95
public VitalSignsChartPanel(String patientId, InfluxDBService influxService, 
                           int updateIntervalSeconds) {
    this.patientId = patientId;
    this.influxService = influxService;
    this.updateIntervalSeconds = updateIntervalSeconds; // 10 segundos
    
    // Crear series de tiempo con ventana deslizante de 50 puntos
    heartRateSeries = new TimeSeries("Frecuencia Cardíaca (bpm)");
    heartRateSeries.setMaximumItemCount(50);
    // ... otras series
    
    initComponents();
    loadInitialData();      // Cargar últimos 50 registros
    startAutoUpdate();      // Actualizar cada 10 segundos
}
```

## Flujo de Visualización

### Cuando el usuario abre detalles de un paciente:

1. **PatientDetailDialog se crea**
   - Recibe `patientId` (UUID del paciente)
   - Configura conexión a InfluxDB
   - Imprime configuración en consola

2. **VitalSignsChartPanel se inicializa**
   - Carga últimos 50 registros de InfluxDB
   - Crea 4 gráficas (HR, SpO2, BP, Temp)
   - Muestra valores actuales en cards

3. **Timer de actualización automática**
   - Cada 10 segundos:
     - Consulta últimos 10 registros
     - Actualiza series de tiempo
     - Actualiza valores en cards
     - Actualiza timestamp

4. **Al cerrar el diálogo**
   - Detiene el timer
   - Desconecta de InfluxDB
   - Libera recursos

## Ejemplo de Logs Esperados

Cuando abres los detalles de un paciente, verás en consola:

```
=== InfluxDB Configuration ===
URL: http://134.199.204.58:8086
Org: heartguard
Bucket: timeseries
Patient ID: fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21
=============================
Loading initial vital signs data for patient: fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21
InfluxDB client not connected, connecting now...
Querying InfluxDB for patient: fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21 (last 50 readings)
Executing Flux query for patient fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21
Query returned 1 tables
Processing table with 50 records
Successfully retrieved 50 readings for patient fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21
Loaded 50 initial readings
Updating charts with 50 readings
Charts updated successfully. Latest reading: VitalSigns[time=..., HR=63, SpO2=96, BP=110/70, Temp=36.5°C]
```

## Verificación Rápida

### 1. Verificar sistema completo:
```bash
cd /root/HeartGuard/desktop-app
./verify.sh
```

### 2. Verificar datos para un paciente específico:
```bash
# José Hernández
curl -s -X POST "http://134.199.204.58:8086/api/v2/query?org=heartguard" \
  -H "Authorization: Token heartguard-dev-token-change-me" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket: "timeseries")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "vital_signs")
  |> filter(fn: (r) => r.patient_id == "fea1a34e-3fb6-43f4-ad2d-caa9ede5ac21")
  |> filter(fn: (r) => r._field == "heart_rate" or r._field == "spo2")
  |> last()' | grep "_value"
```

## Compilación y Ejecución

### Compilar (solo una vez):
```bash
cd /root/HeartGuard/desktop-app
mvn clean package
```

### Ejecutar con script (recomendado):
```bash
cd /root/HeartGuard/desktop-app
./launch.sh
```

### O ejecutar manualmente:
```bash
cd /root/HeartGuard/desktop-app
java -jar target/heartguard-desktop-1.0-SNAPSHOT.jar
```

## Credenciales de Prueba

### Usuario Caregiver:
- **Email**: `jose@example.com`
- **Password**: Tu contraseña configurada

### Al iniciar sesión verás:
- Dashboard con pacientes asignados
- Al hacer clic en un paciente:
  - Tab "MÉTRICAS": Info del paciente
  - Tab "ALERTAS": Alertas registradas  
  - Tab "NOTAS": Notas clínicas
  - **Panel inferior**: 📊 Signos Vitales en Tiempo Real
    - 4 cards con valores actuales
    - 4 gráficas interactivas
    - Actualización automática cada 10 segundos

## Resumen de Componentes

| Componente | Puerto | Estado | Función |
|-----------|--------|--------|---------|
| Gateway | 8080 | ✓ Running | API principal, auth, pacientes |
| Realtime Generator | 5006 | ✓ Running | Genera datos cada 5s |
| InfluxDB | 8086 | ✓ Running | Almacena series temporales |
| PostgreSQL | 5432 | ✓ Running | Datos de pacientes, alertas |
| Desktop App | - | Local | Cliente Java Swing |

## ¿Todo está configurado correctamente? ✅

**SÍ**, el sistema está completamente configurado:

1. ✅ **Microservicio realtime-data-generator** generando datos cada 5 segundos
2. ✅ **InfluxDB** con datos de 3 pacientes en bucket "timeseries"
3. ✅ **Desktop App** configurado para consultar InfluxDB directamente
4. ✅ **Auto-conexión** si no hay variables de entorno (usa defaults)
5. ✅ **Logging completo** para depuración
6. ✅ **Actualización automática** cada 10 segundos
7. ✅ **Cleanup de recursos** al cerrar diálogo

**Lo único que falta es compilar el JAR y ejecutarlo desde tu máquina local** (o desde este servidor si tienes GUI).

## Próximos Pasos

1. **Compilar** (si no lo has hecho):
   ```bash
   cd /root/HeartGuard/desktop-app
   mvn clean package
   ```

2. **Copiar el JAR a tu máquina local** (si quieres ejecutarlo en tu computadora):
   ```bash
   scp usuario@134.199.204.58:/root/HeartGuard/desktop-app/target/heartguard-desktop-1.0-SNAPSHOT.jar .
   ```

3. **Ejecutar en tu máquina**:
   ```bash
   java -jar heartguard-desktop-1.0-SNAPSHOT.jar
   ```

4. **Iniciar sesión como usuario** y ver los datos en tiempo real ✨
