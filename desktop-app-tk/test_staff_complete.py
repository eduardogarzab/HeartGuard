"""Test para ver todos los datos disponibles para usuarios staff."""
import sys
sys.path.insert(0, ".")

from heartguard_tk.api.client import ApiClient

def main():
    client = ApiClient(base_url="http://136.115.53.140:8080")
    
    print("=" * 70)
    print("TEST: Usuario Staff - Dra. Ana Ruiz (Organización Familia García)")
    print("=" * 70)
    
    # Login
    print("\n1. LOGIN...")
    try:
        # Probar con el superadmin que tiene acceso a todo
        login_response = client.login_user("ana.ruiz@heartguard.com", "Demo#2025")
        print(f"✅ Login: {login_response.full_name}")
        token = login_response.access_token
    except Exception as e:
        print(f"❌ Login FAILED: {e}")
        return
    
    # Get memberships para obtener org_id
    print("\n2. MEMBERSHIPS...")
    try:
        memberships_response = client.get_current_user_memberships(token=token)
        memberships_data = memberships_response.get("data", {})
        items = memberships_data.get("items", [])
        
        if items:
            org = items[0]
            org_id = org.get("organization_id")
            org_name = org.get("organization_name")
            print(f"✅ Organización: {org_name} (ID: {org_id})")
        else:
            print("❌ No hay organizaciones")
            return
    except Exception as e:
        print(f"❌ Memberships FAILED: {e}")
        return
    
    # Dashboard
    print("\n3. DASHBOARD...")
    try:
        dashboard = client.get_organization_dashboard(org_id=org_id, token=token)
        data = dashboard.get("data", {})
        overview = data.get("overview", {})
        
        print(f"✅ Overview:")
        print(f"   - Pacientes: {overview.get('total_patients')}")
        print(f"   - Alertas abiertas: {overview.get('open_alerts')}")
        print(f"   - Cuidadores: {overview.get('total_caregivers')}")
        print(f"   - Equipos: {overview.get('total_care_teams')}")
        
        recent_alerts = data.get("recent_alerts", [])
        print(f"   - Alertas recientes: {len(recent_alerts)} items")
    except Exception as e:
        print(f"❌ Dashboard FAILED: {e}")
    
    # Care Teams
    print("\n4. CARE TEAMS...")
    try:
        teams_response = client.get_organization_care_teams(org_id=org_id, token=token)
        teams_data = teams_response.get("data", {})
        teams = teams_data.get("items", [])
        
        print(f"✅ Care Teams: {len(teams)} equipos")
        if teams:
            team = teams[0]
            team_id = team.get("id")
            print(f"   - Equipo: {team.get('name')}")
            print(f"     Role: {team.get('my_role')}")
            print(f"     Miembros: {team.get('member_count')}")
    except Exception as e:
        print(f"❌ Care Teams FAILED: {e}")
        teams = []
    
    # Care Team Patients
    if teams:
        print("\n5. CARE TEAM PATIENTS...")
        try:
            patients_response = client.get_care_team_patients(
                org_id=org_id, 
                care_team_id=team_id, 
                token=token
            )
            patients_data = patients_response.get("data", {})
            patients = patients_data.get("patients", [])
            
            print(f"✅ Pacientes del equipo: {len(patients)} pacientes")
            if patients:
                patient = patients[0]
                print(f"   - Paciente: {patient.get('full_name')}")
                print(f"     Risk: {patient.get('risk_level')}")
                print(f"     ID: {patient.get('id')}")
        except Exception as e:
            print(f"❌ Care Team Patients FAILED: {e}")
    
    # Care Team Locations
    print("\n6. CARE TEAM LOCATIONS...")
    try:
        locations_response = client.get_care_team_locations(token=token)
        
        if isinstance(locations_response, dict):
            locations_data = locations_response.get("data", {})
            locations = locations_data.get("items") or locations_data.get("locations", [])
            print(f"✅ Ubicaciones: {len(locations)} ubicaciones")
            if locations:
                loc = locations[0]
                print(f"   - Primera ubicación: {loc}")
        else:
            print(f"⚠️ Locations: formato inesperado")
    except Exception as e:
        print(f"❌ Care Team Locations FAILED: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETADO")
    print("=" * 70)

if __name__ == "__main__":
    main()
