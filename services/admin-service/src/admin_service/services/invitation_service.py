"""Business logic for admin service operations."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable
from uuid import UUID

from flask import g

from ..repositories.care_team_repository import CareTeamRepository
from ..repositories.invitation_repository import InvitationRepository
from ..repositories.patient_repository import PatientRepository
from ..repositories.user_repository import UserRepository


class InvitationService:
    """Service layer orchestrating repository calls."""

    def __init__(
        self,
        invitation_repo: InvitationRepository | None = None,
        user_repo: UserRepository | None = None,
        patient_repo: PatientRepository | None = None,
        care_team_repo: CareTeamRepository | None = None,
    ) -> None:
        self.invitation_repo = invitation_repo or InvitationRepository()
        self.user_repo = user_repo or UserRepository()
        self.patient_repo = patient_repo or PatientRepository()
        self.care_team_repo = care_team_repo or CareTeamRepository()

    def create_invitation(self, org_id: UUID, request) -> Dict[str, Any]:
        token = uuid.uuid4().hex
        invitation = self.invitation_repo.create(org_id=org_id, email=request.email, token=token)
        return {"token": invitation.token, "status": invitation.status}

    def list_org_users(self, org_id: UUID) -> Iterable[Dict[str, Any]]:
        records = self.user_repo.list_by_org(org_id)
        users = []
        for user, membership in records:
            users.append(
                {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": membership.role,
                }
            )
        return users

    def update_user_role(self, org_id: UUID, user_id: UUID, request) -> None:
        membership = self.user_repo.get_membership(org_id=org_id, user_id=user_id)
        if not membership:
            raise ValueError("Membership not found")
        self.user_repo.update_role(membership, role=request.role)

    def remove_user(self, org_id: UUID, user_id: UUID) -> None:
        membership = self.user_repo.get_membership(org_id=org_id, user_id=user_id)
        if membership:
            self.user_repo.remove_membership(membership)

    def list_patients(self, org_id: UUID) -> Iterable[Dict[str, Any]]:
        patients = self.patient_repo.list_by_org(org_id)
        return [self._serialize_patient(patient) for patient in patients]

    def create_patient(self, org_id: UUID, request) -> Dict[str, Any]:
        patient = self.patient_repo.create(
            org_id=org_id,
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=request.date_of_birth,
        )
        return self._serialize_patient(patient)

    def get_patient(self, patient_id: UUID) -> Dict[str, Any]:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise ValueError("Patient not found")
        self._assert_membership(patient.org_id)
        return self._serialize_patient(patient)

    def update_patient(self, patient_id: UUID, request) -> Dict[str, Any]:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise ValueError("Patient not found")
        self._assert_membership(patient.org_id)
        updated = self.patient_repo.update(
            patient,
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=request.date_of_birth,
        )
        return self._serialize_patient(updated)

    def create_care_team(self, org_id: UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        name = payload.get("name", "Care Team")
        team = self.care_team_repo.create_team(org_id=org_id, name=name)
        return {"id": str(team.id), "name": team.name, "org_id": str(team.org_id)}

    def assign_patient_to_team(self, team_id: UUID, request) -> Dict[str, Any]:
        assignment = self.care_team_repo.assign_patient(team_id=team_id, patient_id=request.entity_id)
        return {"id": str(assignment.id), "team_id": str(assignment.care_team_id), "patient_id": str(assignment.patient_id)}

    def assign_user_to_team(self, team_id: UUID, request) -> Dict[str, Any]:
        member = self.care_team_repo.assign_user(team_id=team_id, user_id=request.entity_id, role=request.role)
        return {"id": str(member.id), "team_id": str(member.care_team_id), "user_id": str(member.user_id), "role": member.role}

    def get_org_stats(self, org_id: UUID) -> Dict[str, Any]:
        patients = list(self.patient_repo.list_by_org(org_id))
        members = list(self.user_repo.list_by_org(org_id))
        return {"patients": len(patients), "members": len(members)}

    def get_org_alerts(self, org_id: UUID) -> Iterable[Dict[str, Any]]:
        return []

    def _serialize_patient(self, patient) -> Dict[str, Any]:
        return {
            "id": str(patient.id),
            "org_id": str(patient.org_id),
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        }

    def _assert_membership(self, org_id: UUID) -> None:
        memberships = getattr(g, "org_memberships", [])
        for membership in memberships:
            if str(membership.get("org_id")) == str(org_id):
                return
        raise ValueError("User lacks access to patient organization")


__all__ = ["InvitationService"]
