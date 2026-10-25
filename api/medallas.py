"""
medallas.py — Medallas por desempeño, aparte de los logros.

Cada tipología aprobada da su medalla, y el metal depende de cuántos intentos
costó aprobarla: oro al primero, plata al segundo, bronce del tercero en
adelante. Aprobar las cuatro da además la de platino, «Gran lector». Se
calculan a partir del progreso por tipología: no hay nada que guardar.

Espejo de ProgressionManager.metal_de_medalla y MEDALLAS en el juego.
"""
from game_rules import DIFFICULTY_ORDER
from progression import aprobada

MEDALLAS_TIPOLOGIA = {
    "Narrativo": {
        "id": "medalla_narrativo",
        "name": "Medalla del Narrador",
        "description": "Sigues los hilos de cualquier historia.",
        "emoji": "📜",
        "imagen": "/static/medals/medalla_narrativo.png?v=2",
    },
    "Descriptivo": {
        "id": "medalla_descriptivo",
        "name": "Medalla del Observador",
        "description": "Ningún detalle se escapa de tu mirada.",
        "emoji": "🔍",
        "imagen": "/static/medals/medalla_descriptivo.png?v=2",
    },
    "Argumentativo": {
        "id": "medalla_argumentativo",
        "name": "Medalla del Orador",
        "description": "Distingues una buena razón de una trampa.",
        "emoji": "💬",
        "imagen": "/static/medals/medalla_argumentativo.png?v=2",
    },
    "Expositivo": {
        "id": "medalla_expositivo",
        "name": "Medalla del Divulgador",
        "description": "Conviertes la información en conocimiento.",
        "emoji": "🧪",
        "imagen": "/static/medals/medalla_expositivo.png?v=2",
    },
}

GRAN_LECTOR = {
    "id": "gran_lector",
    "name": "Gran lector",
    "description": "Recorriste todas las tipologías textuales del mundo virtual.",
    "emoji": "👑",
    "imagen": "/static/medals/gran_lector.png?v=2",
    "how_to_unlock": "Aprueba las cuatro tipologías.",
}


def metal_por_intentos(intentos: int) -> str:
    """Metal de la medalla de una tipología aprobada en ese intento."""
    if intentos <= 1:
        return "oro"
    if intentos == 2:
        return "plata"
    return "bronce"


def _intentos(fila) -> int:
    """Intentos que costó aprobar. Quien aprobó antes de que existieran los
    intentos (migración 010) tiene attempts_used a 0: cuentan sus sesiones."""
    return fila.attempts_used or fila.total_sessions or 1


def medallas_del_jugador(filas) -> list[dict]:
    """Las medallas de un slot a partir de sus filas de progreso, en el orden
    del recorrido y con «Gran lector» al final. Una bloqueada tiene tier None."""
    por_tipologia = {f.typology: f for f in filas}
    medallas = []
    for tipologia in DIFFICULTY_ORDER:
        fila = por_tipologia.get(tipologia)
        ganada = fila is not None and aprobada(fila)
        intentos = _intentos(fila) if ganada else None
        medallas.append({
            **MEDALLAS_TIPOLOGIA[tipologia],
            "typology": tipologia,
            "how_to_unlock": f"Aprueba {tipologia}: al primer intento es de oro, al segundo de plata y después de bronce.",
            "is_unlocked": ganada,
            "tier": metal_por_intentos(intentos) if ganada else None,
            "attempts": intentos,
        })
    todas = all(m["is_unlocked"] for m in medallas)
    medallas.append({
        **GRAN_LECTOR,
        "typology": None,
        "is_unlocked": todas,
        "tier": "platino" if todas else None,
        "attempts": None,
    })
    return medallas
