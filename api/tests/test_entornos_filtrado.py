"""El dashboard ve solo el entorno que tiene elegido (cabecera X-Workspace-Id):
jugadores, estadísticas, logros, métricas y exportaciones."""
import pytest

from helpers import cabeceras, crear_entorno, crear_lectura, crear_usuario
from models import (
    AchievementCatalog, NpcInteraction, PlayerAchievement, PlayerAnswer, PlayerSession,
    PlayerTypologyProgress, Question, SessionTool,
)


def _jugador_con_datos(db, email, entorno, lectura, sesiones=1):
    """Jugador con sesiones (6 respuestas y herramientas cada una), un logro,
    una interacción con el NPC y su mejor puntaje en Narrativo."""
    usuario, slot = crear_usuario(db, email, entorno=entorno)
    preguntas = db.query(Question).filter_by(reading_id=lectura.id).all()
    for _ in range(sesiones):
        sesion = PlayerSession(
            user_id=usuario.id, slot_id=slot.id, reading_id=lectura.id, typology="Narrativo",
            session_score=150, reading_time_seconds=120, total_time_seconds=300,
            correct_count=6, incorrect_count=0,
        )
        db.add(sesion)
        db.flush()
        for pregunta in preguntas:
            db.add(PlayerAnswer(
                session_id=sesion.id, question_id=pregunta.id,
                comprehension_level=pregunta.comprehension_level,
                selected_answer="A", correct_answer="A", is_correct=True, points_earned=10,
            ))
        db.add(SessionTool(session_id=sesion.id, tool_name="highlight", was_used=True, usage_count=1))
    db.add(PlayerAchievement(user_id=usuario.id, slot_id=slot.id, achievement_id="first_reading",
                             achievement_name="Primera lectura"))
    db.add(NpcInteraction(user_id=usuario.id, slot_id=slot.id, npc_type="robot", reading_id=lectura.id))
    fila = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology="Narrativo").one()
    fila.best_score = 150
    db.commit()
    return usuario


@pytest.fixture
def dos_entornos(db):
    """A con un jugador y una sesión; B con dos jugadores y tres sesiones."""
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    db.add(AchievementCatalog(
        id="first_reading", name="Primera lectura", description="d", how_to_unlock="h",
        category="progreso", medal_name="Lector novato", medal_tier="bronce", display_order=1,
    ))
    db.commit()
    a = crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    lectura = crear_lectura(db, "Lectura")
    _jugador_con_datos(db, "a@test.com", a, lectura)
    _jugador_con_datos(db, "b1@test.com", b, lectura, sesiones=2)
    _jugador_con_datos(db, "b2@test.com", b, lectura)
    return admin, a, b


def _get(client, admin, entorno, ruta, **params):
    r = client.get(ruta, headers=cabeceras(admin, entorno), params=params)
    assert r.status_code == 200, (ruta, r.status_code, r.text[:200])
    return r


def test_jugadores_y_estadisticas(client, db, dos_entornos):
    admin, a, b = dos_entornos
    assert [j["email"] for j in _get(client, admin, a, "/admin/players").json()] == ["a@test.com"]
    assert sorted(j["email"] for j in _get(client, admin, b, "/admin/players").json()) == ["b1@test.com", "b2@test.com"]
    stats_a = _get(client, admin, a, "/admin/stats").json()
    stats_b = _get(client, admin, b, "/admin/stats").json()
    assert (stats_a["total_players"], stats_a["total_sessions"], stats_a["total_achievements"]) == (1, 1, 1)
    assert (stats_b["total_players"], stats_b["total_sessions"], stats_b["total_achievements"]) == (2, 3, 2)
    assert stats_a["total_points"] == 150 and stats_b["total_points"] == 300
    assert stats_a["sessions_by_typology"] == {"Narrativo": 1}


def test_logros(client, db, dos_entornos):
    admin, a, b = dos_entornos
    item_a = _get(client, admin, a, "/admin/achievements").json()[0]
    item_b = _get(client, admin, b, "/admin/achievements").json()[0]
    assert (item_a["unlock_count"], item_a["total_players"]) == (1, 1)
    assert (item_b["unlock_count"], item_b["total_players"]) == (2, 2)
    assert _get(client, admin, a, "/admin/achievements/stats").json()["total_unlocks"] == 1
    assert _get(client, admin, b, "/admin/achievements/stats").json()["unique_players_with_unlocks"] == 2
    detalle = _get(client, admin, a, "/admin/achievements/first_reading").json()
    assert [p["email"] for p in detalle["players"]] == ["a@test.com"]
    jugadores = _get(client, admin, b, "/admin/achievements/first_reading/players").json()
    assert sorted(p["email"] for p in jugadores) == ["b1@test.com", "b2@test.com"]

    csv_a = _get(client, admin, a, "/admin/achievements/export/csv").text
    assert "first_reading" in csv_a.splitlines()[1] and ",1,1," in csv_a.splitlines()[1]
    jugadores_csv = _get(client, admin, a, "/admin/achievements/first_reading/players/export/csv").text
    assert "a@test.com" in jugadores_csv and "b1@test.com" not in jugadores_csv
    _get(client, admin, a, "/admin/achievements/export/excel")
    _get(client, admin, a, "/admin/achievements/first_reading/players/export/excel")


def test_metricas(client, db, dos_entornos):
    admin, a, b = dos_entornos
    lectura_a = _get(client, admin, a, "/admin/metrics/reading-time").json()
    assert lectura_a["total_sessions"] == 1
    assert [p["display_name"] for p in lectura_a["by_player"]] == ["a"]
    assert _get(client, admin, b, "/admin/metrics/reading-time").json()["total_sessions"] == 3
    assert _get(client, admin, a, "/admin/metrics/answers").json()["total_correct"] == 6
    assert _get(client, admin, b, "/admin/metrics/answers").json()["total_correct"] == 18
    intentos_b = _get(client, admin, b, "/admin/metrics/question-attempts").json()["questions"]
    assert sum(q["total_attempts"] for q in intentos_b) == 18
    assert _get(client, admin, a, "/admin/metrics/npc-interactions").json()["total_all"] == 1
    assert _get(client, admin, b, "/admin/metrics/npc-interactions").json()["total_all"] == 2
    assert _get(client, admin, a, "/admin/metrics/tool-usage").json()["total_sessions"] == 1
    assert _get(client, admin, b, "/admin/metrics/tool-usage").json()["total_sessions"] == 3

    csv_b = _get(client, admin, b, "/admin/metrics/export/csv", metric="answers").text
    assert "b1" in csv_b and "b2" in csv_b and "\na," not in csv_b
    _get(client, admin, b, "/admin/metrics/export/excel", metric="answers")


def test_cabecera_obligatoria(client, db, dos_entornos):
    admin, _, _ = dos_entornos
    for cabecera, codigo, detalle in (
        (None, 400, "WORKSPACE_REQUIRED"),
        ("abc", 400, "WORKSPACE_REQUIRED"),
        ("9999", 404, "WORKSPACE_NOT_FOUND"),
    ):
        h = cabeceras(admin)
        if cabecera is not None:
            h["X-Workspace-Id"] = cabecera
        for ruta in ("/admin/players", "/admin/stats", "/admin/achievements", "/admin/metrics/answers"):
            r = client.get(ruta, headers=h)
            assert (r.status_code, r.json()["detail"]) == (codigo, detalle), (ruta, cabecera)
