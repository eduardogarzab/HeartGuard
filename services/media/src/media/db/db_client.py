"""Cliente de base de datos para el Media Service."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Cliente para interactuar con PostgreSQL."""

    def __init__(self, database_url: str, *, min_conn: int = 1, max_conn: int = 10) -> None:
        """Inicializa el pool de conexiones.
        
        Args:
            database_url: URL de conexión a PostgreSQL
            min_conn: Número mínimo de conexiones en el pool
            max_conn: Número máximo de conexiones en el pool
        """
        self.database_url = database_url
        parsed = urlparse(database_url)
        
        self._pool = psycopg2.pool.SimpleConnectionPool(
            min_conn,
            max_conn,
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password,
            options='-c search_path=heartguard,public'
        )
        logger.info("Database connection pool initialized")

    def get_connection(self):
        """Obtiene una conexión del pool."""
        return self._pool.getconn()

    def return_connection(self, conn) -> None:
        """Devuelve una conexión al pool."""
        self._pool.putconn(conn)

    def close_all(self) -> None:
        """Cierra todas las conexiones del pool."""
        self._pool.closeall()

    def update_user_photo_url(self, user_id: str, photo_url: str | None) -> bool:
        """Actualiza la URL de foto de perfil de un usuario.
        
        Args:
            user_id: UUID del usuario
            photo_url: URL de la foto o None para eliminar
            
        Returns:
            True si se actualizó correctamente, False si no se encontró el usuario
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE heartguard.users 
                    SET profile_photo_url = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                    """,
                    (photo_url, user_id)
                )
                result = cur.fetchone()
                conn.commit()
                return result is not None
        except Exception as exc:
            if conn:
                conn.rollback()
            logger.error(f"Error updating user photo URL: {exc}", exc_info=True)
            raise DatabaseError(f"Error al actualizar foto de usuario: {exc}") from exc
        finally:
            if conn:
                self.return_connection(conn)

    def update_patient_photo_url(self, patient_id: str, photo_url: str | None) -> bool:
        """Actualiza la URL de foto de perfil de un paciente.
        
        Args:
            patient_id: UUID del paciente
            photo_url: URL de la foto o None para eliminar
            
        Returns:
            True si se actualizó correctamente, False si no se encontró el paciente
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE heartguard.patients 
                    SET profile_photo_url = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                    """,
                    (photo_url, patient_id)
                )
                result = cur.fetchone()
                conn.commit()
                return result is not None
        except Exception as exc:
            if conn:
                conn.rollback()
            logger.error(f"Error updating patient photo URL: {exc}", exc_info=True)
            raise DatabaseError(f"Error al actualizar foto de paciente: {exc}") from exc
        finally:
            if conn:
                self.return_connection(conn)

    def get_user_photo_url(self, user_id: str) -> str | None:
        """Obtiene la URL de foto actual de un usuario.
        
        Args:
            user_id: UUID del usuario
            
        Returns:
            URL de la foto o None si no tiene foto o no existe el usuario
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT profile_photo_url FROM heartguard.users WHERE id = %s",
                    (user_id,)
                )
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as exc:
            logger.error(f"Error getting user photo URL: {exc}", exc_info=True)
            raise DatabaseError(f"Error al obtener foto de usuario: {exc}") from exc
        finally:
            if conn:
                self.return_connection(conn)

    def get_patient_photo_url(self, patient_id: str) -> str | None:
        """Obtiene la URL de foto actual de un paciente.
        
        Args:
            patient_id: UUID del paciente
            
        Returns:
            URL de la foto o None si no tiene foto o no existe el paciente
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT profile_photo_url FROM heartguard.patients WHERE id = %s",
                    (patient_id,)
                )
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as exc:
            logger.error(f"Error getting patient photo URL: {exc}", exc_info=True)
            raise DatabaseError(f"Error al obtener foto de paciente: {exc}") from exc
        finally:
            if conn:
                self.return_connection(conn)


class DatabaseError(RuntimeError):
    """Error al interactuar con la base de datos."""
    pass
