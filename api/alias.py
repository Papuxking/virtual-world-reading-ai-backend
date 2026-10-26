"""Espejo de ALIAS en scripts/UI/profile_hud.gd: si una lista cambia,
hay que cambiar también la otra para desbloquear los mismos alias."""

ALIAS = [
    {"id": "intuicion", "nombre": "Intuición", "lecturas": 0},
    {"id": "interes", "nombre": "Interés", "lecturas": 1},
    {"id": "curiosidad", "nombre": "Curiosidad", "lecturas": 3},
    {"id": "comprension", "nombre": "Comprensión", "lecturas": 5},
    {"id": "perspectiva", "nombre": "Perspectiva", "lecturas": 8},
    {"id": "perspicacia", "nombre": "Perspicacia", "lecturas": 12},
    {"id": "sabiduria", "nombre": "Sabiduría", "lecturas": 16},
    {"id": "conocimiento", "nombre": "Conocimiento", "lecturas": 20},
]

ALIAS_POR_ID = {alias["id"]: alias for alias in ALIAS}
