"""Domain models for the Tkinter HeartGuard client."""

from .auth import LoginResponse, UserLoginData, PatientLoginData

__all__ = [
    "LoginResponse",
    "UserLoginData",
    "PatientLoginData",
]
