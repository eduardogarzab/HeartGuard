# HeartGuard Desktop App - Guía de Configuración

## Visualización de Signos Vitales en Tiempo Real

El desktop app está configurado para mostrar los signos vitales de los pacientes en tiempo real, obteniendo los datos directamente desde InfluxDB.

## Requisitos

1. **Servicios en ejecución**:
   - Gateway (puerto 8080)
   - Realtime Data Generator (puerto 5006)
   - InfluxDB (puerto 8086)
   - PostgreSQL (puerto 5432)

2. **Java 17 o superior** instalado
3. **Maven** para compilar (o usar el JAR pre-compilado)

## Configuración

### Archivo .env (Requerido)

El desktop app **NO tiene valores hardcodeados**. Toda la configuración se carga desde el archivo `.env`.

1. **Copia el archivo de ejemplo**:
   ```bash
   cd /root/HeartGuard/desktop-app
   cp .env.example .env
   ```

2. **Edita el archivo .env** con tus valores:
   ```bash
   nano .env
   ```

3. **Configuración requerida**:
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
- El archivo `.env` está en `.gitignore` y **NO se subirá al repositorio**
- Nunca expongas tokens o IPs en el código fuente
- Cada desarrollador/entorno debe tener su propio archivo `.env`

### Variables de Entorno (Alternativa)

También puedes usar variables de entorno del sistema en lugar del archivo .env:

```bash
export GATEWAY_BASE_URL="http://tu-servidor:8080"
export INFLUXDB_URL="http://tu-servidor:8086"
export INFLUXDB_TOKEN="tu-token"
export INFLUXDB_ORG="heartguard"
export INFLUXDB_BUCKET="timeseries"
```

**Nota**: El archivo `.env` tiene prioridad sobre las variables de entorno del sistema.

## Compilación

```bash
cd /root/HeartGuard/desktop-app
mvn clean package
```

Esto generará: `target/heartguard-desktop-1.0-SNAPSHOT.jar`

## Ejecución

### Opción 1: Script de Lanzamiento (Recomendado)

```bash
cd /root/HeartGuard/desktop-app
./launch.sh
```

Este script:
- Verifica que existe el archivo `.env`
- Verifica que el JAR existe
- Lanza la aplicación (lee configuración desde `.env`)

### Opción 2: Ejecución Manual

```bash
cd /root/HeartGuard/desktop-app
java -jar target/heartguard-desktop-1.0-SNAPSHOT.jar
```

La aplicación leerá automáticamente el archivo `.env` del directorio actual.

### Opción 3: Desde IDE (IntelliJ IDEA, Eclipse, VS Code)

**Opción A: Usar archivo .env** (Recomendado)
1. Crear archivo `.env` en el directorio `desktop-app/`
2. Configurar el IDE para que el directorio de trabajo sea `desktop-app/`
3. Ejecutar la clase principal: `com.heartguard.desktop.HeartGuardApp`

**Opción B: Variables de entorno en configuración de ejecución**
1. Abrir configuración de ejecución en tu IDE
2. Agregar variables de entorno:
   - `INFLUXDB_URL=http://tu-servidor:8086`
   - `INFLUXDB_TOKEN=tu-token`
   - `INFLUXDB_ORG=heartguard`
   - `INFLUXDB_BUCKET=timeseries`
3. Ejecutar la clase principal

## Uso - Visualización de Signos Vitales

### Paso 1: Iniciar Sesión como Usuario

1. Abre el desktop app
2. Selecciona el tipo de usuario: **"Usuario (Caregiver/Care Team)"**
3. Ingresa credenciales:
   - **Email**: `jose@example.com` (o cualquier usuario válido)
   - **Password**: Tu contraseña

### Paso 2: Ver Dashboard

Una vez autenticado, verás:
- **Lista de pacientes** que tienes asignados
- **Alertas** recientes
- **Ubicaciones** en el mapa

### Paso 3: Ver Detalles del Paciente

1. **Haz clic en un paciente** de la lista
2. Se abrirá el diálogo **"Resumen Clínico"**
3. Verás:
   - **Tab "MÉTRICAS"**: Información básica del paciente
   - **Tab "ALERTAS"**: Alertas registradas
   - **Tab "NOTAS"**: Notas clínicas
   - **Panel de Gráficas**: Signos vitales en tiempo real (debajo de los tabs)

### Paso 4: Visualización de Signos Vitales

El panel de gráficas muestra:

#### 📊 **Valores Actuales** (parte superior)
- ❤️ **Frecuencia Cardíaca**: Valor actual en bpm
- 🫁 **Oxígeno en Sangre (SpO2)**: Valor actual en %
- 🩺 **Presión Arterial**: Sistólica/Diastólica en mmHg
- 🌡️ **Temperatura**: Valor actual en °C

#### 📈 **Gráficas Históricas** (tabs inferiores)
1. **Tab "Frecuencia Cardíaca"**: Gráfica de tiempo real
2. **Tab "SpO2"**: Gráfica de oxigenación
3. **Tab "Presión Arterial"**: Gráfica con presión sistólica y diastólica
4. **Tab "Temperatura"**: Gráfica de temperatura corporal

**Características**:
- ✅ **Actualización automática cada 10 segundos**
- ✅ **Ventana deslizante** de últimos 50 registros
- ✅ **Gráficas interactivas** (zoom, pan)
- ✅ **Colores diferenciados** por parámetro
- ✅ **Timestamp** de última actualización

## Verificación de Datos

### Antes de iniciar el desktop app, verifica que el generador está funcionando:

```bash
# 1. Verificar que el servicio realtime está corriendo
curl http://localhost:8080/realtime/health

# 2. Verificar que hay pacientes siendo monitoreados
curl http://localhost:8080/realtime/patients

# 3. Verificar que hay datos en InfluxDB
curl -s -X POST "http://134.199.204.58:8086/api/v2/query?org=heartguard" \
  -H "Authorization: Token heartguard-dev-token-change-me" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket: "timeseries")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "vital_signs")
  |> count()'
```

Si estos comandos funcionan, el desktop app podrá conectarse y mostrar los datos.

## Troubleshooting

### Problema: No se muestran datos

**Posibles causas**:

1. **El servicio realtime-data-generator no está corriendo**
   ```bash
   cd /root/HeartGuard/services
   make status
   # Debe mostrar realtime-generator como Running
   ```

2. **InfluxDB no es accesible**
   ```bash
   curl http://134.199.204.58:8086/health
   # Debe responder con {"name":"influxdb","message":"ready for queries and writes","status":"pass"}
   ```

3. **El token de InfluxDB es incorrecto**
   - Verifica que `INFLUXDB_TOKEN` sea: `heartguard-dev-token-change-me`

4. **El paciente no tiene datos generados aún**
   - Espera al menos 5-10 segundos después de iniciar el realtime-generator
   - El generador escribe datos cada 5 segundos

### Problema: Error de conexión al abrir detalles del paciente

**Solución**:
- Verifica que las variables de entorno estén configuradas
- Revisa los logs en la consola del desktop app
- El app imprimirá:
  ```
  === InfluxDB Configuration ===
  URL: http://134.199.204.58:8086
  Org: heartguard
  Bucket: timeseries
  Patient ID: [uuid-del-paciente]
  =============================
  ```

### Problema: "No hay datos disponibles para este paciente"

**Posibles causas**:

1. **El paciente no está siendo monitoreado por el realtime-generator**
   ```bash
   curl http://localhost:8080/realtime/patients | jq '.patients[].id'
   ```
   Compara estos UUIDs con el ID del paciente que intentas ver.

2. **Los datos se están escribiendo con un ID diferente**
   - Verifica en los logs del realtime-generator que el patient_id coincida

## Arquitectura del Sistema

```
Desktop App (Java)
    ↓
    ├─→ Gateway (8080) → Backend APIs → PostgreSQL (pacientes, alertas, notas)
    └─→ InfluxDB (8086) → Bucket: timeseries (signos vitales)
          ↑
          └─── Realtime Generator (5006) → Escribe datos cada 5 segundos
```

## Flujo de Datos

1. **Realtime Generator** consulta pacientes activos en PostgreSQL
2. **Genera datos sintéticos** de signos vitales realistas
3. **Escribe a InfluxDB** bucket "timeseries" con measurement "vital_signs"
4. **Desktop App** consulta InfluxDB directamente usando el `patient_id`
5. **VitalSignsChartPanel** se actualiza automáticamente cada 10 segundos

## Logs de Depuración

Cuando abres los detalles de un paciente, el desktop app imprime en consola:

```
=== InfluxDB Configuration ===
URL: http://134.199.204.58:8086
Org: heartguard
Bucket: timeseries
Patient ID: ae15cd87-5ac2-4f90-8712-184b02c541a5
=============================
Loading initial vital signs data for patient: ae15cd87-5ac2-4f90-8712-184b02c541a5
Querying InfluxDB for patient: ae15cd87-5ac2-4f90-8712-184b02c541a5 (last 50 readings)
Executing Flux query for patient ae15cd87-5ac2-4f90-8712-184b02c541a5
Query returned 1 tables
Processing table with 50 records
Successfully retrieved 50 readings for patient ae15cd87-5ac2-4f90-8712-184b02c541a5
Loaded 50 initial readings
Updating charts with 50 readings
Charts updated successfully. Latest reading: VitalSigns[...]
```

## Notas Importantes

- **Conexión directa a InfluxDB**: El desktop app se conecta directamente a InfluxDB, no pasa por el gateway para las métricas (para mejor rendimiento).
- **Datos en tiempo real**: Se generan cada 5 segundos por el realtime-generator.
- **Ventana deslizante**: Solo se muestran los últimos 50 registros en las gráficas.
- **Actualización automática**: Las gráficas se refrescan cada 10 segundos automáticamente.

## Pacientes de Prueba

Los pacientes incluidos en el seed de la base de datos son:

1. **José Hernández** - `jose.hernandez@patients.heartguard.com` (Medium Risk)
2. **María Delgado** - `maria.delgado@patients.heartguard.com` (High Risk)
3. **Valeria Ortiz** - `valeria.ortiz@patients.heartguard.com` (Low Risk)

Todos tienen datos generándose en tiempo real.
