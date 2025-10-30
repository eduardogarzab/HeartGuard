"""In-memory user store for the Auth service.
TODO: replace with persistent storage (Postgres/Mongo) when available.
"""
from typing import Dict, Optional
from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash

USERS: Dict[str, Dict] = {}
USERS_BY_EMAIL: Dict[str, str] = {}


def create_user(email: str, password: str, name: str, org_id: str) -> Dict:
    if email.lower() in USERS_BY_EMAIL:
        raise ValueError("User already exists")
    user_id = str(uuid4())
    hashed_password = generate_password_hash(password)
    existing_roles = [u for u in USERS.values() if u["org_id"] == org_id]
    role = "org_admin" if not existing_roles else "user"
    record = {
        "user_id": user_id,
        "email": email.lower(),
        "password_hash": hashed_password,
        "name": name,
        "org_id": org_id,
        "role": role,
    }
    USERS[user_id] = record
    USERS_BY_EMAIL[email.lower()] = user_id
    return {k: record[k] for k in ("user_id", "email", "name", "org_id", "role")}


def get_user_by_email(email: str) -> Optional[Dict]:
    user_id = USERS_BY_EMAIL.get(email.lower())
    if not user_id:
        return None
    return USERS.get(user_id)


def get_user_by_id(user_id: str) -> Optional[Dict]:
    return USERS.get(user_id)


def verify_credentials(email: str, password: str) -> Optional[Dict]:
    record = get_user_by_email(email)
    if not record:
        return None
    if check_password_hash(record["password_hash"], password):
        return record
    return None
