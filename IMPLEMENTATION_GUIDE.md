# HeartGuard - Sistema de Monitoreo en Tiempo Real

## Resumen de Implementación

Este documento describe la implementación completa del sistema de monitoreo de signos vitales en tiempo real para HeartGuard.

## Arquitectura del Sistema

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
│   PostgreSQL    │◄─────┤  Generator   │─────►│   InfluxDB      │
│   (Pacientes)   │      │   (Python)   │      │ (Time Series)   │
└─────────────────┘      └──────────────┘      └─────────────────┘
                                                         ▲
                                                         │
                                                         │ Query
                                                         │
                                          ┌──────────────┴─────────┐
                                          │   Desktop App (Java)   │
                                          │  Patient Detail View   │
                                          │   Real-time Charts     │
                                          └────────────────────────┘
```

## Componentes Implementados

### 1. Generador de Datos en Tiempo Real (`services/realtime-data-generator/`)

**Archivo**: `generator.py`

**Funcionalidad**:
- Se conecta a PostgreSQL para obtener la lista de pacientes activos
- Genera datos sintéticos realistas de signos vitales cada N segundos
- Envía los datos a InfluxDB con tags de identificación del paciente

**Parámetros Generados** (basados en el dataset Excel):
- **GPS Longitude**: -100.56 a -100.21 (Monterrey)
- **GPS Latitude**: 25.52 a 25.84 (Monterrey)
- **Frecuencia Cardíaca**: 45-92 bpm
- **SpO2**: 91-100%
- **Presión Arterial Sistólica**: 102-154 mmHg
- **Presión Arterial Diastólica**: 59-94 mmHg
- **Temperatura**: 36.14-37.02°C

**Características**:
- Cada paciente tiene valores base ligeramente diferentes
- Variaciones realistas en cada lectura
- Movimientos GPS simulados
- NO genera alertas (se reservan para el modelo de IA)

**Configuración** (`.env`):
```bash
DATABASE_URL=postgres://heartguard_app:dev_change_me@134.199.204.58:5432/heartguard?sslmode=disable
INFLUXDB_URL=http://134.199.204.58:8086
INFLUXDB_TOKEN=heartguard-dev-token-change-me
INFLUXDB_ORG=heartguard
INFLUXDB_BUCKET=timeseries
GENERATION_INTERVAL=5  # Segundos entre generaciones
LOG_LEVEL=INFO
```

### 2. Servicio InfluxDB para Desktop App

**Archivo**: `desktop-app/src/main/java/com/heartguard/desktop/api/InfluxDBService.java`

**Funcionalidad**:
- Conexión con InfluxDB
- Consulta de datos de series temporales
- Filtrado por paciente
- Soporte para ventanas de tiempo

**Métodos principales**:
- `getPatientVitalSigns(patientId, hoursBack)`: Obtiene datos históricos
- `getLatestPatientVitalSigns(patientId, limit)`: Obtiene últimos N registros

### 3. Panel de Gráficas en Tiempo Real

**Archivo**: `desktop-app/src/main/java/com/heartguard/desktop/ui/user/VitalSignsChartPanel.java`

**Características**:
- **4 tarjetas de valores actuales**:
  - ❤️ Frecuencia Cardíaca (rojo)
  - 🫁 Oxígeno en Sangre (azul)
  - 🩺 Presión Arterial (verde)
  - 🌡️ Temperatura (naranja)

- **4 gráficas en tiempo real** (tabs):
  - Frecuencia Cardíaca vs Tiempo
  - SpO2 vs Tiempo
  - Presión Arterial (sistólica/diastólica) vs Tiempo
  - Temperatura vs Tiempo

- **Actualización automática**: Cada 10 segundos por defecto
- **Ventana deslizante**: Últimas 50 lecturas
- **Timestamp**: Última actualización visible

### 4. Integración en Patient Detail Dialog

**Archivo**: `desktop-app/src/main/java/com/heartguard/desktop/ui/user/PatientDetailDialog.java`

**Modificaciones**:
- Tamaño aumentado: 1000x800px para acomodar gráficas
- Estructura reorganizada:
  - Tabs superiores: Métricas, Alertas, Notas (250px altura)
  - Panel inferior: Gráficas en tiempo real
- Configuración de InfluxDB desde variables de entorno
- Cleanup adecuado de recursos al cerrar

## Instalación y Configuración

### Backend (Generador de Datos)

1. **Navegar al directorio**:
```bash
cd /root/HeartGuard/services/realtime-data-generator
```

2. **Crear entorno virtual** (si no existe):
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**:
```bash
# El archivo .env ya está configurado con la IP correcta
cat .env
```

5. **Ejecutar el generador**:
```bash
# Opción 1: Con el script
./start.sh

# Opción 2: Directamente
python generator.py
```

### Desktop App

1. **Configurar variables de entorno**:
```bash
cd /root/HeartGuard/desktop-app
cp .env.example .env
# Editar .env si es necesario (ya tiene valores por defecto correctos)
```

2. **Compilar con Maven**:
```bash
mvn clean package
```

3. **Ejecutar**:
```bash
java -jar target/desktop-app-1.0.0.jar
```

## Flujo de Datos

1. **PostgreSQL** contiene:
   - Tabla `heartguard.patients` con información de pacientes
   - Cada paciente tiene: id, nombre, email, org_id, risk_level

2. **Generador Python**:
   - Lee pacientes de PostgreSQL cada N segundos
   - Genera signos vitales sintéticos para cada paciente
   - Escribe en InfluxDB con measurement `vital_signs`

3. **InfluxDB** almacena:
   - **Measurement**: `vital_signs`
   - **Tags**: `patient_id`, `patient_name`, `org_id`, `risk_level`
   - **Fields**: `heart_rate`, `spo2`, `systolic_bp`, `diastolic_bp`, `temperature`, `gps_longitude`, `gps_latitude`
   - **Timestamp**: Automático

4. **Desktop App**:
   - Usuario abre detalle de paciente
   - App consulta InfluxDB filtrando por `patient_id`
   - Muestra gráficas actualizadas cada 10 segundos
   - Cleanup al cerrar

## Estructura de Datos en InfluxDB

### Ejemplo de Query Flux:
```flux
from(bucket: "timeseries")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
  |> filter(fn: (r) => r["patient_id"] == "some-uuid")
  |> filter(fn: (r) => 
      r["_field"] == "heart_rate" or
      r["_field"] == "spo2" or
      r["_field"] == "systolic_bp" or
      r["_field"] == "diastolic_bp" or
      r["_field"] == "temperature"
  )
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"], desc: false)
```

## Testing

### 1. Verificar conexiones

**PostgreSQL**:
```bash
psql -h 134.199.204.58 -U heartguard_app -d heartguard -c "SELECT COUNT(*) FROM heartguard.patients;"
```

**InfluxDB**:
```bash
curl -v http://134.199.204.58:8086/health
```

### 2. Probar generador

```bash
cd /root/HeartGuard/services/realtime-data-generator
source venv/bin/activate
python generator.py
```

Deberías ver logs como:
```
2024-11-21 12:00:00 - __main__ - INFO - Connecting to PostgreSQL...
2024-11-21 12:00:00 - __main__ - INFO - PostgreSQL connection established
2024-11-21 12:00:00 - __main__ - INFO - Connecting to InfluxDB...
2024-11-21 12:00:00 - __main__ - INFO - InfluxDB connection established
2024-11-21 12:00:00 - __main__ - INFO - Retrieved 5 active patients from database
2024-11-21 12:00:00 - __main__ - INFO - Successfully generated and sent data for 5/5 patients
```

### 3. Verificar datos en InfluxDB

Accede a la UI de InfluxDB en `http://134.199.204.58:8086` y ejecuta:
```flux
from(bucket: "timeseries")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "vital_signs")
  |> limit(n: 10)
```

### 4. Probar desktop app

1. Compilar: `mvn clean package`
2. Ejecutar: `java -jar target/desktop-app-1.0.0.jar`
3. Iniciar sesión
4. Navegar a un paciente
5. Abrir "Ver Detalles"
6. Verificar que las gráficas aparecen y se actualizan

## Troubleshooting

### Generador no encuentra pacientes

**Problema**: `No patients found in database`

**Solución**:
```bash
# Verificar que existen pacientes
psql -h 134.199.204.58 -U heartguard_app -d heartguard -c "SELECT id, name FROM heartguard.patients LIMIT 5;"

# Si no hay pacientes, ejecutar seed
psql -h 134.199.204.58 -U heartguard_app -d heartguard -f /root/HeartGuard/db/seed.sql
```

### Desktop app no muestra gráficas

**Problema**: Gráficas vacías o error de conexión

**Soluciones**:
1. Verificar que el generador está corriendo
2. Verificar que hay datos en InfluxDB (ver testing paso 3)
3. Verificar variables de entorno en desktop app
4. Revisar logs de la aplicación

### Error de conexión a InfluxDB

**Problema**: `Connection refused` o `Unauthorized`

**Soluciones**:
1. Verificar que InfluxDB está corriendo:
   ```bash
   docker ps | grep influxdb
   ```
2. Verificar token en `.env`:
   ```bash
   # Debe coincidir con el token configurado en docker-compose.yml
   echo $INFLUXDB_TOKEN
   ```
3. Verificar firewall/red

### Gráficas no se actualizan

**Problema**: Valores estáticos, no hay actualización automática

**Soluciones**:
1. Verificar que el generador sigue corriendo
2. Aumentar el intervalo de actualización si hay latencia de red
3. Revisar logs del generador para errores

## Archivos Creados/Modificados

### Nuevos Archivos:
- `services/realtime-data-generator/generator.py`
- `services/realtime-data-generator/requirements.txt`
- `services/realtime-data-generator/README.md`
- `services/realtime-data-generator/start.sh`
- `services/realtime-data-generator/.env` (actualizado)
- `desktop-app/src/main/java/com/heartguard/desktop/api/InfluxDBService.java`
- `desktop-app/src/main/java/com/heartguard/desktop/ui/user/VitalSignsChartPanel.java`
- `IMPLEMENTATION_GUIDE.md` (este archivo)

### Archivos Modificados:
- `desktop-app/pom.xml` (agregado InfluxDB client)
- `desktop-app/src/main/java/com/heartguard/desktop/ui/user/PatientDetailDialog.java`
- `desktop-app/.env.example` (agregadas variables de InfluxDB)

## Notas Importantes

1. **Alertas NO incluidas**: Las columnas de alertas del Excel NO se generan porque son para el modelo de IA
2. **Datos sintéticos**: Los valores son aleatorios pero realistas, respetando rangos del dataset
3. **Variabilidad individual**: Cada paciente tiene valores base ligeramente diferentes
4. **IP hardcoded**: 134.199.204.58 está configurada como la VM del backend
5. **Performance**: El generador puede manejar cientos de pacientes sin problemas
6. **Escalabilidad**: Para producción, considerar:
   - Rate limiting en InfluxDB queries
   - Caching de datos recientes
   - Batch writes al generar datos

## Próximos Pasos

1. **Modelo de IA**: Implementar detección de alertas basada en los signos vitales
2. **Notificaciones**: Enviar alertas en tiempo real cuando se detecten anomalías
3. **Historial**: Agregar vista de tendencias a largo plazo
4. **Exportación**: Permitir exportar datos para análisis
5. **Dashboard agregado**: Vista de múltiples pacientes simultáneamente

## Contacto y Soporte

Para preguntas o problemas, revisar:
- Logs del generador: `services/realtime-data-generator/generator.log`
- Logs de InfluxDB: `docker logs heartguard-influxdb`
- Logs de PostgreSQL: `docker logs heartguard-postgres`
