import os
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("audit_DATABASE_URL", "sqlite:///audit.db")
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(36), unique=True, nullable=False)
    service = Column(String(100), nullable=False)
    actor = Column(String(255))
    action = Column(String(100), nullable=False)
    resource = Column(String(255))
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    Base.metadata.create_all(bind=engine)
