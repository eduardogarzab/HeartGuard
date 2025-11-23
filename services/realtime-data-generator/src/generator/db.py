"""Database operations for Generator Service."""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
import logging
import json

from .data_generator import Patient, StreamConfig

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
    
    def get_patient_device_streams(self) -> List[StreamConfig]:
        """
        Fetch complete stream configurations for all active patients.
        Returns full JOIN of patients + devices + streams + bindings + tags + locations.
        
        CRITICAL FILTERS:
        - Only devices that are ASSIGNED to a patient (owner_patient_id IS NOT NULL)
        - Only devices that are ACTIVE (d.active = TRUE)
        - Only streams that are ACTIVE (ended_at IS NULL)
        
        This ensures we only generate synthetic data for devices that are:
        1. Purchased by organization (in devices table)
        2. Assigned to a specific patient
        3. Currently active and operational
        
        Query includes:
        - Patient metadata (id, name, org, risk_level)
        - Device metadata (id, serial, brand, model)
        - Stream metadata (id, signal_type)
        - InfluxDB binding (bucket, measurement, org)
        - Custom tags from timeseries_binding_tag
        - GPS coordinates from patient_locations (latest)
        """
        try:
            # Asegurar que la conexión está activa
            self.ensure_connection()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        p.id::text AS patient_id,
                        p.person_name AS patient_name,
                        p.email AS patient_email,
                        p.org_id::text AS org_id,
                        o.name AS org_name,
                        rl.code AS risk_level_code,
                        d.id::text AS device_id,
                        d.serial AS device_serial,
                        d.brand AS device_brand,
                        d.model AS device_model,
                        ss.id::text AS stream_id,
                        st.code AS signal_type_code,
                        tb.id::text AS binding_id,
                        tb.influx_org,
                        tb.influx_bucket,
                        tb.measurement,
                        tb.retention_hint,
                        COALESCE(
                            json_object_agg(tbt.tag_key, tbt.tag_value) 
                            FILTER (WHERE tbt.tag_key IS NOT NULL),
                            '{}'::json
                        ) AS custom_tags,
                        pl_latest.gps_longitude,
                        pl_latest.gps_latitude
                    FROM heartguard.patients p
                    LEFT JOIN heartguard.organizations o ON o.id = p.org_id
                    LEFT JOIN heartguard.risk_levels rl ON rl.id = p.risk_level_id
                    JOIN heartguard.devices d ON d.owner_patient_id = p.id 
                        AND d.active = TRUE
                        AND d.owner_patient_id IS NOT NULL
                    JOIN heartguard.signal_streams ss ON ss.patient_id = p.id 
                        AND ss.device_id = d.id 
                        AND ss.ended_at IS NULL
                    JOIN heartguard.signal_types st ON st.id = ss.signal_type_id
                    JOIN heartguard.timeseries_binding tb ON tb.stream_id = ss.id
                    LEFT JOIN heartguard.timeseries_binding_tag tbt ON tbt.binding_id = tb.id
                    LEFT JOIN LATERAL (
                        SELECT 
                            ST_X(geom) AS gps_longitude,
                            ST_Y(geom) AS gps_latitude
                        FROM heartguard.patient_locations
                        WHERE patient_id = p.id
                        ORDER BY ts DESC
                        LIMIT 1
                    ) pl_latest ON TRUE
                    GROUP BY 
                        p.id, p.person_name, p.email, p.org_id, o.name, rl.code,
                        d.id, d.serial, d.brand, d.model, ss.id, st.code,
                        tb.id, tb.influx_org, tb.influx_bucket, tb.measurement, tb.retention_hint,
                        pl_latest.gps_longitude, pl_latest.gps_latitude
                    ORDER BY p.person_name
                """
                cursor.execute(query)
                results = cursor.fetchall()
                
                stream_configs = []
                for row in results:
                    # Parse custom_tags JSON
                    custom_tags = {}
                    if row['custom_tags']:
                        if isinstance(row['custom_tags'], str):
                            custom_tags = json.loads(row['custom_tags'])
                        elif isinstance(row['custom_tags'], dict):
                            custom_tags = row['custom_tags']
                    
                    # Add GPS coordinates to custom_tags if available from patient_locations
                    if row.get('gps_longitude') is not None and row.get('gps_latitude') is not None:
                        custom_tags['gps_longitude_pg'] = str(row['gps_longitude'])
                        custom_tags['gps_latitude_pg'] = str(row['gps_latitude'])
                    
                    stream_configs.append(
                        StreamConfig(
                            patient_id=row['patient_id'],
                            patient_name=row['patient_name'],
                            patient_email=row['patient_email'],
                            org_id=row['org_id'],
                            org_name=row['org_name'],
                            risk_level_code=row['risk_level_code'],
                            device_id=row['device_id'],
                            device_serial=row['device_serial'],
                            device_brand=row.get('device_brand'),
                            device_model=row.get('device_model'),
                            stream_id=row['stream_id'],
                            signal_type_code=row['signal_type_code'],
                            binding_id=row['binding_id'],
                            influx_org=row['influx_org'] or 'heartguard',
                            influx_bucket=row['influx_bucket'],
                            measurement=row['measurement'],
                            retention_hint=row['retention_hint'],
                            custom_tags=custom_tags
                        )
                    )
                
                logger.info(f"Retrieved {len(stream_configs)} stream configurations from database")
                return stream_configs
        except Exception as e:
            logger.error(f"Error fetching stream configurations: {e}")
            return []
    
    def get_binding_tags(self, binding_id: str) -> Dict[str, str]:
        """
        Get custom tags for a specific timeseries_binding.
        
        Args:
            binding_id: UUID of the timeseries_binding record
            
        Returns:
            Dictionary of tag_key -> tag_value mappings
        """
        try:
            self.ensure_connection()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT tag_key, tag_value
                    FROM heartguard.timeseries_binding_tag
                    WHERE binding_id = %s
                """
                cursor.execute(query, (binding_id,))
                results = cursor.fetchall()
                
                tags = {row['tag_key']: row['tag_value'] for row in results}
                logger.debug(f"Retrieved {len(tags)} tags for binding {binding_id}")
                return tags
        except Exception as e:
            logger.error(f"Error fetching binding tags: {e}")
            return {}
