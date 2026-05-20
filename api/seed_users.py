"""
seed_users.py — Crea 10 usuarios de prueba con datos de progreso variados.
Ejecutar después de iniciar la base de datos:
    python seed_users.py

Perfiles:
  1. Principiante    - 1 sesión en Narrativo, puntaje bajo
  2. Intermedia      - 2 tipologías desbloqueadas
  3. Avanzado        - 3 tipologías, varios logros
  4. Experta         - Todas las tipologías, sesiones perfectas
  5. Nuevo           - Sin progreso (recién registrado)
  6. Con Notas       - Usa muchas herramientas y notas
  7. Rápido          - Tiempos de lectura cortos
  8. Perfeccionista  - Todas las sesiones perfectas
  9. Luchador        - Muchos intentos, mejora progresiva
  10. Administrador  - Cuenta admin para el dashboard
"""
import os
import sys
from datetime import datetime, timedelta, timezone

# Configurar DATABASE_URL si no está en entorno
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = (
        "postgresql://DB-virtual-world-reading-ai:GodotWorldAdmin@localhost:5433/godot_readings"
    )

from database import SessionLocal, engine, Base
from models import (
    User, PlayerSession, PlayerAnswer, SessionTool,
    PlayerNote, PlayerTypologyProgress, PlayerAchievement,
)
from auth import hash_password

# Orden de dificultad
DIFFICULTY_ORDER = ["Narrativo", "Descriptivo", "Argumentativo", "Instructivo", "Expositivo"]

# Datos de los 10 usuarios
USERS_DATA = [
    {"email": "alumno1@test.com", "display_name": "Alumno Principiante", "character": "male", "is_admin": False},
    {"email": "alumno2@test.com", "display_name": "Alumna Intermedia", "character": "women", "is_admin": False},
    {"email": "alumno3@test.com", "display_name": "Alumno Avanzado", "character": "male", "is_admin": False},
    {"email": "alumno4@test.com", "display_name": "Alumna Experta", "character": "women", "is_admin": False},
    {"email": "alumno5@test.com", "display_name": "Alumno Nuevo", "character": "male", "is_admin": False},
    {"email": "alumno6@test.com", "display_name": "Alumna Con Notas", "character": "women", "is_admin": False},
    {"email": "alumno7@test.com", "display_name": "Alumno Rápido", "character": "male", "is_admin": False},
    {"email": "alumno8@test.com", "display_name": "Alumna Perfeccionista", "character": "women", "is_admin": False},
    {"email": "alumno9@test.com", "display_name": "Alumno Luchador", "character": "male", "is_admin": False},
    {"email": "admin@test.com", "display_name": "Administrador", "character": "male", "is_admin": True},
]

PASSWORD = "Test1234!"
ADMIN_PASSWORD = "Admin1234!"


def create_users(db):
    """Crea los 10 usuarios."""
    users = []
    for data in USERS_DATA:
        existing = db.query(User).filter(User.email == data["email"]).first()
        if existing:
            print(f"  ⏭ Usuario ya existe: {data['email']}")
            users.append(existing)
            continue

        pwd = ADMIN_PASSWORD if data["is_admin"] else PASSWORD
        user = User(
            email=data["email"],
            hashed_password=hash_password(pwd),
            display_name=data["display_name"],
            character=data["character"],
            is_admin=data["is_admin"],
            created_at=datetime.now(timezone.utc) - timedelta(days=10),
        )
        db.add(user)
        db.flush()
        users.append(user)
        print(f"  ✅ Creado: {data['email']} (ID: {user.id})")

    return users


def init_typology_progress(db, user, unlocked_list, scores=None):
    """Inicializa progreso de tipologías para un usuario."""
    scores = scores or {}
    for typology in DIFFICULTY_ORDER:
        existing = (
            db.query(PlayerTypologyProgress)
            .filter(PlayerTypologyProgress.user_id == user.id, PlayerTypologyProgress.typology == typology)
            .first()
        )
        if existing:
            continue

        best = scores.get(typology, 0)
        total_s = 1 if best > 0 else 0
        p = PlayerTypologyProgress(
            user_id=user.id,
            typology=typology,
            best_score=best,
            total_sessions=total_s,
            is_unlocked=(typology in unlocked_list),
            first_completed_at=datetime.now(timezone.utc) - timedelta(days=5) if best > 0 else None,
            last_played_at=datetime.now(timezone.utc) - timedelta(days=1) if best > 0 else None,
        )
        db.add(p)


def add_session(db, user_id, reading_id, typology, score, correct, incorrect, perfect=False, tool_bonus=0, days_ago=1):
    """Agrega una sesión de juego."""
    session = PlayerSession(
        user_id=user_id,
        reading_id=reading_id,
        typology=typology,
        session_score=score,
        reading_time_seconds=180 + (score % 120),
        total_time_seconds=360 + (score % 200),
        is_perfect=perfect,
        correct_count=correct,
        incorrect_count=incorrect,
        tool_bonus=tool_bonus,
        started_at=datetime.now(timezone.utc) - timedelta(days=days_ago, hours=2),
        completed_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )
    db.add(session)
    db.flush()
    return session


def add_tools(db, session_id, highlight=False, underline=False, notes=False):
    """Agrega herramientas usadas en una sesión."""
    for name, used in [("highlight", highlight), ("underline", underline), ("notes", notes)]:
        tool = SessionTool(
            session_id=session_id,
            tool_name=name,
            was_used=used,
            usage_count=3 if used else 0,
        )
        db.add(tool)


def add_achievement(db, user_id, aid, aname, days_ago=5):
    """Agrega un logro."""
    existing = (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.user_id == user_id, PlayerAchievement.achievement_id == aid)
        .first()
    )
    if existing:
        return
    db.add(PlayerAchievement(
        user_id=user_id,
        achievement_id=aid,
        achievement_name=aname,
        unlocked_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    ))


def seed():
    """Ejecuta el seed completo."""
    db = SessionLocal()
    try:
        print("\n🌱 Iniciando seed de usuarios de prueba...\n")

        # Verificar que hay lecturas en la BD
        from models import Reading
        reading_count = db.query(Reading).count()
        if reading_count == 0:
            print("⚠️  No hay lecturas en la BD. Las sesiones necesitan reading_id válidos.")
            print("   Ejecuta primero el seed de lecturas o importa datos.")

        # Obtener un reading_id válido para las sesiones
        first_reading = db.query(Reading).first()
        rid = first_reading.id if first_reading else 1

        users = create_users(db)
        db.commit()

        print("\n📊 Configurando progreso de prueba...\n")

        # ── Usuario 1: Principiante ──
        u = users[0]
        init_typology_progress(db, u, ["Narrativo"], {"Narrativo": 120})
        s = add_session(db, u.id, rid, "Narrativo", 120, 3, 3, days_ago=7)
        add_tools(db, s.id, highlight=True)
        add_achievement(db, u.id, "first_reading", "📖 Primera lectura", 7)
        print(f"  📌 {u.display_name}: Principiante (1 sesión)")

        # ── Usuario 2: Intermedia ──
        u = users[1]
        init_typology_progress(db, u, ["Narrativo", "Descriptivo"],
                               {"Narrativo": 280, "Descriptivo": 210})
        add_session(db, u.id, rid, "Narrativo", 280, 5, 1, days_ago=8)
        add_session(db, u.id, rid, "Narrativo", 250, 4, 2, days_ago=6)
        s = add_session(db, u.id, rid, "Descriptivo", 210, 4, 2, tool_bonus=40, days_ago=3)
        add_tools(db, s.id, highlight=True, underline=True)
        add_achievement(db, u.id, "first_reading", "📖 Primera lectura", 8)
        print(f"  📌 {u.display_name}: Intermedia (3 sesiones)")

        # ── Usuario 3: Avanzado ──
        u = users[2]
        init_typology_progress(db, u, ["Narrativo", "Descriptivo", "Argumentativo"],
                               {"Narrativo": 310, "Descriptivo": 275, "Argumentativo": 180})
        add_session(db, u.id, rid, "Narrativo", 310, 5, 1, days_ago=9)
        add_session(db, u.id, rid, "Descriptivo", 275, 5, 1, days_ago=6)
        s = add_session(db, u.id, rid, "Argumentativo", 180, 4, 2, tool_bonus=40, days_ago=2)
        add_tools(db, s.id, highlight=True, underline=True)
        add_achievement(db, u.id, "first_reading", "📖 Primera lectura", 9)
        add_achievement(db, u.id, "centurion", "💯 Centurión", 6)
        add_achievement(db, u.id, "improvement", "📈 En mejora", 3)
        print(f"  📌 {u.display_name}: Avanzado (3 sesiones, 3 logros)")

        # ── Usuario 4: Experta ──
        u = users[3]
        init_typology_progress(db, u, DIFFICULTY_ORDER,
                               {"Narrativo": 350, "Descriptivo": 320, "Argumentativo": 290,
                                "Instructivo": 310, "Expositivo": 280})
        for i, typ in enumerate(DIFFICULTY_ORDER):
            s = add_session(db, u.id, rid, typ, 280 + i * 20, 6, 0, perfect=True,
                          tool_bonus=60, days_ago=10 - i * 2)
            add_tools(db, s.id, highlight=True, underline=True, notes=True)
        add_achievement(db, u.id, "first_reading", "📖 Primera lectura", 10)
        add_achievement(db, u.id, "explorer", "🏅 Explorador", 4)
        add_achievement(db, u.id, "perfectionist", "🎯 Perfeccionista", 8)
        add_achievement(db, u.id, "centurion", "💯 Centurión", 7)
        add_achievement(db, u.id, "half_millennium", "🏆 Medio milenio", 2)
        add_achievement(db, u.id, "star_literal", "⭐ Estrella literal", 5)
        print(f"  📌 {u.display_name}: Experta (5 sesiones perfectas, 6 logros)")

        # ── Usuario 5: Nuevo (sin progreso) ──
        u = users[4]
        init_typology_progress(db, u, ["Narrativo"])
        print(f"  📌 {u.display_name}: Sin progreso")

        # ── Usuario 6: Con Notas ──
        u = users[5]
        init_typology_progress(db, u, ["Narrativo", "Descriptivo"],
                               {"Narrativo": 260, "Descriptivo": 230})
        s = add_session(db, u.id, rid, "Narrativo", 260, 5, 1, tool_bonus=60, days_ago=5)
        add_tools(db, s.id, highlight=True, underline=True, notes=True)
        s2 = add_session(db, u.id, rid, "Descriptivo", 230, 4, 2, tool_bonus=60, days_ago=2)
        add_tools(db, s2.id, highlight=True, underline=True, notes=True)
        # Agregar notas reales
        db.add(PlayerNote(
            user_id=u.id, reading_id=rid, session_id=s.id,
            note_content="La idea principal del texto es que la lectura comprensiva mejora el pensamiento crítico. El autor usa ejemplos de estudios científicos para respaldar su argumento.",
            note_type="free_text",
        ))
        db.add(PlayerNote(
            user_id=u.id, reading_id=rid, session_id=s.id,
            note_content="Palabras clave: comprensión lectora, pensamiento crítico, educación.",
            note_type="annotation",
        ))
        db.add(PlayerNote(
            user_id=u.id, reading_id=rid, session_id=s2.id,
            note_content="Este texto descriptivo utiliza muchos adjetivos calificativos para crear una imagen mental del paisaje. Noté que el autor organiza la descripción de lo general a lo particular.",
            note_type="free_text",
        ))
        add_achievement(db, u.id, "first_reading", "📖 Primera lectura", 5)
        print(f"  📌 {u.display_name}: Con notas (2 sesiones, 3 notas)")

        # ── Usuario 7: Rápido ──
        u = users[6]
        init_typology_progress(db, u, ["Narrativo", "Descriptivo"],
                               {"Narrativo": 290, "Descriptivo": 200})
        s = add_session(db, u.id, rid, "Narrativo", 290, 5, 1, days_ago=4)
        # Override tiempos cortos
        s.reading_time_seconds = 45
        s.total_time_seconds = 120
        s2 = add_session(db, u.id, rid, "Descriptivo", 200, 4, 2, days_ago=1)
        s2.reading_time_seconds = 38
        s2.total_time_seconds = 95
        add_achievement(db, u.id, "first_reading", "📖 Primera lectura", 4)
        print(f"  📌 {u.display_name}: Rápido (tiempos cortos)")

        # ── Usuario 8: Perfeccionista ──
        u = users[7]
        init_typology_progress(db, u, ["Narrativo", "Descriptivo", "Argumentativo"],
                               {"Narrativo": 350, "Descriptivo": 340, "Argumentativo": 330})
        for i, typ in enumerate(["Narrativo", "Descriptivo", "Argumentativo"]):
            s = add_session(db, u.id, rid, typ, 330 + i * 10, 6, 0, perfect=True,
                          tool_bonus=60, days_ago=7 - i * 2)
            add_tools(db, s.id, highlight=True, underline=True, notes=True)
        add_achievement(db, u.id, "first_reading", "📖 Primera lectura", 7)
        add_achievement(db, u.id, "perfectionist", "🎯 Perfeccionista", 5)
        add_achievement(db, u.id, "centurion", "💯 Centurión", 4)
        print(f"  📌 {u.display_name}: Perfeccionista (3 sesiones perfectas)")

        # ── Usuario 9: Luchador ──
        u = users[8]
        init_typology_progress(db, u, ["Narrativo"],
                               {"Narrativo": 270})
        # Múltiples intentos con mejora progresiva
        add_session(db, u.id, rid, "Narrativo", 80, 2, 4, days_ago=10)
        add_session(db, u.id, rid, "Narrativo", 130, 3, 3, days_ago=8)
        add_session(db, u.id, rid, "Narrativo", 190, 4, 2, days_ago=5)
        add_session(db, u.id, rid, "Narrativo", 230, 5, 1, days_ago=3)
        s = add_session(db, u.id, rid, "Narrativo", 270, 5, 1, tool_bonus=20, days_ago=1)
        add_tools(db, s.id, highlight=True)
        add_achievement(db, u.id, "first_reading", "📖 Primera lectura", 10)
        add_achievement(db, u.id, "avid_reader", "📚 Lector ávido", 1)
        add_achievement(db, u.id, "improvement", "📈 En mejora", 3)
        print(f"  📌 {u.display_name}: Luchador (5 sesiones, mejora progresiva)")

        # ── Usuario 10: Admin ──
        u = users[9]
        init_typology_progress(db, u, ["Narrativo"])
        print(f"  📌 {u.display_name}: Administrador (sin progreso de juego)")

        db.commit()
        print("\n✅ Seed completado exitosamente.")
        print(f"   📧 Login de prueba: alumno1@test.com / {PASSWORD}")
        print(f"   🔑 Login admin: admin@test.com / {ADMIN_PASSWORD}")
        print()

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante el seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
