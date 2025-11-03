"""Authorization middleware for the admin service."""

from __future__ import annotations

from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Iterable
from uuid import UUID

from flask import Response, current_app, g, jsonify, request

from ..services.auth_client import AuthClient

JsonResponse = Response


def _forbidden(message: str) -> JsonResponse:
    return jsonify({"error": message}), HTTPStatus.FORBIDDEN


def _unauthorized(message: str) -> JsonResponse:
    return jsonify({"error": message}), HTTPStatus.UNAUTHORIZED


def _extract_membership(org_id: UUID | str, memberships: Iterable[dict[str, Any]]):
    org_id_str = str(org_id)
    for membership in memberships:
        if str(membership.get("org_id")) == org_id_str:
            return membership
    return None


def _has_required_role(membership: dict[str, Any], roles: Iterable[str]) -> bool:
    member_roles: list[str] = []
    if "roles" in membership and isinstance(membership["roles"], list):
        member_roles.extend(str(role) for role in membership["roles"])
    if "role" in membership and membership["role"]:
        member_roles.append(str(membership["role"]))
    return any(role in member_roles for role in roles)


def org_admin_required(roles: Iterable[str] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that enforces organization admin permissions."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return _unauthorized("Missing or invalid authorization header")

            token = auth_header.split(" ", 1)[1].strip()
            if not token:
                return _unauthorized("Missing bearer token")

            client = AuthClient(base_url=current_app.config.get("AUTH_SERVICE_URL"))
            validation = client.validate_token(token)
            if not validation or not validation.get("active"):
                return _unauthorized("Invalid token")

            payload = validation.get("payload") or {}
            if payload.get("account_type") != "user":
                return _forbidden("Unsupported account type")

            view_args = request.view_args or {}
            org_id = view_args.get("org_id")
            memberships = payload.get("org_memberships", [])

            if org_id is not None:
                membership = _extract_membership(org_id, memberships)
                if membership is None:
                    return _forbidden("User is not a member of this organization")

                if roles:
                    if not _has_required_role(membership, roles):
                        return _forbidden("User does not have the required role")
            elif roles:
                # When roles are required but no org scope is provided, deny access.
                return _forbidden("Organization scope is required for this action")

            g.user_payload = payload
            g.user_id = payload.get("user_id")
            g.org_memberships = memberships

            return fn(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["org_admin_required"]
