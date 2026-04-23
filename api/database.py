"""
database.py — Conexión a PostgreSQL con SQLAlchemy
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://DB-virtual-world-reading-ai:GodotWorldAdmin@db:5432/godot_readings"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency que provee una sesión de BD y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
