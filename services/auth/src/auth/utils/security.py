"""Funciones de seguridad y hashing."""
from __future__ import annotations

import bcrypt


def hash_password(password: str, rounds: int = 12) -> str:
    salt = bcrypt.gensalt(rounds)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Hash inválido o corrupto.
        return False


def normalize_email(email: str) -> str:
    return email.strip().lower()
