"""
Script de prueba para diagnosticar el problema de filtrado de pacientes.
Ejecutar con: python diagnostico_filtrado.py
"""

import requests
import json

API_URL = "http://136.115.53.140:5000"
AUTH_URL = f"{API_URL}/auth/login"
PATIENTS_URL = f"{API_URL}/patients"

def login(email, password):
    """Login y retornar token"""
    response = requests.post(AUTH_URL, json={"email": email, "password": password})
    data = response.json()
    
    # Estructura: data.tokens.access_token y data.user
    if 'data' in data and 'tokens' in data['data']:
        token = data['data']['tokens'].get('access_token')
        user_info = data['data'].get('user', {})
        roles = data['data']['tokens'].get('roles', [])
        user_info['roles'] = roles
    else:
        print("❌ Formato de respuesta inesperado")
        return None, {}
    
    if not token:
        print("❌ No se pudo extraer el token")
        return None, {}
    
    print(f"\n✅ Login exitoso: {user_info.get('name', email)}")
    print(f"   Token (primeros 50): {token[:50]}...")
    print(f"   Roles: {roles}")
    return token, user_info

def get_patients(token, username):
    """Obtener pacientes con el token"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(PATIENTS_URL, headers=headers)
    
    # Imprimir info de debug
    print(f"\n📊 Pacientes para {username}:")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        patients = data.get('patients', [])
        print(f"   Total: {len(patients)}")
        for p in patients:
            print(f"   - {p.get('name', 'N/A')} (ID: {p.get('id', 'N/A')})")
        return patients
    else:
        print(f"   Error: {response.text}")
        return []

def main():
    print("=" * 70)
    print("DIAGNÓSTICO DE FILTRADO DE PACIENTES")
    print("=" * 70)
    
    # Test 1: Clinician (Ana Ruiz)
    print("\n" + "=" * 70)
    print("TEST 1: CLINICIAN (Ana Ruiz) - Debe ver 3 pacientes")
    print("=" * 70)
    token_ana, user_ana = login("ana.ruiz@heartguard.com", "Demo#2025")
    patients_ana = get_patients(token_ana, user_ana['name'])
    
    # Test 2: Caregiver (Sofia)
    print("\n" + "=" * 70)
    print("TEST 2: CAREGIVER (Sofia) - Debe ver 1 paciente (María Delgado)")
    print("=" * 70)
    token_sofia, user_sofia = login("sofia.care@heartguard.com", "Demo#2025")
    patients_sofia = get_patients(token_sofia, user_sofia['name'])
    
    # Análisis
    print("\n" + "=" * 70)
    print("ANÁLISIS DE RESULTADOS")
    print("=" * 70)
    print(f"\nAna Ruiz (CLINICIAN):")
    print(f"  - Pacientes obtenidos: {len(patients_ana)}")
    print(f"  - Esperado: 3")
    print(f"  - Estado: {'✅ CORRECTO' if len(patients_ana) == 3 else '❌ INCORRECTO'}")
    
    print(f"\nSofia Cuidadora (CAREGIVER):")
    print(f"  - Pacientes obtenidos: {len(patients_sofia)}")
    print(f"  - Esperado: 1")
    print(f"  - Estado: {'✅ CORRECTO' if len(patients_sofia) == 1 else '❌ INCORRECTO'}")
    
    # Verificar si el filtrado funciona
    if len(patients_sofia) == 1:
        print("\n✅ EL FILTRADO EN EL BACKEND FUNCIONA CORRECTAMENTE")
    else:
        print("\n❌ EL FILTRADO EN EL BACKEND NO FUNCIONA")
        print(f"   Sofia está viendo {len(patients_sofia)} pacientes en vez de 1")
        print("\nPOSIBLES CAUSAS:")
        print("  1. El rol 'caregiver' no se está detectando correctamente")
        print("  2. La tabla caregiver_patient no tiene datos para Sofia")
        print("  3. El query en patient_service/routes.py no está funcionando")
        
        # Verificar si Sofia tiene el rol correcto
        if 'role' in user_sofia:
            if user_sofia['role'] == 'caregiver':
                print(f"\n  ✅ Sofia tiene el rol correcto: '{user_sofia['role']}'")
            else:
                print(f"\n  ❌ Sofia NO tiene el rol caregiver: '{user_sofia['role']}'")
        elif 'roles' in user_sofia:
            if 'caregiver' in user_sofia['roles']:
                print(f"\n  ✅ Sofia tiene el rol correcto en roles: {user_sofia['roles']}")
            else:
                print(f"\n  ❌ Sofia NO tiene el rol caregiver en roles: {user_sofia['roles']}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
