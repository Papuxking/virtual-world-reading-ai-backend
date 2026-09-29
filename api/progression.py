"""
progression.py — Operaciones de progreso compartidas por la API y los scripts.

Las reglas (orden, umbrales, máximo) viven en game_rules.py; aquí solo se
aplican sobre la base de datos.
"""
from sqlalchemy.orm import Session

from game_rules import DIFFICULTY_ORDER, UNLOCK_THRESHOLDS
from models import PlayerTypologyProgress


def _filas_del_slot(db: Session, user_id: int, slot_id: int) -> dict:
    """Filas de progreso de las tipologías del juego, indexadas por tipología."""
    filas = (
        db.query(PlayerTypologyProgress)
        .filter(
            PlayerTypologyProgress.user_id == user_id,
            PlayerTypologyProgress.slot_id == slot_id,
            PlayerTypologyProgress.typology.in_(DIFFICULTY_ORDER),
        )
        .all()
    )
    return {f.typology: f for f in filas}


def ensure_typology_rows(db: Session, user_id: int, slot_id: int) -> list:
    """Garantiza una fila de progreso por cada tipología del juego en el slot.

    Devuelve las filas en el orden de dificultad. Las que faltan se crean con
    solo la primera tipología abierta. No toca filas de tipologías retiradas:
    eso lo hace la migración.
    """
    por_tipologia = _filas_del_slot(db, user_id, slot_id)
    for i, tipologia in enumerate(DIFFICULTY_ORDER):
        if tipologia not in por_tipologia:
            fila = PlayerTypologyProgress(
                user_id=user_id,
                slot_id=slot_id,
                typology=tipologia,
                is_unlocked=(i == 0),
            )
            db.add(fila)
            por_tipologia[tipologia] = fila
    db.flush()
    return [por_tipologia[t] for t in DIFFICULTY_ORDER]


def reevaluate_unlocks(db: Session, user_id: int, slot_id: int, only_unlock: bool = False) -> None:
    """Recalcula qué tipologías del slot están abiertas según la anterior.

    Con only_unlock=True nunca bloquea. Así la usan la migración y el registro
    de sesiones, para no quitar a nadie una tipología que ya tenía abierta.
    """
    por_tipologia = _filas_del_slot(db, user_id, slot_id)
    for i, tipologia in enumerate(DIFFICULTY_ORDER):
        fila = por_tipologia.get(tipologia)
        if fila is None:
            continue
        if i == 0:
            fila.is_unlocked = True
            continue
        anterior = por_tipologia.get(DIFFICULTY_ORDER[i - 1])
        alcanza = anterior is not None and anterior.best_score >= UNLOCK_THRESHOLDS[tipologia]
        if alcanza:
            fila.is_unlocked = True
        elif not only_unlock:
            fila.is_unlocked = False
