"""Intentos por tipología: cada lectura de progresión terminada gasta uno; con
5 gastados sin aprobar, la tipología queda agotada y el juego terminado."""
from game_rules import UNLOCK_THRESHOLDS, pass_threshold, score_rules
from helpers import cabeceras, crear_lectura, crear_usuario, payload_sesion
from models import PlayerTypologyProgress


def _fila(db, slot, tipologia):
    return db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology=tipologia).one()


def _poner(db, slot, tipologia, **valores):
    fila = _fila(db, slot, tipologia)
    for campo, valor in valores.items():
        setattr(fila, campo, valor)
    db.commit()


def _progreso(client, usuario):
    return client.get("/progress/me", headers=cabeceras(usuario)).json()


def test_sesion_de_progresion_suma_un_intento(client, db):
    usuario, slot = crear_usuario(db)
    lectura = crear_lectura(db, "Progresión", "Narrativo")
    r = client.post("/progress/sessions", json=payload_sesion(db, lectura, puntaje=60), headers=cabeceras(usuario))
    assert r.status_code == 201
    db.expire_all()
    assert _fila(db, slot, "Narrativo").attempts_used == 1


def test_sesion_que_aprueba_tambien_suma(client, db):
    usuario, slot = crear_usuario(db)
    lectura = crear_lectura(db, "Progresión", "Narrativo")
    client.post("/progress/sessions", json=payload_sesion(db, lectura, puntaje=200), headers=cabeceras(usuario))
    db.expire_all()
    fila = _fila(db, slot, "Narrativo")
    assert (fila.attempts_used, fila.best_score) == (1, 200)


def test_progress_me_trae_intentos_y_maximo(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db, "Progresión", "Narrativo")
    for _ in range(2):
        client.post("/progress/sessions", json=payload_sesion(db, lectura, puntaje=60), headers=cabeceras(usuario))
    datos = _progreso(client, usuario)
    por_tipologia = {t["typology"]: t for t in datos["typology_progress"]}
    assert por_tipologia["Narrativo"]["attempts_used"] == 2
    assert por_tipologia["Descriptivo"]["attempts_used"] == 0
    assert datos["max_attempts"] == 5
    assert datos["game_over"] is False


def test_game_over_con_cinco_intentos_sin_aprobar(client, db):
    usuario, slot = crear_usuario(db)
    _poner(db, slot, "Narrativo", attempts_used=5, best_score=100)
    assert _progreso(client, usuario)["game_over"] is True


def test_cuatro_intentos_sin_aprobar_no_termina(client, db):
    usuario, slot = crear_usuario(db)
    _poner(db, slot, "Narrativo", attempts_used=4, best_score=100)
    assert _progreso(client, usuario)["game_over"] is False


def test_cinco_intentos_pero_aprobada_no_termina(client, db):
    usuario, slot = crear_usuario(db)
    _poner(db, slot, "Narrativo", attempts_used=5, best_score=130)
    assert _progreso(client, usuario)["game_over"] is False


def test_agotada_la_ultima_tipologia_tambien_termina(client, db):
    usuario, slot = crear_usuario(db)
    for tipologia in ("Narrativo", "Descriptivo", "Argumentativo"):
        _poner(db, slot, tipologia, best_score=200, is_unlocked=True, attempts_used=1)
    _poner(db, slot, "Expositivo", is_unlocked=True, attempts_used=5, best_score=119)
    assert _progreso(client, usuario)["game_over"] is True


def test_umbral_de_aprobacion():
    assert pass_threshold("Narrativo") == UNLOCK_THRESHOLDS["Descriptivo"]
    assert pass_threshold("Argumentativo") == UNLOCK_THRESHOLDS["Expositivo"]
    assert pass_threshold("Expositivo") == UNLOCK_THRESHOLDS["Expositivo"]


def test_score_rules_trae_max_attempts():
    assert score_rules()["max_attempts"] == 5
