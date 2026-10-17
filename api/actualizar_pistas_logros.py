#!/usr/bin/env python3
"""
Pone al día las pistas de cuatro logros con las reglas nuevas del juego.

    docker exec vw-api-1 python actualizar_pistas_logros.py            # simulacro
    docker exec vw-api-1 python actualizar_pistas_logros.py --apply    # aplicar

Desde que las tipologías aprobadas se cierran, quien aprueba todo a la primera
juega exactamente 4 lecturas. Por eso Lector ávido pasa a pedir 4 lecturas y
las tres Estrellas, 6 aciertos acumulados en su nivel. El juego ya evalúa así
los logros; este script cambia el texto que ve el alumno en el panel de logros
(achievement_catalog.how_to_unlock).

Solo se cambia una pista si sigue teniendo el texto original: lo que se haya
editado desde el dashboard no se pisa. Repetirlo no cambia nada.

El simulacro ejecuta todo y al final hace rollback.
"""
from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import text

from database import SessionLocal
from reset_players import _url_censurada, comprobar_base_correcta

# id del logro -> (texto original, texto nuevo)
PISTAS: dict[str, tuple[str, str]] = {
    "avid_reader": (
        "Completar un total de 5 sesiones de lectura en cualquier combinación de tipologías.",
        "Completar un total de 4 sesiones de lectura en cualquier combinación de tipologías.",
    ),
    "star_literal": (
        "Obtener 100% de precisión en preguntas literales en al menos 3 sesiones.",
        "Acumular 6 respuestas correctas de nivel literal.",
    ),
    "star_inferencial": (
        "Responder correctamente todas las preguntas inferenciales en al menos 3 sesiones.",
        "Acumular 6 respuestas correctas de nivel inferencial.",
    ),
    "star_critico": (
        "Obtener 100% de precisión en preguntas de nivel crítico en al menos 3 sesiones.",
        "Acumular 6 respuestas correctas de nivel crítico.",
    ),
}


def actualizar_pistas(db) -> dict[str, bool]:
    """Cambia las pistas que siguen con el texto original. Devuelve, por logro,
    si su fila cambió. No hace commit."""
    cambios = {}
    for id_, (antes, ahora) in PISTAS.items():
        resultado = db.execute(
            text(
                "UPDATE achievement_catalog SET how_to_unlock = :ahora "
                "WHERE id = :id AND how_to_unlock = :antes"
            ),
            {"id": id_, "ahora": ahora, "antes": antes},
        )
        cambios[id_] = resultado.rowcount == 1
    return cambios


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Aplicar de verdad. Sin esto solo simula.")
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL no esta definida. No se adivina por seguridad.", file=sys.stderr)
        return 2

    comprobar_base_correcta()
    print(f"Base de destino: {_url_censurada()}\n")

    db = SessionLocal()
    try:
        cambios = actualizar_pistas(db)
        for id_, cambio in cambios.items():
            estado = "actualizada" if cambio else "sin cambios (ya nueva, editada o inexistente)"
            print(f"  {id_:<18} {estado}")
        if not args.apply:
            db.rollback()
            print("\nSIMULACRO. No se ha modificado nada. Añade --apply para ejecutarlo.")
            return 0
        db.commit()
        print("\nHecho. Pistas actualizadas.")
        return 0
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"\nERROR: {exc}\nRollback hecho: la base queda como estaba.", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
