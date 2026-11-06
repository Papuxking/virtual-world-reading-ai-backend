#!/usr/bin/env python3
"""
Resetea el progreso de jugadores dejandolos como cuentas nuevas.

    docker exec vw-api-1 python reset_players.py --students 50 --demo --apply
    docker exec vw-api-1 python reset_players.py --entorno "Pruebas" --students 50 --apply

Trabaja dentro de un entorno: --entorno NOMBRE o, sin el, el activo. Solo busca
los correos en ese entorno (el mismo correo puede tener cuenta en otros).
Borra sesiones, respuestas, herramientas, notas, logros, interacciones con el
NPC, lecturas activas, slots extra y progreso de tipologias, y:

  - Acepta ademas la cuenta de demostracion (--demo).
  - NO trae un DATABASE_URL por defecto. Los scripts antiguos caian a
    localhost:5433, que hoy es el Postgres de LecturaIA: ejecutarlos fuera del
    contenedor sin la variable puesta habria escrito en la base de otro autor.
  - Comprueba antes de tocar nada que la base de destino es la del entorno
    virtual, mirando que existan sus tablas propias.
  - Por defecto simula. Hay que pasar --apply para escribir.
"""
from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import func, inspect

from database import SessionLocal, engine
from models import (
    ActiveReading,
    NpcInteraction,
    PlayerAchievement,
    PlayerAnswer,
    PlayerNote,
    PlayerSession,
    PlayerSlot,
    PlayerTypologyProgress,
    SessionTool,
    User,
)

from game_rules import DIFFICULTY_ORDER

# Tablas que solo existen en la base del entorno virtual. Si faltan, estamos
# apuntando a otra base y hay que parar.
TABLAS_PROPIAS = {"readings", "player_typology_progress", "achievement_catalog", "player_slots"}


def comprobar_base_correcta() -> None:
    existentes = set(inspect(engine).get_table_names())
    faltan = TABLAS_PROPIAS - existentes
    if faltan:
        print(
            "ABORTADO: la base de datos de destino no parece la del entorno virtual.\n"
            f"  Faltan las tablas: {sorted(faltan)}\n"
            f"  URL usada: {_url_censurada()}\n"
            "  Comprueba DATABASE_URL. El puerto 5433 es el Postgres de LecturaIA.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _url_censurada() -> str:
    url = os.environ.get("DATABASE_URL", "(sin DATABASE_URL)")
    if "@" in url and "//" in url:
        esquema, resto = url.split("//", 1)
        _, destino = resto.split("@", 1)
        return f"{esquema}//***@{destino}"
    return url


def resetear_usuario(db, user: User) -> None:
    """Deja al usuario como recien creado, conservando la cuenta en si."""
    db.query(ActiveReading).filter(ActiveReading.user_id == user.id).delete()
    db.query(NpcInteraction).filter(NpcInteraction.user_id == user.id).delete()
    db.query(PlayerNote).filter(PlayerNote.user_id == user.id).delete()
    db.query(PlayerAchievement).filter(PlayerAchievement.user_id == user.id).delete()

    for s in db.query(PlayerSession).filter(PlayerSession.user_id == user.id).all():
        db.query(PlayerAnswer).filter(PlayerAnswer.session_id == s.id).delete()
        db.query(SessionTool).filter(SessionTool.session_id == s.id).delete()
    db.query(PlayerSession).filter(PlayerSession.user_id == user.id).delete()

    db.query(PlayerSlot).filter(
        PlayerSlot.user_id == user.id, PlayerSlot.slot_number > 1
    ).delete()

    slot1 = (
        db.query(PlayerSlot)
        .filter(PlayerSlot.user_id == user.id, PlayerSlot.slot_number == 1)
        .first()
    )
    if not slot1:
        slot1 = PlayerSlot(user_id=user.id, slot_number=1, label="Sesión 1", is_active=True)
        db.add(slot1)
        db.flush()
    else:
        slot1.is_active = True
        slot1.label = "Sesión 1"

    db.query(PlayerTypologyProgress).filter(
        PlayerTypologyProgress.user_id == user.id
    ).delete()
    for typology in DIFFICULTY_ORDER:
        db.add(
            PlayerTypologyProgress(
                user_id=user.id,
                slot_id=slot1.id,
                typology=typology,
                is_unlocked=(typology == "Narrativo"),
                best_score=0,
                total_sessions=0,
                perfect_sessions=0,
                first_completed_at=None,
                last_played_at=None,
            )
        )

    user.session_version = (user.session_version or 1) + 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entorno", default="", help="Nombre del entorno donde resetear (por defecto, el activo)")
    ap.add_argument("--students", type=int, default=0, help="Resetea alumno1@test.com .. alumnoN@test.com")
    ap.add_argument("--demo", action="store_true", help="Incluye demo@demo.com")
    ap.add_argument("--emails", default="", help="Lista extra de correos separados por coma")
    ap.add_argument("--apply", action="store_true", help="Aplicar de verdad. Sin esto solo simula.")
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL no esta definida. No se adivina por seguridad.", file=sys.stderr)
        return 2

    objetivos: list[str] = [f"alumno{i}@test.com" for i in range(1, args.students + 1)]
    if args.demo:
        objetivos.append("demo@demo.com")
    objetivos += [e.strip() for e in args.emails.split(",") if e.strip()]

    if not objetivos:
        print("No se ha indicado a quien resetear. Usa --students, --demo o --emails.", file=sys.stderr)
        return 2

    comprobar_base_correcta()
    print(f"Base de destino: {_url_censurada()}")
    print(f"Cuentas a resetear: {len(objetivos)}\n")

    db = SessionLocal()
    try:
        from models import Workspace
        from workspaces import entorno_activo

        if args.entorno:
            # Los nombres de entorno son únicos sin distinguir mayúsculas.
            entorno = db.query(Workspace).filter(func.lower(Workspace.name) == args.entorno.strip().lower()).first()
            if not entorno:
                print(f"ERROR: No se encontró el entorno '{args.entorno}'.", file=sys.stderr)
                return 2
        else:
            entorno = entorno_activo(db)
            if not entorno:
                print("ERROR: No hay ningún entorno activo. Pasa --entorno NOMBRE.", file=sys.stderr)
                return 2

        print(f"Entorno objetivo: {entorno.name} (ID: {entorno.id})")

        encontrados, ausentes = [], []
        for email in objetivos:
            user = db.query(User).filter(User.email == email, User.workspace_id == entorno.id).first()
            (encontrados if user else ausentes).append(email)

        print(f"  encontradas: {len(encontrados)}")
        if ausentes:
            print(f"  NO existen ({len(ausentes)}): {', '.join(ausentes[:5])}"
                  f"{'...' if len(ausentes) > 5 else ''}")

        # Cuanto progreso se va a borrar, para que el simulacro sea util.
        if encontrados:
            ids = [db.query(User).filter(User.email == e, User.workspace_id == entorno.id).first().id for e in encontrados]
            n_ses = db.query(PlayerSession).filter(PlayerSession.user_id.in_(ids)).count()
            n_log = db.query(PlayerAchievement).filter(PlayerAchievement.user_id.in_(ids)).count()
            print(f"  sesiones que se borran: {n_ses}")
            print(f"  logros que se borran  : {n_log}")

        if not args.apply:
            print("\nSIMULACRO. No se ha modificado nada. Anade --apply para ejecutarlo.")
            return 0

        print("\nAplicando...")
        for email in encontrados:
            user = db.query(User).filter(User.email == email, User.workspace_id == entorno.id).first()
            resetear_usuario(db, user)
        db.commit()
        print(f"Hecho: {len(encontrados)} cuentas reseteadas a estado inicial "
              "(slot 1, solo Narrativo desbloqueado, 0 sesiones).")
        if ausentes:
            print(f"Sin tocar (no existen): {len(ausentes)}")
        return 0

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"\nERROR: {exc}\nRollback hecho: la base queda como estaba.", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
