"""Repository helpers for device management."""
from __future__ import annotations

from typing import Any

from .. import db


class DevicesRepository:
    """Data access helpers for devices scoped to an organization."""

    def list_for_org(
        self,
        org_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        active: bool | None = None,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 200))
        safe_offset = max(0, int(offset))
        clauses = ["d.org_id = %(org_id)s"]
        params: dict[str, Any] = {
            "org_id": org_id,
            "limit": safe_limit,
            "offset": safe_offset,
        }
        if active is not None:
            clauses.append("d.active = %(active)s")
            params["active"] = active
        query = f"""
            SELECT
                d.id,
                d.org_id,
                d.serial,
                d.brand,
                d.model,
                dt.code AS device_type_code,
                dt.label AS device_type_label,
                d.owner_patient_id,
                p.person_name AS owner_patient_name,
                d.registered_at,
                d.active
            FROM devices d
            JOIN device_types dt ON dt.id = d.device_type_id
            LEFT JOIN patients p ON p.id = d.owner_patient_id
            WHERE {' AND '.join(clauses)}
            ORDER BY d.registered_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """
        return db.fetch_all(query, params)

    def list_for_patient(self, org_id: str, patient_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
                d.id,
                d.org_id,
                d.serial,
                d.brand,
                d.model,
                dt.code AS device_type_code,
                dt.label AS device_type_label,
                d.owner_patient_id,
                p.person_name AS owner_patient_name,
                d.registered_at,
                d.active
            FROM devices d
            JOIN device_types dt ON dt.id = d.device_type_id
            LEFT JOIN patients p ON p.id = d.owner_patient_id
            WHERE d.org_id = %(org_id)s AND d.owner_patient_id = %(patient_id)s
            ORDER BY d.registered_at DESC
        """
        params = {"org_id": org_id, "patient_id": patient_id}
        return db.fetch_all(query, params)

    def get(self, org_id: str, device_id: str) -> dict[str, Any] | None:
        query = """
            SELECT
                d.id,
                d.org_id,
                d.serial,
                d.brand,
                d.model,
                dt.code AS device_type_code,
                dt.label AS device_type_label,
                d.owner_patient_id,
                p.person_name AS owner_patient_name,
                d.registered_at,
                d.active
            FROM devices d
            JOIN device_types dt ON dt.id = d.device_type_id
            LEFT JOIN patients p ON p.id = d.owner_patient_id
            WHERE d.id = %(device_id)s AND d.org_id = %(org_id)s
        """
        params = {"device_id": device_id, "org_id": org_id}
        return db.fetch_one(query, params)

    def create(
        self,
        org_id: str,
        *,
        serial: str,
        device_type_code: str,
        brand: str | None = None,
        model: str | None = None,
        owner_patient_id: str | None = None,
        active: bool | None = True,
    ) -> dict[str, Any] | None:
        query = """
            SELECT *
            FROM heartguard.sp_device_create(
                %(org_id)s,
                %(serial)s,
                %(brand)s,
                %(model)s,
                %(device_type_code)s,
                %(owner_patient_id)s,
                %(active)s
            )
        """
        params = {
            "org_id": org_id,
            "serial": serial,
            "brand": brand,
            "model": model,
            "device_type_code": device_type_code,
            "owner_patient_id": owner_patient_id,
            "active": active,
        }
        return db.fetch_one(query, params)

    def update(
        self,
        org_id: str,
        device_id: str,
        *,
        serial: str,
        device_type_code: str,
        brand: str | None = None,
        model: str | None = None,
        owner_patient_id: str | None = None,
        active: bool | None = None,
    ) -> dict[str, Any] | None:
        query = """
            SELECT *
            FROM heartguard.sp_device_update(
                %(device_id)s,
                %(org_id)s,
                %(serial)s,
                %(brand)s,
                %(model)s,
                %(device_type_code)s,
                %(owner_patient_id)s,
                %(active)s
            )
        """
        params = {
            "device_id": device_id,
            "org_id": org_id,
            "serial": serial,
            "brand": brand,
            "model": model,
            "device_type_code": device_type_code,
            "owner_patient_id": owner_patient_id,
            "active": active,
        }
        return db.fetch_one(query, params)

    def delete(self, device_id: str) -> bool:
        query = """
            SELECT heartguard.sp_device_delete(%(device_id)s) AS deleted
        """
        result = db.fetch_one(query, {"device_id": device_id}) or {}
        return bool(result.get("deleted"))

    def list_device_types(self) -> list[dict[str, Any]]:
        query = """
            SELECT id, code, label
            FROM device_types
            ORDER BY label ASC
        """
        return db.fetch_all(query)
