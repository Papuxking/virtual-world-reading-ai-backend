"""
admin_router.py — Endpoints administrativos para el dashboard.
Lista de jugadores, detalle, estadísticas, reinicio por tipología y reinicio total.
Todos los endpoints requieren rol de administrador.
"""
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc, Integer

from database import get_db
from models import (
    User, PlayerSession, PlayerAnswer, SessionTool,
    PlayerNote, PlayerTypologyProgress, PlayerAchievement, Reading,
    PlayerSlot, ActiveReading,
)
from schemas import (
    PlayerSummary, AdminStatsResponse, UserResponse,
    SessionResponse, NoteResponse, AchievementResponse,
    TypologyProgressResponse, ResetTypologyRequest, ResetAllRequest,
    PlayerSlotResponse, PlayerSlotCreate,
)
from game_rules import DIFFICULTY_ORDER, score_rules
from progression import juego_terminado, reevaluate_unlocks
from auth import get_current_admin, hash_password
from workspaces import generate_temp_password

router = APIRouter(prefix="/admin", tags=["Administración"])


def _sesion_a_dict(s: PlayerSession) -> dict:
    """Sesión con sus respuestas y herramientas, tal como la pinta el dashboard."""
    return {
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


def _sesiones_del_slot(
    db: Session,
    player_id: int,
    slot_id: int,
    limite: int = 50,
    typology: str | None = None,
) -> list:
    """Sesiones del slot, más recientes primero."""
    query = (
        db.query(PlayerSession)
        .options(
            joinedload(PlayerSession.answers),
            joinedload(PlayerSession.tools),
            joinedload(PlayerSession.reading),
        )
        .filter(
            PlayerSession.user_id == player_id,
            PlayerSession.slot_id == slot_id,
        )
    )
    if typology:
        query = query.filter(PlayerSession.typology == typology)
    return query.order_by(PlayerSession.completed_at.desc()).limit(limite).all()


# ── Lista de Jugadores ───────────────────────────────────────────────────────

@router.get("/players", response_model=List[PlayerSummary])
def list_players(
    q: str = Query("", description="Buscar por nombre o email"),
    is_active: bool = Query(None, description="Filtrar por estado"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista todos los jugadores con resumen de progreso para el slot activo."""
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
        # Obtener slot activo
        act_slot = db.query(PlayerSlot).filter(PlayerSlot.user_id == user.id, PlayerSlot.is_active == True).first()
        slot_filter = (PlayerTypologyProgress.slot_id == act_slot.id) if act_slot else True
        sess_filter = (PlayerSession.slot_id == act_slot.id) if act_slot else True
        ach_filter = (PlayerAchievement.slot_id == act_slot.id) if act_slot else True

        total_score = (
            db.query(sqlfunc.coalesce(sqlfunc.sum(PlayerTypologyProgress.best_score), 0))
            .filter(
                PlayerTypologyProgress.user_id == user.id,
                PlayerTypologyProgress.typology.in_(DIFFICULTY_ORDER),
            )
            .filter(slot_filter)
            .scalar()
        )
        total_sessions = (
            db.query(sqlfunc.count(PlayerSession.id))
            .filter(PlayerSession.user_id == user.id)
            .filter(sess_filter)
            .scalar()
        )
        total_achievements = (
            db.query(sqlfunc.count(PlayerAchievement.id))
            .filter(PlayerAchievement.user_id == user.id)
            .filter(ach_filter)
            .scalar()
        )
        last_played = (
            db.query(sqlfunc.max(PlayerSession.completed_at))
            .filter(PlayerSession.user_id == user.id)
            .filter(sess_filter)
            .scalar()
        )
        filas_slot = (
            db.query(PlayerTypologyProgress)
            .filter(PlayerTypologyProgress.user_id == user.id)
            .filter(slot_filter)
            .all()
        ) if act_slot else []

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
            game_over=juego_terminado(filas_slot),
        ))

    return result


# ── Detalle de un Jugador ────────────────────────────────────────────────────

@router.get("/players/{player_id}", response_model=dict)
def get_player_detail(
    player_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retorna el detalle de un jugador para su slot activo."""
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Obtener el slot activo del jugador
    active_slot = db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id, PlayerSlot.is_active == True).first()
    if not active_slot:
        # Crear un slot activo por defecto si no existe por algún motivo
        active_slot = PlayerSlot(
            user_id=player_id,
            slot_number=1,
            label="Sesión 1",
            is_active=True
        )
        db.add(active_slot)
        db.commit()
        db.refresh(active_slot)

    # Progreso de las tipologías del juego, en orden de dificultad
    typology_progress = (
        db.query(PlayerTypologyProgress)
        .filter(
            PlayerTypologyProgress.user_id == player_id,
            PlayerTypologyProgress.slot_id == active_slot.id,
            PlayerTypologyProgress.typology.in_(DIFFICULTY_ORDER),
        )
        .all()
    )
    typology_progress.sort(key=lambda tp: DIFFICULTY_ORDER.index(tp.typology))

    # Logros en el slot activo
    achievements = (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.user_id == player_id, PlayerAchievement.slot_id == active_slot.id)
        .order_by(PlayerAchievement.unlocked_at)
        .all()
    )

    sessions = _sesiones_del_slot(db, player_id, active_slot.id)

    # Notas con título de lectura en el slot activo
    notes_query = (
        db.query(PlayerNote, Reading.title, Reading.typology)
        .join(Reading, PlayerNote.reading_id == Reading.id)
        .filter(PlayerNote.user_id == player_id, PlayerNote.slot_id == active_slot.id)
        .order_by(PlayerNote.created_at.desc())
        .all()
    )

    # Estadísticas de herramientas
    tool_stats = (
        db.query(
            SessionTool.tool_name,
            sqlfunc.count(SessionTool.id).label("total"),
            sqlfunc.sum(sqlfunc.cast(SessionTool.was_used, Integer)).label("used"),
        )
        .join(PlayerSession, SessionTool.session_id == PlayerSession.id)
        .filter(
            PlayerSession.user_id == player_id,
            PlayerSession.slot_id == active_slot.id,
        )
        .group_by(SessionTool.tool_name)
        .all()
    )

    # Estadísticas por nivel de comprensión
    level_stats = (
        db.query(
            PlayerAnswer.comprehension_level,
            sqlfunc.count(PlayerAnswer.id).label("total"),
            sqlfunc.sum(sqlfunc.cast(PlayerAnswer.is_correct, Integer)).label("correct"),
        )
        .join(PlayerSession, PlayerAnswer.session_id == PlayerSession.id)
        .filter(
            PlayerSession.user_id == player_id,
            PlayerSession.slot_id == active_slot.id,
        )
        .group_by(PlayerAnswer.comprehension_level)
        .all()
    )

    total_score = sum(tp.best_score for tp in typology_progress)

    return {
        "user": UserResponse.model_validate(user),
        "score_rules": score_rules(),
        "total_score": total_score,
        "game_over": juego_terminado(typology_progress),
        "active_slot_number": active_slot.slot_number,
        "active_slot_label": active_slot.label,
        "typology_progress": [
            TypologyProgressResponse.model_validate(tp) for tp in typology_progress
        ],
        "achievements": [
            AchievementResponse.model_validate(a) for a in achievements
        ],
        "sessions": [_sesion_a_dict(s) for s in sessions],
        "notes": [
            {
                "id": note.id,
                "reading_id": note.reading_id,
                "reading_title": title,
                "reading_typology": typology,
                "note_content": note.note_content,
                "note_type": note.note_type,
                "created_at": note.created_at.isoformat() if note.created_at else None,
            }
            for note, title, typology in notes_query
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
        .filter(PlayerTypologyProgress.typology.in_(DIFFICULTY_ORDER))
        .scalar()
    )
    total_achievements = db.query(sqlfunc.count(PlayerAchievement.id)).scalar()

    # Precisión promedio
    respuestas = (
        db.query(sqlfunc.count(PlayerAnswer.id))
        .join(PlayerSession, PlayerAnswer.session_id == PlayerSession.id)
    )
    total_answers = respuestas.scalar()
    correct_answers = respuestas.filter(PlayerAnswer.is_correct == True).scalar()
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
    Reinicia el progreso de una tipología Y TODAS LAS SUPERIORES en el SLOT ACTIVO.
    Ejemplo: reiniciar Argumentativo también borra Expositivo.
    """
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Validar confirmación de borrado
    if not data.confirm_delete:
        raise HTTPException(
            status_code=400,
            detail="Debe confirmar explícitamente la eliminación permanente",
        )

    # Verificar confirmación por email
    if data.confirm_email != user.email:
        raise HTTPException(
            status_code=400,
            detail="El email de confirmación no coincide con el jugador",
        )

    # Obtener slot activo
    active_slot = db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id, PlayerSlot.is_active == True).first()
    if not active_slot:
        raise HTTPException(status_code=400, detail="El jugador no tiene un slot de sesión activo")

    # Determinar tipologías a reiniciar (la indicada + todas las superiores)
    try:
        start_idx = DIFFICULTY_ORDER.index(data.typology)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Tipología inválida: {data.typology}")

    typologies_to_reset = DIFFICULTY_ORDER[start_idx:]

    deleted_sessions = 0
    deleted_notes = 0

    for typology in typologies_to_reset:
        # Obtener IDs de sesiones de esta tipología para el slot activo
        session_ids = [
            s.id for s in
            db.query(PlayerSession.id)
            .filter(
                PlayerSession.user_id == player_id,
                PlayerSession.slot_id == active_slot.id,
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

        # Borrar notas de lecturas de esta tipología en el slot activo
        reading_ids_of_typology = [
            r.id for r in
            db.query(Reading.id).filter(Reading.typology == typology).all()
        ]
        if reading_ids_of_typology:
            note_count = db.query(PlayerNote).filter(
                PlayerNote.user_id == player_id,
                PlayerNote.slot_id == active_slot.id,
                PlayerNote.reading_id.in_(reading_ids_of_typology),
            ).delete(synchronize_session=False)
            deleted_notes += note_count

        # Reiniciar progreso de tipología para el slot activo
        progress = (
            db.query(PlayerTypologyProgress)
            .filter(
                PlayerTypologyProgress.user_id == player_id,
                PlayerTypologyProgress.slot_id == active_slot.id,
                PlayerTypologyProgress.typology == typology,
            )
            .first()
        )
        if progress:
            progress.best_score = 0
            progress.total_sessions = 0
            progress.perfect_sessions = 0
            progress.attempts_used = 0
            progress.first_completed_at = None
            progress.last_played_at = None
            # La primera tipología (Narrativo) siempre queda desbloqueada
            if typology == "Narrativo":
                progress.is_unlocked = True
            else:
                progress.is_unlocked = False

    # Re-evaluar desbloqueos desde el principio para el slot activo
    reevaluate_unlocks(db, player_id, active_slot.id)

    # Incrementar versión de sesión para notificar al cliente Godot en tiempo real
    user.session_version += 1

    db.commit()

    return {
        "detail": "Progreso reiniciado en el slot activo",
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
    Reinicia TODO el progreso de un jugador en su SLOT ACTIVO.
    Borra sesiones, respuestas, herramientas, notas, logros y progreso.
    NO borra la cuenta ni el personaje.
    """
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Validar confirmación de borrado
    if not data.confirm_delete:
        raise HTTPException(
            status_code=400,
            detail="Debe confirmar explícitamente la eliminación permanente",
        )

    if data.confirm_email != user.email:
        raise HTTPException(
            status_code=400,
            detail="El email de confirmación no coincide con el jugador",
        )

    # Obtener slot activo
    active_slot = db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id, PlayerSlot.is_active == True).first()
    if not active_slot:
        raise HTTPException(status_code=400, detail="El jugador no tiene un slot de sesión activo")

    # Obtener IDs de sesiones del slot activo
    session_ids = [
        s.id for s in
        db.query(PlayerSession.id)
        .filter(PlayerSession.user_id == player_id, PlayerSession.slot_id == active_slot.id)
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
        PlayerNote.user_id == player_id,
        PlayerNote.slot_id == active_slot.id
    ).delete(synchronize_session=False)

    counts["achievements"] = db.query(PlayerAchievement).filter(
        PlayerAchievement.user_id == player_id,
        PlayerAchievement.slot_id == active_slot.id
    ).delete(synchronize_session=False)

    # Reiniciar progreso de tipologías del slot activo
    db.query(PlayerTypologyProgress).filter(
        PlayerTypologyProgress.user_id == player_id,
        PlayerTypologyProgress.slot_id == active_slot.id
    ).delete(synchronize_session=False)

    # Recrear progreso con solo Narrativo desbloqueado para el slot activo
    for typology in DIFFICULTY_ORDER:
        p = PlayerTypologyProgress(
            user_id=player_id,
            slot_id=active_slot.id,
            typology=typology,
            is_unlocked=(typology == "Narrativo"),
        )
        db.add(p)

    # Incrementar versión de sesión para notificar al cliente Godot en tiempo real
    user.session_version += 1

    db.commit()

    return {
        "detail": "Todo el progreso en el slot activo ha sido reiniciado",
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
    """Lista las sesiones de un jugador en su slot activo (vista admin)."""
    active_slot = db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id, PlayerSlot.is_active == True).first()
    if not active_slot:
        return []
    sesiones = _sesiones_del_slot(
        db, player_id, active_slot.id, limite=limit, typology=typology,
    )
    return [_sesion_a_dict(s) for s in sesiones]


# ── Notas de un jugador ─────────────────────────────────────────────────────

@router.get("/players/{player_id}/notes", response_model=List[dict])
def get_player_notes(
    player_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista las notas de un jugador para su slot activo."""
    # Obtener el slot activo del jugador
    active_slot = db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id, PlayerSlot.is_active == True).first()
    if not active_slot:
        return []

    results = (
        db.query(PlayerNote, Reading.title, Reading.typology)
        .join(Reading, PlayerNote.reading_id == Reading.id)
        .filter(PlayerNote.user_id == player_id, PlayerNote.slot_id == active_slot.id)
        .order_by(PlayerNote.created_at.desc())
        .all()
    )

    return [
        {
            "id": note.id,
            "reading_id": note.reading_id,
            "reading_title": title,
            "reading_typology": typology,
            "note_content": note.note_content,
            "note_type": note.note_type,
            "created_at": note.created_at.isoformat() if note.created_at else None,
        }
        for note, title, typology in results
    ]


# ── Gestión de Slots Administrativa ───────────────────────────────────────────

@router.get("/players/{player_id}/slots", response_model=List[PlayerSlotResponse])
def get_player_slots(
    player_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista todos los slots del jugador con el resumen de su progreso."""
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    slots = db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id).order_by(PlayerSlot.slot_number).all()

    result = []
    for slot in slots:
        # Calcular totales para este slot específico
        total_score = (
            db.query(sqlfunc.coalesce(sqlfunc.sum(PlayerTypologyProgress.best_score), 0))
            .filter(
                PlayerTypologyProgress.user_id == player_id,
                PlayerTypologyProgress.slot_id == slot.id,
                PlayerTypologyProgress.typology.in_(DIFFICULTY_ORDER),
            )
            .scalar()
        )
        total_sessions = (
            db.query(sqlfunc.count(PlayerSession.id))
            .filter(
                PlayerSession.user_id == player_id,
                PlayerSession.slot_id == slot.id,
            )
            .scalar()
        )
        total_achievements = (
            db.query(sqlfunc.count(PlayerAchievement.id))
            .filter(PlayerAchievement.user_id == player_id, PlayerAchievement.slot_id == slot.id)
            .scalar()
        )
        last_played = (
            db.query(sqlfunc.max(PlayerSession.completed_at))
            .filter(PlayerSession.user_id == player_id, PlayerSession.slot_id == slot.id)
            .scalar()
        )

        result.append(PlayerSlotResponse(
            id=slot.id,
            user_id=slot.user_id,
            slot_number=slot.slot_number,
            label=slot.label,
            is_active=slot.is_active,
            created_at=slot.created_at,
            created_by=slot.created_by,
            total_score=total_score or 0,
            total_sessions=total_sessions or 0,
            total_achievements=total_achievements or 0,
            last_played_at=last_played,
        ))

    return result


@router.post("/players/{player_id}/slots", response_model=PlayerSlotResponse, status_code=201)
def create_player_slot(
    player_id: int,
    data: PlayerSlotCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Crea un nuevo slot de sesión para el jugador (máximo 4 slots)."""
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Contar slots actuales
    slots_count = db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id).count()
    if slots_count >= 4:
        raise HTTPException(status_code=400, detail="El jugador ya tiene el límite de 4 slots de sesión")

    # Obtener el siguiente número de slot libre
    existing_numbers = [s.slot_number for s in db.query(PlayerSlot.slot_number).filter(PlayerSlot.user_id == player_id).all()]
    next_slot_number = 1
    for num in range(1, 5):
        if num not in existing_numbers:
            next_slot_number = num
            break

    # Desactivar todos los slots anteriores
    db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id).update({PlayerSlot.is_active: False})

    # Crear nuevo slot activo
    new_slot = PlayerSlot(
        user_id=player_id,
        slot_number=next_slot_number,
        label=data.label,
        is_active=True,
        created_by=admin.id
    )
    db.add(new_slot)

    # Incrementar versión de sesión para notificar al cliente Godot en tiempo real
    user.session_version += 1

    db.commit()
    db.refresh(new_slot)

    # Inicializar el progreso de tipologías del nuevo slot (Narrativo desbloqueado, resto bloqueado)
    for typology in DIFFICULTY_ORDER:
        progress = PlayerTypologyProgress(
            user_id=player_id,
            slot_id=new_slot.id,
            typology=typology,
            is_unlocked=(typology == "Narrativo"),
        )
        db.add(progress)
    db.commit()

    return PlayerSlotResponse(
        id=new_slot.id,
        user_id=new_slot.user_id,
        slot_number=new_slot.slot_number,
        label=new_slot.label,
        is_active=new_slot.is_active,
        created_at=new_slot.created_at,
        created_by=new_slot.created_by,
        total_score=0,
        total_sessions=0,
        total_achievements=0,
        last_played_at=None
    )


@router.put("/players/{player_id}/slots/{slot_number}/activate", response_model=dict)
def activate_player_slot(
    player_id: int,
    slot_number: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Activa un slot de sesión específico para el jugador, desactivando el resto."""
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Verificar existencia del slot
    slot = db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id, PlayerSlot.slot_number == slot_number).first()
    if not slot:
        raise HTTPException(status_code=404, detail=f"El slot número {slot_number} no existe para este jugador")

    # Desactivar todos los slots
    db.query(PlayerSlot).filter(PlayerSlot.user_id == player_id).update({PlayerSlot.is_active: False})

    # Activar el slot seleccionado
    slot.is_active = True

    # Incrementar versión de sesión para notificar al cliente Godot en tiempo real
    user.session_version += 1

    db.commit()

    return {"detail": f"Slot {slot_number} activado exitosamente", "active_slot": slot_number}


# ── Gestión de Contraseñas Administrativa ────────────────────────────────────

@router.post("/players/{player_id}/reset-password", response_model=dict)
def reset_player_password_admin(
    player_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Restablece la contraseña de un jugador y retorna una temporal."""
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Generar contraseña temporal segura
    temp_password = generate_temp_password()
    
    # Actualizar usuario
    user.hashed_password = hash_password(temp_password)
    user.must_change_password = True
    db.commit()
    db.refresh(user)

    return {
        "detail": "Contraseña restablecida exitosamente",
        "temp_password": temp_password
    }


# ── Lectura Activa (Admin) ───────────────────────────────────────────────

@router.delete("/players/{player_id}/active-reading", status_code=200)
def admin_clear_active_reading(
    player_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Permite al administrador limpiar la lectura activa (pendiente) de un jugador.
    Útil cuando un jugador quedó bloqueado con una lectura pendiente.
    Limpia el registro de todos los slots activos del jugador.
    """
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    deleted_count = (
        db.query(ActiveReading)
        .filter(ActiveReading.user_id == player_id)
        .delete(synchronize_session="fetch")
    )
    db.commit()

    return {
        "detail": f"Lectura activa eliminada" if deleted_count > 0 else "No había lectura activa",
        "deleted_count": deleted_count,
        "player_id": player_id,
        "player_email": user.email,
    }
