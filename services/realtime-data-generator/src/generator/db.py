"""Database operations for Generator Service."""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List
import logging

from .data_generator import Patient

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for PostgreSQL database operations."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
    
    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            logger.info("Connecting to PostgreSQL...")
            self.conn = psycopg2.connect(
                self.database_url,
                # Mantener la conexión abierta con keepalives
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            # Evitar que la conexión se cierre en modo autocommit
            self.conn.set_session(autocommit=True)
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def ensure_connection(self):
        """Ensure connection is active, reconnect if needed."""
        try:
            if self.conn is None or self.conn.closed:
                logger.warning("Connection closed, reconnecting...")
                self.connect()
            else:
                # Test connection with a simple query
                with self.conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except Exception as e:
            logger.warning(f"Connection test failed: {e}, reconnecting...")
            try:
                self.connect()
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect: {reconnect_error}")
                raise
    
    def disconnect(self):
        """Disconnect from PostgreSQL."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("PostgreSQL connection closed")
            except Exception as e:
                logger.error(f"Error closing PostgreSQL connection: {e}")
    
    def get_active_patients(self) -> List[Patient]:
        """
        Fetch active patients from PostgreSQL.
        Returns patients from the heartguard.patients table.
        """
        try:
            # Asegurar que la conexión está activa
            self.ensure_connection()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        p.id::text,
                        p.person_name as name,
                        p.email,
                        p.org_id::text,
                        rl.code as risk_level_code,
                        p.created_at
                    FROM heartguard.patients p
                    LEFT JOIN heartguard.risk_levels rl ON p.risk_level_id = rl.id
                    ORDER BY p.created_at DESC
                    LIMIT 100
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                patients = [
                    Patient(
                        id=row['id'],
                        name=row['name'],
                        email=row['email'],
                        org_id=row['org_id'],
                        risk_level_code=row['risk_level_code'],
                        created_at=row['created_at']
                    )
                    for row in results
                ]
                
                logger.info(f"Retrieved {len(patients)} active patients from database")
                return patients
        except Exception as e:
            logger.error(f"Error fetching patients: {e}")
            return []
