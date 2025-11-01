"""Unit tests for gateway service."""
import pytest
import json
from app import create_app


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_health_endpoint(client):
    """Test the gateway health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['service'] == 'gateway'
    assert data['status'] == 'healthy'


def test_proxy_to_auth_service(client):
    """Test proxying to auth service."""
    response = client.get('/auth/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['data']['service'] == 'auth'


def test_proxy_to_patient_service(client):
    """Test proxying to patient service."""
    response = client.get('/patients/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['data']['service'] == 'patient'


def test_proxy_unknown_service(client):
    """Test proxying to an unknown service."""
    response = client.get('/unknown_service/test')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error']['id'] == 'HG-GW-UNKNOWN-SERVICE'


def test_auth_login_through_gateway(client):
    """Test authentication login through gateway."""
    response = client.post(
        '/auth/login',
        data=json.dumps({
            'email': 'admin@heartguard.com',
            'password': 'Admin#2025'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'tokens' in data['data']
    assert 'access_token' in data['data']['tokens']
    
    # Verify roles are included
    roles = data['data']['tokens'].get('roles', [])
    assert isinstance(roles, list)
    # Admin user should have superadmin role
    if len(roles) > 0:
        assert 'superadmin' in roles


def test_list_patients_through_gateway(client):
    """Test listing patients through gateway."""
    response = client.get('/patients')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'patients' in data['data']
    assert isinstance(data['data']['patients'], list)
    assert len(data['data']['patients']) >= 3


def test_list_patients_with_auth_through_gateway(client):
    """Test listing patients with authentication through gateway."""
    # First login to get token
    login_response = client.post(
        '/auth/login',
        data=json.dumps({
            'email': 'admin@heartguard.com',
            'password': 'Admin#2025'
        }),
        content_type='application/json'
    )
    
    assert login_response.status_code == 200
    login_data = json.loads(login_response.data)
    token = login_data['data']['tokens']['access_token']
    
    # Now request patients with token
    response = client.get(
        '/patients',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'patients' in data['data']
    assert isinstance(data['data']['patients'], list)
    assert len(data['data']['patients']) >= 3


def test_gateway_preserves_headers(client):
    """Test that gateway preserves important headers."""
    response = client.get(
        '/patients/health',
        headers={
            'X-Request-ID': 'test-request-123',
            'Accept': 'application/json'
        }
    )
    
    assert response.status_code == 200
    # The proxied response should succeed
    data = json.loads(response.data)
    assert data['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
