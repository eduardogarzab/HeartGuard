"""Patient profile endpoints providing aggregated information."""
from __future__ import annotations

from flask import Blueprint

from ..auth import require_org_admin
from ..repositories.alerts import AlertsRepository
from ..repositories.care_teams import CareTeamsRepository
from ..repositories.caregivers import CaregiversRepository
from ..repositories.devices import DevicesRepository
from ..repositories.ground_truth import GroundTruthRepository
from ..repositories.patient_locations import PatientLocationsRepository
from ..repositories.patients import PatientsRepository
from ..xml import xml_error_response, xml_response

bp = Blueprint(
    "patient_profile",
    __name__,
    url_prefix="/admin/organizations/<org_id>/patients/<patient_id>",
)

_patients_repo = PatientsRepository()
_caregivers_repo = CaregiversRepository()
_care_teams_repo = CareTeamsRepository()
_devices_repo = DevicesRepository()
_ground_truth_repo = GroundTruthRepository()
_locations_repo = PatientLocationsRepository()
_alerts_repo = AlertsRepository()


def _validate_patient(org_id: str, patient_id: str):
    patient = _patients_repo.get_patient(patient_id)
    if not patient:
        return None, xml_error_response("not_found", "Patient not found", status=404)
    if str(patient.get("org_id")) != org_id:
        return None, xml_error_response("forbidden", "Patient does not belong to this organization", status=403)
    return patient, None


@bp.get("/profile")
@require_org_admin
def patient_profile(org_id: str, patient_id: str):
    patient, error = _validate_patient(org_id, patient_id)
    if error:
        return error

    caregivers = _caregivers_repo.list_assignments_for_patient(org_id, patient_id)
    care_teams = _care_teams_repo.list_for_patient(org_id, patient_id)
    devices = _devices_repo.list_for_patient(org_id, patient_id)
    ground_truth = _ground_truth_repo.list_for_patient(patient_id, limit=20)
    locations = _locations_repo.list_for_patient(patient_id, limit=20)
    alerts = _alerts_repo.list_alerts(org_id, patient_id=patient_id, limit=20)

    latest_location = locations[0] if locations else None
    history_locations = locations[1:] if len(locations) > 1 else []

    payload = {
        "patient_profile": {
            "patient": patient,
            "caregivers": caregivers,
            "care_teams": care_teams,
            "devices": devices,
            "ground_truth_labels": ground_truth,
            "alerts": alerts,
            "locations": {
                "latest": latest_location,
                "recent": history_locations,
            },
        }
    }
    return xml_response(payload)
