"""
comics_router.py — Zona de cómics: endpoints del jugador.
Progreso de lectura por episodio y visitas a la sala, siempre del slot activo.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ComicProgress, ComicZoneVisit, User
from routers.progress_router import _get_active_slot, _validate_slot_header
from schemas import (
    ComicProgressList, ComicProgressResponse, ComicProgressSave, ComicVisitResponse,
)

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
    episode_id: str,
    body: ComicProgressSave,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
