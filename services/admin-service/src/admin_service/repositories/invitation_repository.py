"""Repository for organization invitations."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from ..extensions import db
from ..models.organization import OrgInvitation


class InvitationRepository:
    """Data access helpers for invitations."""

    @staticmethod
    def create(org_id: UUID, email: str, token: str) -> OrgInvitation:
        invitation = OrgInvitation(org_id=org_id, email=email, token=token)
        db.session.add(invitation)
        db.session.commit()
        return invitation

    @staticmethod
    def get_by_token(token: str) -> Optional[OrgInvitation]:
        return OrgInvitation.query.filter_by(token=token).first()


__all__ = ["InvitationRepository"]
