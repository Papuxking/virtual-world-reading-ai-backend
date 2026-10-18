#!/usr/bin/env python3
"""
Migra la base al juego de 4 tipologías con zona de práctica.

    docker exec vw-api-1 python migrate_practice_mode.py            # simulacro
    docker exec vw-api-1 python migrate_practice_mode.py --apply    # aplicar

Todo ocurre en UNA transacción, en este orden:
  1. Columnas is_practice (api/sql/009_practice_mode.sql).
  2. Se borra todo lo de Instructivo: lecturas pendientes, respuestas de
     alumnos, herramientas, notas, sesiones, preguntas, opciones, lecturas y
     filas de progreso. Las interacciones con el NPC se conservan, pero pierden
     la referencia a la sesión y a la lectura borradas.
  3. Cada slot queda con sus 4 filas de progreso y se recalculan los
     desbloqueos SIN bloquear nunca: quien llegue al umbral en Argumentativo
     pasa a tener Expositivo abierto.
  4. Se cargan las lecturas de práctica del JSON. Se saltan los títulos que ya
     existen, así que repetir la migración no duplica nada.
  5. El texto del logro Explorador pasa a "4 tipologías" solo si sigue siendo
     el original: no se pisa lo editado desde el dashboard.
  6. Se verifica el resultado. Si algo no cuadra, rollback.

El simulacro ejecuta TODO y al final hace rollback: el informe que enseña es el
de una ejecución real.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import func as sqlfunc, text

from database import SessionLocal
from esquema import sentencias_sql
from game_rules import DIFFICULTY_ORDER
from import_json_readings import join_paragraphs, normalize_level
from models import PlayerSlot, PlayerTypologyProgress, Reading
from progression import ensure_typology_rows, reevaluate_unlocks
from replace_readings import insertar_lecturas, validar_json
from reset_players import _url_censurada, comprobar_base_correcta

TIPOLOGIA_RETIRADA = "Instructivo"
SQL_COLUMNAS = Path(__file__).resolve().parent / "sql" / "009_practice_mode.sql"

LECTURAS_POR_TIPOLOGIA = 3
PREGUNTAS_POR_NIVEL = {"Literal": 4, "Inferencial": 4, "Critico": 4}
CARACTERES_MIN = 2000
CARACTERES_MAX = 4500

EXPLORADOR_ANTES = "Completar al menos 1 sesión en cada una de las 5 tipologías textuales."
EXPLORADOR_AHORA = "Completar al menos 1 sesión en cada una de las 4 tipologías textuales."

_LECTURAS = "SELECT id FROM readings WHERE typology = :t"
_SESIONES = f"SELECT id FROM player_sessions WHERE typology = :t OR reading_id IN ({_LECTURAS})"

# (qué se cuenta en el informe, sentencia). El orden importa: primero lo que
# cuelga de las sesiones y de las lecturas; las lecturas, al final.
BORRADO = [
    ("lecturas pendientes",
     f"DELETE FROM active_readings WHERE typology = :t OR reading_id IN ({_LECTURAS})"),
    ("respuestas de alumnos", f"DELETE FROM player_answers WHERE session_id IN ({_SESIONES})"),
    ("herramientas de sesión", f"DELETE FROM session_tools WHERE session_id IN ({_SESIONES})"),
    ("notas", f"DELETE FROM player_notes WHERE reading_id IN ({_LECTURAS})"),
    ("notas desvinculadas de su sesión",
     f"UPDATE player_notes SET session_id = NULL WHERE session_id IN ({_SESIONES})"),
    ("interacciones NPC desvinculadas de su sesión",
     f"UPDATE npc_interactions SET session_id = NULL WHERE session_id IN ({_SESIONES})"),
    ("sesiones", f"DELETE FROM player_sessions WHERE id IN ({_SESIONES})"),
    ("interacciones NPC desvinculadas de su lectura",
     f"UPDATE npc_interactions SET reading_id = NULL WHERE reading_id IN ({_LECTURAS})"),
    ("lecturas vistas (user_readings)", f"DELETE FROM user_readings WHERE reading_id IN ({_LECTURAS})"),
    ("opciones de respuesta",
     f"DELETE FROM answers WHERE question_id IN (SELECT id FROM questions WHERE reading_id IN ({_LECTURAS}))"),
    ("preguntas", f"DELETE FROM questions WHERE reading_id IN ({_LECTURAS})"),
    ("lecturas", "DELETE FROM readings WHERE typology = :t"),
    ("filas de progreso", "DELETE FROM player_typology_progress WHERE typology = :t"),
]


# ── Validación del JSON de práctica ──────────────────────────────────────────

def validar_lecturas_practica(datos: dict) -> list[str]:
    """Problemas del JSON de práctica; vacío si se puede cargar."""
    problemas = validar_json(datos, None)
    por_tipologia = {t: 0 for t in DIFFICULTY_ORDER}
    for lectura in datos.get("readings", []):
        titulo = (lectura.get("title") or "").strip() or "(sin título)"
        tipologia = (lectura.get("typology") or "").strip()
        if tipologia not in por_tipologia:
            problemas.append(f"{titulo}: tipología '{tipologia}' fuera del juego")
            continue
        por_tipologia[tipologia] += 1

        caracteres = len(join_paragraphs(lectura.get("text") or []))
        if not CARACTERES_MIN <= caracteres <= CARACTERES_MAX:
            problemas.append(
                f"{titulo}: {caracteres} caracteres, se esperaban entre {CARACTERES_MIN} y {CARACTERES_MAX}"
            )

        actividades = lectura.get("activites", [])
        niveles = {}
        for act in actividades:
            nivel = normalize_level(act.get("comprehension_level", ""))
            niveles[nivel] = niveles.get(nivel, 0) + 1
        if niveles != PREGUNTAS_POR_NIVEL:
            problemas.append(f"{titulo}: preguntas por nivel {niveles}, se esperaban {PREGUNTAS_POR_NIVEL}")

        correctas = [(a.get("correct_answer") or "").strip().upper() for a in actividades]
        if correctas and max(correctas.count(letra) for letra in "ABCD") > len(correctas) // 2:
            problemas.append(f"{titulo}: más de la mitad de las respuestas correctas son la misma letra")

    for tipologia, n in por_tipologia.items():
        if n != LECTURAS_POR_TIPOLOGIA:
            problemas.append(f"{tipologia}: {n} lecturas de práctica, se esperaban {LECTURAS_POR_TIPOLOGIA}")
    return problemas


# ── Pasos de la migración ────────────────────────────────────────────────────

def aplicar_columnas(db) -> None:
    for sentencia in sentencias_sql(SQL_COLUMNAS):
        db.execute(text(sentencia))


def alumnos_afectados(db) -> list[tuple]:
    """(email, slot, puntos) de quienes tenían puntaje en la tipología retirada."""
    filas = db.execute(text(
        "SELECT u.email, s.slot_number, p.best_score "
        "FROM player_typology_progress p "
        "JOIN users u ON u.id = p.user_id "
        "JOIN player_slots s ON s.id = p.slot_id "
        "WHERE p.typology = :t AND p.best_score > 0 "
        "ORDER BY p.best_score DESC, u.email"
    ), {"t": TIPOLOGIA_RETIRADA}).fetchall()
    return [tuple(f) for f in filas]


def borrar_tipologia_retirada(db) -> dict:
    """Ejecuta BORRADO en orden. Devuelve cuántas filas tocó cada sentencia."""
    return {
        etiqueta: db.execute(text(sentencia), {"t": TIPOLOGIA_RETIRADA}).rowcount
        for etiqueta, sentencia in BORRADO
    }


def _desbloqueadas(db) -> dict:
    filas = (
        db.query(PlayerTypologyProgress.typology, sqlfunc.count(PlayerTypologyProgress.id))
        .filter(PlayerTypologyProgress.is_unlocked == True)
        .group_by(PlayerTypologyProgress.typology)
        .all()
    )
    return dict(filas)


def normalizar_slots(db) -> dict:
    """Cada slot con sus 4 filas y los desbloqueos recalculados sin bloquear.
    Devuelve, por tipología, cuántos slots la tenían abierta antes y después."""
    antes = _desbloqueadas(db)
    for slot in db.query(PlayerSlot).all():
        ensure_typology_rows(db, slot.user_id, slot.id)
        reevaluate_unlocks(db, slot.user_id, slot.id, only_unlock=True)
    db.flush()
    despues = _desbloqueadas(db)
    return {t: (antes.get(t, 0), despues.get(t, 0)) for t in DIFFICULTY_ORDER}


def cargar_lecturas_practica(db, lecturas: list[dict]) -> dict:
    """Inserta como práctica las lecturas cuyo título aún no existe."""
    existentes = {titulo for (titulo,) in db.execute(text("SELECT title FROM readings")).fetchall()}
    nuevas = [lectura for lectura in lecturas if lectura["title"].strip() not in existentes]
    stats = insertar_lecturas(db, nuevas, is_practice=True)
    stats["omitidas"] = len(lecturas) - len(nuevas)
    return stats


def actualizar_logro_explorador(db) -> bool:
    resultado = db.execute(
        text(
            "UPDATE achievement_catalog SET how_to_unlock = :ahora "
            "WHERE id = 'explorer' AND how_to_unlock = :antes"
        ),
        {"ahora": EXPLORADOR_AHORA, "antes": EXPLORADOR_ANTES},
    )
    return resultado.rowcount == 1


def verificar(db, titulos_practica: list[str]) -> list[str]:
    """Comprueba el estado final. Vacío si todo cuadra."""
    problemas = []
    for tabla in ("readings", "player_sessions", "player_typology_progress", "active_readings"):
        n = db.execute(
            text(f"SELECT count(*) FROM {tabla} WHERE typology = :t"), {"t": TIPOLOGIA_RETIRADA}
        ).scalar()
        if n:
            problemas.append(f"{tabla}: quedan {n} filas de {TIPOLOGIA_RETIRADA}")
    fuera = (
        db.query(PlayerTypologyProgress)
        .filter(PlayerTypologyProgress.typology.notin_(DIFFICULTY_ORDER))
        .count()
    )
    if fuera:
        problemas.append(f"player_typology_progress: {fuera} filas de tipologías fuera del juego")
    for slot in db.query(PlayerSlot).all():
        n = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id).count()
        if n != len(DIFFICULTY_ORDER):
            problemas.append(f"slot {slot.id}: {n} filas de progreso, se esperaban {len(DIFFICULTY_ORDER)}")
    for titulo in titulos_practica:
        lectura = db.query(Reading).filter(Reading.title == titulo).first()
        if lectura is None or not lectura.is_practice:
            problemas.append(f"lectura de práctica ausente o sin marcar: {titulo}")
    return problemas


def migrar(db, lecturas_practica: list[dict]) -> dict:
    """Ejecuta la migración completa en la transacción de `db`, sin confirmarla."""
    aplicar_columnas(db)
    informe = {"alumnos_afectados": alumnos_afectados(db)}
    informe["borrado"] = borrar_tipologia_retirada(db)
    informe["desbloqueos"] = normalizar_slots(db)
    informe["practica"] = cargar_lecturas_practica(db, lecturas_practica)
    informe["explorador_actualizado"] = actualizar_logro_explorador(db)
    informe["problemas"] = verificar(db, [lectura["title"].strip() for lectura in lecturas_practica])
    return informe


# ── Salida ───────────────────────────────────────────────────────────────────

def imprimir_informe(informe: dict) -> None:
    afectados = informe["alumnos_afectados"]
    print(f"Alumnos que pierden su puntaje de {TIPOLOGIA_RETIRADA}: {len(afectados)}")
    for email, slot, puntos in afectados[:50]:
        print(f"  {email:<40} slot {slot}  -{puntos} pts")
    if len(afectados) > 50:
        print(f"  ... y {len(afectados) - 50} más")

    print(f"\nBorrado de {TIPOLOGIA_RETIRADA}:")
    for etiqueta, n in informe["borrado"].items():
        print(f"  {etiqueta:<46} {n:>5}")

    print("\nSlots con cada tipología abierta (antes -> después):")
    for tipologia, (antes, despues) in informe["desbloqueos"].items():
        print(f"  {tipologia:<15} {antes:>4} -> {despues:>4}")

    p = informe["practica"]
    print(f"\nLecturas de práctica: {p['lecturas']} nuevas ({p['preguntas']} preguntas, "
          f"{p['respuestas']} respuestas), {p['omitidas']} ya existían")
    actualizado = "sí" if informe["explorador_actualizado"] else "no (ya estaba o fue editado)"
    print(f"Logro Explorador actualizado: {actualizado}")

    if informe["problemas"]:
        print("\nPROBLEMAS EN LA VERIFICACIÓN:")
        for problema in informe["problemas"]:
            print(f"  - {problema}")
    else:
        print("\nVerificación: OK")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default="/data/LECTURAS_PRACTICA.json", help="JSON con las lecturas de práctica")
    ap.add_argument("--apply", action="store_true", help="Aplicar de verdad. Sin esto solo simula.")
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL no esta definida. No se adivina por seguridad.", file=sys.stderr)
        return 2

    comprobar_base_correcta()
    print(f"Base de destino: {_url_censurada()}\n")

    with open(args.json, encoding="utf-8") as fh:
        datos = json.load(fh)
    problemas = validar_lecturas_practica(datos)
    if problemas:
        print(f"El JSON de práctica tiene {len(problemas)} problemas. No se toca la base:\n")
        for problema in problemas[:30]:
            print(f"  - {problema}")
        return 1

    db = SessionLocal()
    try:
        informe = migrar(db, datos["readings"])
        imprimir_informe(informe)
        if informe["problemas"]:
            db.rollback()
            print("\nRollback hecho: la base queda como estaba.", file=sys.stderr)
            return 1
        if not args.apply:
            db.rollback()
            print("\nSIMULACRO. No se ha modificado nada. Añade --apply para ejecutarlo.")
            return 0
        db.commit()
        print("\nHecho. Migración aplicada.")
        return 0
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"\nERROR: {exc}\nRollback hecho: la base queda como estaba.", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
