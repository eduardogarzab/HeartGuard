# signal_service/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List
import datetime

class TimeseriesDataItem(BaseModel):
    """
    Pydantic model for a single data point in the ingest payload.
    Ensures that 'ts' is a valid Unix timestamp and 'val' is a string.
    """
    ts: datetime.datetime = Field(..., alias='ts')
    val: str = Field(..., alias='val')
