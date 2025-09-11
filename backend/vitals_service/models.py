# heartguard-backend/vitals_service/models.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Numeric, TIMESTAMP, ForeignKey, func

Base = declarative_base()

class Vital(Base):
    __tablename__ = "vitals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    hr = Column(Integer)
    spo2 = Column(Integer)
    sbp = Column(Integer)
    dbp = Column(Integer)
    temp_c = Column(Numeric(4, 1))
    measured_at = Column(TIMESTAMP, server_default=func.now())
