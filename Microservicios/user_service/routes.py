"""User service managing application user profiles."""
from __future__ import annotations

import copy
import datetime as dt
from typing import Dict

from flask import Blueprint, Response, g, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response

bp = Blueprint("users", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "user", "status": "healthy"})


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_users() -> "Response":
    """List users from the database, optionally filtered by organization."""
    # Get org_id from query params if provided
    org_code = request.args.get("org_id") or request.args.get("org_code")
    
    try:
        # Base query to get users with their roles and organization membership
        # When filtering by org_code, use INNER JOIN to only get users in that org
        if org_code:
            query = """
                SELECT DISTINCT
                    u.id,
                    u.name,
                    u.email,
                    u.created_at,
                    us.code as status,
                    r.name as global_role,
                    org.code as org_code,
                    org.name as org_name,
                    orgr.code as org_role
                FROM users u
                LEFT JOIN user_statuses us ON u.user_status_id = us.id
                LEFT JOIN user_role ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                INNER JOIN user_org_membership uom ON u.id = uom.user_id
                INNER JOIN organizations org ON uom.org_id = org.id AND org.code = :org_code
                LEFT JOIN org_roles orgr ON uom.org_role_id = orgr.id
                ORDER BY u.created_at DESC
            """
            params = {'org_code': org_code}
        else:
            query = """
                SELECT DISTINCT
                    u.id,
                    u.name,
                    u.email,
                    u.created_at,
                    us.code as status,
                    r.name as global_role,
                    org.code as org_code,
                    org.name as org_name,
                    orgr.code as org_role
                FROM users u
                LEFT JOIN user_statuses us ON u.user_status_id = us.id
                LEFT JOIN user_role ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                LEFT JOIN user_org_membership uom ON u.id = uom.user_id
                LEFT JOIN organizations org ON uom.org_id = org.id
                LEFT JOIN org_roles orgr ON uom.org_role_id = orgr.id
                ORDER BY u.created_at DESC
            """
            params = {}
        
        result = db.session.execute(db.text(query), params)
        rows = result.fetchall()
        
        # Group by user to handle multiple roles
        users_dict = {}
        for row in rows:
            user_id = str(row[0])
            if user_id not in users_dict:
                users_dict[user_id] = {
                    'id': user_id,
                    'name': row[1],
                    'email': row[2],
                    'created_at': row[3].isoformat() if row[3] else None,
                    'status': row[4] or 'unknown',
                    'roles': [],
                    'organizations': []
                }
            
            # Add global role if present
            if row[5] and row[5] not in users_dict[user_id]['roles']:
                users_dict[user_id]['roles'].append(row[5])
            
            # Add organization info if present
            if row[6]:
                org_info = {
                    'code': row[6],
                    'name': row[7],
                    'role': row[8]
                }
                if org_info not in users_dict[user_id]['organizations']:
                    users_dict[user_id]['organizations'].append(org_info)
        
        users_list = list(users_dict.values())
        return render_response({"users": users_list}, meta={"total": len(users_list)})
        
    except Exception as e:
        g.logger.error(f"Error listing users: {str(e)}")
        raise APIError("Failed to retrieve users", status_code=500, error_id="HG-USER-LIST-ERROR")


@bp.route("/<user_id>", methods=["GET"])
@require_auth(optional=True)
def get_user(user_id: str) -> "Response":
    """Get a specific user by ID."""
    try:
        query = """
            SELECT 
                u.id,
                u.name,
                u.email,
                u.created_at,
                us.code as status,
                u.profile_photo_url
            FROM users u
            LEFT JOIN user_statuses us ON u.user_status_id = us.id
            WHERE u.id = :user_id
        """
        
        result = db.session.execute(db.text(query), {'user_id': user_id})
        row = result.fetchone()
        
        if not row:
            raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
        
        user = {
            'id': str(row[0]),
            'name': row[1],
            'email': row[2],
            'created_at': row[3].isoformat() if row[3] else None,
            'status': row[4] or 'unknown',
            'profile_photo_url': row[5]
        }
        
        return render_response({"user": user})
        
    except APIError:
        raise
    except Exception as e:
        g.logger.error(f"Error getting user {user_id}: {str(e)}")
        raise APIError("Failed to retrieve user", status_code=500, error_id="HG-USER-GET-ERROR")


@bp.route("/<user_id>", methods=["PATCH"])
@require_auth(required_roles=["admin", "clinician", "org_admin"])
def update_user(user_id: str) -> "Response":
    """Update user information."""
    payload, _ = parse_request_data(request)
    
    try:
        # Check if user exists
        check_query = "SELECT id FROM users WHERE id = :user_id"
        result = db.session.execute(db.text(check_query), {'user_id': user_id})
        if not result.fetchone():
            raise APIError("User not found", status_code=404, error_id="HG-USER-NOT-FOUND")
        
        # Build update query dynamically
        allowed = {"name", "profile_photo_url"}
        updates = []
        params = {'user_id': user_id}
        
        for key, value in payload.items():
            if key in allowed:
                updates.append(f"{key} = :{key}")
                params[key] = value
        
        if not updates:
            raise APIError("No valid fields to update", status_code=400, error_id="HG-USER-NO-UPDATES")
        
        update_query = f"UPDATE users SET {', '.join(updates)}, updated_at = NOW() WHERE id = :user_id"
        db.session.execute(db.text(update_query), params)
        db.session.commit()
        
        # Return updated user
        return get_user(user_id)
        
    except APIError:
        raise
    except Exception as e:
        db.session.rollback()
        g.logger.error(f"Error updating user {user_id}: {str(e)}")
        raise APIError("Failed to update user", status_code=500, error_id="HG-USER-UPDATE-ERROR")


@bp.route("/me", methods=["GET"])
@require_auth()
def get_me() -> "Response":
    """Get current authenticated user."""
    user_id = g.current_user.get("sub")
    return get_user(user_id)


@bp.route("/me", methods=["PATCH"])
@require_auth()
def update_me() -> "Response":
    """Update current authenticated user."""
    user_id = g.current_user.get("sub")
    return update_user(user_id)


@bp.route("/count", methods=["POST"])
@require_auth(optional=True)
def count_users() -> "Response":
    """Count users, optionally filtered by organization."""
    payload, _ = parse_request_data(request)
    org_code = payload.get("org_id") or payload.get("org_code")
    
    try:
        if org_code:
            query = """
                SELECT COUNT(DISTINCT u.id)
                FROM users u
                JOIN user_org_membership uom ON u.id = uom.user_id
                JOIN organizations org ON uom.org_id = org.id
                WHERE org.code = :org_code
            """
            result = db.session.execute(db.text(query), {'org_code': org_code})
        else:
            query = "SELECT COUNT(*) FROM users"
            result = db.session.execute(db.text(query))
        
        count = result.scalar()
        return render_response({"count": count})
        
    except Exception as e:
        g.logger.error(f"Error counting users: {str(e)}")
        raise APIError("Failed to count users", status_code=500, error_id="HG-USER-COUNT-ERROR")


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/users")
