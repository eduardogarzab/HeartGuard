"""
Servicio de lógica de negocio para pacientes
"""
from typing import Optional, Dict, List
from ..repositories.patient_repo import PatientRepository


class PatientService:
    """Servicio que contiene la lógica de negocio para el portal del paciente"""
    
    def __init__(self):
        self.repo = PatientRepository()
    
    def get_dashboard_data(self, patient_id: str) -> Dict:
        """
        Obtiene todos los datos necesarios para el dashboard del paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con todos los datos del dashboard
            
        Raises:
            ValueError: Si el paciente no existe
        """
        # Obtener perfil
        profile = self.repo.get_patient_profile(patient_id)
        if not profile:
            raise ValueError("Paciente no encontrado")
        
        # Obtener estadísticas
        stats = self.repo.get_patient_stats(patient_id)
        
        # Obtener alertas recientes
        recent_alerts = self.repo.get_recent_alerts(patient_id, limit=5)
        
        # Obtener equipo de cuidado
        care_team_raw = self.repo.get_care_team(patient_id)
        
        # Obtener cuidadores (caregivers)
        caregivers_raw = self.repo.get_caregivers(patient_id)
        
        # Formatear datos
        return {
            'patient': {
                'id': str(profile['id']),
                'name': profile['name'],
                'email': profile['email'],
                'birthdate': profile['birthdate'].isoformat() if profile['birthdate'] else None,
                'sex': self._format_sex(profile['sex']),
                'risk_level': self._format_risk_level(profile['risk_level']),
                'profile_photo_url': profile.get('profile_photo_url'),
                'org_name': profile['org_name']
            },
            'stats': stats,
            'recent_alerts': [self._format_alert(alert) for alert in recent_alerts],
            'care_team': self._group_care_team(care_team_raw),
            'caregivers': [self._format_caregiver(cg) for cg in caregivers_raw]
        }
    
    def get_profile(self, patient_id: str) -> Dict:
        """
        Obtiene el perfil completo del paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con información del perfil
            
        Raises:
            ValueError: Si el paciente no existe
        """
        profile = self.repo.get_patient_profile(patient_id)
        if not profile:
            raise ValueError("Paciente no encontrado")
        
        return {
            'id': str(profile['id']),
            'name': profile['name'],
            'email': profile['email'],
            'birthdate': profile['birthdate'].isoformat() if profile['birthdate'] else None,
            'sex': self._format_sex(profile['sex']),
            'risk_level': self._format_risk_level(profile['risk_level']),
            'profile_photo_url': profile.get('profile_photo_url'),
            'organization': {
                'id': str(profile['org_id']) if profile['org_id'] else None,
                'code': profile['org_code'],
                'name': profile['org_name']
            },
            'created_at': profile['created_at'].isoformat() if profile['created_at'] else None
        }
    
    def get_alerts(self, patient_id: str, status: Optional[str] = None, limit: int = 20, offset: int = 0) -> Dict:
        """
        Obtiene alertas del paciente con paginación
        
        Args:
            patient_id: UUID del paciente
            status: Filtro por estado
            limit: Cantidad de resultados
            offset: Desplazamiento
            
        Returns:
            Dict con alertas y metadata de paginación
        """
        alerts, total = self.repo.get_alerts(patient_id, status, limit, offset)
        
        return {
            'alerts': [self._format_alert(alert) for alert in alerts],
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    def get_devices(self, patient_id: str) -> Dict:
        """
        Obtiene dispositivos del paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con lista de dispositivos
        """
        devices = self.repo.get_devices(patient_id)
        
        return {
            'devices': [self._format_device(device) for device in devices]
        }
    
    def get_caregivers(self, patient_id: str) -> Dict:
        """
        Obtiene cuidadores (caregivers) del paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con lista de cuidadores
        """
        caregivers = self.repo.get_caregivers(patient_id)
        
        return {
            'caregivers': [self._format_caregiver(cg) for cg in caregivers]
        }
    
    def get_signal_readings(self, patient_id: str, limit: int = 50, offset: int = 0) -> Dict:
        """
        Obtiene historial de lecturas de señales
        
        Args:
            patient_id: UUID del paciente
            limit: Cantidad de resultados
            offset: Desplazamiento
            
        Returns:
            Dict con lecturas y metadata
        """
        readings, total = self.repo.get_signal_streams(patient_id, limit, offset)
        
        return {
            'readings': [self._format_signal_stream(reading) for reading in readings],
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    def get_care_team(self, patient_id: str) -> Dict:
        """
        Obtiene equipo de cuidado del paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con equipos y miembros
        """
        care_team_raw = self.repo.get_care_team(patient_id)
        
        return {
            'teams': self._group_care_team(care_team_raw)
        }
    
    def get_latest_location(self, patient_id: str) -> Dict:
        """
        Obtiene la última ubicación del paciente
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            Dict con ubicación o None
        """
        location = self.repo.get_latest_location(patient_id)
        
        if not location:
            return {'location': None}
        
        return {
            'location': {
                'latitude': float(location['latitude']) if location['latitude'] else None,
                'longitude': float(location['longitude']) if location['longitude'] else None,
                'timestamp': location['timestamp'].isoformat() if location['timestamp'] else None,
                'source': location['source'],
                'accuracy_meters': float(location['accuracy_meters']) if location['accuracy_meters'] else None
            }
        }
    
    def get_location_history(self, patient_id: str, limit: int = 50, offset: int = 0) -> Dict:
        """
        Obtiene el historial de ubicaciones del paciente
        
        Args:
            patient_id: UUID del paciente
            limit: Cantidad de resultados
            offset: Desplazamiento
            
        Returns:
            Dict con historial de ubicaciones y metadata
        """
        locations, total = self.repo.get_location_history(patient_id, limit, offset)
        
        return {
            'locations': [self._format_location(loc) for loc in locations],
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    # Métodos auxiliares de formateo
    
    @staticmethod
    def _format_sex(sex: Optional[str]) -> str:
        """Formatea el sexo del paciente"""
        sex_map = {
            'M': 'Masculino',
            'F': 'Femenino',
            'O': 'Otro'
        }
        return sex_map.get(sex, 'No especificado')
    
    @staticmethod
    def _format_risk_level(risk: Optional[str]) -> str:
        """Formatea el nivel de riesgo"""
        risk_map = {
            'low': 'Bajo',
            'medium': 'Medio',
            'high': 'Alto',
            'critical': 'Crítico'
        }
        return risk_map.get(risk, 'No especificado')
    
    @staticmethod
    def _format_alert_level(level: Optional[str]) -> str:
        """Formatea el nivel de alerta"""
        level_map = {
            'low': 'Bajo',
            'medium': 'Medio',
            'high': 'Alto',
            'critical': 'Crítico'
        }
        return level_map.get(level, level or 'N/A')
    
    @staticmethod
    def _format_alert_status(status: Optional[str]) -> str:
        """Formatea el estado de alerta"""
        status_map = {
            'new': 'Nueva',
            'ack': 'Reconocida',
            'resolved': 'Resuelta'
        }
        return status_map.get(status, status or 'N/A')
    
    def _format_alert(self, alert: Dict) -> Dict:
        """
        Formatea una alerta para respuesta
        Incluye información de IA y ground truth
        """
        formatted = {
            'id': str(alert['id']),
            'type': alert['type'],
            'level': alert['level'],
            'level_label': self._format_alert_level(alert['level']),
            'description': alert['description'],
            'status': alert['status'],
            'status_label': self._format_alert_status(alert['status']),
            'created_at': alert['created_at'].isoformat() if alert['created_at'] else None,
            'location': {
                'lat': float(alert['latitude']) if alert.get('latitude') else None,
                'lng': float(alert['longitude']) if alert.get('longitude') else None
            } if alert.get('latitude') and alert.get('longitude') else None,
            # ✨ NUEVO: Información de IA
            'created_by_model_id': str(alert['created_by_model_id']) if alert.get('created_by_model_id') else None,
            'model_name': alert.get('model_name'),
            'source_inference_id': str(alert['source_inference_id']) if alert.get('source_inference_id') else None,
        }
        
        # ✨ NUEVO: Información de Ground Truth (validación médica)
        if alert.get('ground_truth_id'):
            formatted['ground_truth_validated'] = True
            formatted['ground_truth_id'] = str(alert['ground_truth_id'])
            formatted['ground_truth_event_code'] = alert.get('ground_truth_event_code')
            formatted['ground_truth_event_label'] = alert.get('ground_truth_event_label')
            formatted['ground_truth_doctor'] = alert.get('ground_truth_doctor')
            formatted['ground_truth_doctor_id'] = str(alert['ground_truth_doctor_id']) if alert.get('ground_truth_doctor_id') else None
            formatted['ground_truth_note'] = alert.get('ground_truth_note')
            formatted['ground_truth_created_at'] = alert['ground_truth_created_at'].isoformat() if alert.get('ground_truth_created_at') else None
        else:
            formatted['ground_truth_validated'] = False
        
        return formatted
    
    @staticmethod
    def _format_device(device: Dict) -> Dict:
        """Formatea un dispositivo para respuesta"""
        return {
            'id': str(device['id']),
            'serial': device['serial'],
            'brand': device.get('brand'),
            'model': device.get('model'),
            'type': device.get('device_type'),
            'active': device['active'],
            'registered_at': device['registered_at'].isoformat() if device.get('registered_at') else None
        }
    
    @staticmethod
    def _format_signal_stream(reading: Dict) -> Dict:
        """Formatea una lectura de señal para respuesta"""
        return {
            'id': str(reading['id']),
            'device_serial': reading.get('device_serial'),
            'signal_type': reading['signal_type'],
            'started_at': reading['started_at'].isoformat() if reading['started_at'] else None,
            'ended_at': reading['ended_at'].isoformat() if reading['ended_at'] else None,
            'duration_minutes': round(float(reading['duration_minutes']), 2) if reading.get('duration_minutes') else None,
            'sample_rate_hz': reading.get('sample_rate_hz')
        }
    
    @staticmethod
    def _format_location(location: Dict) -> Dict:
        """Formatea una ubicación para respuesta"""
        return {
            'id': str(location['id']),
            'latitude': float(location['latitude']) if location['latitude'] else None,
            'longitude': float(location['longitude']) if location['longitude'] else None,
            'timestamp': location['timestamp'].isoformat() if location['timestamp'] else None,
            'source': location.get('source'),
            'accuracy_meters': float(location['accuracy_meters']) if location.get('accuracy_meters') else None
        }
    
    @staticmethod
    def _group_care_team(care_team_raw: List[Dict]) -> List[Dict]:
        """Agrupa miembros del equipo de cuidado por equipo"""
        teams_dict = {}
        
        for row in care_team_raw:
            team_id = str(row['team_id'])
            team_name = row['team_name']
            
            if team_id not in teams_dict:
                teams_dict[team_id] = {
                    'team_name': team_name,
                    'members': []
                }
            
            teams_dict[team_id]['members'].append({
                'name': row['member_name'],
                'role': row['role'],
                'email': row['email']
            })
        
        return list(teams_dict.values())
    
    @staticmethod
    def _format_caregiver(caregiver: Dict) -> Dict:
        """Formatea un cuidador para respuesta"""
        return {
            'id': str(caregiver['user_id']),
            'name': caregiver['caregiver_name'],
            'email': caregiver['email'],
            'relationship': caregiver.get('relationship_type'),
            'relationship_label': caregiver.get('relationship_label', 'Cuidador'),
            'is_primary': caregiver['is_primary'],
            'started_at': caregiver['started_at'].isoformat() if caregiver.get('started_at') else None,
            'ended_at': caregiver['ended_at'].isoformat() if caregiver.get('ended_at') else None,
            'note': caregiver.get('note'),
            'active': caregiver.get('ended_at') is None
        }
