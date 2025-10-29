"""Catalog service routes."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, g, jsonify, request

from ..repository import CatalogNotFound, CatalogRepository, PermissionDenied
from ..utils.auth import AuthenticationError, token_required
from ..utils.helpers import log_analytics_event, log_audit_event
from ..utils.responses import auto_response

catalog_bp = Blueprint("catalog", __name__)
repository = CatalogRepository()


@catalog_bp.errorhandler(AuthenticationError)
def _handle_auth_error(exc: AuthenticationError):
    return jsonify({"error": str(exc)}), 401


@catalog_bp.errorhandler(PermissionDenied)
def _handle_permission_error(exc: PermissionDenied):
    return jsonify({"error": str(exc)}), 403


@catalog_bp.errorhandler(CatalogNotFound)
def _handle_not_found(exc: CatalogNotFound):
    return jsonify({"error": str(exc)}), 404


@catalog_bp.route("/v1/catalog/<string:catalog_name>", methods=["GET"])
@token_required
def list_catalog(catalog_name: str):
    entries = repository.list_entries(catalog_name, g.org_id)
    log_analytics_event(
        "catalog_list",
        {"catalog": catalog_name, "org_id": g.org_id, "count": len(entries)},
    )
    return auto_response({"items": entries}, 200)


@catalog_bp.route("/v1/catalog/<string:catalog_name>", methods=["POST"])
@token_required
def create_catalog_entry(catalog_name: str):
    payload = request.get_json(force=True) or {}
    if "name" not in payload:
        return jsonify({"error": "Field 'name' is required"}), 400

    entry = repository.create_entry(catalog_name, payload)
    log_audit_event("create", catalog_name, entry)
    log_analytics_event("catalog_create", {"catalog": catalog_name, "entry_id": entry["id"]})
    return auto_response(entry, 201)


@catalog_bp.route("/v1/catalog/<string:catalog_name>/<uuid:entry_id>", methods=["PATCH"])
@token_required
def update_catalog_entry(catalog_name: str, entry_id: UUID):
    payload = request.get_json(force=True) or {}
    if not payload:
        return jsonify({"error": "No fields to update"}), 400

    entry = repository.update_entry(catalog_name, str(entry_id), payload, g.org_id)
    log_audit_event("update", catalog_name, entry)
    log_analytics_event("catalog_update", {"catalog": catalog_name, "entry_id": entry["id"]})
    return auto_response(entry, 200)


@catalog_bp.route("/v1/catalog/<string:catalog_name>/<uuid:entry_id>", methods=["DELETE"])
@token_required
def delete_catalog_entry(catalog_name: str, entry_id: UUID):
    repository.delete_entry(catalog_name, str(entry_id), g.org_id)
    log_audit_event("delete", catalog_name, {"id": str(entry_id)})
    log_analytics_event("catalog_delete", {"catalog": catalog_name, "entry_id": str(entry_id)})
    return auto_response(None, 204)
