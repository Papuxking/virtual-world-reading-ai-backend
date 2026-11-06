"""seed_entorno_prueba.py — Crea o rehace el entorno de pruebas con 50 estudiantes.

Puebla el catálogo de logros, crea el entorno «Pruebas» (color #d97706),
lo activa si no hay ningún entorno activo, y genera alumno1@test.com .. alumno50@test.com
con contraseña Test1234!.
Los alumnos 1 a 40 están recién creados (slot 1, solo Narrativo desbloqueado, sin sesiones).
Los alumnos 41 a 50 tienen progreso variado y coherente con las reglas del juego.
Si no hay administrador, crea admin@test.com / Admin1234!.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect

from auth import hash_password
from catalogo_logros import INITIAL_ACHIEVEMENTS, seed_achievements_catalog
from database import SessionLocal, engine
from game_rules import (
    DIFFICULTY_ORDER,
    MAX_INTENTOS_POR_TIPOLOGIA,
    UNLOCK_THRESHOLDS,
)
from models import (
    ActiveReading,
    NpcInteraction,
    PlayerAchievement,
    PlayerAnswer,
    PlayerNote,
    PlayerSession,
    PlayerSlot,
    PlayerTypologyProgress,
    Question,
    Reading,
    SessionTool,
    User,
    Workspace,
)
from workspaces import crear_jugador, entorno_activo

TABLAS_PROPIAS = {"readings", "player_typology_progress", "achievement_catalog", "player_slots"}
COLOR_PRUEBAS = "#d97706"
PASSWORD = "Test1234!"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "Admin1234!"


def comprobar_base_correcta() -> None:
    existentes = set(inspect(engine).get_table_names())
    faltan = TABLAS_PROPIAS - existentes
    if faltan:
        print(
            "ABORTADO: la base de datos de destino no parece la del entorno virtual.\n"
            f"  Faltan las tablas: {sorted(faltan)}\n"
            "  Comprueba DATABASE_URL. El puerto 5433 es el Postgres de LecturaIA.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def puntaje_sesion(aciertos: dict[str, list[bool]], herramientas: int) -> int:
    """Calcula el puntaje de una sesión según las reglas de game_session.gd."""
    puntaje = 0
    errores_totales = 0
    for nivel, puntos, penalizacion in (("Literal", 10, 3), ("Inferencial", 20, 5), ("Critico", 30, 8)):
        respuestas = aciertos.get(nivel, [])
        errores_nivel = 0
        for ok in respuestas:
            if ok:
                puntaje += puntos
            else:
                puntaje = max(0, puntaje - penalizacion)
                errores_nivel += 1
        errores_totales += errores_nivel
        if len(respuestas) == 2 and errores_nivel == 0:
            puntaje += 15
    puntaje += 50  # Bono sesión completada
    if errores_totales == 0:
        puntaje += 25  # Bono sesión perfecta
    puntaje += 20 * herramientas
    return puntaje


def _crear_sesion(
    db,
    usuario: User,
    slot: PlayerSlot,
    lectura: Reading,
    tipologia: str,
    aciertos_config: dict[str, list[bool]],
    herramientas_usadas: list[str],
    fecha: datetime,
) -> PlayerSession:
    score = puntaje_sesion(aciertos_config, len(herramientas_usadas))
    correct_count = sum(sum(1 for ok in lst if ok) for lst in aciertos_config.values())
    incorrect_count = sum(sum(1 for ok in lst if not ok) for lst in aciertos_config.values())
    is_perfect = (incorrect_count == 0)
    tool_bonus = 20 * len(herramientas_usadas)

    session = PlayerSession(
        user_id=usuario.id,
        slot_id=slot.id,
        reading_id=lectura.id,
        typology=tipologia,
        session_score=score,
        reading_time_seconds=120,
        total_time_seconds=300,
        is_perfect=is_perfect,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        tool_bonus=tool_bonus,
        started_at=fecha - timedelta(minutes=5),
        completed_at=fecha,
    )
    db.add(session)
    db.flush()

    preguntas = db.query(Question).filter_by(reading_id=lectura.id).order_by(Question.question_number).all()
    preguntas_por_nivel: dict[str, list[Question]] = {}
    for q in preguntas:
        preguntas_por_nivel.setdefault(q.comprehension_level, []).append(q)

    # Insertar siempre 2 Literal, 2 Inferencial, 2 Critico
    for nivel in ("Literal", "Inferencial", "Critico"):
        qs = preguntas_por_nivel.get(nivel, [])
        oks = aciertos_config.get(nivel, [True, True])
        for idx in range(2):
            q = qs[idx] if idx < len(qs) else None
            qid = q.id if q else idx + 1
            corr_ans = q.correct_answer if q else "A"
            ok = oks[idx] if idx < len(oks) else True
            sel_ans = corr_ans if ok else ("B" if corr_ans == "A" else "A")
            pts = (10 if nivel == "Literal" else 20 if nivel == "Inferencial" else 30) if ok else 0
            pen = 0 if ok else (3 if nivel == "Literal" else 5 if nivel == "Inferencial" else 8)
            ans = PlayerAnswer(
                session_id=session.id,
                question_id=qid,
                comprehension_level=nivel,
                selected_answer=sel_ans,
                correct_answer=corr_ans,
                is_correct=ok,
                points_earned=pts,
                penalty_applied=pen,
                response_time_ms=5000,
                answered_at=fecha - timedelta(minutes=4 - idx),
            )
            db.add(ans)

    for t_name in ("highlight", "underline", "notes"):
        was_used = t_name in herramientas_usadas
        st = SessionTool(
            session_id=session.id,
            tool_name=t_name,
            was_used=was_used,
            usage_count=2 if was_used else 0,
            duration_seconds=30 if was_used else 0,
        )
        db.add(st)

    db.flush()
    return session


def _actualizar_progreso_y_logros(
    db,
    usuario: User,
    slot: PlayerSlot,
    sesiones: list[PlayerSession],
    nombres_logros: dict[str, str],
) -> None:
    filas = {
        f.typology: f
        for f in db.query(PlayerTypologyProgress).filter_by(user_id=usuario.id, slot_id=slot.id).all()
    }

    for tipologia in DIFFICULTY_ORDER:
        propias = [s for s in sesiones if s.typology == tipologia]
        fila = filas[tipologia]
        fila.attempts_used = len(propias)
        fila.total_sessions = len(propias)
        fila.best_score = max((s.session_score for s in propias), default=0)
        fila.perfect_sessions = sum(1 for s in propias if s.is_perfect)
        fila.first_completed_at = propias[0].completed_at if propias else None
        fila.last_played_at = propias[-1].completed_at if propias else None

    # Desbloqueos en cadena
    for i, tipologia in enumerate(DIFFICULTY_ORDER):
        fila = filas[tipologia]
        if i == 0:
            fila.is_unlocked = True
        else:
            anterior = filas[DIFFICULTY_ORDER[i - 1]]
            fila.is_unlocked = (fila.total_sessions > 0 or anterior.best_score >= UNLOCK_THRESHOLDS[tipologia])

    # Logros coherentes
    total_score = sum(f.best_score for f in filas.values())
    condiciones = {
        "first_reading": bool(sesiones),
        "explorer": all(f.total_sessions > 0 for f in filas.values()),
        "avid_reader": len(sesiones) >= 4,
        "perfectionist": any(s.is_perfect for s in sesiones),
        "centurion": total_score >= 100,
        "half_millennium": total_score >= 500,
    }
    for ach_id, aplica in condiciones.items():
        if aplica:
            db.add(PlayerAchievement(
                user_id=usuario.id,
                slot_id=slot.id,
                achievement_id=ach_id,
                achievement_name=nombres_logros.get(ach_id, ach_id),
                unlocked_at=sesiones[-1].completed_at if sesiones else datetime.now(timezone.utc),
            ))
    db.flush()


def sembrar(db, nombre: str = "Pruebas") -> dict:
    """Siembra el catálogo de logros y el entorno con 50 estudiantes."""
    # 1. Comprobar corpus: al menos 5 lecturas por tipología
    readings_by_typology: dict[str, list[Reading]] = {}
    for t in DIFFICULTY_ORDER:
        lecturas = db.query(Reading).filter_by(typology=t).order_by(Reading.id).all()
        if len(lecturas) < 5:
            raise SystemExit(f"Falta corpus: se requieren al menos 5 lecturas de progresión para la tipología {t}")
        readings_by_typology[t] = lecturas

    # 2. Catálogo de logros
    seed_achievements_catalog(db)
    nombres_logros = {item["id"]: item["name"] for item in INITIAL_ACHIEVEMENTS}

    # 3. Administrador local si no existe ninguno
    admin = db.query(User).filter_by(is_admin=True).first()
    if not admin:
        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            display_name="Administrador",
            character="male",
            is_admin=True,
            is_active=True,
            workspace_id=None,
        )
        db.add(admin)
        db.flush()

    # 4. Entorno de trabajo
    activo_existente = entorno_activo(db)
    workspace = db.query(Workspace).filter(Workspace.name == nombre).first()
    activado = False
    if not workspace:
        workspace = Workspace(name=nombre, color=COLOR_PRUEBAS, is_active=False)
        db.add(workspace)
        db.flush()

    if activo_existente is None and not workspace.is_active:
        workspace.is_active = True
        activado = True
    elif workspace.is_active:
        activado = True

    # 5. Si ya existían estudiantes en este entorno, limpiarlos
    existentes = db.query(User).filter_by(workspace_id=workspace.id).all()
    for u in existentes:
        db.delete(u)
    db.flush()

    # bcrypt es lento: la misma contraseña se calcula una vez para las 50 cuentas.
    hash_clave = hash_password(PASSWORD)

    # 6. Crear alumnos 1..40 (recién creados)
    usuarios: dict[int, User] = {}
    slots: dict[int, PlayerSlot] = {}
    for n in range(1, 41):
        email = f"alumno{n}@test.com"
        u = crear_jugador(
            db,
            workspace_id=workspace.id,
            email=email,
            display_name=f"Alumno {n}",
            password=PASSWORD,
            hashed_password=hash_clave,
            must_change_password=False,
            character="male" if n % 2 != 0 else "women",
        )
        usuarios[n] = u
        slot = db.query(PlayerSlot).filter_by(user_id=u.id, slot_number=1).one()
        slots[n] = slot

    # 7. Crear alumnos 41..50 con progreso coherente
    for n in range(41, 51):
        email = f"alumno{n}@test.com"
        u = crear_jugador(
            db,
            workspace_id=workspace.id,
            email=email,
            display_name=f"Alumno {n}",
            password=PASSWORD,
            hashed_password=hash_clave,
            must_change_password=False,
            character="male" if n % 2 != 0 else "women",
        )
        usuarios[n] = u
        slot = db.query(PlayerSlot).filter_by(user_id=u.id, slot_number=1).one()
        slots[n] = slot

    ahora = datetime.now(timezone.utc)
    fechas = [ahora - timedelta(days=d) for d in [20, 16, 13, 10, 8, 6, 4, 3, 2, 1]]

    # Configuraciones de respuestas
    # Aciertos para puntaje aprobatorio (~187 pts, con 1 fallo en Literal)
    aprobatoria = {"Literal": [True, False], "Inferencial": [True, True], "Critico": [True, True]}
    # Aciertos para puntaje fallido (< 120 pts, 56 pts)
    fallida = {"Literal": [True, False], "Inferencial": [True, False], "Critico": [False, False]}
    # Aciertos perfecta
    perfecta = {"Literal": [True, True], "Inferencial": [True, True], "Critico": [True, True]}

    perfiles_resumen = {}

    # alumno41: 1 intento fallido en Narrativo
    s41 = [
        _crear_sesion(db, usuarios[41], slots[41], readings_by_typology["Narrativo"][0],
                      "Narrativo", fallida, [], fechas[0]),
    ]
    _actualizar_progreso_y_logros(db, usuarios[41], slots[41], s41, nombres_logros)
    perfiles_resumen[41] = "1 intento fallido en Narrativo (sin aprobar)"

    # alumno42: aprobada al segundo intento (Narrativo: fallido + aprobado)
    s42 = [
        _crear_sesion(db, usuarios[42], slots[42], readings_by_typology["Narrativo"][0],
                      "Narrativo", fallida, [], fechas[1]),
        _crear_sesion(db, usuarios[42], slots[42], readings_by_typology["Narrativo"][1],
                      "Narrativo", aprobatoria, [], fechas[2]),
    ]
    _actualizar_progreso_y_logros(db, usuarios[42], slots[42], s42, nombres_logros)
    perfiles_resumen[42] = "Aprobó Narrativo al segundo intento"

    # alumno43: 2 tipologías aprobadas (Narrativo, Descriptivo)
    s43 = [
        _crear_sesion(db, usuarios[43], slots[43], readings_by_typology["Narrativo"][0],
                      "Narrativo", aprobatoria, [], fechas[1]),
        _crear_sesion(db, usuarios[43], slots[43], readings_by_typology["Descriptivo"][0],
                      "Descriptivo", aprobatoria, [], fechas[3]),
    ]
    _actualizar_progreso_y_logros(db, usuarios[43], slots[43], s43, nombres_logros)
    perfiles_resumen[43] = "2 tipologías aprobadas (Narrativo y Descriptivo)"

    # alumno44: 3 tipologías aprobadas (Narrativo, Descriptivo, Argumentativo)
    s44 = [
        _crear_sesion(db, usuarios[44], slots[44], readings_by_typology["Narrativo"][0],
                      "Narrativo", aprobatoria, [], fechas[1]),
        _crear_sesion(db, usuarios[44], slots[44], readings_by_typology["Descriptivo"][0],
                      "Descriptivo", aprobatoria, [], fechas[2]),
        _crear_sesion(db, usuarios[44], slots[44], readings_by_typology["Argumentativo"][0],
                      "Argumentativo", aprobatoria, [], fechas[4]),
    ]
    _actualizar_progreso_y_logros(db, usuarios[44], slots[44], s44, nombres_logros)
    perfiles_resumen[44] = "3 tipologías aprobadas"

    # alumno45: 4 tipologías aprobadas (juego completo)
    s45 = [
        _crear_sesion(db, usuarios[45], slots[45], readings_by_typology["Narrativo"][0],
                      "Narrativo", aprobatoria, [], fechas[1]),
        _crear_sesion(db, usuarios[45], slots[45], readings_by_typology["Descriptivo"][0],
                      "Descriptivo", aprobatoria, [], fechas[3]),
        _crear_sesion(db, usuarios[45], slots[45], readings_by_typology["Argumentativo"][0],
                      "Argumentativo", aprobatoria, [], fechas[5]),
        _crear_sesion(db, usuarios[45], slots[45], readings_by_typology["Expositivo"][0],
                      "Expositivo", aprobatoria, [], fechas[7]),
    ]
    _actualizar_progreso_y_logros(db, usuarios[45], slots[45], s45, nombres_logros)
    perfiles_resumen[45] = "4 tipologías aprobadas (Juego Completo)"

    # alumno46: 5 intentos agotados en Narrativo sin aprobar (juego terminado)
    s46 = [
        _crear_sesion(db, usuarios[46], slots[46], readings_by_typology["Narrativo"][i],
                      "Narrativo", fallida, [], fechas[i])
        for i in range(5)
    ]
    _actualizar_progreso_y_logros(db, usuarios[46], slots[46], s46, nombres_logros)
    perfiles_resumen[46] = "5 intentos agotados en Narrativo (Juego Terminado)"

    # alumno47: Narrativo aprobado y lectura activa en Descriptivo para reanudar
    s47 = [
        _crear_sesion(db, usuarios[47], slots[47], readings_by_typology["Narrativo"][0],
                      "Narrativo", aprobatoria, [], fechas[2]),
    ]
    _actualizar_progreso_y_logros(db, usuarios[47], slots[47], s47, nombres_logros)
    # Lectura activa en Descriptivo (lectura distinta a las jugadas)
    desc_activa = readings_by_typology["Descriptivo"][1]
    db.add(ActiveReading(
        user_id=usuarios[47].id,
        slot_id=slots[47].id,
        reading_id=desc_activa.id,
        typology="Descriptivo",
        current_level_index=1,
        current_question_index=0,
        reading_completed=True,
        results_json=json.dumps([{"level": "Literal", "question_id": 1, "correct": True},
                                 {"level": "Literal", "question_id": 2, "correct": True}]),
        tools_used_json='{"highlight":false,"underline":false,"notes":false}',
        reading_start_time="0",
        reading_seconds=75,
        total_seconds=120,
    ))
    db.flush()
    perfiles_resumen[47] = "Lectura en curso para reanudar en Descriptivo"

    # alumno48: 4 intentos de 5 usados en Narrativo sin aprobar
    s48 = [
        _crear_sesion(db, usuarios[48], slots[48], readings_by_typology["Narrativo"][i],
                      "Narrativo", fallida, [], fechas[i])
        for i in range(4)
    ]
    _actualizar_progreso_y_logros(db, usuarios[48], slots[48], s48, nombres_logros)
    perfiles_resumen[48] = "4 de 5 intentos usados en Narrativo"

    # alumno49: sesión perfecta con todas las herramientas usadas (bonus 60)
    s49 = [
        _crear_sesion(db, usuarios[49], slots[49], readings_by_typology["Narrativo"][0],
                      "Narrativo", perfecta, ["highlight", "underline", "notes"], fechas[6]),
    ]
    _actualizar_progreso_y_logros(db, usuarios[49], slots[49], s49, nombres_logros)
    perfiles_resumen[49] = "Sesión perfecta con 3 herramientas usadas (300 pts)"

    # alumno50: notas e interacción con NPC
    s50 = [
        _crear_sesion(db, usuarios[50], slots[50], readings_by_typology["Narrativo"][0],
                      "Narrativo", aprobatoria, ["notes"], fechas[8]),
    ]
    _actualizar_progreso_y_logros(db, usuarios[50], slots[50], s50, nombres_logros)
    db.add(PlayerNote(
        user_id=usuarios[50].id,
        slot_id=slots[50].id,
        reading_id=readings_by_typology["Narrativo"][0].id,
        session_id=s50[0].id,
        note_content="Nota de prueba tomada durante la lectura.",
    ))
    db.add(NpcInteraction(
        user_id=usuarios[50].id,
        slot_id=slots[50].id,
        npc_type="robot",
        session_id=s50[0].id,
        reading_id=readings_by_typology["Narrativo"][0].id,
    ))
    db.flush()
    perfiles_resumen[50] = "Con notas e interacción con NPC"

    db.commit()

    return {
        "entorno": workspace.name,
        "entorno_id": workspace.id,
        "color": workspace.color,
        "activado": activado,
        "cuentas_creadas": 50,
        "perfiles_progreso": perfiles_resumen,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entorno", default="Pruebas", help="Nombre del entorno (por defecto, 'Pruebas')")
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL no está definida. No se adivina por seguridad.", file=sys.stderr)
        return 2

    comprobar_base_correcta()
    db = SessionLocal()
    try:
        resumen = sembrar(db, nombre=args.entorno)
        print(f"\n✅ Entorno «{resumen['entorno']}» sembrado con éxito (ID: {resumen['entorno_id']}).")
        print(f"  Color: {resumen['color']}")
        print(f"  Activo: {'Sí' if resumen['activado'] else 'No'}")
        print(f"  Cuentas de estudiantes: 50 (alumno1@test.com .. alumno50@test.com / {PASSWORD})")
        print("\nPerfiles con progreso (alumnos 41 a 50):")
        for n, desc in resumen["perfiles_progreso"].items():
            print(f"  alumno{n}@test.com: {desc}")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
