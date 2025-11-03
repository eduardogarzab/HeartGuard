"""Repository for care team operations."""

from __future__ import annotations

from typing import Iterable
from uuid import UUID

from ..extensions import db
from ..models.care_team import CareTeam, CareTeamMember, PatientCareTeam


class CareTeamRepository:
    """Data access helpers for care teams."""

    @staticmethod
    def create_team(org_id: UUID, name: str) -> CareTeam:
        team = CareTeam(org_id=org_id, name=name)
        db.session.add(team)
        db.session.commit()
        return team

    @staticmethod
    def assign_patient(team_id: UUID, patient_id: UUID) -> PatientCareTeam:
        assignment = PatientCareTeam(care_team_id=team_id, patient_id=patient_id)
        db.session.add(assignment)
        db.session.commit()
        return assignment

    @staticmethod
    def assign_user(team_id: UUID, user_id: UUID, role: str) -> CareTeamMember:
        member = CareTeamMember(care_team_id=team_id, user_id=user_id, role=role)
        db.session.add(member)
        db.session.commit()
        return member

    @staticmethod
    def list_team_members(team_id: UUID) -> Iterable[CareTeamMember]:
        return CareTeamMember.query.filter_by(care_team_id=team_id).all()


__all__ = ["CareTeamRepository"]
