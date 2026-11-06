import json

import import_json_readings as ij
import replace_readings as rr
from helpers import crear_lectura, lectura_json
from models import Reading


def test_reemplazo_sin_keep_borra_todas(db):
    crear_lectura(db, "Narrativa", "Narrativo")
    crear_lectura(db, "Expositiva", "Expositivo")
    assert rr.borrar_lecturas_de_progresion(db, None) == 2
    db.commit()
    assert db.query(Reading).count() == 0


def test_reemplazo_respeta_keep(db):
    crear_lectura(db, "Narrativa", "Narrativo")
    crear_lectura(db, "Expositiva", "Expositivo")
    assert rr.borrar_lecturas_de_progresion(db, "Expositivo") == 1
    db.commit()
    assert [r.title for r in db.query(Reading).all()] == ["Expositiva"]


def test_insertar_lecturas(db):
    stats = rr.insertar_lecturas(db, [lectura_json("Nueva", "Descriptivo")])
    db.commit()
    assert stats == {"lecturas": 1, "preguntas": 12, "respuestas": 48}
    assert db.query(Reading).filter_by(title="Nueva").one().typology == "Descriptivo"


def test_validar_json_sin_tipologia_conservada():
    assert rr.validar_json({"readings": [lectura_json("Nueva", "Descriptivo")]}, None) == []


def test_import_json_readings(db, tmp_path):
    ruta = tmp_path / "lecturas.json"
    ruta.write_text(json.dumps({"readings": [lectura_json("Importada", "Argumentativo")]}), encoding="utf-8")
    stats = {"readings": 0, "questions": 0, "answers": 0, "skipped": 0}
    ij.import_json_file(db, str(ruta), stats)
    assert db.query(Reading).filter_by(title="Importada").one().typology == "Argumentativo"
    assert stats["readings"] == 1
