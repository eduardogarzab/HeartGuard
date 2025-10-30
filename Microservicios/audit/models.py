"""Simple in-memory append-only audit log.
TODO: replace with durable storage (e.g., BigQuery/Cloud Logging).
"""
from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4

AUDIT_EVENTS: List[Dict] = []


def append_event(payload: Dict) -> Dict:
    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor_user_id": payload.get("actor_user_id"),
        "action": payload.get("action"),
        "entity_type": payload.get("entity_type"),
        "entity_id": payload.get("entity_id"),
        "ip": payload.get("ip"),
        "metadata": payload.get("metadata", {}),
    }
    AUDIT_EVENTS.append(event)
    return event


def list_events(filters: Dict) -> List[Dict]:
    results = AUDIT_EVENTS
    actor = filters.get("actor_user_id")
    if actor:
        results = [event for event in results if event.get("actor_user_id") == actor]
    entity_type = filters.get("entity_type")
    if entity_type:
        results = [event for event in results if event.get("entity_type") == entity_type]
    since = filters.get("since")
    until = filters.get("until")
    if since:
        results = [event for event in results if event["timestamp"] >= since]
    if until:
        results = [event for event in results if event["timestamp"] <= until]
    return results[-1000:]
