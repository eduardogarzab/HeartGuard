from __future__ import annotations

import datetime as dt
from typing import List

from werkzeug.security import check_password_hash, generate_password_hash

from common.database import db


class User(db.Model):
    __tablename__ = "auth_users"

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    roles = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    refresh_tokens = db.relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class RefreshToken(db.Model):
    __tablename__ = "auth_refresh_tokens"

    token = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("auth_users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="refresh_tokens")


def create_default_admin(default_email: str, default_password: str, roles: List[str] | None = None) -> None:
    roles = roles or ["admin"]
    existing = User.query.filter_by(email=default_email).first()
    if existing:
        return
    user = User(id="usr-admin", email=default_email, roles=roles)
    user.set_password(default_password)
    db.session.add(user)
    db.session.commit()
