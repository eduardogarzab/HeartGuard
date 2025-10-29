# signal_service/app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Importar y cargar la configuración primero
from . import config

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set for SQLAlchemy")

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Crear una fábrica de sesiones configurada
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear una sesión "scoped" para asegurar que cada hilo/request tenga su propia sesión
SessionLocal = scoped_session(session_factory)
