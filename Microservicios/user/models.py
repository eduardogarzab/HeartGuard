"""In-memory user profile storage.
TODO: replace with persistent storage in future iterations.
"""
from typing import Dict

USERS: Dict[str, Dict] = {}

DEFAULT_PROFILE = {
    "email": "demo@heartguard.com",
    "name": "Demo User",
    "phone": "+52-555-0101",
    "preferences": {"language": "es-MX", "units": "metric"},
    "org_id": "default",
    "role": "user",
}


def get_user(user_id: str) -> Dict:
    record = USERS.get(user_id)
    if not record:
        # Fallback to default profile clone
        record = {**DEFAULT_PROFILE, "user_id": user_id}
        USERS[user_id] = record
    return record


def update_user(user_id: str, payload: Dict) -> Dict:
    profile = get_user(user_id)
    for key in ["email", "name", "phone"]:
        if key in payload:
            profile[key] = str(payload[key]).strip()
    if "preferences" in payload and isinstance(payload["preferences"], dict):
        prefs = profile.setdefault("preferences", {})
        for pref_key in ["language", "units"]:
            if pref_key in payload["preferences"]:
                prefs[pref_key] = str(payload["preferences"][pref_key]).strip()
    return profile
