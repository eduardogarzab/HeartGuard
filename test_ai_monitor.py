#!/usr/bin/env python3
"""
Script para probar el flujo completo del AI Monitor
Inserta datos de prueba en InfluxDB con valores anormales para generar alertas
"""
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import time

# Configuración
INFLUX_URL = "http://134.199.204.58:8086"
INFLUX_TOKEN = "heartguard-dev-token-change-me"
INFLUX_ORG = "heartguard"
INFLUX_BUCKET = "timeseries"

# ID de paciente de prueba
PATIENT_ID = "8c9436b4-f085-405f-a3d2-87cb1d1cf097"

# Valores ANORMALES para generar alertas
ANOMALY_VITALS = {
    "heart_rate": 140,  # Taquicardia
    "spo2": 85,         # Desaturación crítica
    "systolic_bp": 170, # Hipertensión severa
    "diastolic_bp": 110,
    "temperature": 39.5, # Fiebre alta
    "respiratory_rate": 28,
    "gps_latitude": 19.432608,
    "gps_longitude": -99.133209
}

print("=" * 60)
print("🧪 Iniciando prueba del flujo completo AI Monitor")
print("=" * 60)

# Conectar a InfluxDB
print(f"\n1. Conectando a InfluxDB: {INFLUX_URL}")
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Escribir datos ANORMALES
print(f"2. Insertando datos ANORMALES para paciente: {PATIENT_ID}")
print(f"   ⚠️  FC: {ANOMALY_VITALS['heart_rate']} bpm (ALTO)")
print(f"   ⚠️  SpO2: {ANOMALY_VITALS['spo2']}% (BAJO - Desaturación)")
print(f"   ⚠️  PA: {ANOMALY_VITALS['systolic_bp']}/{ANOMALY_VITALS['diastolic_bp']} mmHg (ALTO)")
print(f"   ⚠️  Temp: {ANOMALY_VITALS['temperature']}°C (FIEBRE)")

timestamp = datetime.utcnow()

# Crear un point por cada medida
for measurement, value in ANOMALY_VITALS.items():
    point = (
        Point(measurement)
        .tag("patient_id", PATIENT_ID)
        .field("value", float(value))
        .time(timestamp)
    )
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    print(f"   ✅ {measurement}: {value}")

print(f"\n3. ✅ Datos insertados en InfluxDB")
print(f"   Timestamp: {timestamp.isoformat()}Z")

# Cerrar conexión
client.close()

print("\n4. ⏳ Esperando 65 segundos para que el AI Monitor procese...")
print("   (El monitor se ejecuta cada 60 segundos)")
print("\n" + "=" * 60)
print("IMPORTANTE:")
print("- El AI Monitor detectará estos datos anormales")
print("- Enviará a AI Prediction Service (localhost:5007)")
print("- El modelo RandomForest predecirá problemas de salud")
print("- Creará alertas en PostgreSQL con model_id")
print("=" * 60)

# Esperar
for i in range(65, 0, -5):
    print(f"⏰ {i} segundos restantes...", end="\r")
    time.sleep(5)

print("\n\n5. Verificando alertas creadas en PostgreSQL...")
print("\nEjecuta este comando para ver las alertas:")
print("=" * 60)
print("PGPASSWORD=dev_change_me psql -h 134.199.204.58 -U heartguard_app -d heartguard -c \"")
print("SELECT ")
print("    a.id,")
print("    at.code as alert_type,")
print("    al.code as severity,")
print("    a.description,")
print("    m.name as model_name,")
print("    a.created_at")
print("FROM heartguard.alerts a")
print("JOIN heartguard.alert_types at ON a.type_id = at.id")
print("JOIN heartguard.alert_levels al ON a.alert_level_id = al.id")
print("LEFT JOIN heartguard.models m ON a.created_by_model_id = m.id")
print(f"WHERE a.patient_id = '{PATIENT_ID}'")
print("ORDER BY a.created_at DESC")
print("LIMIT 5;\"")
print("=" * 60)
