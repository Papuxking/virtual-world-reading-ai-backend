"""
leaderboard_router.py — Endpoint de leaderboard para el Lobby de Godot.
Retorna Top N jugadores del entorno activo con caché en memoria (TTL 60s), una
por entorno.
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
from workspaces import entorno_activo
from datetime import datetime, timezone

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

# ── Caché en memoria ─────────────────────────────────────────────────────────

CACHE_TTL = 60  # Segundos

# Una entrada por entorno: id del entorno → {"data": [...], "timestamp": float}.
# Guarda el ranking entero (hasta 50), así sirve para cualquier limit.
_cache: dict = {}


def _cache_valida(entorno_id: int) -> Optional[dict]:
    entrada = _cache.get(entorno_id)
    if entrada and (time.time() - entrada["timestamp"]) < CACHE_TTL:
        return entrada
    return None


# ── Endpoint de Leaderboard ──────────────────────────────────────────────────

@router.get("/top", response_model=LeaderboardResponse)
def get_leaderboard(
    limit: int = Query(5, ge=1, le=50, description="Cantidad de jugadores (5 o 20)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna el Top N de jugadores del entorno activo ordenados por puntaje
    total. Los datos se cachean por 60 segundos para evitar consultas costosas.
    El puntaje es la suma de best_score de las tipologías del juego en el slot
    activo de cada jugador.
    """
    activo = entorno_activo(db)
    if activo is None:
        return LeaderboardResponse(players=[], updated_at=datetime.now(timezone.utc))

    cached = _cache_valida(activo.id)
    if cached:
        return LeaderboardResponse(
            players=cached["data"][:limit],
            updated_at=datetime.fromtimestamp(cached["timestamp"], tz=timezone.utc),
        )

    # Jugadores del entorno activo
    users = (
        db.query(User)
        .filter(User.workspace_id == activo.id, User.is_admin == False, User.is_active == True)
        .all()
    )

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
    _cache[activo.id] = {"data": ranked, "timestamp": time.time()}

    return LeaderboardResponse(
        players=ranked[:limit],
        updated_at=datetime.now(timezone.utc),
    )
