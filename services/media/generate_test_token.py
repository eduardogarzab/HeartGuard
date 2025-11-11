#!/usr/bin/env python3
"""Generate test JWT tokens for media service testing."""
import jwt
import uuid
from datetime import datetime, timedelta, timezone

JWT_SECRET = "change-me-secret-key-12345"
JWT_ALGORITHM = "HS256"

def generate_user_token(user_id: str = None) -> str:
    """Generate a token for a user account."""
    if user_id is None:
        user_id = str(uuid.uuid4())
    
    payload = {
        "account_type": "user",
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_patient_token(patient_id: str = None) -> str:
    """Generate a token for a patient account."""
    if patient_id is None:
        patient_id = str(uuid.uuid4())
    
    payload = {
        "account_type": "patient",
        "patient_id": patient_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


if __name__ == "__main__":
    import sys
    
    test_user_id = "11111111-1111-1111-1111-111111111111"
    test_patient_id = "22222222-2222-2222-2222-222222222222"
    
    user_token = generate_user_token(test_user_id)
    patient_token = generate_patient_token(test_patient_id)
    
    print("=" * 70)
    print("TEST JWT TOKENS FOR MEDIA SERVICE")
    print("=" * 70)
    print()
    print(f"User ID: {test_user_id}")
    print(f"User Token:\n{user_token}")
    print()
    print(f"Patient ID: {test_patient_id}")
    print(f"Patient Token:\n{patient_token}")
    print()
    print("=" * 70)
    print("USAGE EXAMPLES:")
    print("=" * 70)
    print()
    print("# Upload user photo:")
    print(f'curl -X POST http://localhost:8080/media/users/{test_user_id}/photo \\')
    print(f'  -H "Authorization: Bearer {user_token}" \\')
    print('  -F "photo=@/path/to/image.jpg"')
    print()
    print("# Upload patient photo:")
    print(f'curl -X POST http://localhost:8080/media/patients/{test_patient_id}/photo \\')
    print(f'  -H "Authorization: Bearer {patient_token}" \\')
    print('  -F "photo=@/path/to/image.jpg"')
    print()
    print("# Delete user photo:")
    print(f'curl -X DELETE http://localhost:8080/media/users/{test_user_id}/photo \\')
    print(f'  -H "Authorization: Bearer {user_token}"')
    print()
