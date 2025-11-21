# Sistema de Monitoreo en Tiempo Real - HeartGuard

## 🎯 Resumen

Se ha implementado un sistema completo de monitoreo de signos vitales en tiempo real que incluye:

1. **Generador de datos sintéticos** (Python) que lee pacientes de PostgreSQL y genera signos vitales realistas
2. **Almacenamiento en InfluxDB** para datos de series temporales
3. **Visualización en tiempo real** en la aplicación de escritorio con gráficas interactivas

## 📊 Datos Generados

Basados en los rangos del dataset Excel proporcionado:

| Parámetro | Rango | Unidad |
|-----------|-------|--------|
| GPS Longitude | -100.56 a -100.21 | Monterrey, MX |
| GPS Latitude | 25.52 a 25.84 | Monterrey, MX |
| Frecuencia Cardíaca | 45-92 | bpm |
| SpO2 | 91-100 | % |
| Presión Sistólica | 102-154 | mmHg |
| Presión Diastólica | 59-94 | mmHg |
| Temperatura | 36.14-37.02 | °C |

**Nota**: Las alertas NO se generan sintéticamente, están reservadas para el modelo de IA.

## 🚀 Inicio Rápido

### Opción 1: Script Automatizado
```bash
./quick-start.sh
```

### Opción 2: Manual

#### 1. Iniciar Generador de Datos
```bash
cd services/realtime-data-generator
./start.sh
```

El generador:
- ✅ Se conecta a PostgreSQL en 134.199.204.58:5432
- ✅ Lee pacientes activos
- ✅ Genera signos vitales cada 5 segundos
- ✅ Envía datos a InfluxDB en 134.199.204.58:8086

#### 2. Compilar Desktop App
```bash
cd desktop-app
cp .env.example .env
mvn clean package
```

#### 3. Ejecutar Desktop App
```bash
java -jar target/desktop-app-1.0.0.jar
```

En la app:
1. Inicia sesión
2. Navega a un paciente
3. Haz clic en "Ver Detalles"
4. 📊 Verás las gráficas de signos vitales en tiempo real

## 📁 Estructura del Sistema

```
HeartGuard/
├── services/
│   └── realtime-data-generator/      # Generador Python
│       ├── generator.py               # Script principal
│       ├── requirements.txt           # Dependencias Python
│       ├── start.sh                   # Script de inicio
│       ├── .env                       # Configuración (IP: 134.199.204.58)
│       └── README.md                  # Documentación del generador
│
├── desktop-app/
│   ├── pom.xml                        # Maven (InfluxDB client agregado)
│   ├── .env.example                   # Variables de entorno
│   └── src/main/java/.../
│       ├── api/
│       │   └── InfluxDBService.java   # Cliente InfluxDB
│       └── ui/user/
│           ├── VitalSignsChartPanel.java        # Panel de gráficas
│           └── PatientDetailDialog.java         # Diálogo modificado
│
├── IMPLEMENTATION_GUIDE.md            # Guía detallada de implementación
├── quick-start.sh                     # Script de inicio rápido
└── README_REALTIME.md                 # Este archivo
```

## 🔄 Flujo de Datos

```
┌─────────────────┐
│   PostgreSQL    │  ← Pacientes registrados
│ 134.199.204.58  │
│     :5432       │
└────────┬────────┘
         │
         │ Query cada 5s
         ▼
┌─────────────────┐
│   Generator     │  ← Genera signos vitales sintéticos
│   (Python)      │
└────────┬────────┘
         │
         │ Write
         ▼
┌─────────────────┐
│   InfluxDB      │  ← Almacena series temporales
│ 134.199.204.58  │     Measurement: vital_signs
│     :8086       │     Tags: patient_id, org_id, risk_level
└────────┬────────┘     Fields: heart_rate, spo2, BP, temp, GPS
         │
         │ Query cada 10s
         ▼
┌─────────────────┐
│  Desktop App    │  ← Muestra gráficas en tiempo real
│   (Java/Swing)  │     4 tarjetas + 4 gráficas interactivas
└─────────────────┘
```

## 🎨 Interfaz de Usuario

### Tarjetas de Valores Actuales
- ❤️ **Frecuencia Cardíaca** (rojo) - bpm
- 🫁 **Oxígeno en Sangre** (azul) - %
- 🩺 **Presión Arterial** (verde) - mmHg
- 🌡️ **Temperatura** (naranja) - °C

### Gráficas (Tabs)
1. Frecuencia Cardíaca vs Tiempo
2. SpO2 vs Tiempo
3. Presión Arterial (sistólica/diastólica) vs Tiempo
4. Temperatura vs Tiempo

**Actualización**: Cada 10 segundos
**Ventana**: Últimas 50 lecturas

## ✅ Verificación

### 1. Verificar Generador
```bash
cd services/realtime-data-generator
source venv/bin/activate
python generator.py
```

Deberías ver:
```
2024-11-21 12:00:00 - INFO - PostgreSQL connection established
2024-11-21 12:00:00 - INFO - InfluxDB connection established
2024-11-21 12:00:00 - INFO - Retrieved 3 active patients from database
2024-11-21 12:00:00 - INFO - Successfully generated and sent data for 3/3 patients
```

### 2. Verificar Datos en InfluxDB
```bash
curl "http://134.199.204.58:8086/api/v2/query?org=heartguard" \
  -H "Authorization: Token heartguard-dev-token-change-me" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket: "timeseries")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
  |> limit(n: 10)'
```

### 3. Verificar Desktop App
1. Ejecuta la aplicación
2. Abre detalle de cualquier paciente
3. Las gráficas deberían mostrar datos y actualizarse automáticamente

## 🔧 Configuración

### Variables de Entorno - Generador
```bash
# services/realtime-data-generator/.env
DATABASE_URL=postgres://heartguard_app:dev_change_me@134.199.204.58:5432/heartguard
INFLUXDB_URL=http://134.199.204.58:8086
INFLUXDB_TOKEN=heartguard-dev-token-change-me
INFLUXDB_ORG=heartguard
INFLUXDB_BUCKET=timeseries
GENERATION_INTERVAL=5
```

### Variables de Entorno - Desktop App
```bash
# desktop-app/.env (opcional, hay valores por defecto)
INFLUXDB_URL=http://134.199.204.58:8086
INFLUXDB_TOKEN=heartguard-dev-token-change-me
INFLUXDB_ORG=heartguard
INFLUXDB_BUCKET=timeseries
```

## 🐛 Troubleshooting

### Generador no encuentra pacientes
```bash
# Verificar pacientes
PGPASSWORD=dev_change_me psql -h 134.199.204.58 -U heartguard_app -d heartguard \
  -c "SELECT id, person_name FROM heartguard.patients LIMIT 5;"

# Si no hay pacientes, ejecutar seed
PGPASSWORD=dev_change_me psql -h 134.199.204.58 -U heartguard_app -d heartguard \
  -f db/seed.sql
```

### Desktop app no muestra gráficas
1. Verificar que el generador está corriendo
2. Verificar datos en InfluxDB (comando anterior)
3. Revisar logs de la aplicación

### Error de conexión
```bash
# Verificar servicios
docker ps | grep -E "postgres|influx"

# Verificar puertos abiertos
nc -zv 134.199.204.58 5432
nc -zv 134.199.204.58 8086
```

## 📦 Dependencias Agregadas

### Python (Generador)
- `psycopg2-binary==2.9.9` - PostgreSQL client
- `influxdb-client==1.38.0` - InfluxDB client
- `python-dotenv==1.0.0` - Environment variables

### Java (Desktop App)
```xml
<dependency>
    <groupId>com.influxdb</groupId>
    <artifactId>influxdb-client-java</artifactId>
    <version>6.11.0</version>
</dependency>
```

## 📈 Características Implementadas

✅ Generación de datos sintéticos realistas
✅ Conexión PostgreSQL → InfluxDB
✅ Variabilidad individual por paciente
✅ GPS con simulación de movimiento
✅ Cliente InfluxDB en desktop app
✅ Panel de gráficas con 4 tabs
✅ Actualización automática cada 10s
✅ Tarjetas de valores actuales
✅ Ventana deslizante de 50 lecturas
✅ Cleanup adecuado de recursos
✅ Documentación completa

## 🚧 Próximos Pasos

1. **Modelo de IA**: Detección de alertas basada en signos vitales
2. **Notificaciones**: Alertas en tiempo real
3. **Historial**: Tendencias a largo plazo
4. **Exportación**: Datos para análisis externo
5. **Dashboard agregado**: Múltiples pacientes simultáneamente

## 📚 Documentación Adicional

- `IMPLEMENTATION_GUIDE.md` - Guía completa de implementación
- `services/realtime-data-generator/README.md` - Detalles del generador
- `desktop-app/.env.example` - Variables de entorno

## 🎉 Estado del Proyecto

**COMPLETADO** ✅

Todos los componentes están implementados y funcionando:
- Generador de datos ✅
- Almacenamiento en InfluxDB ✅
- Visualización en desktop app ✅
- Documentación completa ✅
- Scripts de inicio rápido ✅

El sistema está listo para ser usado. Solo es necesario:
1. Iniciar el generador: `cd services/realtime-data-generator && ./start.sh`
2. Abrir la desktop app y navegar a un paciente
3. Las gráficas se actualizarán automáticamente cada 10 segundos
