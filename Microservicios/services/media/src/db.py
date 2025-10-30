import os
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("media_DATABASE_URL", "sqlite:///media.db")
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class MediaItem(Base):
    __tablename__ = "media_items"

    id = Column(String(36), primary_key=True)
    file_name = Column(String(255), nullable=False)
    content_type = Column(String(128))
    size_bytes = Column(Integer)
    gcs_path = Column(String(512), nullable=False)
    owner_id = Column(String(36), nullable=False)
    organization_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_metadata = Column(Text)


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
