# signal_service/app/repository/device_key_repository.py
import bcrypt
from sqlalchemy.orm import joinedload
from ..database import SessionLocal
from ..models.models import DeviceKey

def find_key_by_uuid(device_uuid: str):
    """
    Finds a device key by its UUID, eagerly loading associated signal streams.

    Args:
        device_uuid: The UUID of the device to find.

    Returns:
        The DeviceKey object or None if not found.
    """
    db = SessionLocal()
    try:
        return (
            db.query(DeviceKey)
            .options(joinedload(DeviceKey.signal_streams))
            .filter(DeviceKey.device_uuid == device_uuid)
            .first()
        )
    finally:
        db.close()

def verify_api_key(device_key: DeviceKey, plain_api_key: str) -> bool:
    """
    Verifies a plain-text API key against the hashed key stored in the database.

    Args:
        device_key: The DeviceKey object from the database.
        plain_api_key: The plain-text API key received from the device.

    Returns:
        True if the key is valid, False otherwise.
    """
    if not device_key or not plain_api_key:
        return False

    # bcrypt.checkpw expects bytes, so we encode the strings
    return bcrypt.checkpw(
        plain_api_key.encode('utf-8'),
        device_key.hashed_api_key.encode('utf-8')
    )
