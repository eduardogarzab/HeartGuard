"""Modelos relacionados con usuarios staff."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class OrgMembership:
    org_id: str
    org_code: Optional[str]
    org_name: Optional[str]
    role_code: Optional[str]
    role_label: Optional[str]
    joined_at: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgMembership":
        return cls(
            org_id=data.get("org_id"),
            org_code=data.get("org_code"),
            org_name=data.get("org_name"),
            role_code=data.get("role_code"),
            role_label=data.get("role_label"),
            joined_at=data.get("joined_at"),
        )

    def display_name(self) -> str:
        if self.org_name:
            return self.org_name
        if self.org_code:
            return self.org_code
        return self.org_id

    def __str__(self) -> str:  # pragma: no cover - usado por Tkinter
        return self.display_name()


@dataclass
class UserProfileStatus:
    code: Optional[str] = None
    label: Optional[str] = None


@dataclass
class UserProfile:
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role_code: Optional[str] = None
    status: Optional[UserProfileStatus] = None
    two_factor_enabled: bool = False
    profile_photo_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        status_data = data.get("status") or {}
        status = None
        if status_data:
            status = UserProfileStatus(
                code=status_data.get("code"),
                label=status_data.get("label"),
            )
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            email=data.get("email"),
            role_code=data.get("role_code"),
            status=status,
            two_factor_enabled=bool(data.get("two_factor_enabled")),
            profile_photo_url=data.get("profile_photo_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


def parse_memberships(payload: Dict[str, Any]) -> List[OrgMembership]:
    data = payload.get("data") or {}
    memberships = []
    if isinstance(data, dict):
        raw_memberships = data.get("memberships") or []
    else:
        raw_memberships = data
    for item in raw_memberships:
        if isinstance(item, dict):
            memberships.append(OrgMembership.from_dict(item))
    return memberships


def parse_invitations(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = payload.get("data") or {}
    if isinstance(data, dict):
        invitations = data.get("invitations") or []
    else:
        invitations = []
    return [inv for inv in invitations if isinstance(inv, dict)]
