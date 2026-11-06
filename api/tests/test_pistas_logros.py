"""Pistas visibles de Lector ávido y las tres Estrellas, acordes a las reglas
nuevas del juego (4 lecturas; 6 aciertos por nivel)."""
import sys

import actualizar_pistas_logros as pistas
from catalogo_logros import seed_achievements_catalog
from models import AchievementCatalog


def _catalogo_antiguo(db):
    seed_achievements_catalog(db)
    for id_, (antes, _) in pistas.PISTAS.items():
        db.query(AchievementCatalog).filter_by(id=id_).update({"how_to_unlock": antes})
    db.commit()


def _pista(db, id_):
    db.expire_all()
    return db.query(AchievementCatalog).filter_by(id=id_).one().how_to_unlock


def test_actualiza_las_cuatro_pistas(db):
    _catalogo_antiguo(db)
    assert pistas.actualizar_pistas(db) == {i: True for i in pistas.PISTAS}
    db.commit()
    for id_, (_, ahora) in pistas.PISTAS.items():
        assert _pista(db, id_) == ahora


def test_es_idempotente(db):
    _catalogo_antiguo(db)
    pistas.actualizar_pistas(db)
    db.commit()
    assert pistas.actualizar_pistas(db) == {i: False for i in pistas.PISTAS}


def test_no_pisa_una_pista_editada(db):
    _catalogo_antiguo(db)
    db.query(AchievementCatalog).filter_by(id="star_literal").update({"how_to_unlock": "Texto editado"})
    db.commit()
    assert pistas.actualizar_pistas(db)["star_literal"] is False
    db.commit()
    assert _pista(db, "star_literal") == "Texto editado"


def test_el_catalogo_inicial_ya_trae_las_nuevas(db):
    seed_achievements_catalog(db)
    for id_, (_, ahora) in pistas.PISTAS.items():
        assert _pista(db, id_) == ahora


def test_main_en_simulacro_no_escribe(db, monkeypatch, capsys):
    _catalogo_antiguo(db)
    monkeypatch.setattr(sys, "argv", ["actualizar_pistas_logros.py"])
    assert pistas.main() == 0
    assert _pista(db, "avid_reader") == pistas.PISTAS["avid_reader"][0]
    assert "SIMULACRO" in capsys.readouterr().out


def test_main_con_apply_escribe(db, monkeypatch):
    _catalogo_antiguo(db)
    monkeypatch.setattr(sys, "argv", ["actualizar_pistas_logros.py", "--apply"])
    assert pistas.main() == 0
    assert _pista(db, "avid_reader") == pistas.PISTAS["avid_reader"][1]
