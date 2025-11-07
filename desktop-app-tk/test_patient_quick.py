"""Test rápido de endpoints del paciente."""
import sys
sys.path.insert(0, '.')

from heartguard_tk.api import ApiClient

print("=" * 80)
print("PRUEBA RÁPIDA - ENDPOINTS DEL PACIENTE")
print("=" * 80)

api = ApiClient()

# Login
print("\n1. Login paciente...")
try:
    response = api.login_patient("maria.delgado@patients.heartguard.com", "Paciente#2025")
    print(f"✓ Login exitoso: {response.full_name}")
    token = response.access_token
except Exception as e:
    print(f"❌ Error en login: {e}")
    sys.exit(1)

# Dashboard
print("\n2. Dashboard...")
try:
    dashboard = api.get_patient_dashboard(token=token)
    print(f"✓ Dashboard obtenido")
    print(f"   Keys: {list(dashboard.keys())}")
    
    data = dashboard.get("data", dashboard)
    print(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
    
    if isinstance(data, dict):
        patient = data.get("patient", {})
        print(f"\n   PACIENTE:")
        print(f"     - name: {patient.get('name')}")
        print(f"     - org_name: {patient.get('org_name')}")
        print(f"     - risk_level: {patient.get('risk_level')}")
        print(f"     - birthdate: {patient.get('birthdate')}")
        
        stats = data.get("stats", {})
        print(f"\n   STATS:")
        print(f"     - total_alerts: {stats.get('total_alerts')}")
        print(f"     - pending_alerts: {stats.get('pending_alerts')}")
        print(f"     - devices_count: {stats.get('devices_count')}")
        print(f"     - last_reading: {stats.get('last_reading')}")
        
except Exception as e:
    print(f"❌ Error en dashboard: {e}")
    import traceback
    traceback.print_exc()

# Alertas
print("\n3. Alertas...")
try:
    alerts = api.get_patient_alerts(token=token)
    print(f"✓ Alertas obtenidas")
    data = alerts.get("data", alerts)
    items = data.get("items", [])
    print(f"   Total alertas: {len(items)}")
    for alert in items[:2]:
        print(f"     - {alert.get('alert_type')}: {alert.get('severity')} ({alert.get('status')})")
except Exception as e:
    print(f"❌ Error en alertas: {e}")

# Dispositivos
print("\n4. Dispositivos...")
try:
    devices = api.get_patient_devices(token=token)
    print(f"✓ Dispositivos obtenidos")
    data = devices.get("data", devices)
    items = data.get("items", [])
    print(f"   Total dispositivos: {len(items)}")
    for device in items:
        print(f"     - {device.get('serial_number')}: {device.get('device_type')}")
except Exception as e:
    print(f"❌ Error en dispositivos: {e}")

# Cuidadores
print("\n5. Cuidadores...")
try:
    caregivers = api.get_patient_caregivers(token=token)
    print(f"✓ Cuidadores obtenidos")
    data = caregivers.get("data", caregivers)
    items = data.get("items", [])
    print(f"   Total cuidadores: {len(items)}")
    for cg in items:
        print(f"     - {cg.get('full_name')}: {cg.get('email')}")
except Exception as e:
    print(f"❌ Error en cuidadores: {e}")

# Care Team
print("\n6. Care Team...")
try:
    care_team = api.get_patient_care_team(token=token)
    print(f"✓ Care Team obtenido")
    data = care_team.get("data", care_team)
    team = data.get("care_team", {})
    print(f"   Nombre: {team.get('name')}")
except Exception as e:
    print(f"❌ Error en care team: {e}")

# Ubicaciones
print("\n7. Ubicaciones...")
try:
    locations = api.get_patient_locations(token=token)
    print(f"✓ Ubicaciones obtenidas")
    data = locations.get("data", locations)
    items = data.get("items", [])
    print(f"   Total ubicaciones: {len(items)}")
except Exception as e:
    print(f"❌ Error en ubicaciones: {e}")

print("\n" + "=" * 80)
print("PRUEBA COMPLETADA")
print("=" * 80)
