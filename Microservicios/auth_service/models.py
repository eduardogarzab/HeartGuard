from __future__ import annotations

import datetime as dt
import uuid
from typing import Iterable, List

from werkzeug.security import check_password_hash, generate_password_hash

from common.database import db
from common.models import Permission, RefreshToken, Role, User, UserRole, UserStatus


def ensure_roles(role_names: Iterable[str]) -> List[Role]:
    roles = Role.query.filter(Role.name.in_(list(role_names))).all()
    missing = {name for name in role_names} - {role.name for role in roles}
    if missing:
        raise ValueError(f"Roles no encontrados: {', '.join(sorted(missing))}")
    return roles


def resolve_user_status(code: str = "active") -> UserStatus:
    status = UserStatus.query.filter_by(code=code).first()
    if not status:
        raise ValueError(f"User status '{code}' no existe en la base de datos")
    return status


def create_default_admin(default_email: str, default_password: str, roles: List[str] | None = None) -> None:
    roles = roles or ["superadmin"]
    existing = User.query.filter_by(email=default_email).first()
    if existing:
        return

    status = resolve_user_status("active")
    db_roles = ensure_roles(roles)

    user = User(
        id=str(uuid.uuid4()),
        name="System Admin",
        email=default_email,
        user_status_id=status.id,
        two_factor_enabled=False,
    )
    user.set_password(default_password)
    db.session.add(user)
    db.session.flush()

    for role in db_roles:
        db.session.add(UserRole(user_id=user.id, role_id=role.id, assigned_at=dt.datetime.utcnow()))

    db.session.commit()


def hash_refresh_token(raw_token: str) -> str:
    return generate_password_hash(raw_token)


def refresh_token_matches(stored_hash: str, candidate: str) -> bool:
    return check_password_hash(stored_hash, candidate)


__all__ = [
    "Permission",
    "RefreshToken",
    "Role",
    "User",
    "UserRole",
    "UserStatus",
    "create_default_admin",
    "ensure_roles",
    "hash_refresh_token",
    "refresh_token_matches",
    "resolve_user_status",
]
