"""
Repositorio para acceso a datos del paciente
"""
from typing import Optional, List, Dict
from ..extensions import get_db_cursor


class PatientRepository:
    """Repositorio para operaciones de base de datos relacionadas con pacientes"""
    
    @staticmethod
    def get_patient_profile(patient_id: str) -> Optional[Dict]:
        """
        Obtiene el perfil completo de un paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con información del paciente o None si no existe
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.id,
                    p.person_name as name,
                    p.email,
                    p.birthdate,
                    s.code as sex,
                    rl.code as risk_level,
                    p.created_at,
                    o.id as org_id,
                    o.code as org_code,
                    o.name as org_name
                FROM patients p
                LEFT JOIN sexes s ON p.sex_id = s.id
                LEFT JOIN risk_levels rl ON p.risk_level_id = rl.id
                LEFT JOIN organizations o ON p.org_id = o.id
                WHERE p.id = %s
            """, (patient_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_patient_stats(patient_id: str) -> Dict:
        """
        Obtiene estadísticas del paciente (alertas, dispositivos, etc.)
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con estadísticas
        """
        with get_db_cursor() as cursor:
            # Total de alertas
            cursor.execute("""
                SELECT COUNT(*) as total_alerts
                FROM alerts
                WHERE patient_id = %s
            """, (patient_id,))
            total_alerts = cursor.fetchone()['total_alerts']
            
            # Alertas pendientes (usando JOIN con alert_status para filtrar por código)
            cursor.execute("""
                SELECT COUNT(*) as pending_alerts
                FROM alerts a
                JOIN alert_status ast ON a.status_id = ast.id
                WHERE a.patient_id = %s AND ast.code IN ('created', 'notified', 'ack')
            """, (patient_id,))
            pending_alerts = cursor.fetchone()['pending_alerts']
            
            # Dispositivos (usando owner_patient_id en lugar de patient_id)
            cursor.execute("""
                SELECT COUNT(*) as devices_count
                FROM devices
                WHERE owner_patient_id = %s AND active = true
            """, (patient_id,))
            devices_count = cursor.fetchone()['devices_count']
            
            # Última lectura
            cursor.execute("""
                SELECT MAX(started_at) as last_reading
                FROM signal_streams
                WHERE patient_id = %s
            """, (patient_id,))
            last_reading_row = cursor.fetchone()
            last_reading = last_reading_row['last_reading'] if last_reading_row else None
            
            return {
                'total_alerts': total_alerts,
                'pending_alerts': pending_alerts,
                'devices_count': devices_count,
                'last_reading': last_reading.isoformat() if last_reading else None
            }
    
    @staticmethod
    def get_recent_alerts(patient_id: str, limit: int = 5) -> List[Dict]:
        """
        Obtiene las alertas más recientes del paciente
        
        Args:
            patient_id: UUID del paciente
            limit: Número máximo de alertas a retornar
            
        Returns:
            Lista de alertas
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.id,
                    at.code as type,
                    al.code as level,
                    a.description,
                    a.created_at,
                    ast.code as status,
                    ST_Y(a.location) as latitude,
                    ST_X(a.location) as longitude
                FROM alerts a
                LEFT JOIN alert_types at ON a.type_id = at.id
                LEFT JOIN alert_levels al ON a.alert_level_id = al.id
                LEFT JOIN alert_status ast ON a.status_id = ast.id
                WHERE a.patient_id = %s
                ORDER BY a.created_at DESC
                LIMIT %s
            """, (patient_id, limit))
            return cursor.fetchall()
    
    @staticmethod
    def get_alerts(patient_id: str, status: Optional[str] = None, limit: int = 20, offset: int = 0) -> tuple:
        """
        Obtiene alertas del paciente con paginación
        
        Args:
            patient_id: UUID del paciente
            status: Filtro por estado (new, ack, resolved)
            limit: Cantidad de resultados
            offset: Desplazamiento para paginación
            
        Returns:
            Tupla (alertas, total)
        """
        with get_db_cursor() as cursor:
            # Query base
            query = """
                SELECT 
                    a.id,
                    at.code as type,
                    al.code as level,
                    a.description,
                    a.created_at,
                    ast.code as status,
                    ST_Y(a.location) as latitude,
                    ST_X(a.location) as longitude
                FROM alerts a
                LEFT JOIN alert_types at ON a.type_id = at.id
                LEFT JOIN alert_levels al ON a.alert_level_id = al.id
                LEFT JOIN alert_status ast ON a.status_id = ast.id
                WHERE a.patient_id = %s
            """
            params = [patient_id]
            
            # Filtro por estado
            if status:
                query += " AND ast.code = %s"
                params.append(status)
            
            # Total
            count_query = f"SELECT COUNT(*) as total FROM ({query}) as subq"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Resultados paginados
            query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cursor.execute(query, params)
            alerts = cursor.fetchall()
            
            return alerts, total
    
    @staticmethod
    def get_care_team(patient_id: str) -> List[Dict]:
        """
        Obtiene el equipo de cuidado asignado al paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Lista de equipos y sus miembros
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ct.id as team_id,
                    ct.name as team_name,
                    u.name as member_name,
                    tmr.label as role,
                    u.email
                FROM patient_care_team pct
                JOIN care_teams ct ON pct.care_team_id = ct.id
                JOIN care_team_member ctm ON ct.id = ctm.care_team_id
                JOIN users u ON ctm.user_id = u.id
                LEFT JOIN team_member_roles tmr ON ctm.role_id = tmr.id
                WHERE pct.patient_id = %s
                ORDER BY ct.name, tmr.label
            """, (patient_id,))
            return cursor.fetchall()
    
    @staticmethod
    def get_caregivers(patient_id: str) -> List[Dict]:
        """
        Obtiene los cuidadores (caregivers) asignados al paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Lista de cuidadores con su información y relación
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.id as user_id,
                    u.name as caregiver_name,
                    u.email,
                    crt.code as relationship_type,
                    crt.label as relationship_label,
                    cp.is_primary,
                    cp.started_at,
                    cp.ended_at,
                    cp.note
                FROM caregiver_patient cp
                JOIN users u ON cp.user_id = u.id
                LEFT JOIN caregiver_relationship_types crt ON cp.rel_type_id = crt.id
                WHERE cp.patient_id = %s
                ORDER BY cp.is_primary DESC, u.name
            """, (patient_id,))
            return cursor.fetchall()
    
    @staticmethod
    def get_devices(patient_id: str) -> List[Dict]:
        """
        Obtiene los dispositivos asignados al paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Lista de dispositivos
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    d.id,
                    d.serial,
                    d.brand,
                    d.model,
                    dt.label as device_type,
                    d.active,
                    d.registered_at
                FROM devices d
                LEFT JOIN device_types dt ON d.device_type_id = dt.id
                WHERE d.owner_patient_id = %s
                ORDER BY d.registered_at DESC
            """, (patient_id,))
            return cursor.fetchall()
    
    @staticmethod
    def get_signal_streams(patient_id: str, limit: int = 50, offset: int = 0) -> tuple:
        """
        Obtiene el historial de lecturas de señales del paciente
        
        Args:
            patient_id: UUID del paciente
            limit: Cantidad de resultados
            offset: Desplazamiento para paginación
            
        Returns:
            Tupla (lecturas, total)
        """
        with get_db_cursor() as cursor:
            # Total
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM signal_streams
                WHERE patient_id = %s
            """, (patient_id,))
            total = cursor.fetchone()['total']
            
            # Lecturas paginadas
            cursor.execute("""
                SELECT 
                    ss.id,
                    d.serial as device_serial,
                    ss.signal_type,
                    ss.started_at,
                    ss.ended_at,
                    ss.sample_rate_hz,
                    EXTRACT(EPOCH FROM (ss.ended_at - ss.started_at))/60 as duration_minutes
                FROM signal_streams ss
                LEFT JOIN devices d ON ss.device_id = d.id
                WHERE ss.patient_id = %s
                ORDER BY ss.started_at DESC
                LIMIT %s OFFSET %s
            """, (patient_id, limit, offset))
            readings = cursor.fetchall()
            
            return readings, total
    
    @staticmethod
    def get_latest_location(patient_id: str) -> Optional[Dict]:
        """
        Obtiene la última ubicación registrada del paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con la ubicación o None
        """
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ST_Y(geom) as latitude,
                    ST_X(geom) as longitude,
                    ts as timestamp,
                    source,
                    accuracy_m as accuracy_meters
                FROM patient_locations
                WHERE patient_id = %s
                ORDER BY ts DESC
                LIMIT 1
            """, (patient_id,))
            return cursor.fetchone()
