"""Script para ver TODOS los datos que trae el dashboard del paciente."""
import sys
import json
sys.path.insert(0, ".")

from heartguard_tk.api.client import ApiClient

def main():
    client = ApiClient(base_url="http://localhost:8000")
    
    # Login como paciente
    print("=== LOGIN PACIENTE ===")
    login_response = client.login("maria.delgado@patients.heartguard.com", "Paciente#2025")
    if not login_response.get("success"):
        print(f"❌ Login failed: {login_response}")
        return
    
    print(f"✅ Login exitoso: {login_response.get('user', {}).get('name')}")
    print()
    
    # Obtener dashboard COMPLETO
    print("=== DASHBOARD COMPLETO ===")
    dashboard = client.get_patient_dashboard()
    
    if not dashboard.get("success"):
        print(f"❌ Dashboard failed: {dashboard}")
        return
    
    # Mostrar estructura COMPLETA con formato bonito
    print(json.dumps(dashboard, indent=2, ensure_ascii=False))
    print()
    
    # Analizar lo que viene
    print("=== ANÁLISIS DE DATOS ===")
    data = dashboard.get("data", {})
    
    print(f"\n📊 Keys en dashboard: {list(data.keys())}")
    
    # Recent alerts
    recent_alerts = data.get("recent_alerts", [])
    print(f"\n🚨 recent_alerts: {len(recent_alerts)} items")
    if recent_alerts:
        print(f"   Primera alerta: {recent_alerts[0]}")
    
    # Care team
    care_team = data.get("care_team", {})
    print(f"\n👨‍⚕️ care_team: {care_team}")
    
    # Caregivers
    caregivers = data.get("caregivers", [])
    print(f"\n👥 caregivers: {len(caregivers)} items")
    if caregivers:
        print(f"   Primer cuidador: {caregivers[0]}")
    
    # Patient
    patient = data.get("patient", {})
    print(f"\n🏥 patient keys: {list(patient.keys())}")
    
    # Stats
    stats = data.get("stats", {})
    print(f"\n📈 stats: {stats}")

if __name__ == "__main__":
    main()
