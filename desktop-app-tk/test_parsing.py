"""Test de parsing de datos del dashboard."""

from heartguard_tk.api import ApiClient

client = ApiClient()
login = client.login_user('ana.ruiz@heartguard.com', 'Demo#2025')
token = login.access_token

memberships = client.get_current_user_memberships(token=token)
org_id = memberships['data']['memberships'][0]['org_id']

print('=== PRUEBA DE PARSING ===')
dashboard = client.get_organization_dashboard(org_id, token=token)
metrics = client.get_organization_metrics(org_id, token=token)
teams = client.get_organization_care_teams(org_id, token=token)
patients = client.get_organization_care_team_patients(org_id, token=token)

# Simular el parsing
def _dict_from(payload, key):
    value = payload.get(key) if isinstance(payload, dict) else None
    return value if isinstance(value, dict) else {}

def _list_from(payload, key):
    value = payload.get(key) if isinstance(payload, dict) else None
    return value if isinstance(value, list) else None

# Métricas
dashboard_data = _dict_from(dashboard, 'data')
metrics_data = _dict_from(metrics, 'data')
overview = _dict_from(dashboard_data, 'overview')
metrics_dict = _dict_from(metrics_data, 'metrics')

print(f'\nPacientes: {overview.get("total_patients", 0)}')
print(f'Equipos: {overview.get("total_care_teams", 0)}')
print(f'Cuidadores: {overview.get("total_caregivers", 0)}')
print(f'Alertas abiertas: {overview.get("open_alerts", 0)}')
print(f'Alertas 7d: {overview.get("alerts_last_7d", 0)}')
print(f'Promedio alertas/paciente: {metrics_dict.get("avg_alerts_per_patient", 0)}')

# Equipos
care_teams_data = _dict_from(teams, 'data')
teams_list = _list_from(care_teams_data, 'care_teams')
print(f'\nEquipos encontrados: {len(teams_list or [])}')
for team in teams_list or []:
    print(f'  - {team.get("name")}: {len(team.get("members", []))} miembros')

# Pacientes
patients_data = _dict_from(patients, 'data')
care_team_patients = _list_from(patients_data, 'care_teams') or []
print(f'\nEquipos con pacientes: {len(care_team_patients)}')
for team in care_team_patients:
    team_name = team.get('name')
    patients_list = team.get('patients', [])
    print(f'  - {team_name}: {len(patients_list)} pacientes')
    for patient in patients_list:
        risk = patient.get('risk_level')
        if isinstance(risk, dict):
            risk_str = risk.get('label', '')
        else:
            risk_str = str(risk or '')
        print(f'    • {patient.get("name")} - Riesgo: {risk_str}')
