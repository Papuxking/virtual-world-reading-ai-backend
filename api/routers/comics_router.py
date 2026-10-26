"""
comics_router.py — Zona de cómics: endpoints del jugador.
Progreso de lectura por episodio y visitas a la sala, siempre del slot activo.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy import and_, case, distinct, func, or_, select
from sqlalchemy.orm import Session

from auth import get_current_admin, get_current_user
from database import get_db
from game_rules import DIFFICULTY_ORDER, pass_threshold
from models import ComicProgress, ComicZoneVisit, PlayerTypologyProgress, User
from routers.progress_router import _get_active_slot, _validate_slot_header
from schemas import (
    ComicJugadorResponse, ComicProgressList, ComicProgressResponse, ComicProgressSave,
    ComicResumenResponse, ComicVisitResponse,
)
from workspaces import get_viewed_workspace, ids_jugadores

router = APIRouter(prefix="/comics", tags=["Zona de cómics"])


@router.get("/progress", response_model=ComicProgressList)
def get_comic_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Progreso en cada episodio y visitas a la sala del slot activo."""
    slot = _get_active_slot(db, current_user.id)
    episodios = (
        db.query(ComicProgress)
        .filter(ComicProgress.user_id == current_user.id, ComicProgress.slot_id == slot.id)
        .order_by(ComicProgress.episode_id)
        .all()
    )
    visita = (
        db.query(ComicZoneVisit)
        .filter(ComicZoneVisit.user_id == current_user.id, ComicZoneVisit.slot_id == slot.id)
        .first()
    )
    return {"episodios": episodios, "visitas": visita.visits if visita else 0}


@router.put("/progress/{episode_id}", response_model=ComicProgressResponse)
def save_comic_progress(
    body: ComicProgressSave,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    episode_id: str = Path(..., max_length=20),
):
    """Crea o actualiza el progreso del jugador en un episodio."""
    slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, slot, current_user)
    fila = (
        db.query(ComicProgress)
        .filter(
            ComicProgress.user_id == current_user.id,
            ComicProgress.slot_id == slot.id,
            ComicProgress.episode_id == episode_id,
        )
        .first()
    )
    if fila is None:
        fila = ComicProgress(user_id=current_user.id, slot_id=slot.id, episode_id=episode_id)
        db.add(fila)
    fila.last_page = body.last_page
    fila.finished = body.finished
    fila.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(fila)
    return fila


@router.post("/visit", response_model=ComicVisitResponse)
def register_comic_visit(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cuenta una visita a la sala de cómics (crea la fila o la incrementa)."""
    slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, slot, current_user)
    visita = (
        db.query(ComicZoneVisit)
        .filter(ComicZoneVisit.user_id == current_user.id, ComicZoneVisit.slot_id == slot.id)
        .first()
    )
    if visita is None:
        visita = ComicZoneVisit(user_id=current_user.id, slot_id=slot.id, visits=1)
        db.add(visita)
    else:
        visita.visits += 1
        visita.last_visit_at = datetime.now(timezone.utc)
    db.commit()
    return {"visitas": visita.visits}


# ── Dashboard (solo administradores, acotado al entorno que se mira) ─────────

EPISODIOS_TOP = 5


def _aprobo_las_cuatro():
    """Condición SQL «tipología aprobada»: el mismo umbral que progression.aprobada
    (pass_threshold), expresado como filtro para contar en la base."""
    return or_(*[
        and_(PlayerTypologyProgress.typology == t,
             PlayerTypologyProgress.best_score >= pass_threshold(t))
        for t in DIFFICULTY_ORDER
    ])


@router.get("/admin/resumen", response_model=ComicResumenResponse)
def resumen_comics(
    _admin: User = Depends(get_current_admin),
    entorno=Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Cuántos alumnos del entorno desbloquearon la zona, entraron y leyeron."""
    jugadores = ids_jugadores(entorno.id)
    # Un jugador desbloquea si en algún slot tiene aprobadas las cuatro tipologías.
    completos = (
        select(PlayerTypologyProgress.user_id)
        .where(PlayerTypologyProgress.user_id.in_(jugadores), _aprobo_las_cuatro())
        .group_by(PlayerTypologyProgress.user_id, PlayerTypologyProgress.slot_id)
        .having(func.count(distinct(PlayerTypologyProgress.typology)) == len(DIFFICULTY_ORDER))
        .subquery()
    )
    desbloquearon = db.query(func.count(distinct(completos.c.user_id))).scalar() or 0
    entraron = (
        db.query(func.count(distinct(ComicZoneVisit.user_id)))
        .filter(ComicZoneVisit.user_id.in_(jugadores)).scalar() or 0
    )
    lectores = (
        db.query(func.count(distinct(ComicProgress.user_id)))
        .filter(ComicProgress.user_id.in_(jugadores)).scalar() or 0
    )
    lecturas = func.count(distinct(ComicProgress.user_id)).label("lecturas")
    top = (
        db.query(ComicProgress.episode_id, lecturas)
        .filter(ComicProgress.user_id.in_(jugadores))
        .group_by(ComicProgress.episode_id)
        .order_by(lecturas.desc(), ComicProgress.episode_id)
        .limit(EPISODIOS_TOP)
        .all()
    )
    return {
        "desbloquearon": desbloquearon,
        "entraron": entraron,
        "lectores": lectores,
        "episodios_top": [{"episode_id": e, "lecturas": n} for e, n in top],
    }


@router.get("/admin/jugadores", response_model=list[ComicJugadorResponse])
def jugadores_comics(
    _admin: User = Depends(get_current_admin),
    entorno=Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Alumnos del entorno que entraron a la zona o leyeron algún episodio."""
    lectura = (
        db.query(
            ComicProgress.user_id.label("user_id"),
            func.sum(case((ComicProgress.finished.is_(True), 1), else_=0)).label("terminados"),
            func.sum(ComicProgress.last_page).label("paginas"),
        )
        .group_by(ComicProgress.user_id)
        .subquery()
    )
    visitas = (
        db.query(
            ComicZoneVisit.user_id.label("user_id"),
            func.max(ComicZoneVisit.last_visit_at).label("ultima"),
        )
        .group_by(ComicZoneVisit.user_id)
        .subquery()
    )
    filas = (
        db.query(
            User.id, User.display_name, User.email,
            func.coalesce(lectura.c.terminados, 0),
            func.coalesce(lectura.c.paginas, 0),
            visitas.c.ultima,
        )
        .outerjoin(lectura, lectura.c.user_id == User.id)
        .outerjoin(visitas, visitas.c.user_id == User.id)
        .filter(
            User.id.in_(ids_jugadores(entorno.id)),
            or_(lectura.c.user_id.isnot(None), visitas.c.user_id.isnot(None)),
        )
        .order_by(func.coalesce(lectura.c.paginas, 0).desc(), User.display_name)
        .all()
    )
    return [
        {"player_id": i, "display_name": nombre, "email": email,
         "episodios_terminados": int(t), "paginas_leidas": int(p), "ultima_visita": u}
        for i, nombre, email, t, p, u in filas
    ]
