from __future__ import annotations

import io
import uuid

import pytest
from werkzeug.datastructures import FileStorage

from media.services.photo_service import (
    MediaService,
    MediaStorageError,
    MediaValidationError,
)


class FakeSpacesClient:
    def __init__(self) -> None:
        self.uploads: list[dict[str, str]] = []
        self.deleted_prefixes: list[str] = []

    def upload_object(self, *, key: str, data: bytes, content_type: str) -> dict[str, str]:
        self.uploads.append({"key": key, "content_type": content_type, "size": str(len(data))})
        return {"etag": "fake-etag", "url": f"https://cdn.fake/{key}"}

    def delete_prefix(self, prefix: str) -> int:
        self.deleted_prefixes.append(prefix)
        return 1


class FakeDatabaseClient:
    def __init__(self) -> None:
        self.user_updates: list[tuple[str, str | None]] = []
        self.patient_updates: list[tuple[str, str | None]] = []
        self.existing_users = set()
        self.existing_patients = set()

    def update_user_photo_url(self, user_id: str, photo_url: str | None) -> bool:
        self.user_updates.append((user_id, photo_url))
        return user_id in self.existing_users

    def update_patient_photo_url(self, patient_id: str, photo_url: str | None) -> bool:
        self.patient_updates.append((patient_id, photo_url))
        return patient_id in self.existing_patients

    def get_user_photo_url(self, user_id: str) -> str | None:
        return None

    def get_patient_photo_url(self, patient_id: str) -> str | None:
        return None


@pytest.fixture
def fake_db_client() -> FakeDatabaseClient:
    return FakeDatabaseClient()


@pytest.fixture
def media_service(fake_db_client: FakeDatabaseClient) -> MediaService:
    return MediaService(
        storage=FakeSpacesClient(),
        db_client=fake_db_client,
        allowed_content_types=["image/jpeg", "image/png"],
        max_file_size=1024 * 1024,
        namespace_users="users",
        namespace_patients="patients",
    )


def _file(content: bytes, *, filename: str, content_type: str) -> FileStorage:
    stream = io.BytesIO(content)
    return FileStorage(stream=stream, filename=filename, content_type=content_type)


def test_save_photo_generates_key(monkeypatch: pytest.MonkeyPatch, media_service: MediaService, fake_db_client: FakeDatabaseClient):
    fake_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    monkeypatch.setattr(uuid, "uuid4", lambda: fake_uuid)

    user_id = str(uuid.uuid4())
    fake_db_client.existing_users.add(user_id)
    
    file = _file(b"binary-data", filename="photo.jpg", content_type="image/jpeg")
    result = media_service.save_photo(entity_type="users", entity_id=user_id, file=file)

    assert result.object_key.endswith(".jpg")
    assert result.object_key.startswith("users/")
    assert result.url.endswith(result.object_key)
    assert result.size_bytes == len(b"binary-data")
    assert result.etag == "fake-etag"
    
    # Verificar que se actualizó la DB
    assert len(fake_db_client.user_updates) == 1
    assert fake_db_client.user_updates[0][0] == user_id
    assert fake_db_client.user_updates[0][1] == result.url


def test_save_photo_rejects_large_file(media_service: MediaService, fake_db_client: FakeDatabaseClient):
    large_content = b"0" * (2 * 1024 * 1024)
    user_id = str(uuid.uuid4())
    fake_db_client.existing_users.add(user_id)
    
    file = _file(large_content, filename="photo.jpg", content_type="image/jpeg")
    with pytest.raises(MediaValidationError) as exc:
        media_service.save_photo(entity_type="users", entity_id=user_id, file=file)
    assert "excede el tamaño" in str(exc.value)


def test_save_photo_rejects_invalid_type(media_service: MediaService, fake_db_client: FakeDatabaseClient):
    patient_id = str(uuid.uuid4())
    fake_db_client.existing_patients.add(patient_id)
    
    file = _file(b"data", filename="photo.gif", content_type="image/gif")
    with pytest.raises(MediaValidationError) as exc:
        media_service.save_photo(entity_type="patients", entity_id=patient_id, file=file)
    assert exc.value.error_code == "unsupported_media_type"


def test_save_photo_fails_if_entity_not_found(media_service: MediaService):
    """Test que falle si el usuario/paciente no existe en la DB."""
    file = _file(b"data", filename="photo.jpg", content_type="image/jpeg")
    non_existent_id = str(uuid.uuid4())
    
    with pytest.raises(MediaValidationError) as exc:
        media_service.save_photo(entity_type="users", entity_id=non_existent_id, file=file)
    assert exc.value.error_code == "entity_not_found"
    assert "No se encontró" in str(exc.value)


def test_delete_photo_returns_count(media_service: MediaService):
    result = media_service.delete_photo(entity_type="users", entity_id=str(uuid.uuid4()))
    assert result.deleted_objects == 1
    assert result.prefix.startswith("users/")
