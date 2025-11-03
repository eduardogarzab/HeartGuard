"""Repository for user and membership persistence."""

from __future__ import annotations

from typing import Iterable, Optional
from uuid import UUID

from ..extensions import db
from ..models.organization import UserOrgMembership
from ..models.user import User


class UserRepository:
    """User related data access helpers."""

    @staticmethod
    def list_by_org(org_id: UUID) -> Iterable[tuple[User, UserOrgMembership]]:
        return (
            db.session.query(User, UserOrgMembership)
            .join(UserOrgMembership, User.id == UserOrgMembership.user_id)
            .filter(UserOrgMembership.org_id == org_id)
            .all()
        )

    @staticmethod
    def get_membership(org_id: UUID, user_id: UUID) -> Optional[UserOrgMembership]:
        return UserOrgMembership.query.filter_by(org_id=org_id, user_id=user_id).first()

    @staticmethod
    def update_role(membership: UserOrgMembership, role: str) -> UserOrgMembership:
        membership.role = role
        db.session.commit()
        return membership

    @staticmethod
    def remove_membership(membership: UserOrgMembership) -> None:
        db.session.delete(membership)
        db.session.commit()


__all__ = ["UserRepository"]
