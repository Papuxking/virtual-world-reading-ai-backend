"""
progress_router.py — Endpoints de progreso del jugador.
Registrar sesiones, logros, notas y consultar progreso completo.
Todos los endpoints requieren autenticación JWT y se segmentan por el slot activo del jugador.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc

from database import get_db
from models import (
    User, PlayerSession, PlayerAnswer, SessionTool,
    PlayerNote, PlayerTypologyProgress, PlayerAchievement, Reading, Question,
    PlayerSlot, AchievementCatalog, NpcInteraction, ActiveReading,
)
from schemas import (
    MedalResponse, PerfilJugador,
    SessionCreate, SessionResponse, NoteCreate, NoteResponse,
    AchievementCreate, AchievementResponse, TypologyProgressResponse,
    PlayerProgressResponse, UserResponse,
    AchievementFullResponse, NpcInteractionCreate, NpcInteractionResponse,
    ActiveReadingSave, ActiveReadingResponse, ReadingFullResponse,
)
from game_rules import DIFFICULTY_ORDER, MAX_INTENTOS_POR_TIPOLOGIA
from progression import agotada, ensure_typology_rows, juego_terminado, reevaluate_unlocks
from auth import get_current_user
from medallas import medallas_del_jugador
from alias import ALIAS_POR_ID
from perfiles import progreso_del_slot, elementos_desbloqueados

router = APIRouter(prefix="/progress", tags=["Progreso del Jugador"])


def _get_active_slot(db: Session, user_id: int) -> PlayerSlot:
    """Helper para obtener el slot activo del jugador, creándolo si no existe."""
    slot = db.query(PlayerSlot).filter(PlayerSlot.user_id == user_id, PlayerSlot.is_active == True).first()
    if not slot:
        slot = PlayerSlot(
            user_id=user_id,
            slot_number=1,
            label="Sesión 1",
            is_active=True
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)
    return slot


def _validate_slot_header(request: Request, active_slot: PlayerSlot, user: User):
    """Valida si el slot y versión de sesión enviados coinciden con los del usuario."""
    client_slot_id_str = request.headers.get("X-Slot-Id")
    if client_slot_id_str:
        try:
            client_slot_id = int(client_slot_id_str)
            if client_slot_id != active_slot.id:
                raise HTTPException(
                    status_code=409,
                    detail="SESSION_INVALIDATED"
                )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid X-Slot-Id header format"
            )

    client_version_str = request.headers.get("X-Session-Version")
    if client_version_str:
        try:
            client_version = int(client_version_str)
            if client_version != user.session_version:
                raise HTTPException(
                    status_code=409,
                    detail="SESSION_INVALIDATED"
                )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid X-Session-Version header format"
            )


def _aciertos_por_nivel(db: Session, user_id: int, slot_id: int) -> dict:
    """Respuestas correctas del slot por nivel de comprensión.
    Siempre con los 3 niveles del juego; un nivel desconocido no cuenta."""
    aciertos = {"Literal": 0, "Inferencial": 0, "Critico": 0}
    filas = (
        db.query(PlayerAnswer.comprehension_level, sqlfunc.count(PlayerAnswer.id))
        .join(PlayerSession, PlayerAnswer.session_id == PlayerSession.id)
        .filter(
            PlayerSession.user_id == user_id,
            PlayerSession.slot_id == slot_id,
            PlayerAnswer.is_correct == True,
        )
        .group_by(PlayerAnswer.comprehension_level)
        .all()
    )
    for nivel, cantidad in filas:
        clave = (nivel or "").replace("í", "i").replace("Í", "I").capitalize()
        if clave in aciertos:
            aciertos[clave] += cantidad
    return aciertos


# ── Progreso Completo ────────────────────────────────────────────────────────

@router.get("/me", response_model=PlayerProgressResponse)
def get_my_progress(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna el progreso completo del jugador autenticado en su slot activo."""
    active_slot = _get_active_slot(db, current_user.id)
    # Sin esta validacion una sesion ya expulsada volvia a la vida: al pedir el
    # progreso adoptaba el session_version nuevo que viene en la respuesta y
    # pasaba de nuevo los controles de escritura.
    _validate_slot_header(request, active_slot, current_user)

    # Progreso de las tipologías del juego; se crean las filas que falten.
    typology_rows = ensure_typology_rows(db, current_user.id, active_slot.id)
    db.commit()

    total_score = sum(tp.best_score for tp in typology_rows)

    # Logros del slot activo
    achievements = (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.user_id == current_user.id, PlayerAchievement.slot_id == active_slot.id)
        .order_by(PlayerAchievement.unlocked_at)
        .all()
    )

    # Últimas 10 sesiones de progresión del slot activo
    recent_sessions = (
        db.query(PlayerSession)
        .options(
            joinedload(PlayerSession.answers),
            joinedload(PlayerSession.tools),
        )
        .filter(
            PlayerSession.user_id == current_user.id,
            PlayerSession.slot_id == active_slot.id,
        )
        .order_by(PlayerSession.completed_at.desc())
        .limit(10)
        .all()
    )

    return PlayerProgressResponse(
        user=UserResponse.model_validate(current_user),
        active_slot_id=active_slot.id,
        total_score=total_score,
        max_attempts=MAX_INTENTOS_POR_TIPOLOGIA,
        game_over=juego_terminado(typology_rows),
        correct_by_level=_aciertos_por_nivel(db, current_user.id, active_slot.id),
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


# ── Lectura siguiente ────────────────────────────────────────────────────────

def _elegir_lectura(db: Session, user_id: int, slot_id: int, typology: str) -> Optional[int]:
    """Lectura de progresión de la tipología que el alumno aún no ha terminado
    en este slot, al azar. Si ya las terminó todas, la que lleva más tiempo sin
    leerse. Nunca la que tiene a medias, salvo que no quede otra."""
    activa = (
        db.query(ActiveReading.reading_id)
        .filter(ActiveReading.user_id == user_id, ActiveReading.slot_id == slot_id)
        .scalar()
    )
    candidatas = db.query(Reading.id).filter(Reading.typology == typology)
    if activa is not None:
        candidatas = candidatas.filter(Reading.id != activa)

    # Última vez que terminó cada lectura de la tipología en este slot.
    ultima_vez = (
        db.query(
            PlayerSession.reading_id.label("reading_id"),
            sqlfunc.max(PlayerSession.completed_at).label("ultima"),
        )
        .filter(
            PlayerSession.user_id == user_id,
            PlayerSession.slot_id == slot_id,
            PlayerSession.typology == typology,
        )
        .group_by(PlayerSession.reading_id)
        .subquery()
    )

    sin_leer = (
        candidatas.outerjoin(ultima_vez, ultima_vez.c.reading_id == Reading.id)
        .filter(ultima_vez.c.reading_id.is_(None))
        .order_by(sqlfunc.random())
        .first()
    )
    if sin_leer:
        return sin_leer[0]

    mas_antigua = (
        candidatas.join(ultima_vez, ultima_vez.c.reading_id == Reading.id)
        .order_by(ultima_vez.c.ultima.asc())
        .first()
    )
    if mas_antigua:
        return mas_antigua[0]
    return activa


@router.get("/next-reading", response_model=ReadingFullResponse)
def get_next_reading(
    request: Request,
    typology: str = Query(..., description="Tipología de la progresión"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lectura de progresión que toca en una tipología: sin repetir las que el
    alumno ya terminó y nunca si se quedó sin intentos (403 SIN_INTENTOS, no
    409: el juego trata el 409 como sesión invalidada)."""
    if typology not in DIFFICULTY_ORDER:
        raise HTTPException(status_code=400, detail=f"Tipología fuera de la progresión: {typology}")

    active_slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, active_slot, current_user)

    filas = {f.typology: f for f in ensure_typology_rows(db, current_user.id, active_slot.id)}
    db.commit()
    if agotada(filas[typology]):
        raise HTTPException(status_code=403, detail="SIN_INTENTOS")

    reading_id = _elegir_lectura(db, current_user.id, active_slot.id, typology)
    if reading_id is None:
        raise HTTPException(status_code=404, detail="No hay lecturas de esta tipología")

    return (
        db.query(Reading)
        .options(joinedload(Reading.questions).joinedload(Question.answers))
        .filter(Reading.id == reading_id)
        .first()
    )


# ── Sesiones ─────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    data: SessionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra una sesión completada desde Godot en el slot activo."""
    active_slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, active_slot, current_user)

    # Un juego viejo puede mandar la sesión de una lectura que ya no existe
    # (las de la práctica se borraron): sin esto la base la rechaza con un 500.
    if db.get(Reading, data.reading_id) is None:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")

    # Crear la sesión vinculada al slot activo
    session = PlayerSession(
        user_id=current_user.id,
        slot_id=active_slot.id,
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

    # Una tipología que ya no es del juego (solo puede llegar de un cliente
    # antiguo) se guarda, pero no toca el progreso.
    if data.typology in DIFFICULTY_ORDER:
        _registrar_progreso(db, current_user.id, active_slot.id, data)

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


def _registrar_progreso(db: Session, user_id: int, slot_id: int, data: SessionCreate) -> None:
    """Suma la sesión al progreso de su tipología y desbloquea la siguiente si toca."""
    ensure_typology_rows(db, user_id, slot_id)
    progress = (
        db.query(PlayerTypologyProgress)
        .filter(
            PlayerTypologyProgress.user_id == user_id,
            PlayerTypologyProgress.slot_id == slot_id,
            PlayerTypologyProgress.typology == data.typology,
        )
        .one()
    )
    ahora = datetime.now(timezone.utc)
    # Una tipología que se acaba de jugar está, por definición, abierta.
    progress.is_unlocked = True
    progress.total_sessions += 1
    # Cada lectura terminada gasta un intento, apruebe o no.
    progress.attempts_used = (progress.attempts_used or 0) + 1
    progress.best_score = max(progress.best_score, data.session_score)
    progress.last_played_at = ahora
    if progress.first_completed_at is None:
        progress.first_completed_at = ahora
    if data.is_perfect:
        progress.perfect_sessions += 1
    reevaluate_unlocks(db, user_id, slot_id, only_unlock=True)


@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(
    typology: str = Query(None, description="Filtrar por tipología"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista el historial de sesiones del jugador autenticado en su slot activo."""
    active_slot = _get_active_slot(db, current_user.id)

    query = (
        db.query(PlayerSession)
        .options(
            joinedload(PlayerSession.answers),
            joinedload(PlayerSession.tools),
        )
        .filter(
            PlayerSession.user_id == current_user.id,
            PlayerSession.slot_id == active_slot.id,
        )
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
    """Retorna el progreso del jugador en cada tipología del juego (slot activo)."""
    active_slot = _get_active_slot(db, current_user.id)
    rows = ensure_typology_rows(db, current_user.id, active_slot.id)
    db.commit()
    return rows


# ── Logros ───────────────────────────────────────────────────────────────────

@router.post("/achievements", response_model=AchievementResponse, status_code=201)
def register_achievement(
    data: AchievementCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra un logro desbloqueado en el slot activo (idempotente)."""
    active_slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, active_slot, current_user)

    existing = (
        db.query(PlayerAchievement)
        .filter(
            PlayerAchievement.user_id == current_user.id,
            PlayerAchievement.slot_id == active_slot.id,
            PlayerAchievement.achievement_id == data.achievement_id,
        )
        .first()
    )
    if existing:
        return existing

    achievement = PlayerAchievement(
        user_id=current_user.id,
        slot_id=active_slot.id,
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
    """Lista todos los logros del jugador autenticado en su slot activo."""
    active_slot = _get_active_slot(db, current_user.id)

    return (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.user_id == current_user.id, PlayerAchievement.slot_id == active_slot.id)
        .order_by(PlayerAchievement.unlocked_at)
        .all()
    )


# ── Notas ────────────────────────────────────────────────────────────────────

@router.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(
    data: NoteCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Guarda una nota/apunte del jugador asociada a una lectura en el slot activo."""
    # Verificar que la lectura existe
    reading = db.query(Reading).filter(Reading.id == data.reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")

    active_slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, active_slot, current_user)

    note = PlayerNote(
        user_id=current_user.id,
        slot_id=active_slot.id,
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
    """Lista las notas del jugador autenticado en su slot activo."""
    active_slot = _get_active_slot(db, current_user.id)

    query = (
        db.query(PlayerNote, Reading.title)
        .join(Reading, PlayerNote.reading_id == Reading.id)
        .filter(PlayerNote.user_id == current_user.id, PlayerNote.slot_id == active_slot.id)
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


@router.get("/validate-session")
def validate_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint liviano para el polling periódico (heartbeat) de Godot.
    Verifica si el slot_id en memoria del cliente coincide con el slot activo actual del usuario.
    """
    active_slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, active_slot, current_user)
    return {"status": "ok", "active_slot_id": active_slot.id, "slot_number": active_slot.slot_number}


@router.get("/achievements-full", response_model=List[AchievementFullResponse])
def get_achievements_full(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna la lista completa de logros y medallas en el catálogo global,
    cruzada con el estado de desbloqueo del jugador en su slot activo.
    """
    active_slot = _get_active_slot(db, current_user.id)

    # 1. Obtener catálogo completo de logros activos
    catalog = (
        db.query(AchievementCatalog)
        .filter(AchievementCatalog.is_active == True)
        .order_by(AchievementCatalog.display_order.asc())
        .all()
    )

    # 2. Obtener logros desbloqueados por el jugador en este slot
    unlocked = (
        db.query(PlayerAchievement)
        .filter(
            PlayerAchievement.user_id == current_user.id,
            PlayerAchievement.slot_id == active_slot.id
        )
        .all()
    )
    unlocked_map = {a.achievement_id: a for a in unlocked}

    # 3. Cruzar datos
    result = []
    for item in catalog:
        unlocked_record = unlocked_map.get(item.id)
        is_unlocked = unlocked_record is not None
        unlocked_at = unlocked_record.unlocked_at if is_unlocked else None

        # Construir URL de la medalla si existe path
        medal_url = None
        if item.medal_image_path:
            # medal_image_path ya almacena la ruta completa: /static/medals/xxx.png?v=...
            medal_url = item.medal_image_path

        result.append(AchievementFullResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            how_to_unlock=item.how_to_unlock,
            category=item.category,
            icon=item.icon,
            medal_name=item.medal_name,
            medal_tier=item.medal_tier,
            medal_description=item.medal_description,
            medal_image_path=medal_url,
            medal_placeholder_emoji=item.medal_placeholder_emoji,
            is_unlocked=is_unlocked,
            unlocked_at=unlocked_at
        ))

    return result


# ── Medallas ─────────────────────────────────────────────────────────────────

@router.get("/medals", response_model=List[MedalResponse])
def get_my_medals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Medallas por desempeño del slot activo (ver medallas.py)."""
    active_slot = _get_active_slot(db, current_user.id)
    filas = ensure_typology_rows(db, current_user.id, active_slot.id)
    db.commit()
    return medallas_del_jugador(filas)


# ── Interacciones NPC ────────────────────────────────────────────────────────

@router.post("/npc-interaction", response_model=NpcInteractionResponse, status_code=201)
def register_npc_interaction(
    data: NpcInteractionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Registra una interacción del jugador con un NPC (robot o sabio)."""
    if data.npc_type not in ("robot", "sabio"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="npc_type debe ser 'robot' o 'sabio'")

    active_slot = _get_active_slot(db, current_user.id)

    interaction = NpcInteraction(
        user_id=current_user.id,
        slot_id=active_slot.id,
        npc_type=data.npc_type,
        session_id=data.session_id,
        reading_id=data.reading_id,
        user_message=data.user_message,
        assistant_reply=data.assistant_reply,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return interaction


# ── Lectura Activa (Progreso en curso) ────────────────────────────────────────

@router.get("/active-reading", response_model=ActiveReadingResponse)
def get_active_reading(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna la lectura activa (en progreso) del jugador en su slot activo.
    Si no hay lectura activa, retorna 204 No Content. No caduca: con intentos
    limitados, perderla le daría al alumno otra lectura gratis.
    Si la lectura referenciada fue eliminada de la BD, limpia automáticamente.
    """
    active_slot = _get_active_slot(db, current_user.id)

    record = (
        db.query(ActiveReading)
        .filter(
            ActiveReading.user_id == current_user.id,
            ActiveReading.slot_id == active_slot.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=204)

    # Verificar que la lectura referenciada aún existe en la BD
    reading_exists = db.query(Reading).filter(Reading.id == record.reading_id).first()
    if not reading_exists:
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=204)

    return record


@router.put("/active-reading", response_model=ActiveReadingResponse)
def save_active_reading(
    data: ActiveReadingSave,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Guarda o actualiza la lectura activa del jugador.
    Usa upsert: si ya existe un registro para este usuario/slot, lo actualiza.
    No caduca (expires_at queda vacío): se borra al terminar la lectura.
    """
    active_slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, active_slot, current_user)

    # Verificar que la lectura existe
    reading = db.query(Reading).filter(Reading.id == data.reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")

    # Buscar registro existente (upsert)
    record = (
        db.query(ActiveReading)
        .filter(
            ActiveReading.user_id == current_user.id,
            ActiveReading.slot_id == active_slot.id,
        )
        .first()
    )

    now = datetime.now(timezone.utc)

    if record:
        # Actualizar existente
        record.reading_id = data.reading_id
        record.typology = data.typology
        record.current_level_index = data.current_level_index
        record.current_question_index = data.current_question_index
        record.reading_completed = data.reading_completed
        record.session_score = data.session_score
        record.results_json = data.results_json
        record.tools_used_json = data.tools_used_json
        record.reading_start_time = data.reading_start_time
        record.reading_seconds = data.reading_seconds
        record.total_seconds = data.total_seconds
        record.updated_at = now
        record.expires_at = None
    else:
        # Crear nuevo
        record = ActiveReading(
            user_id=current_user.id,
            slot_id=active_slot.id,
            reading_id=data.reading_id,
            typology=data.typology,
            current_level_index=data.current_level_index,
            current_question_index=data.current_question_index,
            reading_completed=data.reading_completed,
            session_score=data.session_score,
            results_json=data.results_json,
            tools_used_json=data.tools_used_json,
            reading_start_time=data.reading_start_time,
            reading_seconds=data.reading_seconds,
            total_seconds=data.total_seconds,
            expires_at=None,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/active-reading", status_code=204)
def clear_active_reading(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Limpia la lectura activa del jugador.
    Llamar cuando completa la sesión o elige explícitamente iniciar una nueva.
    """
    active_slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, active_slot, current_user)

    record = (
        db.query(ActiveReading)
        .filter(
            ActiveReading.user_id == current_user.id,
            ActiveReading.slot_id == active_slot.id,
        )
        .first()
    )

    if record:
        db.delete(record)
        db.commit()

    return None


@router.get("/profile", response_model=PerfilJugador)
def obtener_perfil(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, slot, current_user)
    return PerfilJugador(alias=slot.alias, vitrina=slot.vitrina)


@router.put("/profile", response_model=PerfilJugador)
def guardar_perfil(
    data: PerfilJugador,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, slot, current_user)
    filas = progreso_del_slot(db, slot)
    if data.alias is not None:
        elegido = ALIAS_POR_ID.get(data.alias)
        if elegido is None:
            raise HTTPException(status_code=422, detail="El alias no existe")
        lecturas = sum(fila.total_sessions or 0 for fila in filas)
        if lecturas < elegido["lecturas"]:
            raise HTTPException(
                status_code=422,
                detail=f"El alias {elegido['nombre']} requiere {elegido['lecturas']} lecturas completadas",
            )
    desbloqueados = elementos_desbloqueados(db, slot, filas)
    for item in data.vitrina:
        if (item.tipo, item.id) not in desbloqueados:
            raise HTTPException(
                status_code=422, detail=f"No has desbloqueado {item.tipo}: {item.id} en esta partida",
            )
    slot.alias = data.alias
    slot.vitrina = [item.model_dump() for item in data.vitrina]
    db.commit()
    db.refresh(slot)
    return PerfilJugador(alias=slot.alias, vitrina=slot.vitrina)
