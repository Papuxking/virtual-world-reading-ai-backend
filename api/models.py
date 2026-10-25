"""
models.py — Modelos SQLAlchemy para la base de datos de lecturas
Incluye modelos de lecturas, preguntas, respuestas, usuarios y progreso.
"""
from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, DateTime, Boolean,
    UniqueConstraint, ForeignKey, Index, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# ── Modelos de Lecturas (existentes) ─────────────────────────────────────────

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
    external_id = Column(Integer, nullable=True, index=True)

    # Relación 1:N con preguntas
    questions = relationship(
        "Question",
        back_populates="reading",
        cascade="all, delete-orphan",
        order_by="Question.question_number",
    )

    # Relación 1:N con sesiones de jugador
    player_sessions = relationship(
        "PlayerSession",
        back_populates="reading",
        cascade="all, delete-orphan",
    )

    # Relación 1:N con notas de jugador
    player_notes = relationship(
        "PlayerNote",
        back_populates="reading",
        cascade="all, delete-orphan",
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


# ── Modelo de Usuarios ──────────────────────────────────────────────────────

class Workspace(Base):
    """Entorno de trabajo: agrupa las cuentas de jugador y todo lo que generan.
    Como mucho uno está activo, y solo sus jugadores entran al juego."""
    __tablename__ = "workspaces"
    __table_args__ = (
        Index("ux_workspaces_un_activo", "is_active", unique=True, postgresql_where=text("is_active")),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    color = Column(String(7), nullable=False)
    is_active = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Las cuentas las borra la base en cascada al borrar el entorno.
    users = relationship("User", back_populates="workspace", passive_deletes=True)


# Nombre único sin distinguir mayúsculas.
Index("ux_workspaces_nombre", func.lower(Workspace.name), unique=True)


class User(Base):
    """Modelo ORM para la tabla 'users'. Los jugadores son de un entorno; los
    administradores (y las cuentas de antes de los entornos) no tienen."""
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email_login", "email"),
        # El mismo correo puede estar en varios entornos, una vez en cada uno.
        Index("ux_users_workspace_email", "workspace_id", "email",
              unique=True, postgresql_nulls_not_distinct=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    character = Column(String(10), default="male")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)
    session_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    workspace = relationship("Workspace", back_populates="users")
    slots = relationship("PlayerSlot", back_populates="user", cascade="all, delete-orphan", foreign_keys="[PlayerSlot.user_id]")
    sessions = relationship("PlayerSession", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("PlayerAchievement", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("PlayerNote", back_populates="user", cascade="all, delete-orphan")
    typology_progress = relationship("PlayerTypologyProgress", back_populates="user", cascade="all, delete-orphan")


# ── Modelos de Gestión de Slots y Catálogos ───────────────────────────────────

class PlayerSlot(Base):
    """Slots de sesión para los jugadores."""
    __tablename__ = "player_slots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_number = Column(SmallInteger, nullable=False)
    label = Column(String(50), default="Sesión 1")
    alias = Column(String(40), nullable=True)
    vitrina = Column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    user = relationship("User", back_populates="slots", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    sessions = relationship("PlayerSession", back_populates="slot", cascade="all, delete-orphan")
    notes = relationship("PlayerNote", back_populates="slot", cascade="all, delete-orphan")
    typology_progress = relationship("PlayerTypologyProgress", back_populates="slot", cascade="all, delete-orphan")
    achievements = relationship("PlayerAchievement", back_populates="slot", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "slot_number", name="uq_user_slot_number"),
    )


class AchievementCatalog(Base):
    """Catálogo global de logros y medallas."""
    __tablename__ = "achievement_catalog"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    how_to_unlock = Column(Text, nullable=False)
    category = Column(String(30), nullable=False)
    icon = Column(String(10), default="🏆")
    medal_name = Column(String(100), nullable=False)
    medal_tier = Column(String(20), nullable=False, default="bronce")
    medal_description = Column(Text, nullable=True)
    medal_image_path = Column(String(255), nullable=True)
    medal_placeholder_emoji = Column(String(10), default="🏅")
    display_order = Column(SmallInteger, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relación con historial de imágenes
    image_history = relationship(
        "MedalImageHistory",
        back_populates="achievement",
        cascade="all, delete-orphan",
        order_by="MedalImageHistory.uploaded_at.desc()",
    )


class MedalImageHistory(Base):
    """Historial de imágenes de medallas."""
    __tablename__ = "medal_image_history"

    id = Column(Integer, primary_key=True, index=True)
    achievement_id = Column(String(50), ForeignKey("achievement_catalog.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    is_current = Column(Boolean, default=False)

    # Relaciones
    achievement = relationship("AchievementCatalog", back_populates="image_history")
    uploader = relationship("User")


# ── Modelos de Progreso del Jugador ──────────────────────────────────────────

class PlayerSession(Base):
    """Sesión de juego completada por un jugador."""
    __tablename__ = "player_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("player_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    reading_id = Column(Integer, ForeignKey("readings.id", ondelete="CASCADE"), nullable=False)
    typology = Column(String(50), nullable=False)
    session_score = Column(Integer, nullable=False, default=0)
    reading_time_seconds = Column(Integer, nullable=True)
    total_time_seconds = Column(Integer, nullable=True)
    is_perfect = Column(Boolean, default=False)
    correct_count = Column(Integer, nullable=False, default=0)
    incorrect_count = Column(Integer, nullable=False, default=0)
    tool_bonus = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    user = relationship("User", back_populates="sessions")
    slot = relationship("PlayerSlot", back_populates="sessions")
    reading = relationship("Reading", back_populates="player_sessions")
    answers = relationship("PlayerAnswer", back_populates="session", cascade="all, delete-orphan")
    tools = relationship("SessionTool", back_populates="session", cascade="all, delete-orphan")


class PlayerAnswer(Base):
    """Respuesta individual del jugador a una pregunta."""
    __tablename__ = "player_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("player_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    comprehension_level = Column(String(20), nullable=False)
    selected_answer = Column(String(1), nullable=False)
    correct_answer = Column(String(1), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    points_earned = Column(Integer, nullable=False, default=0)
    penalty_applied = Column(Integer, nullable=False, default=0)
    response_time_ms = Column(Integer, nullable=True)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    session = relationship("PlayerSession", back_populates="answers")
    question = relationship("Question")


class SessionTool(Base):
    """Registro de uso de herramienta en una sesión."""
    __tablename__ = "session_tools"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("player_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(30), nullable=False)
    was_used = Column(Boolean, nullable=False, default=False)
    usage_count = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Integer, nullable=True)

    # Relaciones
    session = relationship("PlayerSession", back_populates="tools")

    __table_args__ = (
        UniqueConstraint("session_id", "tool_name", name="uq_session_tool"),
    )


class PlayerNote(Base):
    """Nota/apunte escrito por el jugador durante una lectura."""
    __tablename__ = "player_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("player_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    reading_id = Column(Integer, ForeignKey("readings.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(Integer, ForeignKey("player_sessions.id", ondelete="SET NULL"), nullable=True)
    note_content = Column(Text, nullable=False)
    note_type = Column(String(30), nullable=False, default="free_text")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    user = relationship("User", back_populates="notes")
    slot = relationship("PlayerSlot", back_populates="notes")
    reading = relationship("Reading", back_populates="player_notes")
    session = relationship("PlayerSession")


class PlayerTypologyProgress(Base):
    """Progreso acumulado del jugador en cada tipología."""
    __tablename__ = "player_typology_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("player_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    typology = Column(String(50), nullable=False)
    best_score = Column(Integer, nullable=False, default=0)
    total_sessions = Column(Integer, nullable=False, default=0)
    perfect_sessions = Column(Integer, nullable=False, default=0)
    is_unlocked = Column(Boolean, nullable=False, default=False)
    # Lecturas de progresión terminadas desde la migración 010 (5 como máximo
    # para aprobar la tipología). Reiniciar la tipología lo devuelve a 0.
    attempts_used = Column(Integer, nullable=False, default=0, server_default="0")
    first_completed_at = Column(DateTime(timezone=True), nullable=True)
    last_played_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    user = relationship("User", back_populates="typology_progress")
    slot = relationship("PlayerSlot", back_populates="typology_progress")

    __table_args__ = (
        UniqueConstraint("user_id", "slot_id", "typology", name="uq_user_slot_typology"),
    )


class PlayerAchievement(Base):
    """Logro desbloqueado por un jugador."""
    __tablename__ = "player_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("player_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(String(50), nullable=False)
    achievement_name = Column(String(100), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    user = relationship("User", back_populates="achievements")
    slot = relationship("PlayerSlot", back_populates="achievements")

    __table_args__ = (
        UniqueConstraint("user_id", "slot_id", "achievement_id", name="uq_user_slot_achievement"),
    )


class NpcInteraction(Base):
    """Registro de interacciones del jugador con NPCs (robot asistente / sabio)."""
    __tablename__ = "npc_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("player_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    npc_type = Column(String(30), nullable=False)  # "robot" o "sabio"
    session_id = Column(Integer, ForeignKey("player_sessions.id", ondelete="SET NULL"), nullable=True)
    reading_id = Column(Integer, ForeignKey("readings.id", ondelete="SET NULL"), nullable=True)
    # Lo que preguntó el jugador y lo que respondió el tutor (migración 012).
    # NULL en las interacciones de antes, que solo se contaban.
    user_message = Column(Text, nullable=True)
    assistant_reply = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    user = relationship("User")
    slot = relationship("PlayerSlot")
    session = relationship("PlayerSession")
    reading = relationship("Reading")


class ActiveReading(Base):
    """Lectura activa (en progreso) de un jugador.
    Solo puede existir una por jugador por slot (UNIQUE constraint).
    Se limpia al completar la sesión o al expirar (24h).
    """
    __tablename__ = "active_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("player_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    reading_id = Column(Integer, ForeignKey("readings.id", ondelete="CASCADE"), nullable=False)
    typology = Column(String(50), nullable=False)
    current_level_index = Column(Integer, nullable=False, default=0)
    current_question_index = Column(Integer, nullable=False, default=0)
    reading_completed = Column(Boolean, nullable=False, default=False)
    session_score = Column(Integer, nullable=False, default=0)
    results_json = Column(Text, default="[]")
    tools_used_json = Column(Text, default='{"highlight":false,"underline":false,"notes":false}')
    reading_start_time = Column(String(50), default="0")
    # Segundos acumulados de lectura y de sesión hasta el último guardado: al
    # reanudar tras cerrar el navegador se sigue sumando desde aquí.
    reading_seconds = Column(Integer, nullable=False, default=0, server_default="0")
    total_seconds = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    user = relationship("User")
    slot = relationship("PlayerSlot")
    reading = relationship("Reading")

    __table_args__ = (
        UniqueConstraint("user_id", "slot_id", name="uq_user_slot_active_reading"),
    )
