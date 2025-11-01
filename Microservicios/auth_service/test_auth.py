"""Unit tests for authentication service."""
import pytest
import json
from app import create_app
from common.database import db
from models import User


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


@pytest.fixture
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        # Check if test user already exists
        user = User.query.filter_by(email='test@heartguard.com').first()
        if not user:
            user = User(
                name='Test User',
                email='test@heartguard.com',
                user_status_id='a3306ef6-aa3b-4e4a-bfc9-d66d35c3a7fb'  # active status
            )
            user.set_password('Test#2025')
            db.session.add(user)
            db.session.commit()
        yield user
        # Cleanup: remove test user
        User.query.filter_by(email='test@heartguard.com').delete()
        db.session.commit()


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/auth/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['data']['service'] == 'auth'


def test_login_success(client, app):
    """Test successful login with correct credentials."""
    # Use the seeded admin user
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
    assert 'refresh_token' in data['data']['tokens']
    assert 'roles' in data['data']['tokens']
    
    # Verify roles are loaded from database
    roles = data['data']['tokens']['roles']
    assert isinstance(roles, list)
    assert len(roles) > 0
    # Admin user should have 'superadmin' role
    assert 'superadmin' in roles


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        '/auth/login',
        data=json.dumps({
            'email': 'admin@heartguard.com',
            'password': 'WrongPassword'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error']['id'] == 'HG-AUTH-CREDENTIALS'


def test_login_missing_fields(client):
    """Test login with missing required fields."""
    response = client.post(
        '/auth/login',
        data=json.dumps({
            'email': 'admin@heartguard.com'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error']['id'] == 'HG-AUTH-VALIDATION'


def test_register_new_user(client, app):
    """Test registering a new user."""
    # Use a unique email for this test
    test_email = f'newuser_{id(app)}@heartguard.com'
    
    response = client.post(
        '/auth/register',
        data=json.dumps({
            'name': 'New Test User',
            'email': test_email,
            'password': 'NewPass#2025'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'user' in data['data']
    assert data['data']['user']['email'] == test_email
    assert 'tokens' in data['data']
    
    # Cleanup
    with app.app_context():
        User.query.filter_by(email=test_email).delete()
        db.session.commit()


def test_register_duplicate_user(client):
    """Test registering a user that already exists."""
    response = client.post(
        '/auth/register',
        data=json.dumps({
            'name': 'Duplicate User',
            'email': 'admin@heartguard.com',  # Already exists
            'password': 'Pass#2025'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 409
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert data['error']['id'] == 'HG-AUTH-CONFLICT'


def test_user_get_roles(app):
    """Test the User.get_roles() method."""
    with app.app_context():
        # Test with admin user who has superadmin role
        admin_user = User.query.filter_by(email='admin@heartguard.com').first()
        assert admin_user is not None
        
        roles = admin_user.get_roles()
        assert isinstance(roles, list)
        assert 'superadmin' in roles


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
