"""Encuesta SUS + TAM que el alumno completa antes de abrir los cómics."""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import get_current_admin, get_current_user
from database import get_db
from game_rules import DIFFICULTY_ORDER, pass_threshold
from models import PlayerSlot, PlayerTypologyProgress, TechnologySurveyResponse, User
from routers.progress_router import _get_active_slot, _validate_slot_header
from schemas import (
    TechnologySurveyAdminRow, TechnologySurveyAdminSummary, TechnologySurveyResult,
    TechnologySurveyStatus, TechnologySurveySubmit,
)
from workspaces import get_viewed_workspace, ids_jugadores

router = APIRouter(prefix="/evaluation", tags=["Encuesta SUS + TAM"])

INSTRUMENT_VERSION = "sus10_tam12_v1"


def _tipologia_aprobada():
    return or_(*[
        and_(PlayerTypologyProgress.typology == t,
             PlayerTypologyProgress.best_score >= pass_threshold(t))
        for t in DIFFICULTY_ORDER
    ])


def _slot_habilitado(db: Session, user_id: int, slot_id: int) -> bool:
    total = (
        db.query(func.count(distinct(PlayerTypologyProgress.typology)))
        .filter(
            PlayerTypologyProgress.user_id == user_id,
            PlayerTypologyProgress.slot_id == slot_id,
            _tipologia_aprobada(),
        )
        .scalar()
    ) or 0
    return total == len(DIFFICULTY_ORDER)


def _resultado(fila: TechnologySurveyResponse) -> dict:
    return {
        "completed": True,
        "submitted_at": fila.submitted_at,
        "instrument_version": fila.instrument_version,
        "sus_score": fila.sus_score,
        "tam_usefulness_score": fila.tam_usefulness_score,
        "tam_ease_score": fila.tam_ease_score,
    }


def _valores(fila: TechnologySurveyResponse, prefijo: str, cantidad: int) -> list[int]:
    return [getattr(fila, f"{prefijo}_{i}") for i in range(1, cantidad + 1)]


@router.get("/survey/status", response_model=TechnologySurveyStatus)
def survey_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Indica si el slot activo ya respondió; valida también sesión y slot."""
    slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, slot, current_user)
    fila = db.query(TechnologySurveyResponse).filter_by(
        user_id=current_user.id, slot_id=slot.id).first()
    return {"completed": fila is not None, "submitted_at": fila.submitted_at if fila else None}


@router.post("/survey", response_model=TechnologySurveyResult)
def submit_survey(
    body: TechnologySurveySubmit,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Guarda una sola respuesta cuando las cuatro tipologías están aprobadas.

    Es idempotente: un reintento tras una respuesta HTTP perdida devuelve la
    fila original, pero nunca la modifica.
    """
    slot = _get_active_slot(db, current_user.id)
    _validate_slot_header(request, slot, current_user)
    existente = db.query(TechnologySurveyResponse).filter_by(
        user_id=current_user.id, slot_id=slot.id).first()
    if existente:
        return _resultado(existente)
    if not _slot_habilitado(db, current_user.id, slot.id):
        raise HTTPException(status_code=403, detail="SURVEY_NOT_AVAILABLE")

    sus_score = sum(
        (valor - 1) if i % 2 == 1 else (5 - valor)
        for i, valor in enumerate(body.sus, start=1)
    ) * 2.5
    datos = {
        "user_id": current_user.id,
        "slot_id": slot.id,
        "instrument_version": INSTRUMENT_VERSION,
        "sus_score": sus_score,
        "tam_usefulness_score": round(sum(body.tam_usefulness) / 6, 2),
        "tam_ease_score": round(sum(body.tam_ease) / 6, 2),
    }
    datos.update({f"sus_{i}": v for i, v in enumerate(body.sus, start=1)})
    datos.update({f"tam_pu_{i}": v for i, v in enumerate(body.tam_usefulness, start=1)})
    datos.update({f"tam_peou_{i}": v for i, v in enumerate(body.tam_ease, start=1)})
    fila = TechnologySurveyResponse(**datos)
    db.add(fila)
    try:
        db.commit()
        db.refresh(fila)
    except IntegrityError:
        # Dos clics o un reintento concurrente: conservar siempre la primera.
        db.rollback()
        fila = db.query(TechnologySurveyResponse).filter_by(
            user_id=current_user.id, slot_id=slot.id).one()
    return _resultado(fila)


def _filas_entorno(db: Session, workspace_id: int):
    return (
        db.query(TechnologySurveyResponse, User, PlayerSlot)
        .join(User, User.id == TechnologySurveyResponse.user_id)
        .join(PlayerSlot, PlayerSlot.id == TechnologySurveyResponse.slot_id)
        .filter(TechnologySurveyResponse.user_id.in_(ids_jugadores(workspace_id)))
        .order_by(TechnologySurveyResponse.submitted_at.desc(), User.display_name)
        .all()
    )


def _fila_admin(encuesta, usuario, slot) -> dict:
    return {
        "player_id": usuario.id,
        "display_name": usuario.display_name,
        "email": usuario.email,
        "slot_number": slot.slot_number,
        "slot_label": slot.label,
        "instrument_version": encuesta.instrument_version,
        "sus": _valores(encuesta, "sus", 10),
        "tam_usefulness": _valores(encuesta, "tam_pu", 6),
        "tam_ease": _valores(encuesta, "tam_peou", 6),
        "sus_score": encuesta.sus_score,
        "tam_usefulness_score": encuesta.tam_usefulness_score,
        "tam_ease_score": encuesta.tam_ease_score,
        "submitted_at": encuesta.submitted_at,
    }


@router.get("/admin/responses", response_model=list[TechnologySurveyAdminRow])
def admin_responses(
    _admin: User = Depends(get_current_admin),
    entorno=Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    return [_fila_admin(*fila) for fila in _filas_entorno(db, entorno.id)]


@router.get("/admin/summary", response_model=TechnologySurveyAdminSummary)
def admin_summary(
    _admin: User = Depends(get_current_admin),
    entorno=Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    jugadores = ids_jugadores(entorno.id)
    elegibles = (
        select(PlayerTypologyProgress.user_id, PlayerTypologyProgress.slot_id)
        .where(PlayerTypologyProgress.user_id.in_(jugadores), _tipologia_aprobada())
        .group_by(PlayerTypologyProgress.user_id, PlayerTypologyProgress.slot_id)
        .having(func.count(distinct(PlayerTypologyProgress.typology)) == len(DIFFICULTY_ORDER))
        .subquery()
    )
    eligible_pairs = set(db.query(elegibles.c.user_id, elegibles.c.slot_id).all())
    filas_completas = _filas_entorno(db, entorno.id)
    filas = [f[0] for f in filas_completas]
    # Una respuesta prueba que ese slot fue elegible al enviarla. Si luego un
    # administrador reinicia el progreso, no debe desaparecer del denominador
    # ni producir una tasa superior al 100 %.
    responded_pairs = {(f.user_id, f.slot_id) for f in filas}
    eligible_slots = len(eligible_pairs | responded_pairs)
    responses = len(filas)
    distribuciones = {}
    for prefijo, cantidad, escala in (("sus", 10, 5), ("tam_pu", 6, 7), ("tam_peou", 6, 7)):
        for i in range(1, cantidad + 1):
            valores = [getattr(f, f"{prefijo}_{i}") for f in filas]
            distribuciones[f"{prefijo}_{i}"] = [valores.count(v) for v in range(1, escala + 1)]
    promedio = lambda campo: round(sum(getattr(f, campo) for f in filas) / responses, 2) if filas else None
    return {
        "eligible_slots": eligible_slots,
        "responses": responses,
        "response_rate": round((responses / eligible_slots * 100), 2) if eligible_slots else 0.0,
        "sus_average": promedio("sus_score"),
        "tam_usefulness_average": promedio("tam_usefulness_score"),
        "tam_ease_average": promedio("tam_ease_score"),
        "item_distributions": distribuciones,
    }


@router.get("/admin/export.csv")
def admin_export_csv(
    _admin: User = Depends(get_current_admin),
    entorno=Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    salida = io.StringIO()
    salida.write("\ufeff")
    campos = ["player_id", "display_name", "email", "slot_number", "slot_label",
              "instrument_version", "submitted_at", "sus_score",
              "tam_usefulness_score", "tam_ease_score"]
    campos += [f"sus_{i}" for i in range(1, 11)]
    campos += [f"tam_pu_{i}" for i in range(1, 7)]
    campos += [f"tam_peou_{i}" for i in range(1, 7)]
    writer = csv.DictWriter(salida, fieldnames=campos)
    writer.writeheader()
    for encuesta, usuario, slot in _filas_entorno(db, entorno.id):
        fila = _fila_admin(encuesta, usuario, slot)
        fila["submitted_at"] = encuesta.submitted_at.isoformat()
        sus = fila.pop("sus")
        pu = fila.pop("tam_usefulness")
        peou = fila.pop("tam_ease")
        fila.update({f"sus_{i}": v for i, v in enumerate(sus, 1)})
        fila.update({f"tam_pu_{i}": v for i, v in enumerate(pu, 1)})
        fila.update({f"tam_peou_{i}": v for i, v in enumerate(peou, 1)})
        writer.writerow(fila)
    return StreamingResponse(
        iter([salida.getvalue()]), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=encuesta_sus_tam.csv"},
    )
