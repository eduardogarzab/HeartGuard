# heartguard-backend/auth_service/models.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Text, TIMESTAMP, func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
