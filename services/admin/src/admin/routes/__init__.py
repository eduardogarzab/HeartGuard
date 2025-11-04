"""Route registration for Admin Service."""
from __future__ import annotations

from flask import Flask

from .health import bp as health_bp
from .organizations import bp as organizations_bp
from .dashboard import bp as dashboard_bp
from .staff import bp as staff_bp
from .patients import bp as patients_bp
from .care_teams import bp as care_teams_bp
from .caregivers import bp as caregivers_bp
from .alerts import bp as alerts_bp
from .devices import bp as devices_bp
from .push_devices import bp as push_devices_bp
from .patient_locations import bp as patient_locations_bp
from .ground_truth import bp as ground_truth_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(organizations_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(care_teams_bp)
    app.register_blueprint(caregivers_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(push_devices_bp)
    app.register_blueprint(patient_locations_bp)
    app.register_blueprint(ground_truth_bp)
