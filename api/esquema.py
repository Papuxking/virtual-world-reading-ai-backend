"""
esquema.py — Cambios de esquema que la API aplica sola al arrancar.

create_all solo crea las tablas que faltan: no añade columnas a las que ya
existen. Las migraciones de aquí son sentencias idempotentes (IF NOT EXISTS),
así que se ejecutan en cada arranque y un despliegue no puede olvidarse de
ellas.
"""
from pathlib import Path

from sqlalchemy import text

SQL_DIR = Path(__file__).resolve().parent / "sql"

# Por orden. Cada fichero debe poder ejecutarse cualquier número de veces.
MIGRACIONES_AL_ARRANCAR = [
    SQL_DIR / "010_intentos_y_reanudacion.sql",
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


def aplicar_migraciones(engine) -> None:
    """Aplica las migraciones al arrancar, todas en una transacción."""
    with engine.begin() as conn:
        for ruta in MIGRACIONES_AL_ARRANCAR:
            for sentencia in sentencias_sql(ruta):
                conn.execute(text(sentencia))
        quitar_practica(conn)
