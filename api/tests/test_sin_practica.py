"""La práctica ya no existe: la API borra sus datos y sus columnas al arrancar
(esquema.quitar_practica) y ningún endpoint la acepta ni la devuelve."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import main
from database import engine
from esquema import aplicar_migraciones
from helpers import cabeceras, crear_lectura, crear_usuario, payload_sesion
from models import (
    ActiveReading, Answer, NpcInteraction, PlayerAnswer, PlayerNote, PlayerSession,
    Question, Reading, UserReading,
)


def _columnas(db, tabla):
    return {c for (c,) in db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = :t"
    ), {"t": tabla}).all()}


def _indices_de_practica(db):
    return {n for (n,) in db.execute(text(
        "SELECT indexname FROM pg_indexes "
        "WHERE schemaname = current_schema() AND indexname LIKE '%practice%'"
    )).all()}


@pytest.fixture
def base_con_practica(db):
    """Una base de antes: con las columnas e índices que añadía la 009."""
    with engine.begin() as conn:
        for tabla in ("readings", "player_sessions"):
            conn.execute(text(
                f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS is_practice BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_readings_typology_practice ON readings (typology, is_practice)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_player_sessions_practice "
            "ON player_sessions (user_id, slot_id, is_practice)"
        ))
    yield
    # El esquema de pruebas es compartido: que no quede nada de la simulación.
    # Antes, cerrar la transacción de la prueba: sus bloqueos dejarían el
    # ALTER TABLE esperando para siempre.
    db.rollback()
    with engine.begin() as conn:
        for tabla in ("readings", "player_sessions"):
            conn.execute(text(f"ALTER TABLE {tabla} DROP COLUMN IF EXISTS is_practice"))


def test_migracion_borra_la_practica_y_sus_columnas(client, db, base_con_practica):
    usuario, slot = crear_usuario(db)
    progresion = crear_lectura(db, "Progresión", "Narrativo")
    practica = crear_lectura(db, "Práctica", "Narrativo")
    sesiones = {}
    for nombre, lectura in (("progresion", progresion), ("practica", practica)):
        r = client.post("/progress/sessions", json=payload_sesion(db, lectura), headers=cabeceras(usuario))
        assert r.status_code == 201
        sesiones[nombre] = r.json()["id"]
    db.execute(text("UPDATE readings SET is_practice = true WHERE id = :id"), {"id": practica.id})
    db.execute(text("UPDATE player_sessions SET is_practice = true WHERE id = :id"), {"id": sesiones["practica"]})
    db.add(PlayerNote(user_id=usuario.id, slot_id=slot.id, reading_id=practica.id,
                      session_id=sesiones["practica"], note_content="Nota de práctica"))
    db.add(ActiveReading(user_id=usuario.id, slot_id=slot.id, reading_id=practica.id, typology="Narrativo"))
    db.add(UserReading(user_id=str(usuario.id), reading_id=practica.id))
    npc = NpcInteraction(user_id=usuario.id, slot_id=slot.id, npc_type="robot", reading_id=practica.id)
    db.add(npc)
    db.flush()
    npc_id, practica_id, progresion_id = npc.id, practica.id, progresion.id
    # Sin transacción abierta: la migración cambia tablas que esta sesión leyó.
    db.commit()

    aplicar_migraciones(engine)
    db.expire_all()

    assert "is_practice" not in _columnas(db, "readings")
    assert "is_practice" not in _columnas(db, "player_sessions")
    assert _indices_de_practica(db) == set()
    assert db.get(Reading, practica_id) is None
    assert db.query(Question).filter_by(reading_id=practica_id).count() == 0
    assert db.get(PlayerSession, sesiones["practica"]) is None
    assert db.query(PlayerAnswer).filter_by(session_id=sesiones["practica"]).count() == 0
    assert db.query(PlayerNote).filter_by(reading_id=practica_id).count() == 0
    assert db.query(ActiveReading).filter_by(reading_id=practica_id).count() == 0
    assert db.query(UserReading).filter_by(reading_id=practica_id).count() == 0
    assert db.get(NpcInteraction, npc_id).reading_id is None
    # Lo de progresión no se toca.
    assert db.get(Reading, progresion_id) is not None
    assert db.get(PlayerSession, sesiones["progresion"]) is not None
    assert db.query(Answer).join(Question).filter(Question.reading_id == progresion_id).count() == 24


def test_migracion_sin_practica_no_hace_nada(db):
    aplicar_migraciones(engine)
    aplicar_migraciones(engine)
    assert "is_practice" not in _columnas(db, "readings")
    assert "is_practice" not in _columnas(db, "player_sessions")


def test_la_api_ya_no_habla_de_practica(client, db):
    usuario, _ = crear_usuario(db)
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    lectura = crear_lectura(db, "Única", "Narrativo")

    assert "practice_sessions" not in client.get("/progress/me", headers=cabeceras(usuario)).json()
    jugadores = client.get("/admin/players", headers=cabeceras(admin)).json()
    assert jugadores and all("practice_sessions" not in j for j in jugadores)
    assert "practice_sessions" not in client.get(f"/admin/players/{usuario.id}", headers=cabeceras(admin)).json()
    assert "total_practice_sessions" not in client.get("/admin/stats", headers=cabeceras(admin)).json()

    r = client.get("/readings/random/full", params={"typology": "Narrativo", "practice": "true"})
    assert r.status_code == 200
    assert r.json()["id"] == lectura.id
    assert "is_practice" not in r.json()


def test_sesion_de_lectura_inexistente_da_404(db):
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db, "Borrada", "Narrativo")
    datos = payload_sesion(db, lectura)
    db.delete(lectura)
    db.commit()
    client = TestClient(main.app, raise_server_exceptions=False)
    r = client.post("/progress/sessions", json=datos, headers=cabeceras(usuario))
    assert r.status_code == 404
    assert r.json()["detail"] == "Lectura no encontrada"
