from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from werkzeug.security import check_password_hash, generate_password_hash

from .database import db


class UserStatus(db.Model):
    __tablename__ = "user_statuses"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(Text)
    created_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    users = db.relationship("User", secondary="user_role", back_populates="roles")


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(Text)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(Text, nullable=False)
    user_status_id = db.Column(db.String, ForeignKey("user_statuses.id"), nullable=False)
    two_factor_enabled = db.Column(Boolean, nullable=False, default=False)
    profile_photo_url = db.Column(Text)
    created_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    status = db.relationship("UserStatus")
    roles = db.relationship("Role", secondary="user_role", back_populates="users")
    refresh_tokens = db.relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class UserRole(db.Model):
    __tablename__ = "user_role"

    user_id = db.Column(db.String, ForeignKey("users.id"), primary_key=True)
    role_id = db.Column(db.String, ForeignKey("roles.id"), primary_key=True)
    assigned_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, ForeignKey("users.id"), nullable=False)
    token_hash = db.Column(Text, nullable=False)
    issued_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    expires_at = db.Column(DateTime, nullable=False)
    revoked_at = db.Column(DateTime)
    client_id = db.Column(db.String(120))
    device_fingerprint = db.Column(db.String(200))
    ip_issued = db.Column(db.String(64))

    user = db.relationship("User", back_populates="refresh_tokens")


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(60), unique=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)


class OrgRole(db.Model):
    __tablename__ = "org_roles"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class OrgInvitation(db.Model):
    __tablename__ = "org_invitations"

    id = db.Column(db.String, primary_key=True)
    org_id = db.Column(db.String, ForeignKey("organizations.id"), nullable=False)
    email = db.Column(db.String(150))
    org_role_id = db.Column(db.String, ForeignKey("org_roles.id"), nullable=False)
    token = db.Column(db.String(120), unique=True, nullable=False)
    expires_at = db.Column(DateTime, nullable=False)
    used_at = db.Column(DateTime)
    revoked_at = db.Column(DateTime)
    created_by = db.Column(db.String, ForeignKey("users.id"))
    created_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    organization = db.relationship("Organization")
    role = db.relationship("OrgRole")


class UserOrgMembership(db.Model):
    __tablename__ = "user_org_membership"

    org_id = db.Column(db.String, ForeignKey("organizations.id"), primary_key=True)
    user_id = db.Column(db.String, ForeignKey("users.id"), primary_key=True)
    org_role_id = db.Column(db.String, ForeignKey("org_roles.id"), nullable=False)
    joined_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    organization = db.relationship("Organization")
    role = db.relationship("OrgRole")
    user = db.relationship("User")


class RiskLevel(db.Model):
    __tablename__ = "risk_levels"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    label = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Integer)


class Sex(db.Model):
    __tablename__ = "sexes"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)
    label = db.Column(db.String(40), nullable=False)


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.String, primary_key=True)
    org_id = db.Column(db.String, ForeignKey("organizations.id"))
    person_name = db.Column(db.String(120), nullable=False)
    birthdate = db.Column(Date)
    sex_id = db.Column(db.String, ForeignKey("sexes.id"))
    risk_level_id = db.Column(db.String, ForeignKey("risk_levels.id"))
    profile_photo_url = db.Column(Text)
    created_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    organization = db.relationship("Organization")
    sex = db.relationship("Sex")
    risk_level = db.relationship("RiskLevel")
    care_teams = db.relationship("CareTeam", secondary="patient_care_team", back_populates="patients")
    caregivers = db.relationship("CaregiverPatient", back_populates="patient", cascade="all, delete-orphan")


class CareTeam(db.Model):
    __tablename__ = "care_teams"

    id = db.Column(db.String, primary_key=True)
    org_id = db.Column(db.String, ForeignKey("organizations.id"))
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    patients = db.relationship("Patient", secondary="patient_care_team", back_populates="care_teams")
    members = db.relationship("CareTeamMember", back_populates="team", cascade="all, delete-orphan")


class CareTeamMember(db.Model):
    __tablename__ = "care_team_member"

    care_team_id = db.Column(db.String, ForeignKey("care_teams.id"), primary_key=True)
    user_id = db.Column(db.String, ForeignKey("users.id"), primary_key=True)
    role_id = db.Column(db.String, ForeignKey("team_member_roles.id"), nullable=False)
    joined_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    team = db.relationship("CareTeam", back_populates="members")


class PatientCareTeam(db.Model):
    __tablename__ = "patient_care_team"

    patient_id = db.Column(db.String, ForeignKey("patients.id"), primary_key=True)
    care_team_id = db.Column(db.String, ForeignKey("care_teams.id"), primary_key=True)


class CaregiverRelationshipType(db.Model):
    __tablename__ = "caregiver_relationship_types"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class CaregiverPatient(db.Model):
    __tablename__ = "caregiver_patient"

    patient_id = db.Column(db.String, ForeignKey("patients.id"), primary_key=True)
    user_id = db.Column(db.String, ForeignKey("users.id"), primary_key=True)
    rel_type_id = db.Column(db.String, ForeignKey("caregiver_relationship_types.id"))
    is_primary = db.Column(Boolean, nullable=False, default=False)
    started_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    ended_at = db.Column(DateTime)
    note = db.Column(Text)

    patient = db.relationship("Patient", back_populates="caregivers")


class DeviceType(db.Model):
    __tablename__ = "device_types"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(120), nullable=False)


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.String, primary_key=True)
    org_id = db.Column(db.String, ForeignKey("organizations.id"))
    serial = db.Column(db.String(80), unique=True, nullable=False)
    brand = db.Column(db.String(80))
    model = db.Column(db.String(80))
    device_type_id = db.Column(db.String, ForeignKey("device_types.id"), nullable=False)
    owner_patient_id = db.Column(db.String, ForeignKey("patients.id"))
    registered_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    active = db.Column(Boolean, nullable=False, default=True)

    device_type = db.relationship("DeviceType")
    owner = db.relationship("Patient")
    streams = db.relationship("SignalStream", back_populates="device", cascade="all, delete-orphan")


class SignalType(db.Model):
    __tablename__ = "signal_types"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class SignalStream(db.Model):
    __tablename__ = "signal_streams"

    id = db.Column(db.String, primary_key=True)
    patient_id = db.Column(db.String, ForeignKey("patients.id"), nullable=False)
    device_id = db.Column(db.String, ForeignKey("devices.id"), nullable=False)
    signal_type_id = db.Column(db.String, ForeignKey("signal_types.id"), nullable=False)
    sample_rate_hz = db.Column(Numeric(10, 3))
    started_at = db.Column(DateTime, nullable=False)
    ended_at = db.Column(DateTime)

    patient = db.relationship("Patient")
    device = db.relationship("Device", back_populates="streams")
    signal_type = db.relationship("SignalType")
    bindings = db.relationship("TimeseriesBinding", back_populates="stream", cascade="all, delete-orphan")


class TimeseriesBinding(db.Model):
    __tablename__ = "timeseries_binding"

    id = db.Column(db.String, primary_key=True)
    stream_id = db.Column(db.String, ForeignKey("signal_streams.id"), nullable=False)
    influx_org = db.Column(db.String(120))
    influx_bucket = db.Column(db.String(120), nullable=False)
    measurement = db.Column(db.String(120), nullable=False)
    retention_hint = db.Column(db.String(60))
    created_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)

    stream = db.relationship("SignalStream", back_populates="bindings")
    tags = db.relationship("TimeseriesBindingTag", back_populates="binding", cascade="all, delete-orphan")


class TimeseriesBindingTag(db.Model):
    __tablename__ = "timeseries_binding_tag"

    id = db.Column(db.String, primary_key=True)
    binding_id = db.Column(db.String, ForeignKey("timeseries_binding.id"), nullable=False)
    tag_key = db.Column(db.String(120), nullable=False)
    tag_value = db.Column(db.String(240), nullable=False)

    binding = db.relationship("TimeseriesBinding", back_populates="tags")


class AlertLevel(db.Model):
    __tablename__ = "alert_levels"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class AlertStatus(db.Model):
    __tablename__ = "alert_status"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(Text)
    step_order = db.Column(db.Integer, nullable=False)


class AlertType(db.Model):
    __tablename__ = "alert_types"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    description = db.Column(Text)
    severity_min_id = db.Column(db.String, ForeignKey("alert_levels.id"), nullable=False)
    severity_max_id = db.Column(db.String, ForeignKey("alert_levels.id"), nullable=False)


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.String, primary_key=True)
    patient_id = db.Column(db.String, ForeignKey("patients.id"), nullable=False)
    type_id = db.Column(db.String, ForeignKey("alert_types.id"), nullable=False)
    created_by_model_id = db.Column(db.String, ForeignKey("models.id"))
    source_inference_id = db.Column(db.String, ForeignKey("inferences.id"))
    alert_level_id = db.Column(db.String, ForeignKey("alert_levels.id"), nullable=False)
    status_id = db.Column(db.String, ForeignKey("alert_status.id"), nullable=False)
    created_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    description = db.Column(Text)
    location = db.Column(Text)
    duplicate_of_alert_id = db.Column(db.String, ForeignKey("alerts.id"))

    patient = db.relationship("Patient")
    alert_type = db.relationship("AlertType")
    level = db.relationship("AlertLevel")
    status = db.relationship("AlertStatus")
    assignments = db.relationship("AlertAssignment", back_populates="alert", cascade="all, delete-orphan")
    acknowledgements = db.relationship("AlertAck", back_populates="alert", cascade="all, delete-orphan")
    resolutions = db.relationship("AlertResolution", back_populates="alert", cascade="all, delete-orphan")
    deliveries = db.relationship("AlertDelivery", back_populates="alert", cascade="all, delete-orphan")


class AlertAssignment(db.Model):
    __tablename__ = "alert_assignment"

    alert_id = db.Column(db.String, ForeignKey("alerts.id"), primary_key=True)
    assignee_user_id = db.Column(db.String, ForeignKey("users.id"), primary_key=True)
    assigned_by_user_id = db.Column(db.String, ForeignKey("users.id"), nullable=True)
    assigned_at = db.Column(DateTime, primary_key=True, default=dt.datetime.utcnow)

    alert = db.relationship("Alert", back_populates="assignments")


class AlertAck(db.Model):
    __tablename__ = "alert_ack"

    id = db.Column(db.String, primary_key=True)
    alert_id = db.Column(db.String, ForeignKey("alerts.id"), nullable=False)
    ack_by_user_id = db.Column(db.String, ForeignKey("users.id"))
    ack_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    note = db.Column(Text)

    alert = db.relationship("Alert", back_populates="acknowledgements")


class AlertResolution(db.Model):
    __tablename__ = "alert_resolution"

    id = db.Column(db.String, primary_key=True)
    alert_id = db.Column(db.String, ForeignKey("alerts.id"), nullable=False)
    resolved_by_user_id = db.Column(db.String, ForeignKey("users.id"))
    resolved_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    outcome = db.Column(db.String(80))
    note = db.Column(Text)

    alert = db.relationship("Alert", back_populates="resolutions")


class AlertDelivery(db.Model):
    __tablename__ = "alert_delivery"

    id = db.Column(db.String, primary_key=True)
    alert_id = db.Column(db.String, ForeignKey("alerts.id"), nullable=False)
    channel_id = db.Column(db.String, ForeignKey("alert_channels.id"), nullable=False)
    target = db.Column(db.String(160), nullable=False)
    sent_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    delivery_status_id = db.Column(db.String, ForeignKey("delivery_statuses.id"), nullable=False)
    response_payload = db.Column(JSONB)

    alert = db.relationship("Alert", back_populates="deliveries")


class Platform(db.Model):
    __tablename__ = "platforms"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class PushDevice(db.Model):
    __tablename__ = "push_devices"

    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, ForeignKey("users.id"), nullable=False)
    platform_id = db.Column(db.String, ForeignKey("platforms.id"), nullable=False)
    push_token = db.Column(Text, nullable=False)
    last_seen_at = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    active = db.Column(Boolean, nullable=False, default=True)

    platform = db.relationship("Platform")


class DeliveryStatus(db.Model):
    __tablename__ = "delivery_statuses"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class AlertChannel(db.Model):
    __tablename__ = "alert_channels"

    id = db.Column(db.String, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, ForeignKey("users.id"))
    action = db.Column(db.String(80), nullable=False)
    entity = db.Column(db.String(80))
    entity_id = db.Column(db.String)
    ts = db.Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    ip = db.Column(db.String(64))
    details = db.Column(JSONB)

    user = db.relationship("User")
