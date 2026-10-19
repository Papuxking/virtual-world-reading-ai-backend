"""Fábricas de datos para los tests. Todo se crea directamente en la base."""
from auth import create_access_token, hash_password
from game_rules import DIFFICULTY_ORDER
from models import Answer, PlayerSlot, PlayerTypologyProgress, Question, Reading, User, Workspace

NIVELES_DE_PRUEBA = ["Literal", "Literal", "Inferencial", "Inferencial", "Critico", "Critico"]


def crear_entorno(db, nombre, color="#059669", activo=False):
    """Crea un entorno de trabajo."""
    entorno = Workspace(name=nombre, color=color, is_active=activo)
    db.add(entorno)
    db.commit()
    return entorno


def crear_usuario(db, email="alumno@test.com", admin=False, filas=True, entorno=None):
    """Crea un usuario. Si no es admin, con su slot 1 activo y, si filas=True,
    con las filas de progreso de las 4 tipologías (solo Narrativo abierta).
    Con entorno, la cuenta es de ese entorno."""
    usuario = User(
        email=email,
        hashed_password=hash_password("Test1234!"),
        display_name=email.split("@")[0],
        character="male",
        is_admin=admin,
        workspace_id=entorno.id if entorno else None,
    )
    db.add(usuario)
    db.flush()
    slot = None
    if not admin:
        slot = PlayerSlot(user_id=usuario.id, slot_number=1, label="Sesión 1", is_active=True)
        db.add(slot)
        db.flush()
        if filas:
            for i, tipologia in enumerate(DIFFICULTY_ORDER):
                db.add(PlayerTypologyProgress(
                    user_id=usuario.id, slot_id=slot.id, typology=tipologia, is_unlocked=(i == 0),
                ))
    db.commit()
    return usuario, slot


def cabeceras(usuario):
    token = create_access_token(usuario.id, usuario.email, usuario.is_admin)
    return {"Authorization": f"Bearer {token}"}


def crear_lectura(db, titulo="Lectura", tipologia="Narrativo"):
    """Lectura con 6 preguntas (2 por nivel); la correcta es siempre la A."""
    lectura = Reading(title=titulo, typology=tipologia, content="Texto " * 40)
    db.add(lectura)
    db.flush()
    for numero, nivel in enumerate(NIVELES_DE_PRUEBA, start=1):
        pregunta = Question(
            reading_id=lectura.id, question_number=numero, comprehension_level=nivel,
            question_text=f"Pregunta {numero}", correct_answer="A", justification="Porque sí.",
        )
        db.add(pregunta)
        db.flush()
        for letra in "ABCD":
            db.add(Answer(question_id=pregunta.id, letter=letra, answer_text=f"Opción {letra}"))
    db.commit()
    return lectura


def payload_sesion(db, lectura, tipologia=None, puntaje=200, correctas=6):
    """Cuerpo de POST /progress/sessions tal como lo manda el juego."""
    preguntas = (
        db.query(Question)
        .filter(Question.reading_id == lectura.id)
        .order_by(Question.question_number)
        .all()
    )
    respuestas = []
    for i, pregunta in enumerate(preguntas):
        acierta = i < correctas
        respuestas.append({
            "question_id": pregunta.id,
            "comprehension_level": pregunta.comprehension_level,
            "selected_answer": "A" if acierta else "B",
            "correct_answer": "A",
            "is_correct": acierta,
            "points_earned": 10 if acierta else 0,
            "penalty_applied": 0 if acierta else 3,
        })
    datos = {
        "reading_id": lectura.id,
        "typology": tipologia or lectura.typology,
        "session_score": puntaje,
        "reading_time_seconds": 120,
        "total_time_seconds": 300,
        "is_perfect": correctas >= len(preguntas),
        "correct_count": min(correctas, len(preguntas)),
        "incorrect_count": max(0, len(preguntas) - correctas),
        "tool_bonus": 20,
        "answers": respuestas,
        "tools": [
            {"tool_name": "highlight", "was_used": True, "usage_count": 1},
            {"tool_name": "underline", "was_used": False, "usage_count": 0},
            {"tool_name": "notes", "was_used": False, "usage_count": 0},
        ],
    }
    return datos


def lectura_json(titulo, tipologia):
    """Lectura en el formato de los JSON de corpus (con la errata 'activites'):
    unos 2.800 caracteres, 4 preguntas por nivel y respuestas correctas
    repartidas entre A, B, C y D."""
    parrafo = ("Texto de prueba para una lectura del corpus. " * 10).strip()
    niveles = ["Literal"] * 4 + ["Inferencial"] * 4 + ["Critico"] * 4
    letras = "ABCD" * 3
    return {
        "title": titulo,
        "typology": tipologia,
        "type": "texto de prueba",
        "text": [parrafo] * 6,
        "activites": [
            {
                "question_id": str(i + 1),
                "comprehension_level": nivel,
                "question": f"Pregunta {i + 1}",
                "answers": [f"{letra}) Opción {letra}" for letra in "ABCD"],
                "correct_answer": letras[i],
                "justification": "Porque sí.",
            }
            for i, nivel in enumerate(niveles)
        ],
    }
