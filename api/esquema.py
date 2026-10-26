"""
esquema.py — Cambios de esquema que la API aplica sola al arrancar.

create_all solo crea las tablas que faltan: no añade columnas a las que ya
existen. Las migraciones de aquí son sentencias idempotentes (IF NOT EXISTS),
así que se ejecutan en cada arranque y un despliegue no puede olvidarse de
ellas.
"""
import logging
from pathlib import Path

from sqlalchemy import text

import models  # noqa: F401  (registra las tablas en Base.metadata)
from database import Base

SQL_DIR = Path(__file__).resolve().parent / "sql"

# Clave del candado de Postgres con el que los procesos de la API se turnan
# para preparar la base. Número arbitrario, solo lo usa este código.
CANDADO_ESQUEMA = 7202610

# Por orden. Cada fichero debe poder ejecutarse cualquier número de veces.
MIGRACIONES_AL_ARRANCAR = [
    SQL_DIR / "010_intentos_y_reanudacion.sql",
    SQL_DIR / "011_entornos.sql",
    SQL_DIR / "012_conversaciones_asistente.sql",
    SQL_DIR / "013_alias_y_vitrina.sql",
    SQL_DIR / "014_insignias_logros.sql",
    SQL_DIR / "015_comics.sql",
]


def sentencias_sql(ruta: Path) -> list[str]:
    """Sentencias de un fichero .sql, sin las líneas de comentario."""
    lineas = [
        linea for linea in ruta.read_text(encoding="utf-8").splitlines()
        if not linea.strip().startswith("--")
    ]
    return [s.strip() for s in "\n".join(lineas).split(";") if s.strip()]


def quitar_practica(conn) -> None:
    """Borra la zona de práctica, que ya no existe: sus sesiones, sus lecturas
    (las cascadas arrastran preguntas, respuestas, notas, lecturas en curso e
    historial; las interacciones con el NPC se quedan sin lectura) y las
    columnas is_practice. Solo actúa si las columnas siguen ahí: en una base
    nueva nunca llegan a existir."""
    con_practica = set(conn.execute(text(
        "SELECT table_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND column_name = 'is_practice' "
        "AND table_name IN ('readings', 'player_sessions')"
    )).scalars())
    if "player_sessions" in con_practica:
        conn.execute(text("DELETE FROM player_sessions WHERE is_practice"))
    if "readings" in con_practica:
        conn.execute(text("DELETE FROM readings WHERE is_practice"))
    conn.execute(text("DROP INDEX IF EXISTS idx_readings_typology_practice"))
    conn.execute(text("DROP INDEX IF EXISTS idx_player_sessions_practice"))
    for tabla in con_practica:
        conn.execute(text(f"ALTER TABLE {tabla} DROP COLUMN IF EXISTS is_practice"))


def preparar_base(engine) -> None:
    """Lo que hace la API al arrancar: crear las tablas que falten y aplicar
    las migraciones, en una transacción y con el candado puesto."""
    with engine.begin() as conn:
        _esperar_turno(conn)
        Base.metadata.create_all(bind=conn)
        _migrar(conn)


def aplicar_migraciones(engine) -> None:
    """Aplica las migraciones, todas en una transacción y con el candado."""
    with engine.begin() as conn:
        _esperar_turno(conn)
        _migrar(conn)


def _esperar_turno(conn) -> None:
    """La API arranca varios procesos (2 en producción) y cada uno prepara la
    base al importarse: sin turno, dos crean la misma tabla a la vez y uno se
    cae. El candado dura hasta el final de la transacción."""
    conn.execute(text("SELECT pg_advisory_xact_lock(:clave)"), {"clave": CANDADO_ESQUEMA})


def _migrar(conn) -> None:
    for ruta in MIGRACIONES_AL_ARRANCAR:
        for sentencia in sentencias_sql(ruta):
            conn.execute(text(sentencia))
        logging.getLogger("uvicorn.error").info("Migración aplicada: %s", ruta.name)
    quitar_practica(conn)
