"""Patient related schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PatientCreateRequest(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    date_of_birth: date | None = None


class PatientUpdateRequest(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    date_of_birth: date | None = None


__all__ = ["PatientCreateRequest", "PatientUpdateRequest"]
