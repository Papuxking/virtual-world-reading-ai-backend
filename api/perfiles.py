"""Resuelve la vitrina con el catálogo vigente y los desbloqueos del slot."""
from medallas import medallas_del_jugador
from models import AchievementCatalog, PlayerAchievement, PlayerTypologyProgress


def progreso_del_slot(db, slot):
    return db.query(PlayerTypologyProgress).filter_by(
        user_id=slot.user_id, slot_id=slot.id,
    ).all()


def elementos_desbloqueados(db, slot, filas):
    elementos = {}
    for medalla in medallas_del_jugador(filas):
        if medalla["is_unlocked"]:
            catalogo = db.get(AchievementCatalog, medalla["id"])
            elementos[("medalla", medalla["id"])] = {
                "tipo": "medalla", "id": medalla["id"],
                "nombre": medalla["name"], "emoji": medalla["emoji"],
                "tier": medalla["tier"],
                "imagen": catalogo.medal_image_path if catalogo else None,
            }
    logros = db.query(PlayerAchievement).filter_by(
        user_id=slot.user_id, slot_id=slot.id,
    ).all()
    for logro in logros:
        catalogo = db.get(AchievementCatalog, logro.achievement_id)
        elementos[("logro", logro.achievement_id)] = {
            "tipo": "logro", "id": logro.achievement_id,
            "nombre": catalogo.name if catalogo else logro.achievement_name,
            "emoji": (catalogo.icon or "🏆") if catalogo else "🏆",
            "tier": catalogo.medal_tier if catalogo else None,
            "imagen": catalogo.medal_image_path if catalogo else None,
        }
    return elementos


def resolver_vitrina(slot, elementos):
    # Un catálogo o un progreso corregido no debe dejar insignias ajenas en público.
    return [elementos[(item["tipo"], item["id"])] for item in slot.vitrina or []
            if (item["tipo"], item["id"]) in elementos]
