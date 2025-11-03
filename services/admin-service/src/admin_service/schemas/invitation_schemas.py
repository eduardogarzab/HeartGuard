"""Invitation related schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class InvitationRequest(BaseModel):
    email: EmailStr


class InvitationResponse(BaseModel):
    token: str
    status: str


__all__ = ["InvitationRequest", "InvitationResponse"]
