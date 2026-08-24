"""
clean_30_students.py — Limpia y resetea a los 30 alumnos (alumno1@test.com hasta alumno30@test.com)
dejándolos como usuarios nuevos listos para elegir su personaje al iniciar sesión.
"""
import os
import sys

if not os.getenv("DATABASE_URL"):
    # Antes aqui habia un fallback a localhost:5433 con la contrasena en claro.
    # Ese puerto es hoy el Postgres de LecturaIA, de otro autor: ejecutar este
    # script fuera del contenedor sin la variable puesta habria escrito en su
    # base de datos. Mejor fallar que adivinar.
    raise SystemExit(
        "ERROR: DATABASE_URL no esta definida. Dentro del contenedor ya viene "
        "del .env:  docker exec vw-api-1 python clean_30_students.py  --  fuera, pasala "
        "explicitamente. OJO: el puerto 5432 es el entorno virtual y el 5433 "
        "es LecturaIA."
    )

from database import SessionLocal
from models import (
    User, PlayerSlot, PlayerSession, PlayerAnswer, SessionTool,
    PlayerNote, PlayerTypologyProgress, PlayerAchievement,
    NpcInteraction, ActiveReading,
)
from auth import hash_password

DIFFICULTY_ORDER = ["Narrativo", "Descriptivo", "Argumentativo", "Instructivo", "Expositivo"]
STUDENTS_COUNT = 30
PASSWORD = "Test1234!"


def clean_students():
    db = SessionLocal()
    try:
        print("🧹 [Clean 30 Students] Iniciando reseteo de los 30 alumnos...")

        cleaned_count = 0
        created_count = 0

        for i in range(1, STUDENTS_COUNT + 1):
            email = f"alumno{i}@test.com"
            display_name = f"Alumno {i:02d}"

            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=hash_password(PASSWORD),
                    display_name=display_name,
                    character="male",
                    is_admin=False,
                    is_active=True,
                    must_change_password=False,
                    session_version=1,
                )
                db.add(user)
                db.flush()
                created_count += 1
            else:
                user.character = "male"
                user.display_name = display_name
                user.is_active = True
                user.must_change_password = False
                user.session_version = (user.session_version or 1) + 1
                cleaned_count += 1

            # 1. Limpiar lecturas activas e interacciones
            db.query(ActiveReading).filter(ActiveReading.user_id == user.id).delete()
            db.query(NpcInteraction).filter(NpcInteraction.user_id == user.id).delete()
            db.query(PlayerNote).filter(PlayerNote.user_id == user.id).delete()
            db.query(PlayerAchievement).filter(PlayerAchievement.user_id == user.id).delete()

            # 2. Limpiar respuestas, herramientas y sesiones
            sessions = db.query(PlayerSession).filter(PlayerSession.user_id == user.id).all()
            for s in sessions:
                db.query(PlayerAnswer).filter(PlayerAnswer.session_id == s.id).delete()
                db.query(SessionTool).filter(SessionTool.session_id == s.id).delete()
            db.query(PlayerSession).filter(PlayerSession.user_id == user.id).delete()

            # 3. Limpiar slots adicionales (dejar solo Slot 1)
            db.query(PlayerSlot).filter(
                PlayerSlot.user_id == user.id,
                PlayerSlot.slot_number > 1
            ).delete()

            slot1 = db.query(PlayerSlot).filter(
                PlayerSlot.user_id == user.id,
                PlayerSlot.slot_number == 1
            ).first()

            if not slot1:
                slot1 = PlayerSlot(
                    user_id=user.id,
                    slot_number=1,
                    label="Sesión 1",
                    is_active=True
                )
                db.add(slot1)
                db.flush()
            else:
                slot1.is_active = True
                slot1.label = "Sesión 1"

            # 4. Resetear progreso de tipologías a estado inicial (0 sesiones, solo Narrativo desbloqueado)
            db.query(PlayerTypologyProgress).filter(
                PlayerTypologyProgress.user_id == user.id
            ).delete()

            for typology in DIFFICULTY_ORDER:
                db.add(PlayerTypologyProgress(
                    user_id=user.id,
                    slot_id=slot1.id,
                    typology=typology,
                    is_unlocked=(typology == "Narrativo"),
                    best_score=0,
                    total_sessions=0,
                    perfect_sessions=0,
                    first_completed_at=None,
                    last_played_at=None,
                ))

        db.commit()
        print(f"✨ Éxito: {cleaned_count} alumnos reseteados, {created_count} creados.")
        print(f"🔑 Credenciales: alumno1@test.com hasta alumno30@test.com | Password: {PASSWORD}")
        print("🎮 Al iniciar sesión por primera vez, verán directamente la pantalla de selección de personaje.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al limpiar estudiantes: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clean_students()
