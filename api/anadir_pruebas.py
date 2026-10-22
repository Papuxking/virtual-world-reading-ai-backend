"""
anadir_pruebas.py — Agrega cuentas de prueba a un entorno existente.

No borra nada ni toca el entorno activo: solo añade. Si una cuenta ya
existe en ese entorno, la deja como está.

    python anadir_pruebas.py --entorno Test --cuantos 3
    python anadir_pruebas.py --entorno Test --cuantos 3 --aplicar
"""
from __future__ import annotations

import argparse
import sys

from database import SessionLocal
from models import User, Workspace
from workspaces import crear_jugador

PASSWORD = "Test1234!"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entorno", default="Test")
    ap.add_argument("--cuantos", type=int, default=3)
    ap.add_argument("--prefijo", default="prueba")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        ws = db.query(Workspace).filter(Workspace.name == args.entorno).first()
        if ws is None:
            print("No existe el entorno '%s'. Los que hay: %s"
                  % (args.entorno,
                     [w.name for w in db.query(Workspace).all()]), file=sys.stderr)
            return 2

        previos = db.query(User).filter_by(workspace_id=ws.id).all()
        correos = {u.email.lower() for u in previos}

        pendientes = []
        for n in range(1, args.cuantos + 1):
            correo = "%s%d@test.com" % (args.prefijo, n)
            if correo.lower() in correos:
                continue
            pendientes.append((correo, "Prueba %d" % n))

        print("Entorno '%s' (id %d), activo: %s" % (ws.name, ws.id, ws.is_active))
        print("  cuentas que ya tenia: %d" % len(previos))
        print("  se crearian: %d" % len(pendientes))
        for correo, nombre in pendientes:
            print("    %-24s %s" % (correo, nombre))

        if not args.aplicar:
            print()
            print("SIMULACRO. No se ha tocado nada. Anade --aplicar.")
            return 0

        for i, (correo, nombre) in enumerate(pendientes):
            crear_jugador(
                db,
                workspace_id=ws.id,
                email=correo,
                display_name=nombre,
                password=PASSWORD,
                must_change_password=False,
                character="male" if i % 2 == 0 else "women",
            )
        db.commit()

        total = db.query(User).filter_by(workspace_id=ws.id).count()
        print()
        print("Hecho. %d creadas, %d cuentas en el entorno." % (len(pendientes), total))
        print("Contrasena de todas: %s" % PASSWORD)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
