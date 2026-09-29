#!/usr/bin/env python3
"""
import_readings.py — Importa lecturas desde archivos .txt a la API REST.

Convención de carpetas:
    readings/
    ├── Descriptivo/
    │   ├── bannos.txt           → title="Bannos", typology="Descriptivo"
    │   └── mi lectura.txt       → title="Mi Lectura", typology="Descriptivo"
    ├── Narrativo/
    │   └── ...

Uso:
    python import_readings.py --folder ../readings --api-url http://localhost:8000
    python import_readings.py --zip lecturas.zip --api-url http://localhost:8000
"""
import argparse
import os
import sys
import zipfile
import tempfile
import requests

from game_rules import DIFFICULTY_ORDER

# Solo las tipologías del juego: Instructivo ya no tiene escenario de progresión.
VALID_TYPOLOGIES = set(DIFFICULTY_ORDER)


def infer_title(filename: str) -> str:
    """Infiere el título a partir del nombre del archivo (sin extensión)."""
    name = os.path.splitext(filename)[0]
    return name.strip().title()


def infer_typology(parent_folder: str) -> str | None:
    """Infiere la tipología a partir del nombre de la carpeta padre."""
    # Normalizar: primera letra mayúscula, resto minúsculas
    normalized = parent_folder.strip().capitalize()
    if normalized in VALID_TYPOLOGIES:
        return normalized
    return None


def import_from_folder(folder_path: str, api_url: str) -> None:
    """Recorre una carpeta con subcarpetas por tipología e importa los .txt."""
    base_url = api_url.rstrip("/")
    success = 0
    errors = 0

    for root, _dirs, files in os.walk(folder_path):
        for filename in files:
            if not filename.lower().endswith(".txt"):
                continue

            filepath = os.path.join(root, filename)
            parent = os.path.basename(root)
            typology = infer_typology(parent)

            if not typology:
                print(f"  ⚠  Omitido (tipología no reconocida '{parent}'): {filepath}")
                errors += 1
                continue

            title = infer_title(filename)

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if len(content) < 100:
                print(f"  ⚠  Omitido (contenido < 100 chars): {filepath}")
                errors += 1
                continue

            payload = {
                "title": title,
                "typology": typology,
                "content": content,
            }

            try:
                resp = requests.post(f"{base_url}/readings", json=payload, timeout=10)
                if resp.status_code == 201:
                    data = resp.json()
                    print(f"  ✓  Importado: [{typology}] \"{title}\" → ID {data['id']}")
                    success += 1
                else:
                    print(f"  ✗  Error {resp.status_code}: {resp.text} — {filepath}")
                    errors += 1
            except requests.RequestException as e:
                print(f"  ✗  Error de conexión: {e} — {filepath}")
                errors += 1

    print(f"\n{'='*50}")
    print(f"  Importados: {success}  |  Errores/Omitidos: {errors}")
    print(f"{'='*50}")


def import_from_zip(zip_path: str, api_url: str) -> None:
    """Descomprime un .zip a un directorio temporal y lo importa."""
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"  Descomprimiendo {zip_path} en {tmpdir}...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)
        import_from_folder(tmpdir, api_url)


def main():
    parser = argparse.ArgumentParser(
        description="Importa lecturas .txt al API de lecturas del mundo virtual"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--folder", help="Carpeta con subcarpetas por tipología")
    group.add_argument("--zip", help="Archivo .zip con la estructura de carpetas")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL base de la API (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    print(f"\n  API: {args.api_url}")
    print(f"  Fuente: {args.folder or args.zip}\n")

    # Verificar conexión
    try:
        r = requests.get(f"{args.api_url.rstrip('/')}/health", timeout=5)
        health = r.json()
        print(f"  Estado API: {health.get('status', 'unknown')}")
        print(f"  Base de datos: {health.get('database', 'unknown')}\n")
    except requests.RequestException as e:
        print(f"  ✗  No se pudo conectar a la API: {e}")
        sys.exit(1)

    if args.folder:
        if not os.path.isdir(args.folder):
            print(f"  ✗  La carpeta no existe: {args.folder}")
            sys.exit(1)
        import_from_folder(args.folder, args.api_url)
    else:
        if not os.path.isfile(args.zip):
            print(f"  ✗  El archivo no existe: {args.zip}")
            sys.exit(1)
        import_from_zip(args.zip, args.api_url)


if __name__ == "__main__":
    main()
