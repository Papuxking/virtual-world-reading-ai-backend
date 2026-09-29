"""
leaderboard_router.py — Endpoint de leaderboard para el Lobby de Godot.
Retorna Top N jugadores con caché en memoria (TTL 60s).
"""
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from database import get_db
from models import (
    User, PlayerTypologyProgress, PlayerAchievement, PlayerSlot,
)
from schemas import LeaderboardResponse, LeaderboardEntry
from game_rules import DIFFICULTY_ORDER
from auth import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

# ── Caché en memoria ─────────────────────────────────────────────────────────

_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 60,  # Segundos
}


def _is_cache_valid() -> bool:
    return (
        _cache["data"] is not None
        and (time.time() - _cache["timestamp"]) < _cache["ttl"]
    )


def _update_cache(data):
    _cache["data"] = data
    _cache["timestamp"] = time.time()


# ── Endpoint de Leaderboard ──────────────────────────────────────────────────

@router.get("/top", response_model=LeaderboardResponse)
def get_leaderboard(
    limit: int = Query(5, ge=1, le=50, description="Cantidad de jugadores (5 o 20)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna el Top N de jugadores ordenados por puntaje total.
    Los datos se cachean por 60 segundos para evitar consultas costosas.
    El puntaje es la suma de best_score de las tipologías del juego en el slot
    activo de cada jugador.
    """
    # Verificar caché (solo si el limit coincide o es menor)
    if _is_cache_valid() and _cache.get("limit", 0) >= limit:
        cached = _cache["data"]
        return LeaderboardResponse(
            players=cached[:limit],
            updated_at=datetime.fromtimestamp(_cache["timestamp"], tz=timezone.utc),
        )

    # Obtener todos los jugadores no-admin
    users = db.query(User).filter(User.is_admin == False, User.is_active == True).all()

    entries = []
    for user in users:
        # Obtener slot activo
        active_slot = (
            db.query(PlayerSlot)
            .filter(PlayerSlot.user_id == user.id, PlayerSlot.is_active == True)
            .first()
        )
        if not active_slot:
            continue

        # Calcular puntaje total del slot activo
        total_score = (
            db.query(sqlfunc.coalesce(sqlfunc.sum(PlayerTypologyProgress.best_score), 0))
            .filter(
                PlayerTypologyProgress.user_id == user.id,
                PlayerTypologyProgress.slot_id == active_slot.id,
                PlayerTypologyProgress.typology.in_(DIFFICULTY_ORDER),
            )
            .scalar()
        ) or 0

        # Contar logros del slot activo
        total_achievements = (
            db.query(sqlfunc.count(PlayerAchievement.id))
            .filter(
                PlayerAchievement.user_id == user.id,
                PlayerAchievement.slot_id == active_slot.id,
            )
            .scalar()
        ) or 0

        if total_score > 0 or total_achievements > 0:
            entries.append({
                "display_name": user.display_name,
                "character": user.character,
                "total_score": total_score,
                "total_achievements": total_achievements,
            })

    # Ordenar por puntaje descendente
    entries.sort(key=lambda x: x["total_score"], reverse=True)

    # Asignar rangos y limitar a max 50 para caché
    max_entries = min(len(entries), 50)
    ranked = [
        LeaderboardEntry(
            rank=i + 1,
            display_name=e["display_name"],
            character=e["character"],
            total_score=e["total_score"],
            total_achievements=e["total_achievements"],
        )
        for i, e in enumerate(entries[:max_entries])
    ]

    # Actualizar caché
    _update_cache(ranked)
    _cache["limit"] = max_entries

    return LeaderboardResponse(
        players=ranked[:limit],
        updated_at=datetime.now(timezone.utc),
    )
