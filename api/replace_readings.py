#!/usr/bin/env python3
"""
Reemplaza el corpus de lecturas de PROGRESION.

Borra las lecturas de progresion (todas, o todas menos la tipologia indicada con
--keep) y carga en su lugar las del JSON. Las lecturas de la zona de practica
NUNCA se tocan: tienen su propio corpus (LECTURAS_PRACTICA.json). Pensado para
ejecutarse dentro del contenedor de la API, donde ya estan la conexion a la BD
y el JSON montado en /data.

    docker exec vw-api-1 python replace_readings.py \
        --json /data/LECTURAS_TIPOLOGIAS_TEXTUALES.json

Por defecto NO escribe: hace un simulacro y muestra el impacto. Para aplicar de
verdad hay que pasar --apply.

AVISO SOBRE EL BORRADO EN CASCADA
---------------------------------
readings tiene ON DELETE CASCADE hacia questions (y de ahi a answers),
player_sessions (y de ahi a player_answers y session_tools), player_notes y
user_readings. Borrar una lectura se lleva por delante el progreso de los
alumnos sobre ella. Los logros (player_achievements) y el best_score por
tipologia (player_typology_progress) NO cuelgan de readings y sobreviven, asi
que tras el reemplazo puede quedar puntuacion sin sesiones que la respalden.
El simulacro cuantifica todo eso antes de tocar nada.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Los ayudantes ya resuelven las rarezas del formato: el prefijo "A) " de las
# respuestas, los parrafos como array y los niveles con y sin tilde.
from import_json_readings import (
    join_paragraphs,
    normalize_level,
    strip_answer_prefix,
)

TABLAS_EN_CASCADA = [
    ("questions", "reading_id"),
    ("player_sessions", "reading_id"),
    ("player_notes", "reading_id"),
    ("user_readings", "reading_id"),
]


def validar_json(datos: dict, conservar: str | None) -> list[str]:
    """Devuelve la lista de problemas encontrados. Vacia si el JSON esta sano."""
    problemas: list[str] = []
    lecturas = datos.get("readings", [])
    if not lecturas:
        return ["el JSON no contiene 'readings'"]

    titulos = set()
    for lectura in lecturas:
        titulo = (lectura.get("title") or "").strip()
        tipologia = (lectura.get("typology") or "").strip()

        if not titulo:
            problemas.append("hay una lectura sin titulo")
            continue
        if titulo in titulos:
            problemas.append(f"{titulo}: titulo duplicado dentro del JSON")
        titulos.add(titulo)

        if not tipologia:
            problemas.append(f"{titulo}: sin tipologia")
        # Si el JSON trajera lecturas de la tipologia que se conserva, el
        # resultado seria ambiguo: se conservan las viejas y ademas entran las
        # nuevas. Mejor parar y que lo decida una persona.
        elif conservar and tipologia == conservar:
            problemas.append(
                f"{titulo}: es de la tipologia '{conservar}', que se conserva. "
                "Quita esa lectura del JSON o cambia --keep."
            )
        if not lectura.get("text"):
            problemas.append(f"{titulo}: sin texto")

        actividades = lectura.get("activites", [])  # typo del formato original
        if not actividades:
            problemas.append(f"{titulo}: sin preguntas")

        for act in actividades:
            num = act.get("question_id", "?")
            if not (act.get("question") or "").strip():
                problemas.append(f"{titulo} q{num}: sin enunciado")
            correcta = (act.get("correct_answer") or "").strip().upper()
            if correcta not in {"A", "B", "C", "D"}:
                problemas.append(f"{titulo} q{num}: correct_answer invalida ({correcta!r})")
            opciones = act.get("answers") or []
            if len(opciones) != 4:
                problemas.append(f"{titulo} q{num}: {len(opciones)} opciones, se esperaban 4")
            letras = sorted((o or "?")[0].upper() for o in opciones)
            if opciones and letras != ["A", "B", "C", "D"]:
                problemas.append(f"{titulo} q{num}: letras {letras}")

    return problemas


def _filtro_borrado(conservar: str | None) -> tuple[str, dict]:
    """Lecturas que se reemplazan: las de progresion, menos la tipologia que se
    conserva. Las de practica nunca: tienen su propio corpus."""
    if conservar:
        return "is_practice = false AND typology <> :keep", {"keep": conservar}
    return "is_practice = false", {}


def borrar_lecturas_de_progresion(sesion, conservar: str | None) -> int:
    """Borra las lecturas que se reemplazan. Devuelve cuantas."""
    filtro, params = _filtro_borrado(conservar)
    return sesion.execute(text(f"DELETE FROM readings WHERE {filtro}"), params).rowcount


def informe_previo(sesion, conservar: str | None) -> dict:
    """Cuenta que hay ahora y que se llevaria por delante el borrado."""
    filtro, params = _filtro_borrado(conservar)

    por_tipologia = sesion.execute(
        text("SELECT typology, is_practice, count(*) FROM readings "
             "GROUP BY typology, is_practice ORDER BY typology, is_practice")
    ).fetchall()

    a_borrar = sesion.execute(
        text(f"SELECT count(*) FROM readings WHERE {filtro}"), params
    ).scalar()
    se_conservan = sesion.execute(
        text(f"SELECT count(*) FROM readings WHERE NOT ({filtro})"), params
    ).scalar()

    cascada = {}
    for tabla, columna in TABLAS_EN_CASCADA:
        cascada[tabla] = sesion.execute(
            text(
                f"SELECT count(*) FROM {tabla} WHERE {columna} IN "
                f"(SELECT id FROM readings WHERE {filtro})"
            ),
            params,
        ).scalar()

    # answers y player_answers cuelgan un nivel mas abajo.
    cascada["answers"] = sesion.execute(
        text(
            "SELECT count(*) FROM answers WHERE question_id IN "
            f"(SELECT id FROM questions WHERE reading_id IN (SELECT id FROM readings WHERE {filtro}))"
        ),
        params,
    ).scalar()
    cascada["player_answers"] = sesion.execute(
        text(
            "SELECT count(*) FROM player_answers WHERE session_id IN "
            f"(SELECT id FROM player_sessions WHERE reading_id IN (SELECT id FROM readings WHERE {filtro}))"
        ),
        params,
    ).scalar()

    return {
        "por_tipologia": por_tipologia,
        "a_borrar": a_borrar,
        "se_conservan": se_conservan,
        "cascada": cascada,
    }


def insertar_lecturas(sesion, lecturas: list[dict], is_practice: bool = False) -> dict:
    """Inserta las lecturas del JSON con sus preguntas y respuestas.
    Con is_practice=True quedan como lecturas de la zona de practica."""
    stats = {"lecturas": 0, "preguntas": 0, "respuestas": 0}

    for lectura in lecturas:
        titulo = lectura["title"].strip()
        fila = sesion.execute(
            text(
                "INSERT INTO readings (title, typology, type, content, is_practice) "
                "VALUES (:title, :typology, :type, :content, :is_practice) RETURNING id"
            ),
            {
                "title": titulo,
                "typology": lectura["typology"].strip(),
                "type": lectura.get("type"),
                "content": join_paragraphs(lectura["text"]),
                "is_practice": is_practice,
            },
        ).fetchone()
        reading_id = fila[0]
        stats["lecturas"] += 1

        for act in lectura.get("activites", []):
            q = sesion.execute(
                text(
                    "INSERT INTO questions (reading_id, question_number, "
                    "comprehension_level, question_text, correct_answer, justification) "
                    "VALUES (:rid, :qnum, :level, :qtext, :correct, :just) RETURNING id"
                ),
                {
                    "rid": reading_id,
                    "qnum": int(act.get("question_id", 0)),
                    "level": normalize_level(act.get("comprehension_level", "")),
                    "qtext": act["question"].strip(),
                    "correct": act["correct_answer"].strip().upper(),
                    "just": (act.get("justification") or "").strip() or None,
                },
            ).fetchone()
            stats["preguntas"] += 1

            for opcion in act.get("answers", []):
                sesion.execute(
                    text(
                        "INSERT INTO answers (question_id, letter, answer_text) "
                        "VALUES (:qid, :letter, :text)"
                    ),
                    {
                        "qid": q[0],
                        "letter": opcion[0].upper(),
                        "text": strip_answer_prefix(opcion),
                    },
                )
                stats["respuestas"] += 1

    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", required=True, help="Ruta del JSON con las lecturas nuevas")
    ap.add_argument("--keep", default=None,
                    help="Tipologia de progresion que NO se borra (opcional). Las lecturas de practica nunca se borran.")
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL"), help="Por defecto, $DATABASE_URL")
    ap.add_argument("--apply", action="store_true", help="Aplicar de verdad. Sin esto solo simula.")
    args = ap.parse_args()

    if not args.db_url:
        print("ERROR: no hay DATABASE_URL ni --db-url", file=sys.stderr)
        return 2

    with open(args.json, encoding="utf-8") as fh:
        datos = json.load(fh)
    lecturas = datos["readings"]

    problemas = validar_json(datos, args.keep)
    if problemas:
        print(f"El JSON tiene {len(problemas)} problemas. No se toca la base:\n")
        for p in problemas[:30]:
            print(f"  - {p}")
        if len(problemas) > 30:
            print(f"  ... y {len(problemas) - 30} mas")
        return 1

    esperadas = {
        "lecturas": len(lecturas),
        "preguntas": sum(len(r.get("activites", [])) for r in lecturas),
        "respuestas": sum(len(a.get("answers", [])) for r in lecturas for a in r.get("activites", [])),
    }
    print(f"JSON validado: {esperadas['lecturas']} lecturas, "
          f"{esperadas['preguntas']} preguntas, {esperadas['respuestas']} respuestas\n")

    engine = create_engine(args.db_url)
    Sesion = sessionmaker(bind=engine)
    sesion = Sesion()

    try:
        previo = informe_previo(sesion, args.keep)

        print("Estado actual de la base:")
        for tipologia, practica, n in previo["por_tipologia"]:
            nombre = f"{tipologia} (practica)" if practica else tipologia
            marca = "  (se conserva)" if practica or tipologia == args.keep else ""
            print(f"  {nombre:<26} {n:>3}{marca}")
        print()
        print(f"Se borrarian {previo['a_borrar']} lecturas y se conservarian {previo['se_conservan']}.")
        print("Arrastre en cascada:")
        for tabla, n in previo["cascada"].items():
            aviso = "   <-- PROGRESO DE ALUMNOS" if tabla in ("player_sessions", "player_answers", "player_notes") and n else ""
            print(f"  {tabla:<16} {n:>4}{aviso}")
        print()
        print(f"Resultado final: {previo['se_conservan']} + {esperadas['lecturas']} = "
              f"{previo['se_conservan'] + esperadas['lecturas']} lecturas")
        print()

        if not args.apply:
            print("SIMULACRO. No se ha modificado nada. Anade --apply para ejecutarlo.")
            return 0

        print("Aplicando en una sola transaccion...")
        borradas = borrar_lecturas_de_progresion(sesion, args.keep)
        print(f"  borradas {borradas} lecturas")

        stats = insertar_lecturas(sesion, lecturas)
        print(f"  insertadas {stats['lecturas']} lecturas, {stats['preguntas']} preguntas, "
              f"{stats['respuestas']} respuestas")

        # Si lo insertado no cuadra con lo prometido, se deshace todo.
        if stats != esperadas:
            raise RuntimeError(f"lo insertado no coincide con el JSON: {stats} != {esperadas}")

        sesion.commit()
        print("\nHecho. Estado final:")
        for tipologia, practica, n in sesion.execute(
            text("SELECT typology, is_practice, count(*) FROM readings "
                 "GROUP BY typology, is_practice ORDER BY typology, is_practice")
        ).fetchall():
            nombre = f"{tipologia} (practica)" if practica else tipologia
            print(f"  {nombre:<26} {n:>3}")
        return 0

    except Exception as exc:  # noqa: BLE001
        sesion.rollback()
        print(f"\nERROR: {exc}\nSe ha hecho rollback: la base queda como estaba.", file=sys.stderr)
        return 1
    finally:
        sesion.close()


if __name__ == "__main__":
    sys.exit(main())
