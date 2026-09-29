import pytest

import routers.leaderboard_router as ranking
from helpers import cabeceras, crear_lectura, crear_usuario, payload_sesion
from models import NpcInteraction, PlayerTypologyProgress


@pytest.fixture
def escenario(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    alumno, slot = crear_usuario(db, "alumno@test.com")
    normal = crear_lectura(db, "Progresión", "Narrativo")
    practica = crear_lectura(db, "Práctica", "Narrativo", practica=True)
    h = cabeceras(alumno)
    client.post("/progress/sessions", json=payload_sesion(db, normal, puntaje=260), headers=h)
    client.post(
        "/progress/sessions",
        json=payload_sesion(db, practica, puntaje=100, practica=True, correctas=0),
        headers=h,
    )
    db.add_all([
        NpcInteraction(user_id=alumno.id, slot_id=slot.id, npc_type="robot", reading_id=normal.id),
        NpcInteraction(user_id=alumno.id, slot_id=slot.id, npc_type="robot", reading_id=practica.id),
        NpcInteraction(user_id=alumno.id, slot_id=slot.id, npc_type="sabio", reading_id=None),
    ])
    db.commit()
    return {"h": cabeceras(admin), "alumno": alumno, "slot": slot}


def test_tiempo_de_lectura_sin_practica(client, escenario):
    d = client.get("/admin/metrics/reading-time", headers=escenario["h"]).json()
    assert d["total_sessions"] == 1


def test_respuestas_sin_practica(client, escenario):
    d = client.get("/admin/metrics/answers", headers=escenario["h"]).json()
    assert (d["total_correct"], d["total_incorrect"]) == (6, 0)


def test_intentos_por_pregunta_sin_practica(client, escenario):
    d = client.get("/admin/metrics/question-attempts", headers=escenario["h"]).json()
    assert {q["reading_title"] for q in d["questions"]} == {"Progresión"}


def test_herramientas_sin_practica(client, escenario):
    d = client.get("/admin/metrics/tool-usage", headers=escenario["h"]).json()
    assert d["total_sessions"] == 1


def test_interacciones_npc_sin_lecturas_de_practica(client, escenario):
    d = client.get("/admin/metrics/npc-interactions", headers=escenario["h"]).json()
    assert (d["total_robot"], d["total_sabio"]) == (1, 1)


def test_exportacion_csv_sin_practica(client, escenario):
    r = client.get("/admin/metrics/export/csv", params={"metric": "answers"}, headers=escenario["h"])
    assert r.status_code == 200
    assert r.text.strip().splitlines()[1] == "alumno,6,0,100.0"


def test_ranking_suma_solo_las_cuatro_tipologias(client, db):
    ranking._cache["data"] = None   # la caché es global al proceso
    alumno, slot = crear_usuario(db, "alumno@test.com")
    db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology="Narrativo").one().best_score = 260
    db.add(PlayerTypologyProgress(
        user_id=alumno.id, slot_id=slot.id, typology="Instructivo", best_score=270, is_unlocked=True,
    ))
    db.commit()
    datos = client.get("/leaderboard/top", headers=cabeceras(alumno)).json()
    ranking._cache["data"] = None
    assert datos["players"][0]["total_score"] == 260
