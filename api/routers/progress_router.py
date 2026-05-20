"""
progress_router.py — Endpoints de progreso del jugador.
Registrar sesiones, logros, notas y consultar progreso completo.
Todos los endpoints requieren autenticación JWT.
"""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc

from database import get_db
from models import (
    User, PlayerSession, PlayerAnswer, SessionTool,
    PlayerNote, PlayerTypologyProgress, PlayerAchievement, Reading,
)
from schemas import (
    SessionCreate, SessionResponse, NoteCreate, NoteResponse,
    AchievementCreate, AchievementResponse, TypologyProgressResponse,
    PlayerProgressResponse, UserResponse, DIFFICULTY_ORDER,
)
from auth import get_current_user

router = APIRouter(prefix="/progress", tags=["Progreso del Jugador"])

# ── Umbrales de desbloqueo (deben coincidir con ProgressionManager en Godot) ──
UNLOCK_THRESHOLDS = {
    "Narrativo": 0,
    "Descriptivo": 250,
    "Argumentativo": 250,
    "Instructivo": 250,
    "Expositivo": 250,
}


# ── Progreso Completo ────────────────────────────────────────────────────────

@router.get("/me", response_model=PlayerProgressResponse)
def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna el progreso completo del jugador autenticado."""
    # Progreso por tipología
    typology_rows = (
        db.query(PlayerTypologyProgress)
        .filter(PlayerTypologyProgress.user_id == current_user.id)
        .order_by(PlayerTypologyProgress.id)
        .all()
    )

    # Si no tiene registros de progreso, inicializarlos
    if not typology_rows:
        for typology in DIFFICULTY_ORDER:
            progress = PlayerTypologyProgress(
                user_id=current_user.id,
                typology=typology,
                is_unlocked=(typology == "Narrativo"),
            )
            db.add(progress)
        db.commit()
        typology_rows = (
            db.query(PlayerTypologyProgress)
            .filter(PlayerTypologyProgress.user_id == current_user.id)
            .all()
        )

    # Calcular puntaje total
    total_score = sum(tp.best_score for tp in typology_rows)

    # Logros
    achievements = (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.user_id == current_user.id)
        .order_by(PlayerAchievement.unlocked_at)
        .all()
    )

    # Últimas 10 sesiones
    recent_sessions = (
        db.query(PlayerSession)
        .options(
            joinedload(PlayerSession.answers),
            joinedload(PlayerSession.tools),
        )
        .filter(PlayerSession.user_id == current_user.id)
        .order_by(PlayerSession.completed_at.desc())
        .limit(10)
        .all()
    )

    return PlayerProgressResponse(
        user=UserResponse.model_validate(current_user),
        total_score=total_score,
        typology_progress=[
            TypologyProgressResponse.model_validate(tp) for tp in typology_rows
        ],
        achievements=[
            AchievementResponse.model_validate(a) for a in achievements
        ],
        recent_sessions=[
            SessionResponse.model_validate(s) for s in recent_sessions
        ],
    )


# ── Sesiones ─────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra una sesión completada desde Godot."""
    # Crear la sesión
    session = PlayerSession(
        user_id=current_user.id,
        reading_id=data.reading_id,
        typology=data.typology,
        session_score=data.session_score,
        reading_time_seconds=data.reading_time_seconds,
        total_time_seconds=data.total_time_seconds,
        is_perfect=data.is_perfect,
        correct_count=data.correct_count,
        incorrect_count=data.incorrect_count,
        tool_bonus=data.tool_bonus,
    )
    db.add(session)
    db.flush()  # Para obtener session.id

    # Registrar respuestas
    for answer_data in data.answers:
        answer = PlayerAnswer(
            session_id=session.id,
            question_id=answer_data.question_id,
            comprehension_level=answer_data.comprehension_level,
            selected_answer=answer_data.selected_answer,
            correct_answer=answer_data.correct_answer,
            is_correct=answer_data.is_correct,
            points_earned=answer_data.points_earned,
            penalty_applied=answer_data.penalty_applied,
            response_time_ms=answer_data.response_time_ms,
        )
        db.add(answer)

    # Registrar herramientas
    for tool_data in data.tools:
        tool = SessionTool(
            session_id=session.id,
            tool_name=tool_data.tool_name,
            was_used=tool_data.was_used,
            usage_count=tool_data.usage_count,
            duration_seconds=tool_data.duration_seconds,
        )
        db.add(tool)

    # Actualizar progreso de tipología
    progress = (
        db.query(PlayerTypologyProgress)
        .filter(
            PlayerTypologyProgress.user_id == current_user.id,
            PlayerTypologyProgress.typology == data.typology,
        )
        .first()
    )

    if not progress:
        progress = PlayerTypologyProgress(
            user_id=current_user.id,
            typology=data.typology,
            is_unlocked=True,
        )
        db.add(progress)
        db.flush()

    progress.total_sessions += 1
    progress.best_score = max(progress.best_score, data.session_score)
    progress.last_played_at = datetime.now(timezone.utc)
    if progress.first_completed_at is None:
        progress.first_completed_at = datetime.now(timezone.utc)
    if data.is_perfect:
        progress.perfect_sessions += 1

    # Verificar desbloqueo de la siguiente tipología
    _check_unlock(db, current_user.id, data.typology)

    db.commit()
    db.refresh(session)

    # Recargar con relaciones
    session = (
        db.query(PlayerSession)
        .options(
            joinedload(PlayerSession.answers),
            joinedload(PlayerSession.tools),
        )
        .filter(PlayerSession.id == session.id)
        .first()
    )

    return session


@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(
    typology: str = Query(None, description="Filtrar por tipología"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista el historial de sesiones del jugador autenticado."""
    query = (
        db.query(PlayerSession)
        .options(
            joinedload(PlayerSession.answers),
            joinedload(PlayerSession.tools),
        )
        .filter(PlayerSession.user_id == current_user.id)
    )
    if typology:
        query = query.filter(PlayerSession.typology == typology)
    sessions = query.order_by(PlayerSession.completed_at.desc()).limit(limit).all()
    return sessions


@router.get("/typologies", response_model=List[TypologyProgressResponse])
def get_typology_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna el progreso del jugador en cada tipología."""
    rows = (
        db.query(PlayerTypologyProgress)
        .filter(PlayerTypologyProgress.user_id == current_user.id)
        .all()
    )
    # Asegurar que todas las tipologías existan
    existing_typs = {r.typology for r in rows}
    for typology in DIFFICULTY_ORDER:
        if typology not in existing_typs:
            p = PlayerTypologyProgress(
                user_id=current_user.id,
                typology=typology,
                is_unlocked=(typology == "Narrativo"),
            )
            db.add(p)
            rows.append(p)
    db.commit()
    return rows


# ── Logros ───────────────────────────────────────────────────────────────────

@router.post("/achievements", response_model=AchievementResponse, status_code=201)
def register_achievement(
    data: AchievementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra un logro desbloqueado (idempotente: no duplica si ya existe)."""
    existing = (
        db.query(PlayerAchievement)
        .filter(
            PlayerAchievement.user_id == current_user.id,
            PlayerAchievement.achievement_id == data.achievement_id,
        )
        .first()
    )
    if existing:
        return existing

    achievement = PlayerAchievement(
        user_id=current_user.id,
        achievement_id=data.achievement_id,
        achievement_name=data.achievement_name,
    )
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    return achievement


@router.get("/achievements", response_model=List[AchievementResponse])
def list_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista todos los logros del jugador autenticado."""
    return (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.user_id == current_user.id)
        .order_by(PlayerAchievement.unlocked_at)
        .all()
    )


# ── Notas ────────────────────────────────────────────────────────────────────

@router.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Guarda una nota/apunte del jugador asociada a una lectura."""
    # Verificar que la lectura existe
    reading = db.query(Reading).filter(Reading.id == data.reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")

    note = PlayerNote(
        user_id=current_user.id,
        reading_id=data.reading_id,
        session_id=data.session_id,
        note_content=data.note_content,
        note_type=data.note_type,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return NoteResponse(
        id=note.id,
        user_id=note.user_id,
        reading_id=note.reading_id,
        session_id=note.session_id,
        note_content=note.note_content,
        note_type=note.note_type,
        created_at=note.created_at,
        reading_title=reading.title,
    )


@router.get("/notes", response_model=List[NoteResponse])
def list_notes(
    reading_id: int = Query(None, description="Filtrar por lectura"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista las notas del jugador autenticado."""
    query = (
        db.query(PlayerNote, Reading.title)
        .join(Reading, PlayerNote.reading_id == Reading.id)
        .filter(PlayerNote.user_id == current_user.id)
    )
    if reading_id:
        query = query.filter(PlayerNote.reading_id == reading_id)

    results = query.order_by(PlayerNote.created_at.desc()).all()

    return [
        NoteResponse(
            id=note.id,
            user_id=note.user_id,
            reading_id=note.reading_id,
            session_id=note.session_id,
            note_content=note.note_content,
            note_type=note.note_type,
            created_at=note.created_at,
            reading_title=title,
        )
        for note, title in results
    ]


# ── Lógica de desbloqueo ────────────────────────────────────────────────────

def _check_unlock(db: Session, user_id: int, completed_typology: str) -> None:
    """Verifica si al completar una tipología se desbloquea la siguiente."""
    try:
        idx = DIFFICULTY_ORDER.index(completed_typology)
    except ValueError:
        return

    if idx >= len(DIFFICULTY_ORDER) - 1:
        return  # Es la última tipología

    next_typology = DIFFICULTY_ORDER[idx + 1]

    # Obtener el progreso del completado
    progress = (
        db.query(PlayerTypologyProgress)
        .filter(
            PlayerTypologyProgress.user_id == user_id,
            PlayerTypologyProgress.typology == completed_typology,
        )
        .first()
    )
    if not progress:
        return

    threshold = UNLOCK_THRESHOLDS.get(next_typology, 999)
    if progress.best_score >= threshold:
        # Desbloquear la siguiente
        next_progress = (
            db.query(PlayerTypologyProgress)
            .filter(
                PlayerTypologyProgress.user_id == user_id,
                PlayerTypologyProgress.typology == next_typology,
            )
            .first()
        )
        if next_progress and not next_progress.is_unlocked:
            next_progress.is_unlocked = True
