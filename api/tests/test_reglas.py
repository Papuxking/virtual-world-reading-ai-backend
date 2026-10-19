from game_rules import DIFFICULTY_ORDER, MAX_SESSION_SCORE, UNLOCK_THRESHOLDS, score_rules
from helpers import crear_usuario
from models import PlayerTypologyProgress
from progression import ensure_typology_rows, reevaluate_unlocks


def _fila(db, slot, tipologia):
    return (
        db.query(PlayerTypologyProgress)
        .filter_by(slot_id=slot.id, typology=tipologia)
        .one()
    )


def test_reglas_de_cuatro_tipologias():
    assert DIFFICULTY_ORDER == ["Narrativo", "Descriptivo", "Argumentativo", "Expositivo"]
    assert UNLOCK_THRESHOLDS == {
        "Narrativo": 0, "Descriptivo": 120, "Argumentativo": 120, "Expositivo": 120,
    }
    assert MAX_SESSION_SCORE == 300
    assert score_rules() == {
        "typology_order": DIFFICULTY_ORDER,
        "unlock_thresholds": UNLOCK_THRESHOLDS,
        "max_session_score": 300,
        "max_attempts": 5,
    }


def test_score_rules_devuelve_copias():
    reglas = score_rules()
    reglas["typology_order"].append("Instructivo")
    reglas["unlock_thresholds"]["Instructivo"] = 250
    assert "Instructivo" not in DIFFICULTY_ORDER
    assert "Instructivo" not in UNLOCK_THRESHOLDS


def test_ensure_typology_rows_crea_las_que_faltan(db):
    usuario, slot = crear_usuario(db, filas=False)
    filas = ensure_typology_rows(db, usuario.id, slot.id)
    db.commit()
    assert [f.typology for f in filas] == DIFFICULTY_ORDER
    assert [f.is_unlocked for f in filas] == [True, False, False, False]
    ensure_typology_rows(db, usuario.id, slot.id)
    db.commit()
    assert db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id).count() == 4


def test_ensure_typology_rows_ignora_tipologias_retiradas(db):
    usuario, slot = crear_usuario(db)
    db.add(PlayerTypologyProgress(
        user_id=usuario.id, slot_id=slot.id, typology="Instructivo", best_score=270,
    ))
    db.commit()
    filas = ensure_typology_rows(db, usuario.id, slot.id)
    assert [f.typology for f in filas] == DIFFICULTY_ORDER


def test_reevaluate_desbloquea_expositivo_desde_argumentativo(db):
    usuario, slot = crear_usuario(db)
    _fila(db, slot, "Narrativo").best_score = 260
    _fila(db, slot, "Descriptivo").best_score = 255
    _fila(db, slot, "Argumentativo").best_score = 250
    db.commit()
    reevaluate_unlocks(db, usuario.id, slot.id)
    db.commit()
    assert all(_fila(db, slot, t).is_unlocked for t in DIFFICULTY_ORDER)


def test_umbral_justo_desbloquea_y_uno_menos_no(db):
    usuario, slot = crear_usuario(db)
    _fila(db, slot, "Narrativo").best_score = UNLOCK_THRESHOLDS["Descriptivo"]
    _fila(db, slot, "Descriptivo").best_score = UNLOCK_THRESHOLDS["Argumentativo"] - 1
    db.commit()
    reevaluate_unlocks(db, usuario.id, slot.id)
    db.commit()
    assert _fila(db, slot, "Descriptivo").is_unlocked is True
    assert _fila(db, slot, "Argumentativo").is_unlocked is False


def test_reevaluate_bloquea_si_no_llega_al_umbral(db):
    usuario, slot = crear_usuario(db)
    _fila(db, slot, "Expositivo").is_unlocked = True
    db.commit()
    reevaluate_unlocks(db, usuario.id, slot.id)
    db.commit()
    assert _fila(db, slot, "Expositivo").is_unlocked is False


def test_reevaluate_only_unlock_nunca_bloquea(db):
    usuario, slot = crear_usuario(db)
    _fila(db, slot, "Expositivo").is_unlocked = True
    db.commit()
    reevaluate_unlocks(db, usuario.id, slot.id, only_unlock=True)
    db.commit()
    assert _fila(db, slot, "Expositivo").is_unlocked is True
