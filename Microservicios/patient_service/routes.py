"""models.Patient service managing clinical subject data."""
from __future__ import annotations

import uuid

from flask import Blueprint, request

from common.auth import require_auth
from common.database import db
from common.errors import APIError
from common.serialization import parse_request_data, render_response
import models
# Models accessed via models. models.Patient

bp = Blueprint("patients", __name__)


@bp.route("/health", methods=["GET"])
def health() -> "Response":
    return render_response({"service": "patient", "status": "healthy"})


def get_user_roles_from_jwt():
    """Extract user_id and roles from JWT in request context."""
    from flask import g
    user_id = getattr(g, 'user_id', None)
    roles = getattr(g, 'roles', [])
    return user_id, roles


def get_user_organizations(user_id):
    """Get all organization IDs where user is a member."""
    memberships = models.UserOrgMembership.query.filter_by(
        user_id=user_id
    ).filter(
        models.UserOrgMembership.left_at.is_(None)
    ).all()
    return [str(m.org_id) for m in memberships]


def get_assigned_patient_ids(user_id):
    """Get patient IDs assigned to a caregiver."""
    assignments = models.CaregiverPatient.query.filter_by(
        user_id=user_id
    ).filter(
        models.CaregiverPatient.ended_at.is_(None)
    ).all()
    return [str(a.patient_id) for a in assignments]


@bp.route("", methods=["GET"])
@require_auth(optional=True)
def list_patients() -> "Response":
    """
    List patients based on user role:
    - superadmin: all patients
    - admin/clinician: patients in their organization(s)
    - caregiver: only their assigned patients
    """
    user_id, roles = get_user_roles_from_jwt()
    
    # Log para debug
    print(f"[PATIENT LIST] user_id={user_id}, roles={roles}")
    
    query = models.Patient.query
    
    # Si no hay autenticación, devolver todos (para testing)
    if not user_id:
        print("[PATIENT LIST] No user_id - returning all patients")
        patients = [p.to_dict() for p in query.all()]
        return render_response({"patients": patients}, meta={"total": len(patients)})
    
    # SUPERADMIN: ver todos
    if 'superadmin' in roles:
        print("[PATIENT LIST] User is SUPERADMIN - returning all patients")
        patients = [p.to_dict() for p in query.all()]
        return render_response({"patients": patients}, meta={"total": len(patients)})
    
    # ADMIN/CLINICIAN: ver pacientes de su(s) organización(es)
    if 'admin' in roles or 'clinician' in roles:
        org_ids = get_user_organizations(user_id)
        print(f"[PATIENT LIST] User is ADMIN/CLINICIAN - org_ids={org_ids}")
        if org_ids:
            # Convertir strings a UUID objects
            org_uuid_list = [uuid.UUID(oid) for oid in org_ids]
            query = query.filter(models.Patient.org_id.in_(org_uuid_list))
        else:
            # No pertenece a ninguna org - sin pacientes
            print("[PATIENT LIST] User has no organization memberships")
            return render_response({"patients": []}, meta={"total": 0})
    
    # CAREGIVER: solo pacientes asignados
    elif 'caregiver' in roles:
        patient_ids = get_assigned_patient_ids(user_id)
        print(f"[PATIENT LIST] User is CAREGIVER - patient_ids={patient_ids}")
        if patient_ids:
            # Convertir strings a UUID objects
            patient_uuid_list = [uuid.UUID(pid) for pid in patient_ids]
            query = query.filter(models.Patient.id.in_(patient_uuid_list))
        else:
            # No tiene pacientes asignados
            print("[PATIENT LIST] Caregiver has no assigned patients")
            return render_response({"patients": []}, meta={"total": 0})
    
    # Otros roles: sin acceso a pacientes
    else:
        print(f"[PATIENT LIST] User has no patient access role: {roles}")
        return render_response({"patients": []}, meta={"total": 0})
    
    patients = [p.to_dict() for p in query.all()]
    print(f"[PATIENT LIST] Returning {len(patients)} patients")
    return render_response({"patients": patients}, meta={"total": len(patients)})


@bp.route("", methods=["POST"])
@require_auth(required_roles=["clinician", "admin"])
def create_patient() -> "Response":
    payload, _ = parse_request_data(request)
    person_name = payload.get("person_name")
    if not person_name:
        raise APIError("person_name is required", status_code=400, error_id="HG-PATIENT-VALIDATION")

    new_patient = models.Patient(person_name=person_name, org_id=payload.get("org_id"))

    db.session.add(new_patient)
    db.session.commit()

    return render_response({"patient": new_patient.to_dict()}, status_code=201)


@bp.route("/<patient_id>", methods=["GET"])
@require_auth(optional=True)
def get_patient(patient_id: str) -> "Response":
    patient = models.Patient.query.get(patient_id)
    if not patient:
        raise APIError("models.Patient not found", status_code=404, error_id="HG-PATIENT-NOT-FOUND")
    return render_response({"patient": patient.to_dict()})


@bp.route("/<patient_id>/care-team", methods=["GET"])
@require_auth(optional=True)
def get_care_team(patient_id: str) -> "Response":
    # This route is not yet migrated to the database.
    team = []
    caregivers = []
    return render_response({"care_teams": team, "caregivers": caregivers})


def register_blueprint(app):
    app.register_blueprint(bp, url_prefix="/patients")
