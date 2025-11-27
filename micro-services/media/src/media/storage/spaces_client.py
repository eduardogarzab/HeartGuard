"""Wrapper mínimo sobre boto3 para interactuar con DigitalOcean Spaces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


class SpacesClientError(RuntimeError):
    """Errores de comunicación con Spaces."""

    def __init__(self, message: str, *, error_code: str = "storage_error") -> None:
        self.error_code = error_code
        super().__init__(message)


@dataclass
class SpacesClient:
    """Cliente especializado para operaciones S3 en DigitalOcean Spaces."""

    bucket: str
    region: str
    endpoint_url: str
    access_key: str
    secret_key: str
    cdn_base_url: str
    default_acl: str = "public-read"

    def __post_init__(self) -> None:
        session = boto3.session.Session()
        
        # Configuración de timeouts y reintentos para boto3
        boto_config = Config(
            connect_timeout=10,
            read_timeout=30,
            retries={
                'max_attempts': 3,
                'mode': 'standard'
            }
        )
        
        self._client = session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=boto_config,
        )
        self.cdn_base_url = self.cdn_base_url.rstrip("/")

    def upload_object(self, *, key: str, data: bytes, content_type: str) -> dict[str, Any]:
        try:
            response = self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ACL=self.default_acl,
            )
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover - depende de red
            raise SpacesClientError("Error al subir objeto a Spaces", error_code="upload_failed") from exc

        etag = response.get("ETag")
        return {
            "etag": etag.strip('"') if isinstance(etag, str) else None,
            "url": f"{self.cdn_base_url}/{key}",
        }

    def delete_prefix(self, prefix: str) -> int:
        deleted = 0
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                contents = page.get("Contents", [])
                if not contents:
                    continue
                objects = [{"Key": entry["Key"]} for entry in contents]
                self._client.delete_objects(Bucket=self.bucket, Delete={"Objects": objects, "Quiet": True})
                deleted += len(objects)
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover - depende de red
            raise SpacesClientError("Error al eliminar objetos en Spaces", error_code="delete_failed") from exc
        return deleted

    def delete_object(self, key: str) -> bool:
        """Elimina un objeto específico por su key.
        
        Args:
            key: Key del objeto a eliminar
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            SpacesClientError: Si hay un error al eliminar
        """
        try:
            self._client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover - depende de red
            raise SpacesClientError(f"Error al eliminar objeto {key} en Spaces", error_code="delete_failed") from exc
