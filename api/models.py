"""
models.py — Modelos SQLAlchemy para la base de datos de lecturas
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.sql import func

from database import Base


class Reading(Base):
    """Modelo ORM para la tabla 'readings'."""
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    typology = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserReading(Base):
    """
    Modelo ORM para la tabla 'user_readings'.
    Registra lecturas vistas por cada usuario (para no-repetición futura).
    """
    __tablename__ = "user_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    reading_id = Column(Integer, ForeignKey("readings.id", ondelete="CASCADE"), nullable=False)
    read_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "reading_id", name="uq_user_reading"),
    )
