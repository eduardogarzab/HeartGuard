import os
import psycopg2
import bcrypt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Test Device Data ---
# This data is based on the 'validate_microservices.sh' script
DEVICE_UUID = "device-uuid-test-001"
DEVICE_TOKEN = "heartguard-test-token-abcdef123456"
PATIENT_ID = 101
ORG_ID = "org-uuid-test-001"
STREAM_TYPE = "heart_rate"

def seed_test_device():
    """
    Seeds the database with the test device and signal stream used in the
    validation script.
    """
    print("Seeding test device data...")
    try:
        # Get database connection details from environment variables
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set.")

        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()

        # Hash the device token using bcrypt
        hashed_token = bcrypt.hashpw(DEVICE_TOKEN.encode('utf-8'), bcrypt.gensalt())

        # Insert the test device key
        cur.execute(
            """
            INSERT INTO device_keys (device_uuid, patient_id, hashed_api_key, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (device_uuid) DO NOTHING;
            """,
            (DEVICE_UUID, PATIENT_ID, hashed_token.decode('utf-8'), 'active')
        )
        print(f"Device key for UUID '{DEVICE_UUID}' seeded.")

        # Get the ID of the device key we just inserted
        cur.execute("SELECT id FROM device_keys WHERE device_uuid = %s;", (DEVICE_UUID,))
        device_key_id = cur.fetchone()[0]

        # Insert the corresponding signal stream
        cur.execute(
            """
            INSERT INTO signal_streams (org_id, patient_id, device_key_id, stream_type, status)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (device_key_id, stream_type) DO NOTHING;
            """,
            (ORG_ID, PATIENT_ID, device_key_id, STREAM_TYPE, 'active')
        )
        print(f"Signal stream '{STREAM_TYPE}' for device '{DEVICE_UUID}' seeded.")

        cur.close()
        conn.close()
        print("Test data seeding complete.")

    except Exception as e:
        print(f"An error occurred during test data seeding: {e}")

if __name__ == "__main__":
    seed_test_device()
