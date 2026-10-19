"""
game_rules.py — Reglas del juego que la API necesita conocer.

El juego (Godot) es quien calcula el puntaje. Aquí solo se replica lo que la
API y el dashboard necesitan para no inventárselo:
  - el orden de las tipologías y sus umbrales de desbloqueo, espejo de
    scripts/Global/progression_manager.gd;
  - el puntaje máximo de una sesión, espejo de las constantes de
    scripts/Global/game_session.gd.
Si cambia alguna de esas constantes en el juego, hay que cambiarla aquí.

Sin imports a propósito: lo usan también scripts que corren fuera del
contenedor (import_readings.py).
"""

# Orden de dificultad de la progresión. Instructivo ya no forma parte del juego.
DIFFICULTY_ORDER = ["Narrativo", "Descriptivo", "Argumentativo", "Expositivo"]

# Puntaje mínimo en la tipología ANTERIOR para desbloquear cada una.
# 120 = aprobar con hasta 2 errores sin usar herramientas: el peor caso con 2
# errores (uno inferencial y uno crítico) da 122. Sin herramientas el máximo
# es 240, así que el antiguo 250 obligaba a usarlas.
UNLOCK_THRESHOLDS = {
    "Narrativo": 0,
    "Descriptivo": 120,
    "Argumentativo": 120,
    "Expositivo": 120,
}

# Máximo de una sesión según game_session.gd:
#   respuestas 2x10 + 2x20 + 2x30 = 120
#   nivel perfecto 15 x 3        =  45
#   sesión completa              =  50
#   sesión perfecta              =  25
#   herramientas 20 x 3          =  60
#                                  ---
#                                  300
MAX_SESSION_SCORE = 300

# Lecturas de progresión terminadas que tiene el alumno para aprobar cada
# tipología. Gastadas sin aprobar, el juego termina: ya no puede avanzar.
# Espejo de ProgressionManager.MAX_INTENTOS.
MAX_INTENTOS_POR_TIPOLOGIA = 5


def pass_threshold(typology: str) -> int:
    """Puntaje con el que se aprueba una tipología: el que abre la siguiente.
    La última no abre nada y usa su propio umbral (espejo de
    ProgressionManager.get_pass_threshold)."""
    indice = DIFFICULTY_ORDER.index(typology)
    if indice + 1 < len(DIFFICULTY_ORDER):
        return UNLOCK_THRESHOLDS[DIFFICULTY_ORDER[indice + 1]]
    return UNLOCK_THRESHOLDS[typology]


def score_rules() -> dict:
    """Reglas de puntaje tal como las consume el dashboard (copias)."""
    return {
        "typology_order": list(DIFFICULTY_ORDER),
        "unlock_thresholds": dict(UNLOCK_THRESHOLDS),
        "max_session_score": MAX_SESSION_SCORE,
        "max_attempts": MAX_INTENTOS_POR_TIPOLOGIA,
    }
