from __future__ import annotations

import datetime as dt

from common.database import db


class OrganizationProfile(db.Model):
    __tablename__ = "organization_profiles"

    id = db.Column(db.String, primary_key=True, default="default")
    name = db.Column(db.String, nullable=False)
    website = db.Column(db.String, nullable=True)
    policy_version = db.Column(db.String, nullable=True)
    support_email = db.Column(db.String, nullable=True)
    logo_url = db.Column(db.String, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)


class OrganizationInvitation(db.Model):
    __tablename__ = "organization_invitations"

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default="user")
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
