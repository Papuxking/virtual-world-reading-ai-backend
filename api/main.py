"""
main.py — API REST de lecturas para el mundo virtual educativo
Endpoints CRUD con búsqueda full-text, paginación, filtrado por tipología,
sincronización bidireccional con LecturaIA, tutor NPC,
autenticación JWT y gestión de progreso del jugador.
"""
import math
import os
import requests
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc, text

from database import get_db, SessionLocal, engine, Base
from models import Reading, Question, Answer, ActiveReading
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

# Importar routers
from routers.auth_router import router as auth_router
from routers.progress_router import router as progress_router
from routers.admin_router import router as admin_router
from routers.catalog_router import router as catalog_router
from routers.achievements_admin_router import router as achievements_admin_router
from routers.metrics_router import router as metrics_router
from routers.leaderboard_router import router as leaderboard_router

app = FastAPI(
    title="Virtual World Reading API",
    description="API para gestionar lecturas del mundo virtual educativo en Godot, con autenticación y progreso de jugadores",
    version="2.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server (dashboard)
        "http://localhost:5174",   # Vite dev server alternativo
        "http://localhost:3000",   # Alternativo
        "http://localhost:8001",   # Self (API)
        "http://localhost:8080",   # Adminer
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Crear tablas ─────────────────────────────────────────────────────────────

# Crear todas las tablas que no existen (incluye las nuevas de users y progreso)
Base.metadata.create_all(bind=engine)

# Asegurar que el directorio de archivos estáticos existe
from fastapi.staticfiles import StaticFiles
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
medals_dir = os.path.join(static_dir, "medals")
os.makedirs(medals_dir, exist_ok=True)

# Escribir un placeholder.png mínimo si no existe
placeholder_path = os.path.join(medals_dir, "placeholder.png")
if not os.path.exists(placeholder_path):
    import base64
    min_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    with open(placeholder_path, "wb") as f:
        f.write(min_png)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── Montar Routers ───────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(progress_router)
app.include_router(admin_router)
app.include_router(catalog_router)
app.include_router(achievements_admin_router)
app.include_router(metrics_router)
app.include_router(leaderboard_router)

# ── Configuración de sincronización ──────────────────────────────────────────

_SYNC_SECRET = os.getenv("SYNC_SECRET_KEY", "")
_LECTURAIA_URL = os.getenv("LECTURAIA_API_URL", "http://localhost:8000")


def _verify_sync_key(x_sync_key: str = Header(...)):
    if not _SYNC_SECRET or x_sync_key != _SYNC_SECRET:
        raise HTTPException(status_code=403, detail="Clave de sincronización inválida")


class SyncReadingPayload(BaseModel):
    source_id: int
    title: str
    typology: str
    content: str


# ── Push hacia LecturaIA (background tasks) ───────────────────────────────────

def _push_create_to_la(reading_id: int, title: str, typology: str, content: str):
    if not _SYNC_SECRET or not _LECTURAIA_URL:
        return
    try:
        resp = requests.post(
            f"{_LECTURAIA_URL}/sync/reading",
            json={"source_id": reading_id, "title": title, "typology": typology, "content": content},
            headers={"X-Sync-Key": _SYNC_SECRET, "X-Sync-Source": "virtual-world"},
            timeout=10,
        )
        if resp.ok:
            la_id = resp.json().get("id")
            if la_id:
                db = SessionLocal()
                try:
                    r = db.query(Reading).filter(Reading.id == reading_id).first()
                    if r:
                        r.external_id = la_id
                        db.commit()
                finally:
                    db.close()
    except Exception as e:
        print(f"[Sync VW→LA create] {e}")


def _push_update_to_la(la_doc_id: int, reading_id: int, title: str, typology: str, content: str):
    if not _SYNC_SECRET or not _LECTURAIA_URL or not la_doc_id:
        return
    try:
        requests.put(
            f"{_LECTURAIA_URL}/sync/reading/{la_doc_id}",
            json={"source_id": reading_id, "title": title, "typology": typology, "content": content},
            headers={"X-Sync-Key": _SYNC_SECRET, "X-Sync-Source": "virtual-world"},
            timeout=10,
        )
    except Exception as e:
        print(f"[Sync VW→LA update] {e}")


def _push_delete_to_la(la_doc_id: int):
    if not _SYNC_SECRET or not _LECTURAIA_URL or not la_doc_id:
        return
    try:
        requests.delete(
            f"{_LECTURAIA_URL}/sync/reading/{la_doc_id}",
            headers={"X-Sync-Key": _SYNC_SECRET, "X-Sync-Source": "virtual-world"},
            timeout=10,
        )
    except Exception as e:
        print(f"[Sync VW→LA delete] {e}")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}


# ── Sincronización: recibir desde LecturaIA ───────────────────────────────────

@app.post("/sync/reading", status_code=201, tags=["Sincronización"])
def sync_receive_create(
    payload: SyncReadingPayload,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_sync_key),
):
    """Recibe una nueva lectura desde LecturaIA."""
    if payload.typology not in VALID_TYPOLOGIES:
        raise HTTPException(status_code=400, detail=f"Tipología inválida: {payload.typology}")
    existing = db.query(Reading).filter(Reading.external_id == payload.source_id).first()
    if existing:
        return {"id": existing.id, "detail": "ya_existe"}
    reading = Reading(
        title=payload.title,
        typology=payload.typology,
        content=payload.content,
        external_id=payload.source_id,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return {"id": reading.id, "detail": "creado"}


@app.put("/sync/reading/{vw_reading_id}", tags=["Sincronización"])
def sync_receive_update(
    vw_reading_id: int,
    payload: SyncReadingPayload,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_sync_key),
):
    """Recibe una actualización desde LecturaIA."""
    reading = db.query(Reading).filter(Reading.id == vw_reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    reading.title = payload.title
    reading.typology = payload.typology
    reading.content = payload.content
    db.commit()
    return {"id": reading.id, "detail": "actualizado"}


@app.delete("/sync/reading/{vw_reading_id}", tags=["Sincronización"])
def sync_receive_delete(
    vw_reading_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_sync_key),
):
    """Recibe una eliminación desde LecturaIA."""
    reading = db.query(Reading).filter(Reading.id == vw_reading_id).first()
    if reading:
        db.delete(reading)
        db.commit()
    return {"detail": "eliminado"}


# ── Tipologías ────────────────────────────────────────────────────────────────

@app.get("/typologies", tags=["Tipologías"])
def list_typologies(db: Session = Depends(get_db)):
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


# ── Lectura aleatoria COMPLETA (debe ir antes de /readings/{id}) ──────────────

@app.get("/readings/random/full", response_model=ReadingFullResponse, tags=["Lecturas"])
def get_random_reading_full(
    typology: str | None = Query(None, description="Filtrar por tipología"),
    db: Session = Depends(get_db),
):
    if typology and typology not in VALID_TYPOLOGIES:
        raise HTTPException(status_code=400, detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}")
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
    if typology and typology not in VALID_TYPOLOGIES:
        raise HTTPException(status_code=400, detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}")
    query = db.query(Reading)
    if typology:
        query = query.filter(Reading.typology == typology)
    reading = query.order_by(sqlfunc.random()).first()
    if not reading:
        raise HTTPException(status_code=404, detail="No se encontraron lecturas")
    return reading


# ── CRUD de Lecturas ──────────────────────────────────────────────────────────

@app.get("/readings", response_model=PaginatedReadings, tags=["Lecturas"])
def list_readings(
    q: str = Query("", description="Búsqueda full-text en título y contenido"),
    typology: str | None = Query(None, description="Filtrar por tipología exacta"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    db: Session = Depends(get_db),
):
    query = db.query(Reading)
    if typology:
        if typology not in VALID_TYPOLOGIES:
            raise HTTPException(status_code=400, detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}")
        query = query.filter(Reading.typology == typology)
    if q:
        ts_query = sqlfunc.plainto_tsquery("spanish", q)
        ts_vector = sqlfunc.to_tsvector("spanish", Reading.title).concat(
            sqlfunc.to_tsvector("spanish", Reading.content)
        )
        query = query.filter(ts_vector.match(ts_query))
    total = query.count()
    allowed_sort = {"title": Reading.title, "typology": Reading.typology, "created_at": Reading.created_at}
    sort_column = allowed_sort.get(sort, Reading.created_at)
    query = query.order_by(sort_column.asc() if order == "asc" else sort_column.desc())
    pages = max(1, math.ceil(total / per_page))
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return PaginatedReadings(items=items, total=total, page=page, per_page=per_page, pages=pages)


@app.get("/readings/{reading_id}/full", response_model=ReadingFullResponse, tags=["Lecturas"])
def get_reading_full(reading_id: int, db: Session = Depends(get_db)):
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
    level: str | None = Query(None),
    db: Session = Depends(get_db),
):
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    if level and level not in VALID_COMPREHENSION_LEVELS:
        raise HTTPException(status_code=400, detail=f"Nivel inválido. Opciones: {VALID_COMPREHENSION_LEVELS}")
    query = (
        db.query(Question)
        .options(joinedload(Question.answers))
        .filter(Question.reading_id == reading_id)
    )
    if level:
        query = query.filter(Question.comprehension_level == level)
    return query.order_by(Question.question_number).all()


@app.get("/readings/{reading_id}", response_model=ReadingResponse, tags=["Lecturas"])
def get_reading(reading_id: int, db: Session = Depends(get_db)):
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    return reading


@app.post("/readings", response_model=ReadingResponse, status_code=201, tags=["Lecturas"])
def create_reading(
    data: ReadingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if data.typology not in VALID_TYPOLOGIES:
        raise HTTPException(status_code=400, detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}")
    reading = Reading(title=data.title, typology=data.typology, type=data.type, content=data.content)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    background_tasks.add_task(_push_create_to_la, reading.id, reading.title, reading.typology, reading.content)
    return reading


@app.put("/readings/{reading_id}", response_model=ReadingResponse, tags=["Lecturas"])
def update_reading(
    reading_id: int,
    data: ReadingUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    if data.typology and data.typology not in VALID_TYPOLOGIES:
        raise HTTPException(status_code=400, detail=f"Tipología inválida. Opciones: {VALID_TYPOLOGIES}")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(reading, key, value)
    db.commit()
    db.refresh(reading)
    if reading.external_id:
        background_tasks.add_task(
            _push_update_to_la,
            reading.external_id,
            reading.id,
            reading.title,
            reading.typology,
            reading.content,
        )
    return reading


@app.delete("/readings/{reading_id}", tags=["Lecturas"])
def delete_reading(
    reading_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    la_doc_id = reading.external_id
    db.delete(reading)
    db.commit()
    if la_doc_id:
        background_tasks.add_task(_push_delete_to_la, la_doc_id)
    return {"detail": "Lectura eliminada", "id": reading_id}


# ── TODO: Activar no-repetición por usuario ──────────────────────────────────
#   POST /users/{user_id}/readings/{reading_id}/mark-read
#   GET  /users/{user_id}/readings/next?typology=...
