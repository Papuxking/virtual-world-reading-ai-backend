"""
import_json_readings.py — Importa lecturas desde archivos JSON a la base de datos.

Lee los archivos JSON generados por el equipo de contenido, extrae lecturas,
preguntas y respuestas, y los inserta directamente en PostgreSQL.

Uso:
    # Desde el host (con la BD levantada):
    docker-compose exec api python import_json_readings.py

    # O directamente si tienes Python + psycopg2 instalado:
    python import_json_readings.py --db-url postgresql://user:pass@localhost:5432/godot_readings
"""
import json
import os
import re
import sys
import argparse
from pathlib import Path

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ── Configuración por defecto ────────────────────────────────────────────────

DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://DB-virtual-world-reading-ai:GodotWorldAdmin@db:5432/godot_readings"
)

# Rutas por defecto para los JSON (dentro del contenedor, montados en /data)
DEFAULT_JSON_FILES = [
    "/data/LECTURAS refact.json",
    "/data/Lecturas para entorno virtual refact.json",
]


# ── Utilidades ───────────────────────────────────────────────────────────────

def strip_answer_prefix(answer_text: str) -> str:
    """Elimina el prefijo 'A) ', 'B) ', etc. del texto de una respuesta."""
    return re.sub(r'^[A-D]\)\s*', '', answer_text).strip()


def join_paragraphs(text_array: list) -> str:
    """Une los párrafos del array en un solo texto separado por doble salto de línea."""
    return "\n\n".join(t.strip() for t in text_array if t.strip())


def normalize_level(level: str) -> str:
    """Normaliza el nivel de comprensión a la convención de la BD."""
    mapping = {
        "literal": "Literal",
        "inferencial": "Inferencial",
        "critico": "Critico",
        "crítico": "Critico",
    }
    return mapping.get(level.lower(), level.capitalize())


# ── Importación ──────────────────────────────────────────────────────────────

def import_json_file(session, filepath: str, stats: dict, is_practice: bool = False):
    """Importa un archivo JSON completo a la base de datos.
    Con is_practice=True las lecturas quedan como exclusivas de la zona de práctica."""
    print(f"\n📖 Procesando: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    readings = data.get("readings", [])
    print(f"   Encontradas {len(readings)} lecturas")

    for reading_data in readings:
        title = reading_data.get("title", "").strip()
        typology = reading_data.get("typology", "").strip()
        reading_type = reading_data.get("type", None)
        text_array = reading_data.get("text", [])
        activities = reading_data.get("activites", [])  # typo en el JSON original

        if not title or not typology or not text_array:
            print(f"   ⚠ Lectura ignorada (datos incompletos): {title[:50]}")
            stats["skipped"] += 1
            continue

        content = join_paragraphs(text_array)

        # Verificar si ya existe
        exists = session.execute(
            text("SELECT id FROM readings WHERE title = :title"),
            {"title": title}
        ).fetchone()

        if exists:
            print(f"   ⏭ Ya existe: {title[:60]}...")
            stats["skipped"] += 1
            continue

        # Insertar lectura
        result = session.execute(
            text("""
                INSERT INTO readings (title, typology, type, content, is_practice)
                VALUES (:title, :typology, :type, :content, :is_practice)
                RETURNING id
            """),
            {
                "title": title,
                "typology": typology,
                "type": reading_type,
                "content": content,
                "is_practice": is_practice,
            }
        )
        reading_id = result.fetchone()[0]
        stats["readings"] += 1
        print(f"   ✅ Lectura #{reading_id}: {title[:60]}...")

        # Insertar preguntas y respuestas
        for activity in activities:
            q_number = int(activity.get("question_id", 0))
            level = normalize_level(activity.get("comprehension_level", ""))
            q_text = activity.get("question", "").strip()
            correct = activity.get("correct_answer", "").strip().upper()
            justification = activity.get("justification", "").strip()
            answer_options = activity.get("answers", [])

            if not q_text or not correct:
                continue

            # Insertar pregunta
            q_result = session.execute(
                text("""
                    INSERT INTO questions
                        (reading_id, question_number, comprehension_level,
                         question_text, correct_answer, justification)
                    VALUES (:rid, :qnum, :level, :qtext, :correct, :just)
                    RETURNING id
                """),
                {
                    "rid": reading_id,
                    "qnum": q_number,
                    "level": level,
                    "qtext": q_text,
                    "correct": correct,
                    "just": justification or None,
                }
            )
            question_id = q_result.fetchone()[0]
            stats["questions"] += 1

            # Insertar opciones de respuesta
            for answer_text in answer_options:
                letter = answer_text[0].upper()  # "A) texto..." → "A"
                clean_text = strip_answer_prefix(answer_text)
                session.execute(
                    text("""
                        INSERT INTO answers (question_id, letter, answer_text)
                        VALUES (:qid, :letter, :text)
                    """),
                    {"qid": question_id, "letter": letter, "text": clean_text}
                )
                stats["answers"] += 1

    session.commit()


def main():
    parser = argparse.ArgumentParser(
        description="Importa lecturas desde archivos JSON a PostgreSQL"
    )
    parser.add_argument(
        "--db-url",
        default=DEFAULT_DB_URL,
        help="URL de conexión a PostgreSQL"
    )
    parser.add_argument(
        "json_files",
        nargs="*",
        default=DEFAULT_JSON_FILES,
        help="Rutas a los archivos JSON a importar"
    )
    parser.add_argument(
        "--practice",
        action="store_true",
        help="Importa las lecturas como exclusivas de la zona de práctica"
    )
    args = parser.parse_args()

    # Verificar que los archivos existen
    valid_files = []
    for fp in args.json_files:
        if os.path.isfile(fp):
            valid_files.append(fp)
        else:
            print(f"⚠ Archivo no encontrado: {fp}")

    if not valid_files:
        print("❌ No se encontraron archivos JSON para importar.")
        print("   Asegúrate de montar los JSON en /data o pasar las rutas como argumento.")
        sys.exit(1)

    # Conectar a la BD
    print(f"🔌 Conectando a: {args.db_url.split('@')[1] if '@' in args.db_url else args.db_url}")
    engine = create_engine(args.db_url)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexión exitosa")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)

    Session = sessionmaker(bind=engine)
    session = Session()

    stats = {"readings": 0, "questions": 0, "answers": 0, "skipped": 0}

    try:
        for filepath in valid_files:
            import_json_file(session, filepath, stats, is_practice=args.practice)

        print("\n" + "=" * 60)
        print("📊 Resumen de importación:")
        print(f"   Lecturas insertadas:   {stats['readings']}")
        print(f"   Preguntas insertadas:  {stats['questions']}")
        print(f"   Respuestas insertadas: {stats['answers']}")
        print(f"   Omitidas (duplicadas): {stats['skipped']}")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error durante importación: {e}")
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
