"""
sembrar_entorno.py — Entorno de pruebas con 50 estudiantes.

Variante de seed_entorno_prueba.py del repositorio, sin la parte que
simula progreso. Aquella exige al menos 5 lecturas por tipología y el
catálogo tiene 4 en Narrativo, Argumentativo y Expositivo, así que
abortaba antes de crear nada.

Lo que sí hace, usando las mismas funciones del proyecto:
  - puebla el catálogo de logros
  - crea un administrador para el panel, si no hay ninguno
  - crea el entorno y lo activa si no hay otro activo
  - crea 50 cuentas de jugador, cada una con su partida 1 y las filas de
    progreso de las cuatro tipologías (solo Narrativo abierta)

Las cuentas quedan recién creadas, sin partidas jugadas. Es lo correcto
para unas cuentas de prueba: el progreso lo genera jugando.

Uso:  python sembrar_entorno.py [--entorno Pruebas] [--cuantos 50]
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import inspect

from auth import hash_password
from catalogo_logros import seed_achievements_catalog
from database import SessionLocal, engine
from models import PlayerSlot, User, Workspace
from workspaces import crear_jugador, entorno_activo

COLOR = "#d97706"
PASSWORD = "Test1234!"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "Admin1234!"
TABLAS = {"readings", "users", "workspaces", "player_slots"}


def comprobar_base():
    faltan = TABLAS - set(inspect(engine).get_table_names())
    if faltan:
        print("ABORTADO: no parece la base del entorno virtual. Faltan: %s"
              % sorted(faltan), file=sys.stderr)
        raise SystemExit(2)


def sembrar(db, nombre: str, cuantos: int) -> dict:
    seed_achievements_catalog(db)

    # Administrador del panel. Sin entorno: los admins no pertenecen a uno.
    admin = db.query(User).filter(User.is_admin.is_(True)).first()
    if admin is None:
        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            display_name="Administrador",
            character="male",
            is_admin=True,
            is_active=True,
            must_change_password=False,
        )
        db.add(admin)
        db.flush()
        creado_admin = True
    else:
        creado_admin = False

    # Entorno de trabajo.
    activo = entorno_activo(db)
    workspace = db.query(Workspace).filter(Workspace.name == nombre).first()
    if workspace is None:
        workspace = Workspace(name=nombre, color=COLOR, is_active=False)
        db.add(workspace)
        db.flush()
    if activo is None and not workspace.is_active:
        workspace.is_active = True

    # Si se repite el guion, las cuentas de este entorno se rehacen.
    previos = db.query(User).filter_by(workspace_id=workspace.id).all()
    for u in previos:
        db.delete(u)
    db.flush()

    for n in range(1, cuantos + 1):
        crear_jugador(
            db,
            workspace_id=workspace.id,
            email="alumno%d@test.com" % n,
            display_name="Alumno %d" % n,
            password=PASSWORD,
            must_change_password=False,
            character="male" if n % 2 else "women",
        )

    db.commit()
    return {
        "entorno": workspace.name,
        "activo": workspace.is_active,
        "borrados": len(previos),
        "alumnos": cuantos,
        "admin_creado": creado_admin,
        "partidas": db.query(PlayerSlot).count(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entorno", default="Pruebas")
    ap.add_argument("--cuantos", type=int, default=50)
    args = ap.parse_args()

    comprobar_base()
    db = SessionLocal()
    try:
        r = sembrar(db, args.entorno, args.cuantos)
    finally:
        db.close()

    print("Entorno '%s'%s" % (r["entorno"], ", activo" if r["activo"] else ""))
    if r["borrados"]:
        print("  se rehicieron %d cuentas que ya existian" % r["borrados"])
    print("  %d alumnos: alumno1@test.com .. alumno%d@test.com"
          % (r["alumnos"], r["alumnos"]))
    print("  contrasena de todos: %s" % PASSWORD)
    if r["admin_creado"]:
        print("  administrador creado: %s / %s" % (ADMIN_EMAIL, ADMIN_PASSWORD))
    else:
        print("  ya habia administrador, no se toco")
    print("  partidas creadas en total: %d" % r["partidas"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
