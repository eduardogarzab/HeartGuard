"""User related schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str


class UserInvitationResponse(BaseModel):
    invitation_token: str


class AssignRoleRequest(BaseModel):
    role: str = Field(..., min_length=1)


class CareTeamAssignmentRequest(BaseModel):
    entity_id: UUID
    role: str | None = None


__all__ = [
    "UserResponse",
    "UserInvitationResponse",
    "AssignRoleRequest",
    "CareTeamAssignmentRequest",
]
