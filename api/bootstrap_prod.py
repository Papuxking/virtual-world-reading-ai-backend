"""bootstrap_prod.py — Inicializacion de produccion.

Puebla el catalogo global de logros, crea la cuenta de administrador y una
cuenta de demostracion. A diferencia de seed_users.py no genera alumnos
ficticios ni progreso aleatorio, que falsearian las metricas del dashboard.

Idempotente: se puede ejecutar varias veces sin efectos secundarios.

Uso:
    ADMIN_EMAIL=... ADMIN_PASSWORD=... python bootstrap_prod.py
"""
import os
import sys

from database import SessionLocal
from models import User, PlayerSlot, PlayerTypologyProgress
from auth import hash_password
from seed_users import seed_achievements_catalog

DIFFICULTY_ORDER = ["Narrativo", "Descriptivo", "Argumentativo", "Instructivo", "Expositivo"]

# Cuenta de demostracion solicitada expresamente por el usuario.
# La contrasena es deliberadamente corta y no pasa el minimo de 8 caracteres
# que exige UserRegister; por eso se crea aqui, no por la API. UserLogin solo
# exige 1 caracter, asi que el inicio de sesion funciona igualmente.
DEMO_EMAIL = "demo@demo.com"
DEMO_PASSWORD = "demo"


def _ensure_player_setup(db, user):
    """Crea el slot 1 y el progreso inicial de tipologias si faltan."""
    slot = (
        db.query(PlayerSlot)
        .filter(PlayerSlot.user_id == user.id, PlayerSlot.slot_number == 1)
        .first()
    )
    if not slot:
        slot = PlayerSlot(user_id=user.id, slot_number=1, label="Sesion 1", is_active=True)
        db.add(slot)
        db.flush()

    for typology in DIFFICULTY_ORDER:
        existing = (
            db.query(PlayerTypologyProgress)
            .filter(
                PlayerTypologyProgress.user_id == user.id,
                PlayerTypologyProgress.slot_id == slot.id,
                PlayerTypologyProgress.typology == typology,
            )
            .first()
        )
        if not existing:
            db.add(PlayerTypologyProgress(
                user_id=user.id,
                slot_id=slot.id,
                typology=typology,
                is_unlocked=(typology == "Narrativo"),
                best_score=0,
                total_sessions=0,
            ))


def main() -> None:
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")

    if not email or not password:
        print("Faltan ADMIN_EMAIL y/o ADMIN_PASSWORD en el entorno.")
        sys.exit(1)
    if len(password) < 12:
        print("ADMIN_PASSWORD debe tener al menos 12 caracteres.")
        sys.exit(1)

    db = SessionLocal()
    try:
        seed_achievements_catalog(db)

        admin = db.query(User).filter(User.email == email).first()
        if admin:
            admin.hashed_password = hash_password(password)
            admin.is_admin = True
            admin.is_active = True
            print(f"Admin actualizado: {email}")
        else:
            db.add(User(
                email=email,
                hashed_password=hash_password(password),
                display_name="Administrador",
                character="male",
                is_admin=True,
                is_active=True,
                must_change_password=False,
            ))
            print(f"Admin creado: {email}")

        demo = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if demo:
            demo.hashed_password = hash_password(DEMO_PASSWORD)
            demo.is_admin = False
            demo.is_active = True
            demo.must_change_password = False
            print(f"Demo actualizado: {DEMO_EMAIL}")
        else:
            demo = User(
                email=DEMO_EMAIL,
                hashed_password=hash_password(DEMO_PASSWORD),
                display_name="Demo",
                character="male",
                is_admin=False,
                is_active=True,
                must_change_password=False,
            )
            db.add(demo)
            print(f"Demo creado: {DEMO_EMAIL}")
        db.flush()
        _ensure_player_setup(db, demo)

        db.commit()
        print("Bootstrap de produccion completado.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
