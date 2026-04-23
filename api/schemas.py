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


# ── Schemas de Lectura ───────────────────────────────────────────────────────

class ReadingCreate(BaseModel):
    """Schema para crear una nueva lectura."""
    title: str = Field(..., min_length=1, max_length=255, examples=["Baños de Agua Santa"])
    typology: str = Field(..., examples=["Descriptivo"])
    content: str = Field(..., min_length=100, max_length=50000,
                         examples=["Texto de la lectura con al menos 100 caracteres..."])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Mi lectura descriptiva",
                "typology": "Descriptivo",
                "content": "Contenido de la lectura que debe tener al menos cien caracteres para ser aceptado por la validación del sistema de lecturas del mundo virtual."
            }
        }


class ReadingUpdate(BaseModel):
    """Schema para actualizar una lectura (campos opcionales)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    typology: Optional[str] = None
    content: Optional[str] = Field(None, min_length=100, max_length=50000)


class ReadingResponse(BaseModel):
    """Schema de respuesta para una lectura individual."""
    id: int
    title: str
    typology: str
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
