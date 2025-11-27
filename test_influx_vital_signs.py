#!/usr/bin/env python3
"""
Script de prueba para verificar la visualización de signos vitales desde InfluxDB
"""
import requests
import json
from datetime import datetime
import sys

# Configuración - MODIFICA ESTAS URLs SEGÚN TU ENTORNO
GATEWAY_URL = input("🌐 URL del Gateway (ej: http://IP:8080): ").strip() or "http://localhost:8080"
REALTIME_URL = input("🌐 URL del servicio Realtime (ej: http://IP:5007): ").strip() or "http://localhost:5007"
INFLUX_URL = input("🌐 URL de InfluxDB (ej: http://IP:8086): ").strip() or "http://localhost:8086"

print(f"\n📋 Configuración:")
print(f"   Gateway: {GATEWAY_URL}")
print(f"   Realtime: {REALTIME_URL}")
print(f"   InfluxDB: {INFLUX_URL}")

def test_influx_connection():
    """Verifica que InfluxDB esté disponible"""
    print("\n🔍 1. Verificando conexión a InfluxDB...")
    try:
        response = requests.get(f"{INFLUX_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ InfluxDB está corriendo")
            return True
        else:
            print(f"❌ InfluxDB respondió con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar a InfluxDB: {e}")
        return False

def test_realtime_service():
    """Verifica que el servicio realtime esté disponible"""
    print("\n🔍 2. Verificando servicio realtime...")
    try:
        response = requests.get(f"{REALTIME_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servicio realtime está corriendo")
            return True
        else:
            print(f"❌ Servicio realtime respondió con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servicio realtime: {e}")
        return False

def test_vital_signs_endpoint_direct(patient_id="550e8400-e29b-41d4-a716-446655440000"):
    """Prueba el endpoint de signos vitales directamente"""
    print(f"\n🔍 3. Probando endpoint directo de signos vitales (paciente: {patient_id})...")
    try:
        url = f"{REALTIME_URL}/patients/{patient_id}/vital-signs?limit=10"
        print(f"   URL: {url}")
        
        # Probar con JSON
        response = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta exitosa (JSON):")
            print(f"   - Paciente: {data.get('patient_id')}")
            print(f"   - Dispositivo: {data.get('device_id')}")
            print(f"   - Measurement: {data.get('measurement')}")
            print(f"   - Cantidad de lecturas: {data.get('count')}")
            
            if data.get('readings'):
                print(f"\n   📊 Primera lectura:")
                first = data['readings'][0]
                for key, value in first.items():
                    print(f"      - {key}: {value}")
                return True
            else:
                print("   ⚠️ No hay lecturas disponibles")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Respuesta: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar endpoint: {e}")
        return False

def test_vital_signs_via_gateway(token, patient_id="550e8400-e29b-41d4-a716-446655440000"):
    """Prueba el endpoint a través del gateway"""
    print(f"\n🔍 4. Probando endpoint vía Gateway (paciente: {patient_id})...")
    try:
        url = f"{GATEWAY_URL}/realtime/patients/{patient_id}/vital-signs?limit=10"
        print(f"   URL: {url}")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/xml"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            print(f"✅ Respuesta exitosa vía Gateway")
            print(f"   XML Response (primeros 500 caracteres):")
            print(f"   {response.text[:500]}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Respuesta: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar vía gateway: {e}")
        return False

def get_test_token():
    """Obtiene un token de prueba para org_admin"""
    print("\n🔑 Obteniendo token de autenticación...")
    try:
        # Intenta hacer login como org_admin
        url = f"{GATEWAY_URL}/auth/login"
        payload = {
            "email": "admin@hospital1.com",
            "password": "admin123"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Token obtenido exitosamente")
            return token
        else:
            print(f"⚠️ No se pudo obtener token (status {response.status_code})")
            print("   Continuando sin token para pruebas directas...")
            return None
    except Exception as e:
        print(f"⚠️ Error al obtener token: {e}")
        print("   Continuando sin token para pruebas directas...")
        return None

def check_influx_data():
    """Verifica si hay datos en InfluxDB"""
    print("\n🔍 5. Verificando datos en InfluxDB...")
    try:
        # Esto requeriría acceso directo a InfluxDB
        # Por ahora, solo verificamos que el servicio responda
        print("   (Verificación mediante endpoints de servicio)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("🏥 HEARTGUARD - Test de Signos Vitales desde InfluxDB")
    print("=" * 70)
    
    # 1. Verificar InfluxDB
    if not test_influx_connection():
        print("\n⚠️ InfluxDB no está disponible. ¿Está corriendo docker-compose?")
        return
    
    # 2. Verificar servicio realtime
    if not test_realtime_service():
        print("\n⚠️ El servicio realtime no está disponible.")
        print("   Ejecuta: docker-compose up -d influxdb-service")
        return
    
    # 3. Probar endpoint directo
    patient_id = "550e8400-e29b-41d4-a716-446655440000"  # ID de ejemplo
    direct_works = test_vital_signs_endpoint_direct(patient_id)
    
    # 4. Obtener token y probar vía gateway
    token = get_test_token()
    if token:
        gateway_works = test_vital_signs_via_gateway(token, patient_id)
    else:
        print("\n⚠️ Saltando prueba vía Gateway (no hay token)")
        gateway_works = False
    
    # Resumen
    print("\n" + "=" * 70)
    print("📋 RESUMEN:")
    print("=" * 70)
    print(f"✅ InfluxDB: Disponible")
    print(f"✅ Servicio Realtime: Disponible")
    print(f"{'✅' if direct_works else '❌'} Endpoint Directo: {'Funciona' if direct_works else 'No funciona'}")
    print(f"{'✅' if gateway_works else '❌'} Vía Gateway: {'Funciona' if gateway_works else 'No funciona'}")
    
    if not direct_works:
        print("\n🔧 DIAGNÓSTICO:")
        print("   El servicio está corriendo pero no hay datos de signos vitales.")
        print("   Posibles causas:")
        print("   1. No hay dispositivos generando datos")
        print("   2. El worker no está escribiendo a InfluxDB")
        print("   3. El paciente no tiene dispositivos asignados")
        print("\n   Solución: Ejecuta el generador de datos o asigna dispositivos")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
