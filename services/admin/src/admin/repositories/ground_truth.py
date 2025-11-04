"""Repository helpers for ground truth label management."""
from __future__ import annotations

from typing import Any

from .. import db


class GroundTruthRepository:
    """Data access for ground truth labels scoped to patients."""

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
                gt.id,
                gt.patient_id,
                gt.event_type_id,
                et.code AS event_type_code,
                et.description AS event_type_label,
                gt.onset,
                gt.offset_at,
                gt.annotated_by_user_id,
                u.name AS annotated_by_name,
                gt.source,
                gt.note
            FROM ground_truth_labels gt
            JOIN event_types et ON et.id = gt.event_type_id
            LEFT JOIN users u ON u.id = gt.annotated_by_user_id
            WHERE gt.patient_id = %(patient_id)s
            ORDER BY gt.onset DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        params = {
            "patient_id": patient_id,
            "limit": safe_limit,
            "offset": safe_offset,
        }
        return db.fetch_all(query, params)

    def get(self, label_id: str) -> dict[str, Any] | None:
        query = """
            SELECT
                gt.id,
                gt.patient_id,
                gt.event_type_id,
                et.code AS event_type_code,
                et.description AS event_type_label,
                gt.onset,
                gt.offset_at,
                gt.annotated_by_user_id,
                u.name AS annotated_by_name,
                gt.source,
                gt.note
            FROM ground_truth_labels gt
            JOIN event_types et ON et.id = gt.event_type_id
            LEFT JOIN users u ON u.id = gt.annotated_by_user_id
            WHERE gt.id = %(label_id)s
        """
        return db.fetch_one(query, {"label_id": label_id})

    def create(
        self,
        patient_id: str,
        *,
        event_type_id: str,
        onset: str,
        offset_at: str | None = None,
        annotated_by_user_id: str | None = None,
        source: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        query = """
            INSERT INTO ground_truth_labels (
                patient_id,
                event_type_id,
                onset,
                offset_at,
                annotated_by_user_id,
                source,
                note
            )
            VALUES (%(patient_id)s, %(event_type_id)s, %(onset)s, %(offset_at)s, %(annotated_by_user_id)s, %(source)s, %(note)s)
            RETURNING
                id,
                patient_id,
                event_type_id,
                onset,
                offset_at,
                annotated_by_user_id,
                source,
                note
        """
        params = {
            "patient_id": patient_id,
            "event_type_id": event_type_id,
            "onset": onset,
            "offset_at": offset_at,
            "annotated_by_user_id": annotated_by_user_id,
            "source": source,
            "note": note,
        }
        return db.fetch_one(query, params)

    def update(
        self,
        label_id: str,
        *,
        event_type_id: str | None = None,
        onset: str | None = None,
        offset_at: str | None = None,
        annotated_by_user_id: str | None = None,
        source: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        query = """
            UPDATE ground_truth_labels
               SET event_type_id = COALESCE(%(event_type_id)s, event_type_id),
                   onset = COALESCE(%(onset)s, onset),
                   offset_at = COALESCE(%(offset_at)s, offset_at),
                   annotated_by_user_id = COALESCE(%(annotated_by_user_id)s, annotated_by_user_id),
                   source = COALESCE(NULLIF(%(source)s, ''), source),
                   note = COALESCE(%(note)s, note)
             WHERE id = %(label_id)s
            RETURNING
                id,
                patient_id,
                event_type_id,
                onset,
                offset_at,
                annotated_by_user_id,
                source,
                note
        """
        params = {
            "label_id": label_id,
            "event_type_id": event_type_id,
            "onset": onset,
            "offset_at": offset_at,
            "annotated_by_user_id": annotated_by_user_id,
            "source": source,
            "note": note,
        }
        return db.fetch_one(query, params)

    def delete(self, label_id: str) -> bool:
        query = """
            DELETE FROM ground_truth_labels
            WHERE id = %(label_id)s
            RETURNING id
        """
        result = db.fetch_one(query, {"label_id": label_id})
        return result is not None

    def resolve_event_type_id(self, code: str) -> str | None:
        query = """
            SELECT id
            FROM event_types
            WHERE lower(code) = lower(%(code)s)
            LIMIT 1
        """
        result = db.fetch_one(query, {"code": code})
        return result["id"] if result else None

    def list_event_types(self) -> list[dict[str, Any]]:
        query = """
            SELECT id, code, description
            FROM event_types
            ORDER BY description ASC
        """
        return db.fetch_all(query)
