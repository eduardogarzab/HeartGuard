"""Unit tests for patient service."""
import pytest
import json
from app import create_app
from common.database import db
from models import Patient


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://heartguard_app:dev_change_me@localhost:5432/heartguard'
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/patients/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['data']['service'] == 'patient'


def test_list_patients_without_auth(client):
    """Test listing patients without authentication."""
    response = client.get('/patients')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'patients' in data['data']
    assert isinstance(data['data']['patients'], list)
    # Should return seeded patients
    assert len(data['data']['patients']) >= 3


def test_list_patients_structure(client):
    """Test that patient data has correct structure."""
    response = client.get('/patients')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    patients = data['data']['patients']
    if len(patients) > 0:
        patient = patients[0]
        # Verify required fields
        assert 'id' in patient
        assert 'person_name' in patient
        assert 'org_id' in patient
        # Optional fields
        assert 'birthdate' in patient or patient.get('birthdate') is None
        assert 'sex_id' in patient or patient.get('sex_id') is None
        assert 'risk_level_id' in patient or patient.get('risk_level_id') is None


def test_get_patient_by_id(client, app):
    """Test getting a specific patient by ID."""
    # First, get list of patients to get a valid ID
    response = client.get('/patients')
    data = json.loads(response.data)
    patients = data['data']['patients']
    
    if len(patients) > 0:
        patient_id = patients[0]['id']
        
        # Get specific patient
        response = client.get(f'/patients/{patient_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'patient' in data['data']
        assert data['data']['patient']['id'] == patient_id


def test_get_patient_not_found(client):
    """Test getting a patient that doesn't exist."""
    fake_id = '00000000-0000-0000-0000-000000000000'
    response = client.get(f'/patients/{fake_id}')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error']['id'] == 'HG-PATIENT-NOT-FOUND'


def test_create_patient_without_auth(client):
    """Test creating a patient without authentication (should fail)."""
    response = client.post(
        '/patients',
        data=json.dumps({
            'person_name': 'Test Patient',
            'org_id': '05bc3d9a-f6ce-4a2f-9359-634bf2962f9f'
        }),
        content_type='application/json'
    )
    
    # Should require authentication
    assert response.status_code == 401


def test_patient_model_to_dict(app):
    """Test the Patient.to_dict() method."""
    with app.app_context():
        # Get first patient from database
        patient = Patient.query.first()
        assert patient is not None
        
        patient_dict = patient.to_dict()
        assert isinstance(patient_dict, dict)
        assert 'id' in patient_dict
        assert 'person_name' in patient_dict
        assert 'org_id' in patient_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
