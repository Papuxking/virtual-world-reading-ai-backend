"""
schemas.py — Schemas Pydantic para validación de request/response
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Tipologías válidas ───────────────────────────────────────────────────────

VALID_TYPOLOGIES = [
    "Descriptivo",
    "Narrativo",
    "Argumentativo",
    "Expositivo",
    "Instructivo",
]

VALID_COMPREHENSION_LEVELS = [
    "Literal",
    "Inferencial",
    "Critico",
]


# ── Schemas de Lectura (retrocompatibles) ────────────────────────────────────

class ReadingCreate(BaseModel):
    """Schema para crear una nueva lectura."""
    title: str = Field(..., min_length=1, max_length=255, examples=["Baños de Agua Santa"])
    typology: str = Field(..., examples=["Descriptivo"])
    type: Optional[str] = Field(None, max_length=100, examples=["Texto descriptivo geográfico-cultural"])
    content: str = Field(..., min_length=100, max_length=50000,
                         examples=["Texto de la lectura con al menos 100 caracteres..."])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Mi lectura descriptiva",
                "typology": "Descriptivo",
                "type": "Texto descriptivo",
                "content": "Contenido de la lectura que debe tener al menos cien caracteres para ser aceptado por la validación del sistema de lecturas del mundo virtual."
            }
        }


class ReadingUpdate(BaseModel):
    """Schema para actualizar una lectura (campos opcionales)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    typology: Optional[str] = None
    type: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = Field(None, min_length=100, max_length=50000)


class ReadingResponse(BaseModel):
    """Schema de respuesta para una lectura individual (retrocompatible)."""
    id: int
    title: str
    typology: str
    type: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedReadings(BaseModel):
    """Schema de respuesta paginada para listar lecturas."""
    items: List[ReadingResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ── Schemas de Preguntas y Respuestas ────────────────────────────────────────

class AnswerResponse(BaseModel):
    """Opción de respuesta (A, B, C o D)."""
    letter: str
    answer_text: str

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    """Pregunta de comprensión lectora con sus opciones."""
    id: int
    question_number: int
    comprehension_level: str
    question_text: str
    correct_answer: str
    justification: Optional[str] = None
    answers: List[AnswerResponse]

    class Config:
        from_attributes = True


class ReadingFullResponse(BaseModel):
    """Lectura completa con todas sus preguntas y respuestas (para caché local)."""
    id: int
    title: str
    typology: str
    type: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse]

    class Config:
        from_attributes = True
