# HeartGuard Desktop App

Aplicación de escritorio Java Swing para el sistema HeartGuard, incluyendo visualización de signos vitales en tiempo real.

## Requisitos

- **Java 21** o superior
- **Maven 3.6+** para compilación
- Archivo **`.env`** con configuración (ver abajo)

## Configuración Inicial

### 1. Clonar el repositorio

```bash
git clone https://github.com/eduardogarzab/HeartGuard.git
cd HeartGuard/desktop-app
```

### 2. Crear archivo de configuración

```bash
cp .env.example .env
```

### 3. Editar el archivo .env

Abre el archivo `.env` y configura tus valores:

```dotenv
# Gateway API Configuration
GATEWAY_BASE_URL=http://tu-servidor:8080

# InfluxDB Configuration (for real-time vital signs)
INFLUXDB_URL=http://tu-servidor:8086
INFLUXDB_TOKEN=tu-token-de-influxdb
INFLUXDB_ORG=heartguard
INFLUXDB_BUCKET=timeseries
```

**⚠️ IMPORTANTE**: 
- El archivo `.env` NO se sube al repositorio (está en `.gitignore`)
- Nunca expongas tokens o credenciales en el código fuente
- Cada desarrollador/entorno debe tener su propio `.env`

### 4. Compilar

```bash
mvn clean package
```

Esto generará: `target/heartguard-desktop-1.0-SNAPSHOT.jar`

### 5. Ejecutar

```bash
./launch.sh
```

O manualmente:
```bash
java -jar target/heartguard-desktop-1.0-SNAPSHOT.jar
```

## Arquitectura de Configuración

### AppConfig - Clase Centralizada

Toda la configuración se maneja en `com.heartguard.desktop.config.AppConfig`:

```java
// Singleton que carga configuración desde .env
AppConfig config = AppConfig.getInstance();

// Obtener valores
String influxUrl = config.getInfluxdbUrl();
String token = config.getInfluxdbToken();
```

### Orden de Prioridad

1. **Archivo `.env`** en el directorio actual
2. **Variables de entorno del sistema**
3. **Error si falta configuración requerida**

**NO hay valores por defecto hardcodeados** - todo viene de configuración externa.

## Características

### 🔐 Autenticación
- Login con email y contraseña
- Soporte para múltiples roles (Superadmin, Org Admin, Usuario/Caregiver)
- Tokens JWT para autenticación

### 📊 Dashboard de Usuario
- Lista de pacientes asignados
- Mapa con ubicaciones en tiempo real
- Alertas recientes

### 💓 Signos Vitales en Tiempo Real
- **Frecuencia Cardíaca**: 45-92 bpm
- **SpO2**: 91-100%
- **Presión Arterial**: Sistólica/Diastólica
- **Temperatura**: 36-37°C
- **Gráficas interactivas** con actualización automática cada 10 segundos

### 🗺️ Geolocalización
- Mapa interactivo con JxBrowser (Chromium)
- Ubicación de pacientes en tiempo real
- Historial de ubicaciones

## Estructura del Proyecto

```
desktop-app/
├── src/main/java/com/heartguard/desktop/
│   ├── config/
│   │   └── AppConfig.java          # Configuración centralizada desde .env
│   ├── api/
│   │   ├── ApiClient.java          # Cliente HTTP para backend
│   │   └── InfluxDBService.java    # Cliente para InfluxDB
│   ├── ui/
│   │   ├── LoginFrame.java
│   │   ├── superadmin/
│   │   └── user/
│   │       ├── UserDashboardPanel.java
│   │       ├── PatientDetailDialog.java
│   │       └── VitalSignsChartPanel.java  # Gráficas en tiempo real
│   └── HeartGuardApp.java          # Main
├── .env                            # Configuración local (NO se commitea)
├── .env.example                    # Plantilla de configuración
├── .gitignore                      # Incluye .env
├── pom.xml
├── launch.sh                       # Script de lanzamiento
└── README.md
```

## Dependencias Principales

- **OkHttp 4.12.0**: Cliente HTTP
- **Gson 2.10.1**: Procesamiento JSON
- **FlatLaf 3.2.5**: Look and Feel moderno
- **JxBrowser 7.39.2**: Motor Chromium embebido
- **JFreeChart 1.5.4**: Gráficos estadísticos
- **InfluxDB Client 6.11.0**: Consulta de series temporales
- **dotenv-java 3.0.0**: Carga de configuración desde .env

## Flujo de Datos

```
Desktop App
    ↓
    ├─→ Gateway API (puerto 8080)
    │   ├─→ Auth Service: Login, tokens
    │   ├─→ User Service: Pacientes, alertas, notas
    │   └─→ Patient Service: Detalles de pacientes
    │
    └─→ InfluxDB (puerto 8086)
        └─→ Bucket: timeseries
            └─→ Measurement: vital_signs
                ├─→ Tags: patient_id, patient_name, org_id, risk_level
                └─→ Fields: heart_rate, spo2, systolic_bp, diastolic_bp, temperature
```

## Scripts Útiles

### launch.sh
Lanza la aplicación después de verificar que existe `.env` y el JAR.

### verify.sh
Verifica que todos los servicios backend están disponibles antes de ejecutar.

```bash
./verify.sh
```

Comprueba:
- ✓ Gateway accesible
- ✓ Realtime Generator funcionando
- ✓ InfluxDB disponible
- ✓ Pacientes con datos
- ✓ JAR compilado

## Desarrollo

### Ejecutar desde IDE

1. Crear archivo `.env` en `desktop-app/`
2. Configurar el IDE para que el Working Directory sea `desktop-app/`
3. Ejecutar clase principal: `com.heartguard.desktop.HeartGuardApp`

### Logs de Configuración

Al iniciar, la aplicación mostrará:

```
============================================================
HeartGuard Desktop App - Configuration Loaded
============================================================
Gateway URL: http://tu-servidor:8080
InfluxDB URL: http://tu-servidor:8086
InfluxDB Org: heartguard
InfluxDB Bucket: timeseries
InfluxDB Token: hear...e-me
============================================================
```

Los tokens se enmascaran en los logs para seguridad.

## Troubleshooting

### Error: "INFLUXDB_URL is required"

**Solución**: Crea el archivo `.env` con la configuración necesaria:
```bash
cp .env.example .env
# Edita .env con tus valores
```

### Error: "Could not load .env file"

**Solución**: Asegúrate de ejecutar la aplicación desde el directorio `desktop-app/`:
```bash
cd /path/to/HeartGuard/desktop-app
java -jar target/heartguard-desktop-1.0-SNAPSHOT.jar
```

### No se muestran datos en las gráficas

**Verificar**:
1. El servicio realtime-data-generator está corriendo
2. InfluxDB es accesible desde tu máquina
3. El token de InfluxDB es correcto
4. Hay datos para el paciente seleccionado

```bash
# Verificar servicio realtime
curl http://tu-servidor:8080/realtime/status

# Verificar InfluxDB
curl http://tu-servidor:8086/health
```

## Seguridad

- ✅ **Sin credenciales hardcodeadas**: Todo en `.env`
- ✅ **`.env` en `.gitignore`**: No se sube al repositorio
- ✅ **Tokens enmascarados en logs**: Solo muestra primeros y últimos 4 caracteres
- ✅ **Validación de configuración**: Falla rápido si falta configuración requerida

## Documentación Adicional

- **README_VITAL_SIGNS.md**: Guía detallada de configuración de signos vitales
- **CONFIGURACION_COMPLETA.md**: Documentación exhaustiva del sistema completo

## Licencia

Propietario - HeartGuard Team
