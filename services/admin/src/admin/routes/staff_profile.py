"""Staff profile endpoints providing aggregated context."""
from __future__ import annotations

from flask import Blueprint

from ..auth import require_org_admin
from ..repositories.care_teams import CareTeamsRepository
from ..repositories.caregivers import CaregiversRepository
from ..repositories.ground_truth import GroundTruthRepository
from ..repositories.push_devices import PushDevicesRepository
from ..repositories.staff import StaffRepository
from ..xml import xml_error_response, xml_response

bp = Blueprint(
    "staff_profile",
    __name__,
    url_prefix="/admin/organizations/<org_id>/staff/<user_id>",
)

_staff_repo = StaffRepository()
_care_teams_repo = CareTeamsRepository()
_caregivers_repo = CaregiversRepository()
_ground_truth_repo = GroundTruthRepository()
_push_devices_repo = PushDevicesRepository()


@bp.get("/profile")
@require_org_admin
def staff_profile(org_id: str, user_id: str):
    member = _staff_repo.get_member(org_id, user_id)
    if not member:
        return xml_error_response("not_found", "Staff member not found", status=404)

    care_teams = _care_teams_repo.list_for_member(org_id, user_id)
    caregiver_assignments = _caregivers_repo.list_assignments_for_caregiver(org_id, user_id)
    annotations = _ground_truth_repo.list_for_annotator(user_id, limit=20)
    push_devices = _push_devices_repo.list_for_user(org_id, user_id)

    payload = {
        "staff_profile": {
            "member": member,
            "care_teams": care_teams,
            "caregiver_assignments": caregiver_assignments,
            "ground_truth_annotations": annotations,
            "push_devices": push_devices,
        }
    }
    return xml_response(payload)
