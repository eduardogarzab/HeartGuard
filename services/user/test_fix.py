"""
Script de prueba rápida para verificar el fix de list_org_care_team_patients
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuración de conexión (ajustar según tu configuración)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'heartguard',
    'user': 'postgres',
    'password': 'postgres'
}

def test_query():
    """Prueba la query corregida"""
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # Obtener el ID de la organización FAM-001
    cursor.execute("SELECT id FROM organizations WHERE code = 'FAM-001'")
    org = cursor.fetchone()
    org_id = org['id'] if org else None
    
    # Obtener el ID de ana.ruiz (que SÍ está en un equipo)
    cursor.execute("SELECT id FROM users WHERE email = 'ana.ruiz@heartguard.com'")
    ana = cursor.fetchone()
    ana_id = ana['id'] if ana else None
    
    # Obtener el ID de un usuario que NO está en ningún equipo (juanito)
    cursor.execute("SELECT id FROM users WHERE email = 'juanito@heartguard.com'")
    juanito = cursor.fetchone()
    juanito_id = juanito['id'] if juanito else None
    
    print(f"Org ID (FAM-001): {org_id}")
    print(f"Ana ID: {ana_id}")
    print(f"Juanito ID: {juanito_id}")
    print()
    
    # Nueva query CON filtro por usuario
    new_query = """
        SELECT
            ct.id AS care_team_id,
            ct.name AS care_team_name,
            p.id AS patient_id,
            p.person_name AS patient_name,
            p.email AS patient_email,
            rl.code AS risk_level_code,
            rl.label AS risk_level_label
        FROM care_teams ct
        JOIN care_team_member ctm ON ctm.care_team_id = ct.id
        JOIN patient_care_team pct ON pct.care_team_id = ct.id
        JOIN patients p ON p.id = pct.patient_id
        LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
        WHERE ct.org_id = %s AND ctm.user_id = %s
        ORDER BY ct.name ASC, patient_name ASC
    """
    
    if ana_id and org_id:
        print("=== Resultados para Ana (SÍ está en equipo) ===")
        cursor.execute(new_query, (org_id, ana_id))
        results = cursor.fetchall()
        print(f"Total resultados: {len(results)}")
        for row in results:
            print(f"  - Equipo: {row['care_team_name']}, Paciente: {row['patient_name']}")
        print()
    
    if juanito_id and org_id:
        print("=== Resultados para Juanito (NO está en ningún equipo) ===")
        cursor.execute(new_query, (org_id, juanito_id))
        results = cursor.fetchall()
        print(f"Total resultados: {len(results)}")
        if len(results) == 0:
            print("  ✅ CORRECTO: No devuelve nada porque Juanito NO está en ningún equipo")
        else:
            print("  ❌ ERROR: No debería devolver resultados")
            for row in results:
                print(f"  - Equipo: {row['care_team_name']}, Paciente: {row['patient_name']}")
        print()
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        test_query()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
