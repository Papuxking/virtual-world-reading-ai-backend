"""
main.py — API REST de lecturas para el mundo virtual educativo
Endpoints CRUD con búsqueda full-text, paginación, filtrado por tipología,
y consulta de preguntas/respuestas por nivel de comprensión.
"""
import math
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc, text

from database import get_db
from models import Reading, Question, Answer
from schemas import (
    ReadingCreate,
    ReadingUpdate,
    ReadingResponse,
    ReadingFullResponse,
    QuestionResponse,
    PaginatedReadings,
    VALID_TYPOLOGIES,
    VALID_COMPREHENSION_LEVELS,
)

app = FastAPI(
    title="Virtual World Reading API",
    description="API para gestionar lecturas del mundo virtual educativo en Godot",
    version="1.1.0",
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
def health_check(db: Session = Depends(get_db)):
    """Verifica el estado de la API y la conexión a la base de datos."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}


# ── Tipologías ───────────────────────────────────────────────────────────────

@app.get("/typologies", tags=["Tipologías"])
def list_typologies(db: Session = Depends(get_db)):
    """Lista las tipologías disponibles con el conteo de lecturas de cada una."""
    counts = (
        db.query(Reading.typology, sqlfunc.count(Reading.id))
        .group_by(Reading.typology)
        .all()
    )
    count_map = {t: c for t, c in counts}
    return {
        "typologies": [
            {"name": t, "count": count_map.get(t, 0)}
            for t in VALID_TYPOLOGIES
        ]
    }


# ── Lectura aleatoria COMPLETA (DEBE ir antes de /readings/{id}) ────────────

@app.get("/readings/random/full", response_model=ReadingFullResponse, tags=["Lecturas"])
def get_random_reading_full(
    typology: str | None = Query(None, description="Filtrar por tipología"),
    db: Session = Depends(get_db),
):
    """
    Retorna una lectura aleatoria **con todas sus preguntas y respuestas**.
    Ideal para caché local en el cliente Godot.
    """
    if typology and typology not in VALID_TYPOLOGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}",
        )
    query = (
        db.query(Reading)
        .options(
            joinedload(Reading.questions).joinedload(Question.answers)
        )
    )
    if typology:
        query = query.filter(Reading.typology == typology)
    # random() con eager loading requiere subquery para evitar duplicados
    reading_ids = db.query(Reading.id)
    if typology:
        reading_ids = reading_ids.filter(Reading.typology == typology)
    random_id_row = reading_ids.order_by(sqlfunc.random()).first()
    if not random_id_row:
        raise HTTPException(status_code=404, detail="No se encontraron lecturas")
    reading = (
        db.query(Reading)
        .options(joinedload(Reading.questions).joinedload(Question.answers))
        .filter(Reading.id == random_id_row[0])
        .first()
    )
    return reading


@app.get("/readings/random", response_model=ReadingResponse, tags=["Lecturas"])
def get_random_reading(
    typology: str | None = Query(None, description="Filtrar por tipología"),
    db: Session = Depends(get_db),
):
    """Retorna una lectura aleatoria (sin preguntas), opcionalmente filtrada por tipología."""
    if typology and typology not in VALID_TYPOLOGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}",
        )
    query = db.query(Reading)
    if typology:
        query = query.filter(Reading.typology == typology)
    reading = query.order_by(sqlfunc.random()).first()
    if not reading:
        raise HTTPException(status_code=404, detail="No se encontraron lecturas")
    return reading


# ── CRUD de Lecturas ─────────────────────────────────────────────────────────

@app.get("/readings", response_model=PaginatedReadings, tags=["Lecturas"])
def list_readings(
    q: str = Query("", description="Búsqueda full-text en título y contenido"),
    typology: str | None = Query(None, description="Filtrar por tipología exacta"),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=50, description="Elementos por página"),
    sort: str = Query("created_at", description="Campo de ordenamiento"),
    order: str = Query("desc", description="Dirección: asc o desc"),
    db: Session = Depends(get_db),
):
    """
    Lista lecturas con paginación, búsqueda full-text y filtrado.

    - **q**: búsqueda en español sobre título y contenido
    - **typology**: Descriptivo, Narrativo, Argumentativo, Expositivo, Instructivo
    - **sort**: title, typology, created_at
    - **order**: asc, desc
    """
    query = db.query(Reading)

    # Filtro por tipología
    if typology:
        if typology not in VALID_TYPOLOGIES:
            raise HTTPException(
                status_code=400,
                detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}",
            )
        query = query.filter(Reading.typology == typology)

    # Búsqueda full-text en español
    if q:
        ts_query = sqlfunc.plainto_tsquery("spanish", q)
        ts_vector = sqlfunc.to_tsvector("spanish", Reading.title).concat(
            sqlfunc.to_tsvector("spanish", Reading.content)
        )
        query = query.filter(ts_vector.match(ts_query))

    # Conteo total
    total = query.count()

    # Ordenamiento
    allowed_sort = {"title": Reading.title, "typology": Reading.typology, "created_at": Reading.created_at}
    sort_column = allowed_sort.get(sort, Reading.created_at)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Paginación
    pages = max(1, math.ceil(total / per_page))
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    return PaginatedReadings(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ── Lectura completa con preguntas ───────────────────────────────────────────

@app.get("/readings/{reading_id}/full", response_model=ReadingFullResponse, tags=["Lecturas"])
def get_reading_full(reading_id: int, db: Session = Depends(get_db)):
    """
    Obtiene una lectura con todas sus preguntas y respuestas.
    Incluye correct_answer y justification para validación en caché local.
    """
    reading = (
        db.query(Reading)
        .options(joinedload(Reading.questions).joinedload(Question.answers))
        .filter(Reading.id == reading_id)
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    return reading


@app.get("/readings/{reading_id}/questions", response_model=List[QuestionResponse], tags=["Preguntas"])
def get_reading_questions(
    reading_id: int,
    level: str | None = Query(None, description="Filtrar por nivel: Literal, Inferencial, Critico"),
    db: Session = Depends(get_db),
):
    """
    Obtiene las preguntas de una lectura, opcionalmente filtradas por nivel de comprensión.
    """
    # Verificar que la lectura exista
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")

    if level and level not in VALID_COMPREHENSION_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Nivel inválido. Opciones: {VALID_COMPREHENSION_LEVELS}",
        )

    query = (
        db.query(Question)
        .options(joinedload(Question.answers))
        .filter(Question.reading_id == reading_id)
    )
    if level:
        query = query.filter(Question.comprehension_level == level)

    questions = query.order_by(Question.question_number).all()
    return questions


# ── Lectura por ID (sin preguntas — retrocompatible) ─────────────────────────

@app.get("/readings/{reading_id}", response_model=ReadingResponse, tags=["Lecturas"])
def get_reading(reading_id: int, db: Session = Depends(get_db)):
    """Obtiene una lectura por su ID (sin preguntas)."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    return reading


@app.post("/readings", response_model=ReadingResponse, status_code=201, tags=["Lecturas"])
def create_reading(data: ReadingCreate, db: Session = Depends(get_db)):
    """Crea una nueva lectura."""
    if data.typology not in VALID_TYPOLOGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}",
        )
    reading = Reading(
        title=data.title,
        typology=data.typology,
        type=data.type,
        content=data.content,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@app.put("/readings/{reading_id}", response_model=ReadingResponse, tags=["Lecturas"])
def update_reading(reading_id: int, data: ReadingUpdate, db: Session = Depends(get_db)):
    """Actualiza una lectura existente."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    if data.typology and data.typology not in VALID_TYPOLOGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}",
        )
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reading, key, value)
    db.commit()
    db.refresh(reading)
    return reading


@app.delete("/readings/{reading_id}", tags=["Lecturas"])
def delete_reading(reading_id: int, db: Session = Depends(get_db)):
    """Elimina una lectura por su ID (CASCADE elimina preguntas y respuestas)."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    db.delete(reading)
    db.commit()
    return {"detail": "Lectura eliminada", "id": reading_id}


# ── TODO: Activar no-repetición por usuario ──────────────────────────────────
# Endpoints futuros:
#   POST /users/{user_id}/readings/{reading_id}/mark-read
#   GET  /users/{user_id}/readings/next?typology=...
# Ver tabla user_readings en 001_schema.sql