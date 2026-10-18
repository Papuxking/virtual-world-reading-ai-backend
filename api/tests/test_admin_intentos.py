"""El admin ve los intentos de cada tipología y quién tiene el juego terminado;
reiniciar una tipología le devuelve los intentos al alumno."""
from helpers import cabeceras, crear_usuario
from models import PlayerTypologyProgress


def _fila(db, slot, tipologia):
    return db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology=tipologia).one()


def _agotar(db, slot, tipologia="Narrativo"):
    fila = _fila(db, slot, tipologia)
    fila.attempts_used = 5
    fila.best_score = 100
    fila.is_unlocked = True
    db.commit()


def test_detalle_trae_intentos_y_game_over(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    alumno, slot = crear_usuario(db, "alumno@test.com")
    _agotar(db, slot)
    datos = client.get(f"/admin/players/{alumno.id}", headers=cabeceras(admin)).json()
    assert datos["game_over"] is True
    por_tipologia = {t["typology"]: t for t in datos["typology_progress"]}
    assert por_tipologia["Narrativo"]["attempts_used"] == 5
    assert por_tipologia["Descriptivo"]["attempts_used"] == 0
    assert datos["score_rules"]["max_attempts"] == 5


def test_detalle_sin_agotar_no_es_game_over(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    alumno, _ = crear_usuario(db, "alumno@test.com")
    datos = client.get(f"/admin/players/{alumno.id}", headers=cabeceras(admin)).json()
    assert datos["game_over"] is False


def test_lista_marca_game_over(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    agotado, slot = crear_usuario(db, "agotado@test.com")
    crear_usuario(db, "sigue@test.com")
    _agotar(db, slot)
    lista = client.get("/admin/players", headers=cabeceras(admin)).json()
    estado = {j["email"]: j["game_over"] for j in lista}
    assert estado == {"agotado@test.com": True, "sigue@test.com": False}


def test_reiniciar_tipologia_pone_intentos_a_cero(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    alumno, slot = crear_usuario(db, "alumno@test.com")
    _fila(db, slot, "Narrativo").attempts_used = 2
    _fila(db, slot, "Narrativo").best_score = 200
    _fila(db, slot, "Descriptivo").attempts_used = 5
    _fila(db, slot, "Expositivo").attempts_used = 1
    db.commit()
    r = client.post(
        f"/admin/players/{alumno.id}/reset/typology",
        json={"typology": "Descriptivo", "confirm_email": "alumno@test.com", "confirm_delete": True},
        headers=cabeceras(admin),
    )
    assert r.status_code == 200
    db.expire_all()
    assert _fila(db, slot, "Descriptivo").attempts_used == 0
    assert _fila(db, slot, "Expositivo").attempts_used == 0
    assert _fila(db, slot, "Narrativo").attempts_used == 2


def test_reiniciar_todo_deja_los_intentos_a_cero(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    alumno, slot = crear_usuario(db, "alumno@test.com")
    _agotar(db, slot)
    r = client.post(
        f"/admin/players/{alumno.id}/reset/all",
        json={"confirm_email": "alumno@test.com", "confirm_delete": True},
        headers=cabeceras(admin),
    )
    assert r.status_code == 200
    db.expire_all()
    assert {f.attempts_used for f in db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id)} == {0}
