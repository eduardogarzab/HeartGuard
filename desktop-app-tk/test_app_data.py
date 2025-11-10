"""Script de prueba para verificar que la app carga todos los datos correctamente."""

import sys
import io

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from heartguard_tk.api import ApiClient

# Configuración
GATEWAY_URL = "http://136.115.53.140:8080"

# Credenciales del seed.sql
STAFF_USERS = [
    {"email": "ana.ruiz@heartguard.com", "password": "Demo#2025", "name": "Dra. Ana Ruiz"},
    {"email": "martin.ops@heartguard.com", "password": "Demo#2025", "name": "Martín López"},
]

PATIENT_USERS = [
    {"email": "maria.delgado@patients.heartguard.com", "password": "Paciente#2025", "name": "María Delgado"},
    {"email": "jose.hernandez@patients.heartguard.com", "password": "Paciente#2025", "name": "José Hernández"},
]

def print_section(title):
    """Imprime un encabezado de sección."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def print_success(message):
    """Imprime mensaje de éxito."""
    print(f"✓ {message}")

def print_error(message):
    """Imprime mensaje de error."""
    print(f"✗ ERROR: {message}")

def print_data(label, data):
    """Imprime datos formateados."""
    print(f"  {label}: {data}")

def test_staff_login_and_data(client, user):
    """Prueba login de staff y carga de datos."""
    print_section(f"Probando usuario: {user['name']} ({user['email']})")
    
    try:
        # 1. Login
        print("\n1. Probando login...")
        login_response = client.login_user(user['email'], user['password'])
        print_success(f"Login exitoso: {login_response.full_name}")
        print_data("Token", login_response.access_token[:20] + "...")
        print_data("Rol", login_response.user.system_role if login_response.user else "N/A")
        
        token = login_response.access_token
        
        # 2. Perfil
        print("\n2. Obteniendo perfil...")
        profile = client.get_current_user_profile(token=token)
        print_success("Perfil obtenido")
        if isinstance(profile, dict):
            user_data = profile.get('data', {}).get('user', profile.get('user', {}))
            if isinstance(user_data, dict):
                print_data("Nombre", user_data.get('name', 'N/A'))
                print_data("Email", user_data.get('email', 'N/A'))
                print_data("Rol", user_data.get('role_label', 'N/A'))
        
        # 3. Membresías
        print("\n3. Obteniendo membresías...")
        memberships = client.get_current_user_memberships(token=token)
        print_success("Membresías obtenidas")
        if isinstance(memberships, dict):
            data = memberships.get('data', {})
            items = data.get('memberships', data.get('items', []))
            if isinstance(items, list):
                print_data("Total de organizaciones", len(items))
                for idx, org in enumerate(items, 1):
                    if isinstance(org, dict):
                        print_data(f"  Org {idx}", f"{org.get('org_name', 'N/A')} (ID: {org.get('org_id', 'N/A')})")
                        print_data(f"    Rol", org.get('role_label', 'N/A'))
                
                # 4. Probar datos de cada organización
                if items:
                    org = items[0]
                    org_id = str(org.get('org_id', ''))
                    if org_id:
                        print_section(f"Datos de organización: {org.get('org_name', 'N/A')}")
                        
                        # Dashboard
                        print("\n4a. Dashboard de organización...")
                        try:
                            dashboard = client.get_organization_dashboard(org_id, token=token)
                            print_success("Dashboard obtenido")
                            if isinstance(dashboard, dict):
                                overview = dashboard.get('overview', {})
                                if isinstance(overview, dict):
                                    print_data("  Pacientes totales", overview.get('total_patients', 0))
                                    print_data("  Equipos de cuidado", overview.get('total_care_teams', 0))
                                    print_data("  Cuidadores", overview.get('total_caregivers', 0))
                                    print_data("  Alertas abiertas", overview.get('open_alerts', 0))
                                    print_data("  Alertas últimos 7 días", overview.get('alerts_last_7d', 0))
                        except Exception as e:
                            print_error(f"Dashboard: {e}")
                        
                        # Métricas
                        print("\n4b. Métricas de organización...")
                        try:
                            metrics = client.get_organization_metrics(org_id, token=token)
                            print_success("Métricas obtenidas")
                            if isinstance(metrics, dict):
                                m = metrics.get('metrics', {})
                                if isinstance(m, dict):
                                    print_data("  Promedio alertas/paciente", f"{m.get('avg_alerts_per_patient', 0):.2f}")
                        except Exception as e:
                            print_error(f"Métricas: {e}")
                        
                        # Equipos de cuidado
                        print("\n4c. Equipos de cuidado...")
                        try:
                            teams = client.get_organization_care_teams(org_id, token=token)
                            print_success("Equipos obtenidos")
                            if isinstance(teams, dict):
                                team_list = teams.get('teams', teams.get('care_teams', []))
                                if isinstance(team_list, list):
                                    print_data("  Total de equipos", len(team_list))
                                    for idx, team in enumerate(team_list[:3], 1):
                                        if isinstance(team, dict):
                                            print_data(f"    Equipo {idx}", team.get('name', 'N/A'))
                                            members = team.get('members', [])
                                            if isinstance(members, list):
                                                print_data(f"      Miembros", len(members))
                        except Exception as e:
                            print_error(f"Equipos: {e}")
                        
                        # Pacientes de equipos
                        print("\n4d. Pacientes de equipos...")
                        try:
                            care_team_patients = client.get_organization_care_team_patients(org_id, token=token)
                            print_success("Pacientes obtenidos")
                            if isinstance(care_team_patients, dict):
                                teams = care_team_patients.get('care_teams', [])
                                if isinstance(teams, list):
                                    total_patients = 0
                                    for team in teams:
                                        if isinstance(team, dict):
                                            patients = team.get('patients', [])
                                            if isinstance(patients, list):
                                                total_patients += len(patients)
                                    print_data("  Total de pacientes en equipos", total_patients)
                        except Exception as e:
                            print_error(f"Pacientes de equipos: {e}")
                        
                        # Ubicaciones del equipo
                        print("\n4e. Ubicaciones del equipo de cuidado...")
                        try:
                            locations = client.get_care_team_locations(org_id=org_id, token=token)
                            print_success("Ubicaciones del equipo obtenidas")
                            if isinstance(locations, dict):
                                data = locations.get('data', locations)
                                if isinstance(data, dict):
                                    members = data.get('members', [])
                                    if isinstance(members, list):
                                        print_data("  Miembros con ubicación", len(members))
                                        for idx, member in enumerate(members[:3], 1):
                                            if isinstance(member, dict):
                                                print_data(f"    Miembro {idx}", member.get('name', 'N/A'))
                                                loc = member.get('location', member.get('last_location', {}))
                                                if isinstance(loc, dict):
                                                    coords = loc.get('coords', loc)
                                                    if isinstance(coords, dict):
                                                        lat = coords.get('latitude', coords.get('lat'))
                                                        lon = coords.get('longitude', coords.get('lon'))
                                                        print_data(f"      Coords", f"({lat}, {lon})")
                        except Exception as e:
                            print_error(f"Ubicaciones del equipo: {e}")
                        
                        # Ubicaciones de pacientes
                        print("\n4f. Ubicaciones de pacientes (caregiver)...")
                        try:
                            caregiver_locs = client.get_caregiver_patient_locations(org_id=org_id, token=token)
                            print_success("Ubicaciones de pacientes obtenidas")
                            if isinstance(caregiver_locs, dict):
                                data = caregiver_locs.get('data', caregiver_locs)
                                if isinstance(data, dict):
                                    patients = data.get('patients', [])
                                    if isinstance(patients, list):
                                        print_data("  Pacientes con ubicación", len(patients))
                                        for idx, patient in enumerate(patients[:3], 1):
                                            if isinstance(patient, dict):
                                                print_data(f"    Paciente {idx}", patient.get('name', 'N/A'))
                        except Exception as e:
                            print_error(f"Ubicaciones de pacientes: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"Error durante prueba de staff: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_patient_login_and_data(client, user):
    """Prueba login de paciente y carga de datos."""
    print_section(f"Probando paciente: {user['name']} ({user['email']})")
    
    try:
        # 1. Login
        print("\n1. Probando login de paciente...")
        login_response = client.login_patient(user['email'], user['password'])
        print_success(f"Login exitoso: {login_response.full_name}")
        print_data("Token", login_response.access_token[:20] + "...")
        
        token = login_response.access_token
        
        # 2. Dashboard
        print("\n2. Dashboard de paciente...")
        try:
            dashboard = client.get_patient_dashboard(token=token)
            print_success("Dashboard obtenido")
            if isinstance(dashboard, dict):
                summary = dashboard.get('summary', {})
                if isinstance(summary, dict):
                    print_data("  Alertas totales", summary.get('total_alerts', 0))
                    print_data("  Alertas pendientes", summary.get('pending_alerts', 0))
                    print_data("  Dispositivos", summary.get('devices_count', 0))
        except Exception as e:
            print_error(f"Dashboard: {e}")
        
        # 3. Alertas
        print("\n3. Alertas del paciente...")
        try:
            alerts = client.get_patient_alerts(limit=10, token=token)
            print_success("Alertas obtenidas")
            if isinstance(alerts, dict):
                alert_list = alerts.get('alerts', [])
                if isinstance(alert_list, list):
                    print_data("  Total de alertas", len(alert_list))
                    for idx, alert in enumerate(alert_list[:3], 1):
                        if isinstance(alert, dict):
                            print_data(f"    Alerta {idx}", alert.get('type', 'N/A'))
                            print_data(f"      Nivel", alert.get('level_label', 'N/A'))
        except Exception as e:
            print_error(f"Alertas: {e}")
        
        # 4. Equipo de cuidado
        print("\n4. Equipo de cuidado del paciente...")
        try:
            care_team = client.get_patient_care_team(token=token)
            print_success("Equipo de cuidado obtenido")
            if isinstance(care_team, dict):
                teams = care_team.get('care_teams', [])
                if isinstance(teams, list):
                    print_data("  Equipos asignados", len(teams))
        except Exception as e:
            print_error(f"Equipo de cuidado: {e}")
        
        # 5. Cuidadores
        print("\n5. Cuidadores del paciente...")
        try:
            caregivers = client.get_patient_caregivers(token=token)
            print_success("Cuidadores obtenidos")
            if isinstance(caregivers, dict):
                caregiver_list = caregivers.get('caregivers', [])
                if isinstance(caregiver_list, list):
                    print_data("  Total de cuidadores", len(caregiver_list))
        except Exception as e:
            print_error(f"Cuidadores: {e}")
        
        # 6. Ubicaciones
        print("\n6. Ubicaciones del paciente...")
        try:
            locations = client.get_patient_locations(limit=10, token=token)
            print_success("Ubicaciones obtenidas")
            if isinstance(locations, dict):
                loc_list = locations.get('locations', [])
                if isinstance(loc_list, list):
                    print_data("  Total de ubicaciones", len(loc_list))
        except Exception as e:
            print_error(f"Ubicaciones: {e}")
        
        # 7. Dispositivos
        print("\n7. Dispositivos del paciente...")
        try:
            devices = client.get_patient_devices(token=token)
            print_success("Dispositivos obtenidos")
            if isinstance(devices, dict):
                device_list = devices.get('devices', [])
                if isinstance(device_list, list):
                    print_data("  Total de dispositivos", len(device_list))
        except Exception as e:
            print_error(f"Dispositivos: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"Error durante prueba de paciente: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todas las pruebas."""
    print_section("INICIANDO PRUEBAS DE LA APLICACIÓN HEARTGUARD")
    print(f"Gateway URL: {GATEWAY_URL}")
    
    client = ApiClient(base_url=GATEWAY_URL)
    
    # Pruebas de staff
    print_section("PRUEBAS DE USUARIOS DE STAFF")
    staff_results = []
    for user in STAFF_USERS:
        result = test_staff_login_and_data(client, user)
        staff_results.append((user['name'], result))
    
    # Pruebas de pacientes
    print_section("PRUEBAS DE USUARIOS PACIENTES")
    patient_results = []
    for user in PATIENT_USERS:
        result = test_patient_login_and_data(client, user)
        patient_results.append((user['name'], result))
    
    # Resumen
    print_section("RESUMEN DE PRUEBAS")
    print("\nUsuarios de Staff:")
    for name, result in staff_results:
        status = "✓ EXITOSO" if result else "✗ FALLIDO"
        print(f"  {name}: {status}")
    
    print("\nUsuarios Pacientes:")
    for name, result in patient_results:
        status = "✓ EXITOSO" if result else "✗ FALLIDO"
        print(f"  {name}: {status}")
    
    # Resultado final
    all_passed = all(r for _, r in staff_results) and all(r for _, r in patient_results)
    if all_passed:
        print_section("✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        return 0
    else:
        print_section("✗ ALGUNAS PRUEBAS FALLARON")
        return 1

if __name__ == "__main__":
    sys.exit(main())
