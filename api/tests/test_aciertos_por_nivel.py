"""Aciertos por nivel en GET /progress/me: el juego los necesita al iniciar
sesión para que los logros de las Estrellas acumulen entre partidas."""
from helpers import cabeceras, crear_lectura, crear_usuario, payload_sesion

CEROS = {"Literal": 0, "Inferencial": 0, "Critico": 0}


def _aciertos(client, usuario):
    return client.get("/progress/me", headers=cabeceras(usuario)).json()["correct_by_level"]


def test_sin_sesiones_devuelve_ceros(client, db):
    usuario, _ = crear_usuario(db)
    assert _aciertos(client, usuario) == CEROS


def test_suma_los_aciertos_de_todas_las_sesiones(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db, "Progresión", "Narrativo")
    # Preguntas en orden L, L, I, I, C, C: 4 correctas = L2 I2 C0; 6 = L2 I2 C2.
    for correctas in (4, 6):
        r = client.post("/progress/sessions", json=payload_sesion(db, lectura, correctas=correctas),
                        headers=cabeceras(usuario))
        assert r.status_code == 201
    assert _aciertos(client, usuario) == {"Literal": 4, "Inferencial": 4, "Critico": 2}


def test_no_cuenta_los_de_otro_alumno(client, db):
    alumno, _ = crear_usuario(db, "uno@test.com")
    otro, _ = crear_usuario(db, "otro@test.com")
    lectura = crear_lectura(db, "Progresión", "Narrativo")
    client.post("/progress/sessions", json=payload_sesion(db, lectura, correctas=6), headers=cabeceras(otro))
    assert _aciertos(client, alumno) == CEROS
