import pytest

from game_rules import DIFFICULTY_ORDER, MAX_SESSION_SCORE, UNLOCK_THRESHOLDS
from helpers import cabeceras, crear_lectura, crear_usuario, payload_sesion
from models import PlayerNote, PlayerSession, PlayerTypologyProgress


@pytest.fixture
def escenario(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    alumno, slot = crear_usuario(db, "alumno@test.com")
    # Fila heredada de la tipología retirada: no debe contar en ningún total.
    db.add(PlayerTypologyProgress(
        user_id=alumno.id, slot_id=slot.id, typology="Instructivo",
        best_score=270, total_sessions=1, is_unlocked=True,
    ))
    db.commit()
    normal = crear_lectura(db, "Progresión", "Narrativo")
    practica = crear_lectura(db, "Práctica", "Narrativo", practica=True)
    h = cabeceras(alumno)
    r1 = client.post("/progress/sessions", json=payload_sesion(db, normal, puntaje=260), headers=h)
    # Práctica con todas las respuestas mal: si se colara, bajaría la precisión.
    r2 = client.post(
        "/progress/sessions",
        json=payload_sesion(db, practica, puntaje=150, practica=True, correctas=0),
        headers=h,
    )
    assert (r1.status_code, r2.status_code) == (201, 201)
    db.add_all([
        PlayerNote(user_id=alumno.id, slot_id=slot.id, reading_id=normal.id, note_content="nota normal"),
        PlayerNote(user_id=alumno.id, slot_id=slot.id, reading_id=practica.id, note_content="nota práctica"),
    ])
    db.commit()
    return {"alumno": alumno, "slot": slot, "h": cabeceras(admin)}


def test_detalle_incluye_reglas_de_puntaje(client, escenario):
    d = client.get(f"/admin/players/{escenario['alumno'].id}", headers=escenario["h"]).json()
    assert d["score_rules"] == {
        "typology_order": DIFFICULTY_ORDER,
        "unlock_thresholds": UNLOCK_THRESHOLDS,
        "max_session_score": MAX_SESSION_SCORE,
    }


def test_detalle_separa_la_practica(client, escenario):
    d = client.get(f"/admin/players/{escenario['alumno'].id}", headers=escenario["h"]).json()
    assert [t["typology"] for t in d["typology_progress"]] == DIFFICULTY_ORDER
    assert d["total_score"] == 260
    assert [s["session_score"] for s in d["sessions"]] == [260]
    assert [s["is_practice"] for s in d["sessions"]] == [False]
    assert [s["session_score"] for s in d["practice_sessions"]] == [150]
    assert [s["is_practice"] for s in d["practice_sessions"]] == [True]
    notas = {n["note_content"]: n["reading_is_practice"] for n in d["notes"]}
    assert notas == {"nota normal": False, "nota práctica": True}
    assert sum(nivel["total"] for nivel in d["level_stats"]) == 6
    assert sum(nivel["correct"] for nivel in d["level_stats"]) == 6
    assert {t["tool_name"]: t["total_sessions"] for t in d["tool_stats"]}["highlight"] == 1


def test_listado_de_jugadores(client, escenario):
    jugadores = client.get("/admin/players", headers=escenario["h"]).json()
    fila = next(p for p in jugadores if p["email"] == "alumno@test.com")
    assert (fila["total_score"], fila["total_sessions"], fila["practice_sessions"]) == (260, 1, 1)


def test_estadisticas_globales(client, escenario):
    s = client.get("/admin/stats", headers=escenario["h"]).json()
    assert s["total_sessions"] == 1
    assert s["total_practice_sessions"] == 1
    assert s["total_points"] == 260
    assert s["sessions_by_typology"] == {"Narrativo": 1}
    assert sum(d["sessions"] for d in s["activity_last_7_days"]) == 1
    assert s["average_accuracy"] == 100.0


def test_slots_sin_practica_ni_tipologias_retiradas(client, escenario):
    slot = client.get(f"/admin/players/{escenario['alumno'].id}/slots", headers=escenario["h"]).json()[0]
    assert (slot["total_score"], slot["total_sessions"]) == (260, 1)


def test_sesiones_del_jugador_por_marca(client, escenario):
    base = f"/admin/players/{escenario['alumno'].id}/sessions"
    normales = client.get(base, headers=escenario["h"]).json()
    practica = client.get(base, params={"practice": "true"}, headers=escenario["h"]).json()
    assert [s["session_score"] for s in normales] == [260]
    assert [s["session_score"] for s in practica] == [150]


def test_reinicio_de_tipologia_conserva_la_practica(client, db, escenario):
    r = client.post(
        f"/admin/players/{escenario['alumno'].id}/reset/typology",
        json={"typology": "Narrativo", "confirm_email": "alumno@test.com", "confirm_delete": True},
        headers=escenario["h"],
    )
    assert r.status_code == 200
    db.expire_all()
    assert db.query(PlayerSession).filter_by(is_practice=False).count() == 0
    assert db.query(PlayerSession).filter_by(is_practice=True).count() == 1
    assert {n.note_content for n in db.query(PlayerNote).all()} == {"nota práctica"}


def test_reinicio_de_tipologia_rechaza_instructivo(client, escenario):
    r = client.post(
        f"/admin/players/{escenario['alumno'].id}/reset/typology",
        json={"typology": "Instructivo", "confirm_email": "alumno@test.com", "confirm_delete": True},
        headers=escenario["h"],
    )
    assert r.status_code == 400


def test_reinicio_total_borra_tambien_la_practica(client, db, escenario):
    r = client.post(
        f"/admin/players/{escenario['alumno'].id}/reset/all",
        json={"confirm_email": "alumno@test.com", "confirm_delete": True},
        headers=escenario["h"],
    )
    assert r.status_code == 200
    db.expire_all()
    assert db.query(PlayerSession).count() == 0
    filas = db.query(PlayerTypologyProgress).filter_by(slot_id=escenario["slot"].id).all()
    assert sorted(f.typology for f in filas) == sorted(DIFFICULTY_ORDER)


def test_slot_nuevo_con_cuatro_filas(client, db, escenario):
    r = client.post(
        f"/admin/players/{escenario['alumno'].id}/slots",
        json={"label": "Intento 2"},
        headers=escenario["h"],
    )
    assert r.status_code == 201
    filas = db.query(PlayerTypologyProgress).filter_by(slot_id=r.json()["id"]).all()
    assert sorted(f.typology for f in filas) == sorted(DIFFICULTY_ORDER)
