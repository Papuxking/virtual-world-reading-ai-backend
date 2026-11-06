"""Endpoints de la zona de cómics del jugador: progreso por episodio y visitas,
siempre del slot activo."""
from helpers import cabeceras, crear_usuario
from models import PlayerSlot


def test_guardar_progreso_crea_y_despues_actualiza(client, db):
    usuario, _ = crear_usuario(db)
    token = cabeceras(usuario)
    r = client.put("/comics/progress/ep01", json={"last_page": 3, "finished": False}, headers=token)
    assert r.status_code == 200 and r.json()["last_page"] == 3
    r = client.put("/comics/progress/ep01", json={"last_page": 6, "finished": True}, headers=token)
    assert r.json()["finished"] is True
    assert len(client.get("/comics/progress", headers=token).json()["episodios"]) == 1


def test_visitar_la_zona_suma_sin_abrir_episodios(client, db):
    usuario, _ = crear_usuario(db)
    token = cabeceras(usuario)
    assert client.post("/comics/visit", headers=token).json()["visitas"] == 1
    assert client.post("/comics/visit", headers=token).json()["visitas"] == 2
    datos = client.get("/comics/progress", headers=token).json()
    assert datos["episodios"] == [] and datos["visitas"] == 2


def test_progreso_sin_token_es_401(client):
    assert client.get("/comics/progress").status_code == 401


def test_el_progreso_es_de_cada_slot(client, db):
    usuario, slot1 = crear_usuario(db)
    token = cabeceras(usuario)
    client.put("/comics/progress/ep01", json={"last_page": 3, "finished": False}, headers=token)
    client.post("/comics/visit", headers=token)
    slot1.is_active = False
    db.add(PlayerSlot(user_id=usuario.id, slot_number=2, label="Sesión 2", is_active=True))
    db.commit()
    datos = client.get("/comics/progress", headers=token).json()
    assert datos == {"episodios": [], "visitas": 0}


def test_pagina_negativa_es_422(client, db):
    usuario, _ = crear_usuario(db)
    r = client.put("/comics/progress/ep01", json={"last_page": -1, "finished": False},
                   headers=cabeceras(usuario))
    assert r.status_code == 422
