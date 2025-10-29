# signal_service/init_db.py
import os
from dotenv import load_dotenv
from app.database import engine
from app.models.models import Base

def initialize_database():
    """
    Initializes the database by creating all necessary tables.
    """
    print("Initializing database...")
    try:
        # Load environment variables to ensure the database engine is configured
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

        # Create all tables defined in the models
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")

        # --- TimescaleDB Setup (Optional, for reference) ---
        # print("Note: To enable TimescaleDB features, the following SQL commands should be run:")
        # print("1. CREATE EXTENSION IF NOT EXISTS timescaledb;")
        # print("2. SELECT create_hypertable('timeseries_data', 'timestamp');")
        # print("3. ALTER TABLE timeseries_data SET (timescaledb.compress, timescaledb.compress_segmentby = 'stream_id');")
        # print("4. SELECT add_retention_policy('timeseries_data', INTERVAL '6 months');")

    except Exception as e:
        print(f"An error occurred during database initialization: {e}")

if __name__ == "__main__":
    initialize_database()
