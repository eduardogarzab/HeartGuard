"""Modelos SQLAlchemy del servicio de analytics."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, Enum, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ServiceHealth(Base):
    """Representa el estado de salud reportado por un microservicio."""

    __tablename__ = "service_health"

    service_name = Column(String(100), primary_key=True)
    status = Column(Enum("ok", "degraded", "error", name="service_health_status"), nullable=False)
    last_heartbeat = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    details = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "details": self.details or {},
            "notes": self.notes,
        }


# Documentación sobre integración con bases externas.
EXTERNAL_SOURCES_DOC = """
Los motores ``audit_db_engine`` y ``org_db_engine`` definidos en ``config.py``
permiten consultar bases de datos externas para generar reportes enriquecidos.
Este módulo no establece relaciones directas entre ``ServiceHealth`` y dichas
bases, pero los repositorios pueden utilizarlas para complementar los datos de
salud con métricas auditadas o información de organizaciones.
"""


__all__ = ["Base", "ServiceHealth", "EXTERNAL_SOURCES_DOC"]
