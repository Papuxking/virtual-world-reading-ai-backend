"""
alta_alumnos.py — Da de alta a los estudiantes de nivelación y retira las
cuentas de prueba.

Se ejecuta dentro del contenedor de la API del entorno virtual, que es
donde están la conexión y las funciones del proyecto.

Lee /tmp/alumnos.json con [{email, display_name, password}, ...].

Por defecto solo simula. Con --aplicar escribe.
"""
from __future__ import annotations

import argparse
import json
import sys

from auth import hash_password  # noqa: F401  (lo usa crear_jugador)
from database import SessionLocal
from models import User, Workspace
from workspaces import crear_jugador, entorno_activo

ENTORNO_PRUEBAS = "Pruebas"
COLOR = "#2563eb"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="/tmp/alumnos.json")
    ap.add_argument("--entorno", default="Educacion Basica")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    with open(args.json, encoding="utf-8") as f:
        alumnos = json.load(f)

    db = SessionLocal()
    try:
        # ── Qué se va a retirar ─────────────────────────────────────────
        pruebas = db.query(Workspace).filter(Workspace.name == ENTORNO_PRUEBAS).first()
        a_borrar = []
        if pruebas:
            a_borrar = db.query(User).filter_by(workspace_id=pruebas.id).all()

        # ── Qué se va a crear ───────────────────────────────────────────
        destino = db.query(Workspace).filter(Workspace.name == args.entorno).first()
        ya_estan = []
        if destino:
            correos = {u.email.lower() for u in
                       db.query(User).filter_by(workspace_id=destino.id).all()}
            ya_estan = [a for a in alumnos if a["email"].lower() in correos]

        print("Entorno de pruebas '%s': %d cuentas que se retiran"
              % (ENTORNO_PRUEBAS, len(a_borrar)))
        print("Entorno destino '%s': %s"
              % (args.entorno, "ya existe" if destino else "se crea"))
        print("Alumnos en el archivo: %d" % len(alumnos))
        print("  de esos, ya existian: %d" % len(ya_estan))
        print("  se crearian: %d" % (len(alumnos) - len(ya_estan)))

        if not args.aplicar:
            print()
            print("SIMULACRO. No se ha tocado nada. Anade --aplicar.")
            return 0

        # ── Retirar las de prueba ───────────────────────────────────────
        for u in a_borrar:
            db.delete(u)
        db.flush()

        # ── Crear el entorno destino y activarlo ────────────────────────
        if destino is None:
            destino = Workspace(name=args.entorno, color=COLOR, is_active=False)
            db.add(destino)
            db.flush()

        activo = entorno_activo(db)
        if activo is None or (activo.id == (pruebas.id if pruebas else -1)):
            # El de pruebas se queda sin gente: el activo pasa a ser este.
            if activo is not None and activo.id != destino.id:
                activo.is_active = False
                db.flush()
            destino.is_active = True

        # ── Alta de los alumnos ─────────────────────────────────────────
        creados = 0
        existentes = {u.email.lower() for u in
                      db.query(User).filter_by(workspace_id=destino.id).all()}
        for a in alumnos:
            if a["email"].lower() in existentes:
                continue
            crear_jugador(
                db,
                workspace_id=destino.id,
                email=a["email"],
                display_name=a["display_name"][:100],
                password=a["password"],
                must_change_password=False,
            )
            creados += 1

        db.commit()

        total = db.query(User).filter_by(workspace_id=destino.id).count()
        print()
        print("Hecho.")
        print("  retiradas    : %d cuentas de prueba" % len(a_borrar))
        print("  creadas      : %d" % creados)
        print("  en el entorno: %d alumnos" % total)
        print("  entorno activo: %s" % (destino.name if destino.is_active else "otro"))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
