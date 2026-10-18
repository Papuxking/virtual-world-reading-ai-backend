"""La lectura en curso se conserva hasta que el alumno la termina (sin caducar)
y guarda el tiempo acumulado, para reanudarla tras cerrar el navegador."""
from datetime import datetime, timedelta, timezone

from helpers import cabeceras, crear_lectura, crear_usuario
from models import ActiveReading


def _guardar(client, usuario, lectura, **extra):
    cuerpo = {
        "reading_id": lectura.id,
        "typology": lectura.typology,
        "current_level_index": 1,
        "current_question_index": 0,
        "reading_completed": True,
        "session_score": 35,
        "results_json": "[]",
        "tools_used_json": "{}",
        "reading_start_time": "0",
    }
    cuerpo.update(extra)
    return client.put("/progress/active-reading", json=cuerpo, headers=cabeceras(usuario))


def test_guardar_no_pone_caducidad(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)
    r = _guardar(client, usuario, lectura)
    assert r.status_code == 200
    assert r.json()["expires_at"] is None


def test_lectura_con_caducidad_pasada_no_se_borra(client, db):
    usuario, slot = crear_usuario(db)
    lectura = crear_lectura(db)
    db.add(ActiveReading(
        user_id=usuario.id, slot_id=slot.id, reading_id=lectura.id, typology="Narrativo",
        current_level_index=2, session_score=80,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    ))
    db.commit()
    r = client.get("/progress/active-reading", headers=cabeceras(usuario))
    assert r.status_code == 200
    assert (r.json()["reading_id"], r.json()["current_level_index"]) == (lectura.id, 2)
    db.expire_all()
    assert db.query(ActiveReading).filter_by(user_id=usuario.id).count() == 1


def test_segundos_ida_y_vuelta(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)
    _guardar(client, usuario, lectura, reading_seconds=95, total_seconds=300)
    datos = client.get("/progress/active-reading", headers=cabeceras(usuario)).json()
    assert (datos["reading_seconds"], datos["total_seconds"]) == (95, 300)


def test_volver_a_guardar_actualiza_los_segundos(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)
    _guardar(client, usuario, lectura, reading_seconds=95, total_seconds=300)
    _guardar(client, usuario, lectura, reading_seconds=95, total_seconds=420)
    datos = client.get("/progress/active-reading", headers=cabeceras(usuario)).json()
    assert datos["total_seconds"] == 420


def test_cliente_antiguo_sin_segundos(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)
    datos = _guardar(client, usuario, lectura).json()
    assert (datos["reading_seconds"], datos["total_seconds"]) == (0, 0)


def test_segundos_negativos_se_rechazan(client, db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)
    assert _guardar(client, usuario, lectura, total_seconds=-5).status_code == 422
