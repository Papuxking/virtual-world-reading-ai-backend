from game_rules import DIFFICULTY_ORDER
from helpers import cabeceras, crear_lectura, crear_usuario, payload_sesion
from models import PlayerSession, PlayerTypologyProgress


def _progreso(db, slot, tipologia):
    return db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology=tipologia).one()


def test_sesion_de_practica_no_toca_el_progreso(client, db):
    usuario, slot = crear_usuario(db)
    lectura = crear_lectura(db, "Práctica", "Narrativo", practica=True)
    r = client.post(
        "/progress/sessions",
        json=payload_sesion(db, lectura, puntaje=280, practica=True),
        headers=cabeceras(usuario),
    )
    assert r.status_code == 201
    assert r.json()["is_practice"] is True
    db.expire_all()
    fila = _progreso(db, slot, "Narrativo")
    assert (fila.best_score, fila.total_sessions, fila.perfect_sessions) == (0, 0, 0)
    assert _progreso(db, slot, "Descriptivo").is_unlocked is False
    assert db.query(PlayerSession).filter_by(is_practice=True).count() == 1


def test_cliente_sin_marca_se_comporta_como_hoy(client, db):
    usuario, slot = crear_usuario(db)
    lectura = crear_lectura(db, "Progresión", "Narrativo")
    r = client.post("/progress/sessions", json=payload_sesion(db, lectura, puntaje=260), headers=cabeceras(usuario))
    assert r.status_code == 201
    assert r.json()["is_practice"] is False
    db.expire_all()
    assert _progreso(db, slot, "Narrativo").best_score == 260
    assert _progreso(db, slot, "Narrativo").total_sessions == 1
    assert _progreso(db, slot, "Descriptivo").is_unlocked is True


def test_tipologia_fuera_del_juego_no_crea_progreso(client, db):
    usuario, slot = crear_usuario(db)
    lectura = crear_lectura(db, "Vieja", "Instructivo")
    r = client.post(
        "/progress/sessions",
        json=payload_sesion(db, lectura, puntaje=270),
        headers=cabeceras(usuario),
    )
    assert r.status_code == 201
    db.expire_all()
    assert db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology="Instructivo").count() == 0


def test_progress_me_solo_cuatro_tipologias_y_cuenta_practica(client, db):
    usuario, slot = crear_usuario(db)
    db.add(PlayerTypologyProgress(
        user_id=usuario.id, slot_id=slot.id, typology="Instructivo", best_score=270, is_unlocked=True,
    ))
    db.commit()
    practica = crear_lectura(db, "Práctica", "Descriptivo", practica=True)
    client.post("/progress/sessions", json=payload_sesion(db, practica, practica=True), headers=cabeceras(usuario))
    datos = client.get("/progress/me", headers=cabeceras(usuario)).json()
    assert [t["typology"] for t in datos["typology_progress"]] == DIFFICULTY_ORDER
    assert datos["total_score"] == 0
    assert datos["practice_sessions"] == 1
    assert datos["recent_sessions"] == []


def test_progress_me_crea_las_filas_que_faltan(client, db):
    usuario, _ = crear_usuario(db, filas=False)
    datos = client.get("/progress/me", headers=cabeceras(usuario)).json()
    assert [t["typology"] for t in datos["typology_progress"]] == DIFFICULTY_ORDER
    assert [t["is_unlocked"] for t in datos["typology_progress"]] == [True, False, False, False]


def test_listado_de_sesiones_excluye_practica(client, db):
    usuario, _ = crear_usuario(db)
    normal = crear_lectura(db, "Progresión", "Narrativo")
    practica = crear_lectura(db, "Práctica", "Narrativo", practica=True)
    h = cabeceras(usuario)
    client.post("/progress/sessions", json=payload_sesion(db, normal), headers=h)
    client.post("/progress/sessions", json=payload_sesion(db, practica, practica=True), headers=h)
    sesiones = client.get("/progress/sessions", headers=h).json()
    assert [s["is_practice"] for s in sesiones] == [False]


def test_progress_typologies_solo_cuatro(client, db):
    usuario, slot = crear_usuario(db)
    db.add(PlayerTypologyProgress(
        user_id=usuario.id, slot_id=slot.id, typology="Instructivo", best_score=270, is_unlocked=True,
    ))
    db.commit()
    datos = client.get("/progress/typologies", headers=cabeceras(usuario)).json()
    assert [t["typology"] for t in datos] == DIFFICULTY_ORDER
