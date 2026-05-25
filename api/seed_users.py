"""
seed_users.py — Crea 10 usuarios de prueba con datos de progreso variados y catálogo de logros.
Ejecutar después de iniciar la base de datos:
    python seed_users.py
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
    PlayerSlot, AchievementCatalog,
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

# Catálogo global de logros iniciales
INITIAL_ACHIEVEMENTS = [
    {
        "id": "first_reading",
        "name": "📖 Primera lectura",
        "description": "Has completado tu primera sesión de lectura.",
        "how_to_unlock": "Completar al menos 1 sesión de lectura en cualquier tipología.",
        "category": "progreso",
        "icon": "📖",
        "medal_name": "Lector Novato",
        "medal_tier": "bronce",
        "medal_description": "Tu primer paso en el mundo de la lectura.",
        "display_order": 1,
    },
    {
        "id": "improvement",
        "name": "📈 En mejora",
        "description": "Has demostrado una mejora constante en tus intentos.",
        "how_to_unlock": "Completar al menos 3 sesiones de lectura mostrando un aumento progresivo de puntaje.",
        "category": "superación",
        "icon": "📈",
        "medal_name": "Crecimiento Firme",
        "medal_tier": "bronce",
        "medal_description": "El esfuerzo continuo rinde frutos.",
        "display_order": 2,
    },
    {
        "id": "explorer",
        "name": "🏅 Explorador",
        "description": "Has explorado todas las tipologías textuales del juego.",
        "how_to_unlock": "Completar al menos 1 sesión en cada una de las 5 tipologías textuales.",
        "category": "exploración",
        "icon": "🏅",
        "medal_name": "Explorador Intrépido",
        "medal_tier": "plata",
        "medal_description": "Dominas los viajes a través de todos los estilos textuales.",
        "display_order": 3,
    },
    {
        "id": "avid_reader",
        "name": "📚 Lector ávido",
        "description": "Has completado muchas sesiones de lectura.",
        "how_to_unlock": "Completar un total de 5 sesiones de lectura en cualquier combinación de tipologías.",
        "category": "progreso",
        "icon": "📚",
        "medal_name": "Devorador de Páginas",
        "medal_tier": "plata",
        "medal_description": "La lectura es tu hábito favorito.",
        "display_order": 4,
    },
    {
        "id": "star_literal",
        "name": "⭐ Estrella literal",
        "description": "Tienes una precisión perfecta en preguntas de nivel literal.",
        "how_to_unlock": "Obtener 100% de precisión en preguntas literales en al menos 3 sesiones.",
        "category": "maestría",
        "icon": "⭐",
        "medal_name": "Ojo de Halcón",
        "medal_tier": "plata",
        "medal_description": "No se te escapa ningún detalle explícito del texto.",
        "display_order": 5,
    },
    {
        "id": "perfectionist",
        "name": "🎯 Perfeccionista",
        "description": "Has completado sesiones de lectura con puntajes perfectos.",
        "how_to_unlock": "Responder correctamente todas las preguntas en al menos 3 sesiones de lectura.",
        "category": "maestría",
        "icon": "🎯",
        "medal_name": "Lector Impecable",
        "medal_tier": "oro",
        "medal_description": "Precisión absoluta en la comprensión de textos.",
        "display_order": 6,
    },
    {
        "id": "star_inferencial",
        "name": "🌟 Estrella inferencial",
        "description": "Dominas la lectura entre líneas y deducciones complejas.",
        "how_to_unlock": "Responder correctamente todas las preguntas inferenciales en al menos 3 sesiones.",
        "category": "maestría",
        "icon": "🌟",
        "medal_name": "Sabueso Deductivo",
        "medal_tier": "oro",
        "medal_description": "Descifras el significado oculto del autor con facilidad.",
        "display_order": 7,
    },
    {
        "id": "centurion",
        "name": "💯 Centurión",
        "description": "Has acumulado una gran puntuación en tipologías específicas.",
        "how_to_unlock": "Superar los 300 puntos en la puntuación máxima de cualquier tipología.",
        "category": "progreso",
        "icon": "💯",
        "medal_name": "Guerrero Intelectual",
        "medal_tier": "oro",
        "medal_description": "Has roto la barrera de los 300 puntos de maestría.",
        "display_order": 8,
    },
    {
        "id": "star_critico",
        "name": "💎 Estrella crítica",
        "description": "Excelente capacidad para valorar y juzgar intenciones del autor.",
        "how_to_unlock": "Obtener 100% de precisión en preguntas de nivel crítico en al menos 3 sesiones.",
        "category": "maestría",
        "icon": "💎",
        "medal_name": "Pensador Analítico",
        "medal_tier": "platino",
        "medal_description": "Ningún sesgo ni intención oculta pasa desapercibido ante tu criterio.",
        "display_order": 9,
    },
    {
        "id": "half_millennium",
        "name": "🏆 Medio milenio",
        "description": "Has acumulado una impresionante puntuación en tus mejores tipologías.",
        "how_to_unlock": "Superar los 500 puntos totales combinados de mejores puntuaciones.",
        "category": "progreso",
        "icon": "🏆",
        "medal_name": "Sabio del Reino",
        "medal_tier": "platino",
        "medal_description": "Una leyenda de la comprensión lectora en el mundo virtual.",
        "display_order": 10,
    },
]


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


def create_player_slots(db, user):
    """Crea el slot 1 activo para un jugador."""
    if user.is_admin:
        return None
    
    existing = db.query(PlayerSlot).filter(PlayerSlot.user_id == user.id, PlayerSlot.slot_number == 1).first()
    if existing:
        return existing
        
    slot = PlayerSlot(
        user_id=user.id,
        slot_number=1,
        label="Sesión 1",
        is_active=True
    )
    db.add(slot)
    db.flush()
    return slot


def seed_achievements_catalog(db):
    """Pobla el catálogo global de logros."""
    print("🌱 Población de catálogo global de logros...")
    for item in INITIAL_ACHIEVEMENTS:
        existing = db.query(AchievementCatalog).filter(AchievementCatalog.id == item["id"]).first()
        if existing:
            # Actualizar campos existentes
            for key, val in item.items():
                setattr(existing, key, val)
        else:
            catalog_item = AchievementCatalog(**item)
            db.add(catalog_item)
    db.commit()
    print("  ✅ Catálogo global guardado con éxito.")


def init_typology_progress(db, user, slot, unlocked_list, scores=None):
    """Inicializa progreso de tipologías para un usuario en un slot específico."""
    scores = scores or {}
    for typology in DIFFICULTY_ORDER:
        existing = (
            db.query(PlayerTypologyProgress)
            .filter(
                PlayerTypologyProgress.user_id == user.id,
                PlayerTypologyProgress.slot_id == slot.id,
                PlayerTypologyProgress.typology == typology
            )
            .first()
        )
        if existing:
            continue

        best = scores.get(typology, 0)
        total_s = 1 if best > 0 else 0
        p = PlayerTypologyProgress(
            user_id=user.id,
            slot_id=slot.id,
            typology=typology,
            best_score=best,
            total_sessions=total_s,
            is_unlocked=(typology in unlocked_list),
            first_completed_at=datetime.now(timezone.utc) - timedelta(days=5) if best > 0 else None,
            last_played_at=datetime.now(timezone.utc) - timedelta(days=1) if best > 0 else None,
        )
        db.add(p)


def add_session(db, user_id, slot_id, reading_id, typology, score, correct, incorrect, perfect=False, tool_bonus=0, days_ago=1):
    """Agrega una sesión de juego en un slot específico."""
    session = PlayerSession(
        user_id=user_id,
        slot_id=slot_id,
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


def add_achievement(db, user_id, slot_id, aid, aname, days_ago=5):
    """Agrega un logro desbloqueado en un slot específico."""
    existing = (
        db.query(PlayerAchievement)
        .filter(
            PlayerAchievement.user_id == user_id,
            PlayerAchievement.slot_id == slot_id,
            PlayerAchievement.achievement_id == aid
        )
        .first()
    )
    if existing:
        return
    db.add(PlayerAchievement(
        user_id=user_id,
        slot_id=slot_id,
        achievement_id=aid,
        achievement_name=aname,
        unlocked_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    ))


def seed():
    """Ejecuta el seed completo."""
    db = SessionLocal()
    try:
        print("\n🌱 Iniciando seed de base de datos completa...\n")

        # 1. Poblar catálogo de logros
        seed_achievements_catalog(db)

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

        print("\n📊 Configurando slots y progreso de prueba...\n")

        # Crear slots 1 para todos los no-admins
        slots_map = {}
        for user in users:
            if not user.is_admin:
                slot1 = create_player_slots(db, user)
                slots_map[user.id] = slot1
        db.commit()

        # ── Usuario 1: Principiante ──
        u = users[0]
        s1 = slots_map[u.id]
        init_typology_progress(db, u, s1, ["Narrativo"], {"Narrativo": 120})
        s = add_session(db, u.id, s1.id, rid, "Narrativo", 120, 3, 3, days_ago=7)
        add_tools(db, s.id, highlight=True)
        add_achievement(db, u.id, s1.id, "first_reading", "📖 Primera lectura", 7)
        print(f"  📌 {u.display_name}: Principiante (Slot 1, 1 sesión)")

        # ── Usuario 2: Intermedia ──
        u = users[1]
        s1 = slots_map[u.id]
        init_typology_progress(db, u, s1, ["Narrativo", "Descriptivo"],
                               {"Narrativo": 280, "Descriptivo": 210})
        add_session(db, u.id, s1.id, rid, "Narrativo", 280, 5, 1, days_ago=8)
        add_session(db, u.id, s1.id, rid, "Narrativo", 250, 4, 2, days_ago=6)
        s = add_session(db, u.id, s1.id, rid, "Descriptivo", 210, 4, 2, tool_bonus=40, days_ago=3)
        add_tools(db, s.id, highlight=True, underline=True)
        add_achievement(db, u.id, s1.id, "first_reading", "📖 Primera lectura", 8)
        print(f"  📌 {u.display_name}: Intermedia (Slot 1, 3 sesiones)")

        # ── Usuario 3: Avanzado ──
        u = users[2]
        s1 = slots_map[u.id]
        init_typology_progress(db, u, s1, ["Narrativo", "Descriptivo", "Argumentativo"],
                               {"Narrativo": 310, "Descriptivo": 275, "Argumentativo": 180})
        add_session(db, u.id, s1.id, rid, "Narrativo", 310, 5, 1, days_ago=9)
        add_session(db, u.id, s1.id, rid, "Descriptivo", 275, 5, 1, days_ago=6)
        s = add_session(db, u.id, s1.id, rid, "Argumentativo", 180, 4, 2, tool_bonus=40, days_ago=2)
        add_tools(db, s.id, highlight=True, underline=True)
        add_achievement(db, u.id, s1.id, "first_reading", "📖 Primera lectura", 9)
        add_achievement(db, u.id, s1.id, "centurion", "💯 Centurión", 6)
        add_achievement(db, u.id, s1.id, "improvement", "📈 En mejora", 3)
        print(f"  📌 {u.display_name}: Avanzado (Slot 1, 3 sesiones, 3 logros)")

        # ── Usuario 4: Experta ──
        u = users[3]
        s1 = slots_map[u.id]
        # Slot 1: Completado al máximo
        init_typology_progress(db, u, s1, DIFFICULTY_ORDER,
                               {"Narrativo": 350, "Descriptivo": 320, "Argumentativo": 290,
                                "Instructivo": 310, "Expositivo": 280})
        for i, typ in enumerate(DIFFICULTY_ORDER):
            s = add_session(db, u.id, s1.id, rid, typ, 280 + i * 20, 6, 0, perfect=True,
                          tool_bonus=60, days_ago=10 - i * 2)
            add_tools(db, s.id, highlight=True, underline=True, notes=True)
        add_achievement(db, u.id, s1.id, "first_reading", "📖 Primera lectura", 10)
        add_achievement(db, u.id, s1.id, "explorer", "🏅 Explorador", 4)
        add_achievement(db, u.id, s1.id, "perfectionist", "🎯 Perfeccionista", 8)
        add_achievement(db, u.id, s1.id, "centurion", "💯 Centurión", 7)
        add_achievement(db, u.id, s1.id, "half_millennium", "🏆 Medio milenio", 2)
        add_achievement(db, u.id, s1.id, "star_literal", "⭐ Estrella literal", 5)
        
        # CREAR SLOT 2 INACTIVO con progreso intermedio para demostrar multi-slot
        slot2 = PlayerSlot(
            user_id=u.id,
            slot_number=2,
            label="Intento 2",
            is_active=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        db.add(slot2)
        db.flush()
        
        init_typology_progress(db, u, slot2, ["Narrativo", "Descriptivo"],
                               {"Narrativo": 240, "Descriptivo": 0})
        s_s2 = add_session(db, u.id, slot2.id, rid, "Narrativo", 240, 4, 2, days_ago=1)
        add_tools(db, s_s2.id, highlight=True)
        add_achievement(db, u.id, slot2.id, "first_reading", "📖 Primera lectura", 1)
        
        print(f"  📌 {u.display_name}: Experta (Slot 1 completo + Slot 2 inactivo con progreso intermedio)")

        # ── Usuario 5: Nuevo (sin progreso) ──
        u = users[4]
        s1 = slots_map[u.id]
        init_typology_progress(db, u, s1, ["Narrativo"])
        print(f"  📌 {u.display_name}: Sin progreso")

        # ── Usuario 6: Con Notas ──
        u = users[5]
        s1 = slots_map[u.id]
        init_typology_progress(db, u, s1, ["Narrativo", "Descriptivo"],
                               {"Narrativo": 260, "Descriptivo": 230})
        s = add_session(db, u.id, s1.id, rid, "Narrativo", 260, 5, 1, tool_bonus=60, days_ago=5)
        add_tools(db, s.id, highlight=True, underline=True, notes=True)
        s2 = add_session(db, u.id, s1.id, rid, "Descriptivo", 230, 4, 2, tool_bonus=60, days_ago=2)
        add_tools(db, s2.id, highlight=True, underline=True, notes=True)
        # Agregar notas reales
        db.add(PlayerNote(
            user_id=u.id, slot_id=s1.id, reading_id=rid, session_id=s.id,
            note_content="La idea principal del texto es que la lectura comprensiva mejora el pensamiento crítico. El autor usa ejemplos de estudios científicos para respaldar su argumento.",
            note_type="free_text",
        ))
        db.add(PlayerNote(
            user_id=u.id, slot_id=s1.id, reading_id=rid, session_id=s.id,
            note_content="Palabras clave: comprensión lectora, pensamiento crítico, educación.",
            note_type="annotation",
        ))
        db.add(PlayerNote(
            user_id=u.id, slot_id=s1.id, reading_id=rid, session_id=s2.id,
            note_content="Este texto descriptivo utiliza muchos adjetivos calificativos para crear una imagen mental del paisaje. Noté que el autor organiza la descripción de lo general a lo particular.",
            note_type="free_text",
        ))
        add_achievement(db, u.id, s1.id, "first_reading", "📖 Primera lectura", 5)
        print(f"  📌 {u.display_name}: Con notas (Slot 1, 2 sesiones, 3 notas)")

        # ── Usuario 7: Rápido ──
        u = users[6]
        s1 = slots_map[u.id]
        init_typology_progress(db, u, s1, ["Narrativo", "Descriptivo"],
                               {"Narrativo": 290, "Descriptivo": 200})
        s = add_session(db, u.id, s1.id, rid, "Narrativo", 290, 5, 1, days_ago=4)
        # Override tiempos cortos
        s.reading_time_seconds = 45
        s.total_time_seconds = 120
        s2 = add_session(db, u.id, s1.id, rid, "Descriptivo", 200, 4, 2, days_ago=1)
        s2.reading_time_seconds = 38
        s2.total_time_seconds = 95
        add_achievement(db, u.id, s1.id, "first_reading", "📖 Primera lectura", 4)
        print(f"  📌 {u.display_name}: Rápido (Slot 1, tiempos cortos)")

        # ── Usuario 8: Perfeccionista ──
        u = users[7]
        s1 = slots_map[u.id]
        init_typology_progress(db, u, s1, ["Narrativo", "Descriptivo", "Argumentativo"],
                               {"Narrativo": 350, "Descriptivo": 340, "Argumentativo": 330})
        for i, typ in enumerate(["Narrativo", "Descriptivo", "Argumentativo"]):
            s = add_session(db, u.id, s1.id, rid, typ, 330 + i * 10, 6, 0, perfect=True,
                          tool_bonus=60, days_ago=7 - i * 2)
            add_tools(db, s.id, highlight=True, underline=True, notes=True)
        add_achievement(db, u.id, s1.id, "first_reading", "📖 Primera lectura", 7)
        add_achievement(db, u.id, s1.id, "perfectionist", "🎯 Perfeccionista", 5)
        add_achievement(db, u.id, s1.id, "centurion", "💯 Centurión", 4)
        print(f"  📌 {u.display_name}: Perfeccionista (Slot 1, 3 sesiones perfectas)")

        # ── Usuario 9: Luchador ──
        u = users[8]
        s1 = slots_map[u.id]
        init_typology_progress(db, u, s1, ["Narrativo"],
                               {"Narrativo": 270})
        # Múltiples intentos con mejora progresiva
        add_session(db, u.id, s1.id, rid, "Narrativo", 80, 2, 4, days_ago=10)
        add_session(db, u.id, s1.id, rid, "Narrativo", 130, 3, 3, days_ago=8)
        add_session(db, u.id, s1.id, rid, "Narrativo", 190, 4, 2, days_ago=5)
        add_session(db, u.id, s1.id, rid, "Narrativo", 230, 5, 1, days_ago=3)
        s = add_session(db, u.id, s1.id, rid, "Narrativo", 270, 5, 1, tool_bonus=20, days_ago=1)
        add_tools(db, s.id, highlight=True)
        add_achievement(db, u.id, s1.id, "first_reading", "📖 Primera lectura", 10)
        add_achievement(db, u.id, s1.id, "avid_reader", "📚 Lector ávido", 1)
        add_achievement(db, u.id, s1.id, "improvement", "📈 En mejora", 3)
        print(f"  📌 {u.display_name}: Luchador (Slot 1, 5 sesiones, mejora progresiva)")

        # ── Usuario 10: Admin ──
        u = users[9]
        # No tiene progreso ni slots ya que es un admin
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
