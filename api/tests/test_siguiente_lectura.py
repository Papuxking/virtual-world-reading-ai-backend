"""GET /progress/next-reading: la lectura de progresión que toca, sin repetir las
que el alumno ya terminó en esa tipología, y nada si se quedó sin intentos."""
from datetime import datetime, timedelta, timezone

from helpers import cabeceras, crear_lectura, crear_usuario
from models import ActiveReading, PlayerSession, PlayerSlot, PlayerTypologyProgress


def _terminar(db, usuario, slot, lectura, hace_dias=0):
    """Sesión de progresión terminada con esa lectura, en ese slot."""
    db.add(PlayerSession(
        user_id=usuario.id, slot_id=slot.id, reading_id=lectura.id, typology=lectura.typology,
        session_score=60, is_practice=False,
        completed_at=datetime.now(timezone.utc) - timedelta(days=hace_dias),
    ))
    db.commit()


def _siguiente(client, usuario, tipologia="Narrativo"):
    return client.get("/progress/next-reading", params={"typology": tipologia}, headers=cabeceras(usuario))


def test_excluye_las_lecturas_terminadas(client, db):
    usuario, slot = crear_usuario(db)
    a = crear_lectura(db, "A")
    b = crear_lectura(db, "B")
    c = crear_lectura(db, "C")
    _terminar(db, usuario, slot, a)
    _terminar(db, usuario, slot, b)
    for _ in range(10):
        r = _siguiente(client, usuario)
        assert r.status_code == 200
        assert r.json()["id"] == c.id


def test_devuelve_la_lectura_completa(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db, "Única")
    datos = _siguiente(client, usuario).json()
    assert datos["id"] == lectura.id
    assert datos["is_practice"] is False
    assert len(datos["questions"]) == 6
    assert len(datos["questions"][0]["answers"]) == 4


def test_si_no_quedan_devuelve_la_terminada_hace_mas_tiempo(client, db):
    usuario, slot = crear_usuario(db)
    a = crear_lectura(db, "A")
    b = crear_lectura(db, "B")
    _terminar(db, usuario, slot, a, hace_dias=3)
    _terminar(db, usuario, slot, b, hace_dias=1)
    for _ in range(5):
        assert _siguiente(client, usuario).json()["id"] == a.id


def test_la_repetida_hace_mas_tiempo_cuenta_su_ultima_vez(client, db):
    usuario, slot = crear_usuario(db)
    a = crear_lectura(db, "A")
    b = crear_lectura(db, "B")
    _terminar(db, usuario, slot, a, hace_dias=5)
    _terminar(db, usuario, slot, b, hace_dias=3)
    _terminar(db, usuario, slot, a, hace_dias=1)     # A se volvió a leer hace poco
    assert _siguiente(client, usuario).json()["id"] == b.id


def test_excluye_la_lectura_activa(client, db):
    usuario, slot = crear_usuario(db)
    a = crear_lectura(db, "A")
    b = crear_lectura(db, "B")
    db.add(ActiveReading(user_id=usuario.id, slot_id=slot.id, reading_id=a.id, typology="Narrativo"))
    db.commit()
    for _ in range(10):
        assert _siguiente(client, usuario).json()["id"] == b.id


def test_si_solo_queda_la_activa_la_devuelve(client, db):
    # El juego reanuda en vez de pedir otra, pero si lo pidiera, mejor la suya
    # que un «no hay lecturas».
    usuario, slot = crear_usuario(db)
    a = crear_lectura(db, "A")
    db.add(ActiveReading(user_id=usuario.id, slot_id=slot.id, reading_id=a.id, typology="Narrativo"))
    db.commit()
    assert _siguiente(client, usuario).json()["id"] == a.id


def test_no_ofrece_practica_ni_otra_tipologia(client, db):
    usuario, _ = crear_usuario(db)
    crear_lectura(db, "Práctica", "Narrativo", practica=True)
    crear_lectura(db, "Otra", "Descriptivo")
    buena = crear_lectura(db, "Buena", "Narrativo")
    for _ in range(10):
        assert _siguiente(client, usuario).json()["id"] == buena.id


def test_sesiones_de_otro_slot_no_cuentan(client, db):
    usuario, slot = crear_usuario(db)
    viejo = PlayerSlot(user_id=usuario.id, slot_number=2, label="Sesión 2", is_active=False)
    db.add(viejo)
    db.commit()
    a = crear_lectura(db, "A")
    b = crear_lectura(db, "B")
    _terminar(db, usuario, viejo, a)
    _terminar(db, usuario, slot, b)
    for _ in range(10):
        assert _siguiente(client, usuario).json()["id"] == a.id


def test_403_sin_intentos(client, db):
    usuario, slot = crear_usuario(db)
    crear_lectura(db, "A")
    fila = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology="Narrativo").one()
    fila.attempts_used = 5
    fila.best_score = 0
    db.commit()
    r = _siguiente(client, usuario)
    assert r.status_code == 403
    assert r.json()["detail"] == "SIN_INTENTOS"


def test_con_intentos_agotados_pero_aprobada_no_bloquea(client, db):
    usuario, slot = crear_usuario(db)
    crear_lectura(db, "A")
    fila = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology="Narrativo").one()
    fila.attempts_used = 5
    fila.best_score = 200
    db.commit()
    assert _siguiente(client, usuario).status_code == 200


def test_400_tipologia_fuera_del_juego(client, db):
    usuario, _ = crear_usuario(db)
    crear_lectura(db, "Vieja", "Instructivo")
    assert _siguiente(client, usuario, "Instructivo").status_code == 400


def test_404_sin_lecturas(client, db):
    usuario, _ = crear_usuario(db)
    r = _siguiente(client, usuario)
    assert r.status_code == 404
    assert r.json()["detail"] == "No hay lecturas de esta tipología"


def test_requiere_token(client, db):
    crear_lectura(db, "A")
    assert client.get("/progress/next-reading", params={"typology": "Narrativo"}).status_code == 401
