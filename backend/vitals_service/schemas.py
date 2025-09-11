# heartguard-backend/vitals_service/schemas.py
from pydantic import BaseModel
from datetime import datetime

class VitalOut(BaseModel):
    id: int
    hr: int | None
    spo2: int | None
    sbp: int | None
    dbp: int | None
    temp_c: float | None
    measured_at: datetime

class VitalIn(BaseModel):
    hr: int | None = None
    spo2: int | None = None
    sbp: int | None = None
    dbp: int | None = None
    temp_c: float | None = None
