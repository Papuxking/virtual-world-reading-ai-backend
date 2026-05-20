"""
admin_router.py — Endpoints administrativos para el dashboard.
Lista de jugadores, detalle, estadísticas, reinicio por tipología y reinicio total.
Todos los endpoints requieren rol de administrador.
"""
from datetime import datetime, timedelta, timezone
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
    PlayerSummary, AdminStatsResponse, UserResponse,
    SessionResponse, NoteResponse, AchievementResponse,
    TypologyProgressResponse, ResetTypologyRequest, ResetAllRequest,
    DIFFICULTY_ORDER,
)
from auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Administración"])


# ── Lista de Jugadores ───────────────────────────────────────────────────────

@router.get("/players", response_model=List[PlayerSummary])
def list_players(
    q: str = Query("", description="Buscar por nombre o email"),
    is_active: bool = Query(None, description="Filtrar por estado"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista todos los jugadores con resumen de progreso."""
    query = db.query(User).filter(User.is_admin == False)

    if q:
        search = f"%{q}%"
        query = query.filter(
            (User.display_name.ilike(search)) | (User.email.ilike(search))
        )
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.order_by(User.created_at.desc()).all()

    result = []
    for user in users:
        # Calcular resumen
        total_score = (
            db.query(sqlfunc.coalesce(sqlfunc.sum(PlayerTypologyProgress.best_score), 0))
            .filter(PlayerTypologyProgress.user_id == user.id)
            .scalar()
        )
        total_sessions = (
            db.query(sqlfunc.count(PlayerSession.id))
            .filter(PlayerSession.user_id == user.id)
            .scalar()
        )
        total_achievements = (
            db.query(sqlfunc.count(PlayerAchievement.id))
            .filter(PlayerAchievement.user_id == user.id)
            .scalar()
        )
        last_played = (
            db.query(sqlfunc.max(PlayerSession.completed_at))
            .filter(PlayerSession.user_id == user.id)
            .scalar()
        )

        result.append(PlayerSummary(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            character=user.character,
            is_active=user.is_active,
            total_score=total_score or 0,
            total_sessions=total_sessions or 0,
            total_achievements=total_achievements or 0,
            last_played_at=last_played,
            created_at=user.created_at,
        ))

    return result


# ── Detalle de un Jugador ────────────────────────────────────────────────────

@router.get("/players/{player_id}", response_model=dict)
def get_player_detail(
    player_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retorna el detalle completo de un jugador específico."""
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Progreso por tipología
    typology_progress = (
        db.query(PlayerTypologyProgress)
        .filter(PlayerTypologyProgress.user_id == player_id)
        .all()
    )

    # Logros
    achievements = (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.user_id == player_id)
        .order_by(PlayerAchievement.unlocked_at)
        .all()
    )

    # Sesiones con detalle
    sessions = (
        db.query(PlayerSession)
        .options(
            joinedload(PlayerSession.answers),
            joinedload(PlayerSession.tools),
            joinedload(PlayerSession.reading),
        )
        .filter(PlayerSession.user_id == player_id)
        .order_by(PlayerSession.completed_at.desc())
        .limit(50)
        .all()
    )

    # Notas con título de lectura
    notes_query = (
        db.query(PlayerNote, Reading.title)
        .join(Reading, PlayerNote.reading_id == Reading.id)
        .filter(PlayerNote.user_id == player_id)
        .order_by(PlayerNote.created_at.desc())
        .all()
    )

    # Estadísticas de herramientas
    tool_stats = (
        db.query(
            SessionTool.tool_name,
            sqlfunc.count(SessionTool.id).label("total"),
            sqlfunc.sum(sqlfunc.cast(SessionTool.was_used, sqlfunc.integer())).label("used"),
        )
        .join(PlayerSession, SessionTool.session_id == PlayerSession.id)
        .filter(PlayerSession.user_id == player_id)
        .group_by(SessionTool.tool_name)
        .all()
    )

    # Estadísticas por nivel de comprensión
    level_stats = (
        db.query(
            PlayerAnswer.comprehension_level,
            sqlfunc.count(PlayerAnswer.id).label("total"),
            sqlfunc.sum(sqlfunc.cast(PlayerAnswer.is_correct, sqlfunc.integer())).label("correct"),
        )
        .join(PlayerSession, PlayerAnswer.session_id == PlayerSession.id)
        .filter(PlayerSession.user_id == player_id)
        .group_by(PlayerAnswer.comprehension_level)
        .all()
    )

    total_score = sum(tp.best_score for tp in typology_progress)

    return {
        "user": UserResponse.model_validate(user),
        "total_score": total_score,
        "typology_progress": [
            TypologyProgressResponse.model_validate(tp) for tp in typology_progress
        ],
        "achievements": [
            AchievementResponse.model_validate(a) for a in achievements
        ],
        "sessions": [
            {
                "id": s.id,
                "reading_id": s.reading_id,
                "reading_title": s.reading.title if s.reading else "Desconocida",
                "typology": s.typology,
                "session_score": s.session_score,
                "reading_time_seconds": s.reading_time_seconds,
                "total_time_seconds": s.total_time_seconds,
                "is_perfect": s.is_perfect,
                "correct_count": s.correct_count,
                "incorrect_count": s.incorrect_count,
                "tool_bonus": s.tool_bonus,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "answers": [
                    {
                        "question_id": a.question_id,
                        "comprehension_level": a.comprehension_level,
                        "selected_answer": a.selected_answer,
                        "correct_answer": a.correct_answer,
                        "is_correct": a.is_correct,
                        "points_earned": a.points_earned,
                        "penalty_applied": a.penalty_applied,
                    }
                    for a in s.answers
                ],
                "tools": [
                    {
                        "tool_name": t.tool_name,
                        "was_used": t.was_used,
                        "usage_count": t.usage_count,
                    }
                    for t in s.tools
                ],
            }
            for s in sessions
        ],
        "notes": [
            {
                "id": note.id,
                "reading_id": note.reading_id,
                "reading_title": title,
                "note_content": note.note_content,
                "note_type": note.note_type,
                "created_at": note.created_at.isoformat() if note.created_at else None,
            }
            for note, title in notes_query
        ],
        "tool_stats": [
            {
                "tool_name": name,
                "total_sessions": total,
                "times_used": used or 0,
                "usage_rate": round((used or 0) / total * 100, 1) if total > 0 else 0,
            }
            for name, total, used in tool_stats
        ],
        "level_stats": [
            {
                "level": level,
                "total": total,
                "correct": correct or 0,
                "accuracy": round((correct or 0) / total * 100, 1) if total > 0 else 0,
            }
            for level, total, correct in level_stats
        ],
    }


# ── Estadísticas Globales ────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retorna estadísticas globales para el dashboard."""
    total_players = db.query(sqlfunc.count(User.id)).filter(User.is_admin == False).scalar()
    active_players = (
        db.query(sqlfunc.count(User.id))
        .filter(User.is_admin == False, User.is_active == True)
        .scalar()
    )
    total_sessions = db.query(sqlfunc.count(PlayerSession.id)).scalar()
    total_points = (
        db.query(sqlfunc.coalesce(sqlfunc.sum(PlayerTypologyProgress.best_score), 0))
        .scalar()
    )
    total_achievements = db.query(sqlfunc.count(PlayerAchievement.id)).scalar()

    # Precisión promedio
    total_answers = db.query(sqlfunc.count(PlayerAnswer.id)).scalar()
    correct_answers = (
        db.query(sqlfunc.count(PlayerAnswer.id))
        .filter(PlayerAnswer.is_correct == True)
        .scalar()
    )
    avg_accuracy = round(correct_answers / total_answers * 100, 1) if total_answers > 0 else 0

    # Sesiones por tipología
    sessions_by_typ = (
        db.query(PlayerSession.typology, sqlfunc.count(PlayerSession.id))
        .group_by(PlayerSession.typology)
        .all()
    )

    # Actividad últimos 7 días
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    activity = (
        db.query(
            sqlfunc.date(PlayerSession.completed_at).label("day"),
            sqlfunc.count(PlayerSession.id).label("count"),
        )
        .filter(PlayerSession.completed_at >= seven_days_ago)
        .group_by(sqlfunc.date(PlayerSession.completed_at))
        .order_by(sqlfunc.date(PlayerSession.completed_at))
        .all()
    )

    return AdminStatsResponse(
        total_players=total_players or 0,
        active_players=active_players or 0,
        total_sessions=total_sessions or 0,
        total_points=total_points or 0,
        total_achievements=total_achievements or 0,
        average_accuracy=avg_accuracy,
        sessions_by_typology={t: c for t, c in sessions_by_typ},
        activity_last_7_days=[
            {"date": str(day), "sessions": count} for day, count in activity
        ],
    )


# ── Reinicio por Tipología (Cascada Hacia Arriba) ────────────────────────────

@router.post("/players/{player_id}/reset/typology")
def reset_typology(
    player_id: int,
    data: ResetTypologyRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Reinicia el progreso de una tipología Y TODAS LAS SUPERIORES.
    Ejemplo: reiniciar Argumentativo también borra Instructivo y Expositivo.
    Los logros NO se borran (son permanentes).
    """
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Verificar confirmación por email
    if data.confirm_email != user.email:
        raise HTTPException(
            status_code=400,
            detail="El email de confirmación no coincide con el jugador",
        )

    # Determinar tipologías a reiniciar (la indicada + todas las superiores)
    try:
        start_idx = DIFFICULTY_ORDER.index(data.typology)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipología inválida: {data.typology}")

    typologies_to_reset = DIFFICULTY_ORDER[start_idx:]

    deleted_sessions = 0
    deleted_notes = 0

    for typology in typologies_to_reset:
        # Obtener IDs de sesiones de esta tipología
        session_ids = [
            s.id for s in
            db.query(PlayerSession.id)
            .filter(
                PlayerSession.user_id == player_id,
                PlayerSession.typology == typology,
            )
            .all()
        ]

        if session_ids:
            # Borrar respuestas de esas sesiones
            db.query(PlayerAnswer).filter(
                PlayerAnswer.session_id.in_(session_ids)
            ).delete(synchronize_session=False)

            # Borrar herramientas de esas sesiones
            db.query(SessionTool).filter(
                SessionTool.session_id.in_(session_ids)
            ).delete(synchronize_session=False)

            # Borrar las sesiones
            count = db.query(PlayerSession).filter(
                PlayerSession.id.in_(session_ids)
            ).delete(synchronize_session=False)
            deleted_sessions += count

        # Borrar notas de lecturas de esta tipología
        reading_ids_of_typology = [
            r.id for r in
            db.query(Reading.id).filter(Reading.typology == typology).all()
        ]
        if reading_ids_of_typology:
            note_count = db.query(PlayerNote).filter(
                PlayerNote.user_id == player_id,
                PlayerNote.reading_id.in_(reading_ids_of_typology),
            ).delete(synchronize_session=False)
            deleted_notes += note_count

        # Reiniciar progreso de tipología
        progress = (
            db.query(PlayerTypologyProgress)
            .filter(
                PlayerTypologyProgress.user_id == player_id,
                PlayerTypologyProgress.typology == typology,
            )
            .first()
        )
        if progress:
            progress.best_score = 0
            progress.total_sessions = 0
            progress.perfect_sessions = 0
            progress.first_completed_at = None
            progress.last_played_at = None
            # La primera tipología (Narrativo) siempre queda desbloqueada
            if typology == "Narrativo":
                progress.is_unlocked = True
            else:
                progress.is_unlocked = False

    # Re-evaluar desbloqueos desde el principio
    _reevaluate_unlocks(db, player_id)

    db.commit()

    return {
        "detail": "Progreso reiniciado",
        "typologies_reset": typologies_to_reset,
        "sessions_deleted": deleted_sessions,
        "notes_deleted": deleted_notes,
    }


# ── Reinicio Total ───────────────────────────────────────────────────────────

@router.post("/players/{player_id}/reset/all")
def reset_all_progress(
    player_id: int,
    data: ResetAllRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Reinicia TODO el progreso de un jugador.
    Borra sesiones, respuestas, herramientas, notas, logros y progreso.
    NO borra la cuenta ni el personaje.
    """
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    if data.confirm_email != user.email:
        raise HTTPException(
            status_code=400,
            detail="El email de confirmación no coincide con el jugador",
        )

    # Obtener IDs de sesiones
    session_ids = [
        s.id for s in
        db.query(PlayerSession.id)
        .filter(PlayerSession.user_id == player_id)
        .all()
    ]

    counts = {
        "sessions": 0,
        "answers": 0,
        "tools": 0,
        "notes": 0,
        "achievements": 0,
    }

    if session_ids:
        counts["answers"] = db.query(PlayerAnswer).filter(
            PlayerAnswer.session_id.in_(session_ids)
        ).delete(synchronize_session=False)

        counts["tools"] = db.query(SessionTool).filter(
            SessionTool.session_id.in_(session_ids)
        ).delete(synchronize_session=False)

        counts["sessions"] = db.query(PlayerSession).filter(
            PlayerSession.id.in_(session_ids)
        ).delete(synchronize_session=False)

    counts["notes"] = db.query(PlayerNote).filter(
        PlayerNote.user_id == player_id
    ).delete(synchronize_session=False)

    counts["achievements"] = db.query(PlayerAchievement).filter(
        PlayerAchievement.user_id == player_id
    ).delete(synchronize_session=False)

    # Reiniciar progreso de tipologías
    db.query(PlayerTypologyProgress).filter(
        PlayerTypologyProgress.user_id == player_id
    ).delete(synchronize_session=False)

    # Recrear progreso con solo Narrativo desbloqueado
    for typology in DIFFICULTY_ORDER:
        p = PlayerTypologyProgress(
            user_id=player_id,
            typology=typology,
            is_unlocked=(typology == "Narrativo"),
        )
        db.add(p)

    db.commit()

    return {
        "detail": "Todo el progreso ha sido reiniciado",
        "deleted": counts,
    }


# ── Sesiones de un jugador específico ────────────────────────────────────────

@router.get("/players/{player_id}/sessions", response_model=List[dict])
def get_player_sessions(
    player_id: int,
    typology: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista las sesiones de un jugador específico (vista admin)."""
    query = (
        db.query(PlayerSession)
        .options(
            joinedload(PlayerSession.answers),
            joinedload(PlayerSession.tools),
            joinedload(PlayerSession.reading),
        )
        .filter(PlayerSession.user_id == player_id)
    )
    if typology:
        query = query.filter(PlayerSession.typology == typology)

    sessions = query.order_by(PlayerSession.completed_at.desc()).limit(limit).all()

    return [
        {
            "id": s.id,
            "reading_id": s.reading_id,
            "reading_title": s.reading.title if s.reading else "Desconocida",
            "typology": s.typology,
            "session_score": s.session_score,
            "reading_time_seconds": s.reading_time_seconds,
            "total_time_seconds": s.total_time_seconds,
            "is_perfect": s.is_perfect,
            "correct_count": s.correct_count,
            "incorrect_count": s.incorrect_count,
            "tool_bonus": s.tool_bonus,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "answers": [
                {
                    "question_id": a.question_id,
                    "comprehension_level": a.comprehension_level,
                    "selected_answer": a.selected_answer,
                    "correct_answer": a.correct_answer,
                    "is_correct": a.is_correct,
                    "points_earned": a.points_earned,
                    "penalty_applied": a.penalty_applied,
                }
                for a in s.answers
            ],
            "tools": [
                {"tool_name": t.tool_name, "was_used": t.was_used, "usage_count": t.usage_count}
                for t in s.tools
            ],
        }
        for s in sessions
    ]


# ── Notas de un jugador ─────────────────────────────────────────────────────

@router.get("/players/{player_id}/notes", response_model=List[dict])
def get_player_notes(
    player_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista las notas de un jugador con el título de la lectura asociada."""
    results = (
        db.query(PlayerNote, Reading.title)
        .join(Reading, PlayerNote.reading_id == Reading.id)
        .filter(PlayerNote.user_id == player_id)
        .order_by(PlayerNote.created_at.desc())
        .all()
    )

    return [
        {
            "id": note.id,
            "reading_id": note.reading_id,
            "reading_title": title,
            "note_content": note.note_content,
            "note_type": note.note_type,
            "created_at": note.created_at.isoformat() if note.created_at else None,
        }
        for note, title in results
    ]


# ── Utilidad: Re-evaluar desbloqueos ────────────────────────────────────────

UNLOCK_THRESHOLDS = {
    "Narrativo": 0,
    "Descriptivo": 250,
    "Argumentativo": 250,
    "Instructivo": 250,
    "Expositivo": 250,
}


def _reevaluate_unlocks(db: Session, user_id: int) -> None:
    """
    Re-evalúa qué tipologías deben estar desbloqueadas
    después de un reinicio parcial.
    """
    for i, typology in enumerate(DIFFICULTY_ORDER):
        progress = (
            db.query(PlayerTypologyProgress)
            .filter(
                PlayerTypologyProgress.user_id == user_id,
                PlayerTypologyProgress.typology == typology,
            )
            .first()
        )
        if not progress:
            continue

        if typology == "Narrativo":
            progress.is_unlocked = True
            continue

        # Verificar si la tipología anterior cumple el umbral
        prev_typology = DIFFICULTY_ORDER[i - 1]
        prev_progress = (
            db.query(PlayerTypologyProgress)
            .filter(
                PlayerTypologyProgress.user_id == user_id,
                PlayerTypologyProgress.typology == prev_typology,
            )
            .first()
        )

        threshold = UNLOCK_THRESHOLDS.get(typology, 999)
        if prev_progress and prev_progress.best_score >= threshold:
            progress.is_unlocked = True
        else:
            progress.is_unlocked = False
