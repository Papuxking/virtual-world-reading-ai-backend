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


def aplicar_migraciones(engine) -> None:
    """Aplica las migraciones al arrancar, todas en una transacción."""
    with engine.begin() as conn:
        for ruta in MIGRACIONES_AL_ARRANCAR:
            for sentencia in sentencias_sql(ruta):
                conn.execute(text(sentencia))
