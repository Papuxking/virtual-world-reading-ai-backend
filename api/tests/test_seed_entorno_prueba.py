"""Entorno de prueba: 50 estudiantes, los 10 últimos con progreso coherente con
las reglas del juego; y los scripts que crean o tocan jugadores, con entornos."""
import json
import sys
from datetime import datetime, timedelta, timezone

import pytest

import bootstrap_prod
import reset_players
import seed_entorno_prueba as seed
from game_rules import DIFFICULTY_ORDER, MAX_INTENTOS_POR_TIPOLOGIA, MAX_SESSION_SCORE, UNLOCK_THRESHOLDS
from helpers import crear_entorno, crear_lectura, crear_usuario
from models import (
    AchievementCatalog, ActiveReading, NpcInteraction, PlayerAchievement, PlayerAnswer,
    PlayerNote, PlayerSession, PlayerSlot, PlayerTypologyProgress, SessionTool, User, Workspace,
)
from progression import aprobada, juego_terminado

CLAVE = "Test1234!"


@pytest.fixture
def corpus(db):
    for tipologia in DIFFICULTY_ORDER:
        for i in range(5):
            crear_lectura(db, f"{tipologia} {i}", tipologia)


def _pruebas(db):
    return db.query(Workspace).filter_by(name="Pruebas").one()


def _alumno(db, n):
    return db.query(User).filter_by(email=f"alumno{n}@test.com", workspace_id=_pruebas(db).id).one()


def _filas(db, usuario):
    return {f.typology: f for f in db.query(PlayerTypologyProgress).filter_by(user_id=usuario.id)}


def _sesiones(db, usuario):
    return db.query(PlayerSession).filter_by(user_id=usuario.id).order_by(PlayerSession.completed_at).all()


def _logros(db, usuario):
    return {a.achievement_id for a in db.query(PlayerAchievement).filter_by(user_id=usuario.id)}


def test_crea_pruebas_con_50_cuentas(client, db, corpus):
    resumen = seed.sembrar(db)
    pruebas = _pruebas(db)
    assert (pruebas.color, pruebas.is_active, resumen["activado"]) == ("#d97706", True, True)
    cuentas = db.query(User).filter_by(workspace_id=pruebas.id).all()
    assert {u.email for u in cuentas} == {f"alumno{i}@test.com" for i in range(1, 51)}
    assert db.get(AchievementCatalog, "explorer") is not None
    r = client.post("/auth/login", json={"email": "alumno41@test.com", "password": CLAVE})
    assert r.status_code == 200
    assert r.json()["must_change_password"] is False


def test_los_40_primeros_estan_nuevos(db, corpus):
    seed.sembrar(db)
    for n in range(1, 41):
        usuario = _alumno(db, n)
        assert _sesiones(db, usuario) == []
        assert {t: f.is_unlocked for t, f in _filas(db, usuario).items()} == {
            "Narrativo": True, "Descriptivo": False, "Argumentativo": False, "Expositivo": False,
        }


def test_los_10_ultimos_son_coherentes(db, corpus):
    seed.sembrar(db)
    ahora = datetime.now(timezone.utc)
    fechas = set()
    for n in range(41, 51):
        usuario = _alumno(db, n)
        filas = _filas(db, usuario)
        sesiones = _sesiones(db, usuario)
        assert sesiones, n
        for tipologia in DIFFICULTY_ORDER:
            propias = [s for s in sesiones if s.typology == tipologia]
            fila = filas[tipologia]
            assert fila.attempts_used == fila.total_sessions == len(propias) <= MAX_INTENTOS_POR_TIPOLOGIA, (n, tipologia)
            assert fila.best_score == max((s.session_score for s in propias), default=0), (n, tipologia)
            assert fila.perfect_sessions == sum(s.is_perfect for s in propias)
            assert len({s.reading_id for s in propias}) == len(propias), (n, tipologia)
        for i, tipologia in enumerate(DIFFICULTY_ORDER):
            anterior = filas[DIFFICULTY_ORDER[i - 1]] if i else None
            esperado = (i == 0 or filas[tipologia].total_sessions > 0
                        or anterior.best_score >= UNLOCK_THRESHOLDS[tipologia])
            assert filas[tipologia].is_unlocked == esperado, (n, tipologia)
        for sesion in sesiones:
            respuestas = db.query(PlayerAnswer).filter_by(session_id=sesion.id).order_by(PlayerAnswer.id).all()
            assert [r.comprehension_level for r in respuestas] == ["Literal"] * 2 + ["Inferencial"] * 2 + ["Critico"] * 2
            aciertos = {nivel: [r.is_correct for r in respuestas if r.comprehension_level == nivel]
                        for nivel in ("Literal", "Inferencial", "Critico")}
            usadas = db.query(SessionTool).filter_by(session_id=sesion.id, was_used=True).count()
            assert sesion.session_score == seed.puntaje_sesion(aciertos, usadas) <= MAX_SESSION_SCORE
            assert (sesion.correct_count, sesion.incorrect_count) == (
                sum(r.is_correct for r in respuestas), sum(not r.is_correct for r in respuestas))
            assert sesion.is_perfect == all(r.is_correct for r in respuestas)
            assert sesion.tool_bonus == 20 * usadas
            assert ahora - timedelta(days=22) < sesion.completed_at <= ahora
            fechas.add(sesion.completed_at.date())
    assert len(fechas) >= 5  # repartidas, no todas el mismo día


def test_los_10_cubren_los_casos(db, corpus):
    seed.sembrar(db)

    def estado(n):
        usuario = _alumno(db, n)
        return usuario, _filas(db, usuario), _sesiones(db, usuario)

    _, filas, sesiones = estado(41)
    assert len(sesiones) == 1 and not aprobada(filas["Narrativo"])
    _, filas, sesiones = estado(42)
    assert filas["Narrativo"].attempts_used == 2 and aprobada(filas["Narrativo"])
    assert sesiones[0].session_score < 120 <= sesiones[1].session_score
    for n, cuantas in ((43, 2), (44, 3), (45, 4)):
        _, filas, _ = estado(n)
        assert sum(aprobada(f) for f in filas.values()) == cuantas, n
    _, filas, _ = estado(46)
    assert juego_terminado(filas.values())
    usuario, filas, sesiones = estado(47)
    activa = db.query(ActiveReading).filter_by(user_id=usuario.id).one()
    assert activa.typology == "Descriptivo" and filas["Descriptivo"].is_unlocked
    assert activa.reading_id not in {s.reading_id for s in sesiones}
    resultados = json.loads(activa.results_json)
    assert [r["level"] for r in resultados] == ["Literal", "Literal"] and activa.current_level_index == 1
    _, filas, _ = estado(48)
    assert any(f.attempts_used == 4 and not aprobada(f) for f in filas.values())
    usuario, _, sesiones = estado(49)
    assert any(s.is_perfect and s.tool_bonus == 60 for s in sesiones)
    usuario, _, _ = estado(50)
    assert db.query(PlayerNote).filter_by(user_id=usuario.id).count() >= 1
    assert db.query(NpcInteraction).filter_by(user_id=usuario.id).count() >= 1

    # Logros coherentes con lo jugado, como los da el juego.
    for n in range(41, 51):
        usuario, filas, sesiones = estado(n)
        logros = _logros(db, usuario)
        total = sum(f.best_score for f in filas.values())
        assert ("first_reading" in logros) == bool(sesiones), n
        assert ("explorer" in logros) == all(f.total_sessions > 0 for f in filas.values()), n
        assert ("avid_reader" in logros) == (len(sesiones) >= 4), n
        assert ("perfectionist" in logros) == any(s.is_perfect for s in sesiones), n
        assert ("centurion" in logros) == (total >= 100), n
        assert ("half_millennium" in logros) == (total >= 500), n


def test_repetir_deja_lo_mismo_y_no_toca_otros(db, corpus):
    real = crear_entorno(db, "Real")
    del_real, _ = crear_usuario(db, "alumno1@test.com", entorno=real)
    viejo, _ = crear_usuario(db, "alumno2@test.com", entorno=False)
    seed.sembrar(db)
    pruebas_id = _pruebas(db).id
    antes = (db.query(User).filter_by(workspace_id=pruebas_id).count(),
             db.query(PlayerSession).join(User).filter(User.workspace_id == pruebas_id).count())
    seed.sembrar(db)
    db.expire_all()
    despues = (db.query(User).filter_by(workspace_id=pruebas_id).count(),
               db.query(PlayerSession).join(User).filter(User.workspace_id == pruebas_id).count())
    assert antes == despues
    assert db.get(User, del_real.id) is not None and db.get(User, viejo.id) is not None
    assert db.query(Workspace).count() == 2


def test_solo_activa_si_no_hay_activo(db, corpus):
    real = crear_entorno(db, "Real", activo=True)
    resumen = seed.sembrar(db)
    db.expire_all()
    assert resumen["activado"] is False
    assert db.get(Workspace, real.id).is_active and not _pruebas(db).is_active


def test_falta_corpus(db):
    for tipologia in DIFFICULTY_ORDER:
        for i in range(4 if tipologia == "Descriptivo" else 5):
            crear_lectura(db, f"{tipologia} {i}", tipologia)
    with pytest.raises(SystemExit) as error:
        seed.sembrar(db)
    assert "Descriptivo" in str(error.value)
    db.rollback()
    assert db.query(Workspace).count() == 0
    assert db.query(User).count() == 0


def test_bootstrap_demo_va_al_activo(db, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "jefe@test.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "UnaClaveLarga123")
    bootstrap_prod.main()
    assert db.query(User).filter_by(email="demo@demo.com").count() == 0  # sin entorno activo
    real = crear_entorno(db, "Real", activo=True)
    bootstrap_prod.main()
    db.expire_all()
    demo = db.query(User).filter_by(email="demo@demo.com").one()
    assert demo.workspace_id == real.id
    assert db.query(PlayerSlot).filter_by(user_id=demo.id, is_active=True).count() == 1
    assert db.query(User).filter_by(email="jefe@test.com", is_admin=True, workspace_id=None).count() == 1


def test_reset_players_por_entorno(db, monkeypatch):
    real = crear_entorno(db, "Real", activo=True)
    pruebas = crear_entorno(db, "Pruebas")
    lectura = crear_lectura(db, "Lectura")
    for entorno in (real, pruebas):
        usuario, slot = crear_usuario(db, "alumno1@test.com", entorno=entorno)
        db.add(PlayerSession(user_id=usuario.id, slot_id=slot.id, reading_id=lectura.id,
                             typology="Narrativo", session_score=60))
    db.commit()

    def sesiones(entorno):
        db.expire_all()
        return db.query(PlayerSession).join(User).filter(User.workspace_id == entorno.id).count()

    monkeypatch.setattr(sys, "argv", ["reset_players.py", "--entorno", "Pruebas", "--students", "1", "--apply"])
    assert reset_players.main() == 0
    assert (sesiones(real), sesiones(pruebas)) == (1, 0)
    monkeypatch.setattr(sys, "argv", ["reset_players.py", "--students", "1", "--apply"])  # el activo
    assert reset_players.main() == 0
    assert sesiones(real) == 0


def test_bootstrap_no_convierte_en_admin_una_cuenta_de_jugador(db, monkeypatch):
    real = crear_entorno(db, "Real", activo=True)
    jugador, _ = crear_usuario(db, "jefe@test.com", entorno=real)
    monkeypatch.setenv("ADMIN_EMAIL", "jefe@test.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "UnaClaveLarga123")
    bootstrap_prod.main()
    db.expire_all()
    assert db.get(User, jugador.id).is_admin is False
    assert db.query(User).filter_by(email="jefe@test.com", is_admin=True, workspace_id=None).count() == 1
