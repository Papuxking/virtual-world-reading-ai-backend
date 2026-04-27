"""
models.py — Modelos SQLAlchemy para la base de datos de lecturas
"""
from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, DateTime,
    UniqueConstraint, ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Reading(Base):
    """Modelo ORM para la tabla 'readings'."""
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    typology = Column(String(50), nullable=False)
    type = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relación 1:N con preguntas
    questions = relationship(
        "Question",
        back_populates="reading",
        cascade="all, delete-orphan",
        order_by="Question.question_number",
    )


class Question(Base):
    """Modelo ORM para la tabla 'questions'."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    reading_id = Column(Integer, ForeignKey("readings.id", ondelete="CASCADE"), nullable=False)
    question_number = Column(SmallInteger, nullable=False)
    comprehension_level = Column(String(20), nullable=False)
    question_text = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)
    justification = Column(Text)

    # Relaciones
    reading = relationship("Reading", back_populates="questions")
    answers = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Answer.letter",
    )


class Answer(Base):
    """Modelo ORM para la tabla 'answers'."""
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    letter = Column(String(1), nullable=False)
    answer_text = Column(Text, nullable=False)

    # Relación
    question = relationship("Question", back_populates="answers")

    __table_args__ = (
        UniqueConstraint("question_id", "letter", name="uq_question_letter"),
    )


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
