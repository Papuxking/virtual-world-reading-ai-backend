"""La migración 010 añade las columnas de intentos y de segundos de lectura, y
se puede aplicar las veces que haga falta (la API la ejecuta al arrancar)."""
from sqlalchemy import text

from database import engine
from esquema import aplicar_migraciones
from helpers import crear_usuario
from models import PlayerTypologyProgress


def test_migracion_se_puede_aplicar_dos_veces(db):
    aplicar_migraciones(engine)
    aplicar_migraciones(engine)


def test_columnas_nuevas_existen(db):
    aplicar_migraciones(engine)
    columnas = {
        (tabla, columna)
        for tabla, columna in db.execute(text(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_name IN ('player_typology_progress', 'active_readings')"
        )).all()
    }
    assert ("player_typology_progress", "attempts_used") in columnas
    assert ("active_readings", "reading_seconds") in columnas
    assert ("active_readings", "total_seconds") in columnas


def test_fila_nueva_empieza_con_cero_intentos(db):
    _, slot = crear_usuario(db)
    filas = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id).all()
    assert len(filas) == 4
    assert {f.attempts_used for f in filas} == {0}


def test_fila_creada_por_sql_sin_el_campo_empieza_en_cero(db):
    # Así entran las filas que ya existían: la columna se añade con DEFAULT 0.
    usuario, slot = crear_usuario(db, filas=False)
    db.execute(text(
        "INSERT INTO player_typology_progress (user_id, slot_id, typology, best_score, "
        "total_sessions, perfect_sessions, is_unlocked) VALUES (:u, :s, 'Narrativo', 0, 0, 0, true)"
    ), {"u": usuario.id, "s": slot.id})
    db.commit()
    fila = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id).one()
    assert fila.attempts_used == 0
