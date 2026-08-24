"""
seed_30_users.py — Crea 30 usuarios de prueba para tests de carga y sesiones simultáneas.
Ejecutar:
    python seed_30_users.py
o dentro de docker:
    docker compose exec api python seed_30_users.py
"""
import os
import sys
import random
from datetime import datetime, timedelta, timezone

# Configurar DATABASE_URL si no está en entorno
if not os.getenv("DATABASE_URL"):
    # Antes aqui habia un fallback a localhost:5433 con la contrasena en claro.
    # Ese puerto es hoy el Postgres de LecturaIA, de otro autor: ejecutar este
    # script fuera del contenedor sin la variable puesta habria escrito en su
    # base de datos. Mejor fallar que adivinar.
    raise SystemExit(
        "ERROR: DATABASE_URL no esta definida. Dentro del contenedor ya viene "
        "del .env:  docker exec vw-api-1 python seed_30_users.py  --  fuera, pasala "
        "explicitamente. OJO: el puerto 5432 es el entorno virtual y el 5433 "
        "es LecturaIA."
    )

from database import SessionLocal, engine, Base
from models import (
    User, PlayerSession, PlayerAnswer, SessionTool,
    PlayerNote, PlayerTypologyProgress, PlayerAchievement,
    PlayerSlot, AchievementCatalog, Reading,
)
from auth import hash_password

DIFFICULTY_ORDER = ["Narrativo", "Descriptivo", "Argumentativo", "Instructivo", "Expositivo"]
PASSWORD = "Test1234!"
ADMIN_PASSWORD = "Admin1234!"

# Generar datos para 30 alumnos
STUDENTS_COUNT = 30
USERS_DATA = []

for i in range(1, STUDENTS_COUNT + 1):
    char_type = "male" if i % 2 != 0 else "women"
    USERS_DATA.append({
        "email": f"alumno{i}@test.com",
        "display_name": f"Alumno {i:02d}",
        "character": char_type,
        "is_admin": False,
    })

# Añadir administrador
USERS_DATA.append({
    "email": "admin@test.com",
    "display_name": "Administrador",
    "character": "male",
    "is_admin": True,
})


def seed_30_users():
    db = SessionLocal()
    try:
        print("🚀 [Seed 30 Users] Iniciando creación de usuarios para prueba concurrente...")
        created_count = 0
        existing_count = 0

        # Obtener una lectura de referencia si existe
        first_reading = db.query(Reading).first()
        rid = first_reading.id if first_reading else 1

        for data in USERS_DATA:
            existing = db.query(User).filter(User.email == data["email"]).first()
            if existing:
                existing_count += 1
                user = existing
            else:
                pwd = ADMIN_PASSWORD if data["is_admin"] else PASSWORD
                user = User(
                    email=data["email"],
                    hashed_password=hash_password(pwd),
                    display_name=data["display_name"],
                    character=data["character"],
                    is_admin=data["is_admin"],
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 15)),
                )
                db.add(user)
                db.flush()
                created_count += 1

            if not user.is_admin:
                # Crear slot 1
                slot = db.query(PlayerSlot).filter(
                    PlayerSlot.user_id == user.id,
                    PlayerSlot.slot_number == 1
                ).first()
                if not slot:
                    slot = PlayerSlot(
                        user_id=user.id,
                        slot_number=1,
                        label="Sesión Principal",
                        is_active=True
                    )
                    db.add(slot)
                    db.flush()

                # Crear progreso de tipologías base
                for typology in DIFFICULTY_ORDER:
                    typ_prog = db.query(PlayerTypologyProgress).filter(
                        PlayerTypologyProgress.user_id == user.id,
                        PlayerTypologyProgress.slot_id == slot.id,
                        PlayerTypologyProgress.typology == typology,
                    ).first()
                    if not typ_prog:
                        db.add(PlayerTypologyProgress(
                            user_id=user.id,
                            slot_id=slot.id,
                            typology=typology,
                            is_unlocked=(typology == "Narrativo" or random.random() > 0.5),
                            best_score=random.randint(50, 300) if typology == "Narrativo" else 0,
                            total_sessions=random.randint(0, 3) if typology == "Narrativo" else 0,
                            last_played_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48)),
                        ))

        db.commit()
        print(f"✅ Usuarios procesados: {len(USERS_DATA)} ({created_count} creados, {existing_count} ya existentes).")
        print(f"🔑 Credenciales Alumnos: alumno1@test.com hasta alumno30@test.com | Password: {PASSWORD}")
        print(f"🔑 Credenciales Admin:   admin@test.com | Password: {ADMIN_PASSWORD}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el seed de 30 usuarios: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_30_users()
