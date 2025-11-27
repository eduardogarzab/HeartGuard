"""Repository helpers for patient location history."""
from __future__ import annotations

from typing import Any

from .. import db


class PatientLocationsRepository:
    """Data access layer for patient location entries."""

    def list_for_patient(
        self,
        patient_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 200))
        safe_offset = max(0, int(offset))
        query = """
            SELECT
                pl.id,
                pl.patient_id,
                pl.ts,
                ST_Y(pl.geom)::double precision AS latitude,
                ST_X(pl.geom)::double precision AS longitude,
                pl.source,
                pl.accuracy_m
            FROM patient_locations pl
            WHERE pl.patient_id = %(patient_id)s
            ORDER BY pl.ts DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        params = {
            "patient_id": patient_id,
            "limit": safe_limit,
            "offset": safe_offset,
        }
        return db.fetch_all(query, params)

    def create(
        self,
        patient_id: str,
        *,
        latitude: float,
        longitude: float,
        timestamp: str | None = None,
        source: str | None = None,
        accuracy_m: float | None = None,
    ) -> dict[str, Any] | None:
        query = """
            INSERT INTO patient_locations (
                patient_id,
                ts,
                geom,
                source,
                accuracy_m
            )
            VALUES (
                %(patient_id)s,
                COALESCE(%(timestamp)s, NOW()),
                ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326),
                NULLIF(%(source)s, ''),
                %(accuracy_m)s
            )
            RETURNING
                id,
                patient_id,
                ts,
                ST_Y(geom)::double precision AS latitude,
                ST_X(geom)::double precision AS longitude,
                source,
                accuracy_m
        """
        params = {
            "patient_id": patient_id,
            "timestamp": timestamp,
            "longitude": longitude,
            "latitude": latitude,
            "source": source,
            "accuracy_m": accuracy_m,
        }
        return db.fetch_one(query, params)

    def delete(self, patient_id: str, location_id: str) -> bool:
        query = """
            DELETE FROM patient_locations
            WHERE id = %(location_id)s AND patient_id = %(patient_id)s
            RETURNING id
        """
        params = {"patient_id": patient_id, "location_id": location_id}
        return db.fetch_one(query, params) is not None
