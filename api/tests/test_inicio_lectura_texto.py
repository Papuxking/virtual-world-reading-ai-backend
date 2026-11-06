"""Las bases creadas con sql/009_create_active_readings.sql tienen reading_start_time
como FLOAT, pero el modelo y la respuesta lo declaran texto: guardar o leer la
lectura en curso respondía 500. La migración 010 lo convierte a texto."""
import pytest
from sqlalchemy import text

from database import engine
from esquema import aplicar_migraciones
from helpers import cabeceras, crear_lectura, crear_usuario
from test_lectura_activa import _guardar


def _tipo_columna() -> str:
    with engine.connect() as conn:
        return conn.execute(text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'active_readings' AND column_name = 'reading_start_time'"
        )).scalar()


@pytest.fixture
def columna_float():
    """La columna como en esas bases (FLOAT DEFAULT 0); al final, otra vez texto."""
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE active_readings ALTER COLUMN reading_start_time DROP DEFAULT"))
        conn.execute(text(
            "ALTER TABLE active_readings ALTER COLUMN reading_start_time "
            "TYPE DOUBLE PRECISION USING reading_start_time::double precision"
        ))
        conn.execute(text("ALTER TABLE active_readings ALTER COLUMN reading_start_time SET DEFAULT 0"))
    yield
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE active_readings ALTER COLUMN reading_start_time DROP DEFAULT"))
        conn.execute(text(
            "ALTER TABLE active_readings ALTER COLUMN reading_start_time "
            "TYPE VARCHAR(50) USING reading_start_time::text"
        ))
        conn.execute(text("ALTER TABLE active_readings ALTER COLUMN reading_start_time SET DEFAULT '0'"))


def test_la_migracion_deja_la_columna_como_texto(columna_float):
    aplicar_migraciones(engine)
    assert _tipo_columna() == "character varying"


def test_guardar_y_leer_la_lectura_en_curso_tras_migrar(columna_float, client, db):
    aplicar_migraciones(engine)
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)

    r = _guardar(client, usuario, lectura, reading_start_time="267.014")
    assert r.status_code == 200
    assert r.json()["reading_start_time"] == "267.014"

    r = client.get("/progress/active-reading", headers=cabeceras(usuario))
    assert r.status_code == 200
    assert r.json()["reading_start_time"] == "267.014"


def test_migrar_una_columna_que_ya_es_texto_no_cambia_nada(client, db):
    aplicar_migraciones(engine)
    assert _tipo_columna() == "character varying"
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)
    assert _guardar(client, usuario, lectura, reading_start_time="12.5").json()["reading_start_time"] == "12.5"
