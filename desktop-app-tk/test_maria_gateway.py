"""Test rápido para verificar que el gateway trae datos de María Delgado."""
import sys
sys.path.insert(0, ".")

from heartguard_tk.api.client import ApiClient

def main():
    # Conectar al gateway remoto
    client = ApiClient(base_url="http://136.115.53.140:8080")
    
    print("=" * 60)
    print("TEST: Usuario María Delgado via Gateway")
    print("=" * 60)
    
    # Login
    print("\n1. LOGIN...")
    try:
        login_response = client.login_patient("maria.delgado@patients.heartguard.com", "Paciente#2025")
        
        print(f"✅ Login SUCCESS")
        print(f"   Patient: {login_response.full_name}")
        print(f"   Email: {login_response.email}")
        print(f"   Token: {login_response.access_token[:20] if login_response.access_token else 'N/A'}...")
        
        token = login_response.access_token
    except Exception as e:
        print(f"❌ Login FAILED: {e}")
        return
    
    # Dashboard
    print("\n2. DASHBOARD...")
    try:
        dashboard_response = client.get_patient_dashboard(token=token)
        
        if not isinstance(dashboard_response, dict):
            print(f"❌ Dashboard response no es un dict: {type(dashboard_response)}")
            return
        
        # El dashboard puede venir con wrapper "data" o directo
        if "data" in dashboard_response:
            data = dashboard_response["data"]
        else:
            data = dashboard_response
        
        patient = data.get("patient", {})
        stats = data.get("stats", {})
        recent_alerts = data.get("recent_alerts", [])
        caregivers = data.get("caregivers", [])
        care_team = data.get("care_team", {})
        
        print(f"✅ Dashboard SUCCESS")
        print(f"   Patient: {patient.get('name')}")
        print(f"   Org: {patient.get('org_name')}")
        print(f"   Risk: {patient.get('risk_level')}")
        print(f"   Birthdate: {patient.get('birthdate')}")
        print(f"\n   📊 Stats:")
        print(f"      - Total Alerts: {stats.get('total_alerts')}")
        print(f"      - Pending Alerts: {stats.get('pending_alerts')}")
        print(f"      - Devices: {stats.get('devices_count')}")
        print(f"      - Last Reading: {stats.get('last_reading')}")
        print(f"\n   📋 Recent Alerts: {len(recent_alerts)} items")
        print(f"   👥 Caregivers: {len(caregivers)} items")
        
        # Care team puede ser dict o list
        if isinstance(care_team, dict):
            print(f"   👨‍⚕️ Care Team: {care_team.get('name') if care_team else 'N/A'}")
        elif isinstance(care_team, list):
            print(f"   👨‍⚕️ Care Team: {len(care_team)} miembros")
        else:
            print(f"   👨‍⚕️ Care Team: {care_team}")
        
        if recent_alerts:
            print(f"\n   � Primera alerta:")
            alert = recent_alerts[0]
            print(f"      - Severity: {alert.get('severity')}")
            print(f"      - Type: {alert.get('alert_type')}")
            print(f"      - Status: {alert.get('status')}")
            print(f"      - Timestamp: {alert.get('timestamp')}")
        
        if caregivers:
            print(f"\n   � Primer cuidador:")
            cg = caregivers[0]
            print(f"      - Name: {cg.get('full_name')}")
            print(f"      - Email: {cg.get('email')}")
    except Exception as e:
        print(f"❌ Dashboard FAILED: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Locations
    print("\n3. LOCATIONS...")
    try:
        locations_response = client.get_patient_locations(token=token, limit=5)
        
        if not isinstance(locations_response, dict):
            print(f"❌ Locations response no es un dict: {type(locations_response)}")
        else:
            # Puede venir con wrapper "data" o directo
            if "data" in locations_response:
                data = locations_response["data"]
            else:
                data = locations_response
            
            items = data.get("items", [])
            print(f"✅ Locations SUCCESS: {len(items)} items")
            
            if items:
                loc = items[0]
                print(f"   📍 Primera ubicación:")
                print(f"      - Timestamp: {loc.get('timestamp')}")
                location = loc.get('location', {})
                print(f"      - Lat: {location.get('latitude')}")
                print(f"      - Lon: {location.get('longitude')}")
    except Exception as e:
        print(f"❌ Locations FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    main()
