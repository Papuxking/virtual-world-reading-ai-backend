"""Medallas por desempeño: cada tipología aprobada da una medalla cuyo metal
depende de los intentos que costó, y aprobar las cuatro da la de platino. No
dependen de los logros."""
from game_rules import DIFFICULTY_ORDER, pass_threshold
from helpers import cabeceras, crear_lectura, crear_usuario, payload_sesion
from medallas import metal_por_intentos
from models import PlayerTypologyProgress


def _poner(db, slot, tipologia, **valores):
    fila = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology=tipologia).one()
    for campo, valor in valores.items():
        setattr(fila, campo, valor)
    db.commit()


def _aprobar(db, slot, tipologia, intentos):
    _poner(db, slot, tipologia, best_score=pass_threshold(tipologia), attempts_used=intentos)


def _medallas(client, usuario):
    r = client.get("/progress/medals", headers=cabeceras(usuario))
    assert r.status_code == 200
    return {m["id"]: m for m in r.json()}


def test_metal_segun_intentos():
    assert metal_por_intentos(1) == "oro"
    assert metal_por_intentos(2) == "plata"
    assert [metal_por_intentos(n) for n in (3, 4, 5)] == ["bronce"] * 3


def test_sin_aprobar_no_hay_medallas(client, db):
    usuario, slot = crear_usuario(db)
    _poner(db, slot, "Narrativo", best_score=60, attempts_used=3)
    medallas = _medallas(client, usuario)
    assert len(medallas) == len(DIFFICULTY_ORDER) + 1
    assert not any(m["is_unlocked"] for m in medallas.values())
    assert medallas["medalla_narrativo"]["tier"] is None


def test_cada_tipologia_da_su_metal(client, db):
    usuario, slot = crear_usuario(db)
    _aprobar(db, slot, "Narrativo", 1)
    _aprobar(db, slot, "Descriptivo", 2)
    _aprobar(db, slot, "Argumentativo", 4)
    medallas = _medallas(client, usuario)
    assert medallas["medalla_narrativo"]["tier"] == "oro"
    assert medallas["medalla_descriptivo"]["tier"] == "plata"
    assert medallas["medalla_argumentativo"]["tier"] == "bronce"
    assert medallas["medalla_argumentativo"]["attempts"] == 4
    assert medallas["medalla_expositivo"]["is_unlocked"] is False
    assert medallas["gran_lector"]["is_unlocked"] is False


def test_aprobar_las_cuatro_da_platino(client, db):
    usuario, slot = crear_usuario(db)
    for tipologia in DIFFICULTY_ORDER:
        _aprobar(db, slot, tipologia, 3)
    gran_lector = _medallas(client, usuario)["gran_lector"]
    assert gran_lector["is_unlocked"] is True
    assert gran_lector["tier"] == "platino"


def test_progreso_anterior_a_los_intentos_usa_las_sesiones(client, db):
    """Quien aprobó antes de la migración 010 tiene attempts_used = 0: cuentan
    sus sesiones, para no regalarle el oro."""
    usuario, slot = crear_usuario(db)
    _poner(db, slot, "Narrativo", best_score=200, attempts_used=0, total_sessions=2)
    assert _medallas(client, usuario)["medalla_narrativo"]["tier"] == "plata"


def test_la_sesion_que_aprueba_al_primer_intento_da_oro(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db, "Progresión", "Narrativo")
    client.post("/progress/sessions", json=payload_sesion(db, lectura, puntaje=200), headers=cabeceras(usuario))
    assert _medallas(client, usuario)["medalla_narrativo"]["tier"] == "oro"


def test_el_detalle_del_dashboard_trae_las_medallas(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    usuario, slot = crear_usuario(db)
    _aprobar(db, slot, "Narrativo", 2)
    r = client.get(f"/admin/players/{usuario.id}", headers=cabeceras(admin))
    assert r.status_code == 200
    medallas = {m["id"]: m for m in r.json()["medals"]}
    assert medallas["medalla_narrativo"]["tier"] == "plata"
