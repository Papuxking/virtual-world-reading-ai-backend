import json
import sys

import pytest

import migrate_practice_mode as mig
from game_rules import DIFFICULTY_ORDER
from helpers import crear_lectura, crear_usuario, lectura_json
from models import (
    AchievementCatalog, ActiveReading, NpcInteraction, PlayerAnswer, PlayerNote,
    PlayerSession, PlayerTypologyProgress, Question, Reading, SessionTool,
)

LECTURAS = [lectura_json("Práctica narrativa", "Narrativo")]


def _doce_lecturas():
    return {"readings": [lectura_json(f"{t} {i}", t) for t in DIFFICULTY_ORDER for i in range(3)]}


@pytest.fixture
def base_con_instructivo(db):
    alumno, slot = crear_usuario(db, "alumno@test.com")
    filas = {f.typology: f for f in db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id)}
    filas["Narrativo"].best_score = 280
    filas["Descriptivo"].best_score, filas["Descriptivo"].is_unlocked = 260, True
    filas["Argumentativo"].best_score, filas["Argumentativo"].is_unlocked = 255, True
    db.add(PlayerTypologyProgress(
        user_id=alumno.id, slot_id=slot.id, typology="Instructivo",
        best_score=270, total_sessions=1, is_unlocked=True,
    ))
    instructivo = crear_lectura(db, "Guía", "Instructivo")
    crear_lectura(db, "Cuento", "Narrativo")
    sesion = PlayerSession(
        user_id=alumno.id, slot_id=slot.id, reading_id=instructivo.id,
        typology="Instructivo", session_score=270,
    )
    db.add(sesion)
    db.flush()
    pregunta = db.query(Question).filter_by(reading_id=instructivo.id).first()
    db.add_all([
        PlayerAnswer(session_id=sesion.id, question_id=pregunta.id, comprehension_level="Literal",
                     selected_answer="A", correct_answer="A", is_correct=True),
        SessionTool(session_id=sesion.id, tool_name="highlight", was_used=True, usage_count=1),
        PlayerNote(user_id=alumno.id, slot_id=slot.id, reading_id=instructivo.id,
                   session_id=sesion.id, note_content="nota"),
        ActiveReading(user_id=alumno.id, slot_id=slot.id, reading_id=instructivo.id, typology="Instructivo"),
        NpcInteraction(user_id=alumno.id, slot_id=slot.id, npc_type="robot",
                       reading_id=instructivo.id, session_id=sesion.id),
        AchievementCatalog(id="explorer", name="🏅 Explorador", description="d",
                           how_to_unlock=mig.EXPLORADOR_ANTES, category="exploración",
                           icon="🏅", medal_name="m", medal_tier="plata"),
    ])
    db.commit()
    return {"slot": slot}


def test_migracion_borra_instructivo_y_desbloquea(db, base_con_instructivo):
    informe = mig.migrar(db, LECTURAS)
    db.commit()
    assert informe["problemas"] == []
    assert informe["alumnos_afectados"] == [("alumno@test.com", 1, 270)]
    assert db.query(Reading).filter_by(typology="Instructivo").count() == 0
    assert db.query(PlayerSession).count() == 0
    assert db.query(PlayerAnswer).count() == 0
    assert db.query(SessionTool).count() == 0
    assert db.query(PlayerNote).count() == 0
    assert db.query(ActiveReading).count() == 0
    npc = db.query(NpcInteraction).one()
    assert (npc.reading_id, npc.session_id) == (None, None)
    filas = {f.typology: f for f in db.query(PlayerTypologyProgress).filter_by(
        slot_id=base_con_instructivo["slot"].id)}
    assert sorted(filas) == sorted(DIFFICULTY_ORDER)
    assert filas["Expositivo"].is_unlocked is True      # Argumentativo 255 >= 250
    practica = db.query(Reading).filter_by(title="Práctica narrativa").one()
    assert practica.is_practice is True
    assert len(practica.questions) == 12
    assert db.get(AchievementCatalog, "explorer").how_to_unlock == mig.EXPLORADOR_AHORA
    assert informe["desbloqueos"]["Expositivo"] == (0, 1)


def test_migracion_es_idempotente(db, base_con_instructivo):
    mig.migrar(db, LECTURAS)
    db.commit()
    informe = mig.migrar(db, LECTURAS)
    db.commit()
    assert informe["problemas"] == []
    assert all(n == 0 for n in informe["borrado"].values())
    assert (informe["practica"]["lecturas"], informe["practica"]["omitidas"]) == (0, 1)
    assert db.query(Reading).filter_by(is_practice=True).count() == 1


def test_migracion_no_pisa_un_explorador_editado(db, base_con_instructivo):
    db.get(AchievementCatalog, "explorer").how_to_unlock = "Texto propio del docente"
    db.commit()
    informe = mig.migrar(db, LECTURAS)
    db.commit()
    assert informe["explorador_actualizado"] is False
    assert db.get(AchievementCatalog, "explorer").how_to_unlock == "Texto propio del docente"


def test_migracion_nunca_bloquea(db):
    _, slot = crear_usuario(db)
    db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology="Expositivo").one().is_unlocked = True
    db.commit()
    mig.migrar(db, LECTURAS)
    db.commit()
    db.expire_all()
    fila = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology="Expositivo").one()
    assert fila.is_unlocked is True


def test_migracion_completa_slots_sin_filas(db):
    _, slot = crear_usuario(db, filas=False)
    mig.migrar(db, LECTURAS)
    db.commit()
    assert db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id).count() == 4


def test_validador_acepta_doce_lecturas_correctas():
    assert mig.validar_lecturas_practica(_doce_lecturas()) == []


def test_validador_detecta_problemas():
    datos = _doce_lecturas()
    datos["readings"][0]["typology"] = "Instructivo"
    datos["readings"][1]["activites"][0]["comprehension_level"] = "Inferencial"
    for act in datos["readings"][2]["activites"]:
        act["correct_answer"] = "B"
    datos["readings"][3]["text"] = ["Muy corto."]
    problemas = mig.validar_lecturas_practica(datos)
    assert any("fuera del juego" in p for p in problemas)
    assert any("Narrativo: 2 lecturas" in p for p in problemas)
    assert any("preguntas por nivel" in p for p in problemas)
    assert any("misma letra" in p for p in problemas)
    assert any("caracteres" in p for p in problemas)


def test_main_en_simulacro_no_escribe(db, base_con_instructivo, tmp_path, monkeypatch, capsys):
    ruta = tmp_path / "practica.json"
    ruta.write_text(json.dumps(_doce_lecturas()), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["migrate_practice_mode.py", "--json", str(ruta)])
    assert mig.main() == 0
    db.expire_all()
    assert db.query(Reading).filter_by(typology="Instructivo").count() == 1
    assert db.query(Reading).filter_by(is_practice=True).count() == 0
    assert "SIMULACRO" in capsys.readouterr().out


def test_main_con_apply_escribe(db, base_con_instructivo, tmp_path, monkeypatch):
    ruta = tmp_path / "practica.json"
    ruta.write_text(json.dumps(_doce_lecturas()), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["migrate_practice_mode.py", "--json", str(ruta), "--apply"])
    assert mig.main() == 0
    db.expire_all()
    assert db.query(Reading).filter_by(typology="Instructivo").count() == 0
    assert db.query(Reading).filter_by(is_practice=True).count() == 12
