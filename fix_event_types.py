#!/usr/bin/env python3
"""Script to add missing event types to PostgreSQL database"""

import psycopg2
import sys

# Database connection parameters
DB_HOST = "134.199.204.58"
DB_PORT = 5432
DB_NAME = "heartguard"
DB_USER = "heartguard_app"
DB_PASS = "dev_change_me"

def main():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        
        cur = conn.cursor()
        
        # Check if event_types table exists and what's in it
        print("Checking current event_types...")
        cur.execute("SELECT code, description FROM event_types ORDER BY code;")
        rows = cur.fetchall()
        print(f"Found {len(rows)} event types:")
        for code, desc in rows:
            print(f"  - {code}: {desc}")
        
        # Get alert_levels IDs
        cur.execute("SELECT id FROM alert_levels WHERE code='medium' LIMIT 1;")
        medium_level = cur.fetchone()
        cur.execute("SELECT id FROM alert_levels WHERE code='high' LIMIT 1;")
        high_level = cur.fetchone()
        
        if not medium_level or not high_level:
            print("ERROR: alert_levels not found!")
            return 1
        
        medium_id = medium_level[0]
        high_id = high_level[0]
        
        # Event types to add
        event_types = [
            ('GENERAL_RISK', 'Riesgo general de salud detectado por IA', medium_id),
            ('ARRHYTHMIA', 'Arritmia - Frecuencia cardiaca anormal', high_id),
            ('DESAT', 'Desaturación de oxígeno', high_id),
            ('HYPERTENSION', 'Hipertensión arterial', medium_id),
            ('HYPOTENSION', 'Hipotensión arterial', high_id),
            ('FEVER', 'Fiebre - Temperatura elevada', medium_id),
            ('HYPOTHERMIA', 'Hipotermia - Temperatura baja', high_id),
        ]
        
        print(f"\nInserting event types...")
        for code, description, severity_id in event_types:
            cur.execute(
                """
                INSERT INTO event_types (code, description, severity_default_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (code) DO UPDATE 
                SET description = EXCLUDED.description,
                    severity_default_id = EXCLUDED.severity_default_id;
                """,
                (code, description, severity_id)
            )
            print(f"  ✓ {code}")
        
        conn.commit()
        
        # Verify
        print("\nVerifying event_types after insert...")
        cur.execute("SELECT code, description FROM event_types ORDER BY code;")
        rows = cur.fetchall()
        print(f"Now have {len(rows)} event types:")
        for code, desc in rows:
            print(f"  - {code}: {desc}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Event types fixed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
