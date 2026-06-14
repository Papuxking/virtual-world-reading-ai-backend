"""
schemas.py — Schemas Pydantic para validación de request/response
Incluye schemas de lecturas, autenticación, progreso y administración.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


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

# Orden de dificultad para la progresión
DIFFICULTY_ORDER = [
    "Narrativo", "Descriptivo", "Argumentativo", "Instructivo", "Expositivo"
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


# ── Schemas de Autenticación ─────────────────────────────────────────────────

class UserRegister(BaseModel):
    """Schema para registrar un nuevo usuario."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=100)
    character: str = Field(default="male")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "alumno1@test.com",
                "password": "Test1234!",
                "display_name": "Alumno 1",
                "character": "male",
            }
        }


class UserLogin(BaseModel):
    """Schema para iniciar sesión."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Schema de respuesta con datos del usuario (sin contraseña)."""
    id: int
    email: str
    display_name: str
    character: str
    is_active: bool
    is_admin: bool
    must_change_password: bool = False
    session_version: int = 1
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema de respuesta tras login exitoso."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    must_change_password: bool = False


# ── Schemas de Gestión de Slots y Catálogos ───────────────────────────────────

class PlayerSlotResponse(BaseModel):
    """Schema de respuesta para un slot de jugador."""
    id: int
    user_id: int
    slot_number: int
    label: str
    is_active: bool
    created_at: datetime
    created_by: Optional[int] = None
    total_score: int = 0
    total_sessions: int = 0
    total_achievements: int = 0
    last_played_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlayerSlotCreate(BaseModel):
    """Schema para crear un nuevo slot de jugador."""
    label: str = Field(..., min_length=1, max_length=50, examples=["Intento 2"])


class ChangePasswordRequest(BaseModel):
    """Schema para cambiar la contraseña del jugador."""
    new_password: str = Field(..., min_length=8, max_length=128)


class AchievementCatalogResponse(BaseModel):
    """Schema de respuesta para un logro del catálogo global."""
    id: str
    name: str
    description: str
    how_to_unlock: str
    category: str
    icon: str
    medal_name: str
    medal_tier: str
    medal_description: Optional[str] = None
    medal_image_path: Optional[str] = None
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


class AchievementCatalogUpdate(BaseModel):
    """Schema para actualizar un logro del catálogo."""
    name: Optional[str] = None
    description: Optional[str] = None
    how_to_unlock: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    medal_name: Optional[str] = None
    medal_tier: Optional[str] = None
    medal_description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


# ── Schemas de Progreso del Jugador ──────────────────────────────────────────

class PlayerAnswerCreate(BaseModel):
    """Schema para registrar una respuesta individual."""
    question_id: int
    comprehension_level: str
    selected_answer: str = Field(..., max_length=1)
    correct_answer: str = Field(..., max_length=1)
    is_correct: bool
    points_earned: int = 0
    penalty_applied: int = 0
    response_time_ms: Optional[int] = None


class SessionToolCreate(BaseModel):
    """Schema para registrar uso de herramienta."""
    tool_name: str = Field(..., max_length=30)
    was_used: bool
    usage_count: int = 0
    duration_seconds: Optional[int] = None


class SessionCreate(BaseModel):
    """Schema para registrar una sesión completada desde Godot."""
    reading_id: int
    typology: str
    session_score: int
    reading_time_seconds: Optional[int] = None
    total_time_seconds: Optional[int] = None
    is_perfect: bool = False
    correct_count: int = 0
    incorrect_count: int = 0
    tool_bonus: int = 0
    answers: List[PlayerAnswerCreate] = []
    tools: List[SessionToolCreate] = []

    class Config:
        json_schema_extra = {
            "example": {
                "reading_id": 1,
                "typology": "Narrativo",
                "session_score": 180,
                "reading_time_seconds": 245,
                "total_time_seconds": 480,
                "is_perfect": False,
                "correct_count": 4,
                "incorrect_count": 2,
                "tool_bonus": 40,
                "answers": [
                    {
                        "question_id": 1,
                        "comprehension_level": "Literal",
                        "selected_answer": "B",
                        "correct_answer": "B",
                        "is_correct": True,
                        "points_earned": 10,
                    }
                ],
                "tools": [
                    {"tool_name": "highlight", "was_used": True, "usage_count": 3},
                    {"tool_name": "underline", "was_used": True, "usage_count": 1},
                    {"tool_name": "notes", "was_used": False, "usage_count": 0},
                ],
            }
        }


class NoteCreate(BaseModel):
    """Schema para guardar una nota del jugador."""
    reading_id: int
    session_id: Optional[int] = None
    note_content: str = Field(..., min_length=1, max_length=10000)
    note_type: str = Field(default="free_text")


class AchievementCreate(BaseModel):
    """Schema para registrar un logro desbloqueado."""
    achievement_id: str = Field(..., max_length=50)
    achievement_name: str = Field(..., max_length=100)


# ── Schemas de Respuesta de Progreso ─────────────────────────────────────────

class PlayerAnswerResponse(BaseModel):
    """Respuesta individual en una sesión."""
    id: int
    question_id: int
    comprehension_level: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    points_earned: int
    penalty_applied: int
    response_time_ms: Optional[int] = None
    answered_at: datetime

    class Config:
        from_attributes = True


class SessionToolResponse(BaseModel):
    """Herramienta usada en una sesión."""
    tool_name: str
    was_used: bool
    usage_count: int
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Respuesta de una sesión completada."""
    id: int
    user_id: int
    reading_id: int
    typology: str
    session_score: int
    reading_time_seconds: Optional[int] = None
    total_time_seconds: Optional[int] = None
    is_perfect: bool
    correct_count: int
    incorrect_count: int
    tool_bonus: int
    started_at: datetime
    completed_at: datetime
    answers: List[PlayerAnswerResponse] = []
    tools: List[SessionToolResponse] = []

    class Config:
        from_attributes = True


class NoteResponse(BaseModel):
    """Respuesta de una nota del jugador."""
    id: int
    user_id: int
    reading_id: int
    session_id: Optional[int] = None
    note_content: str
    note_type: str
    created_at: datetime
    reading_title: Optional[str] = None

    class Config:
        from_attributes = True


class AchievementResponse(BaseModel):
    """Logro desbloqueado."""
    id: int
    achievement_id: str
    achievement_name: str
    unlocked_at: datetime

    class Config:
        from_attributes = True


class AchievementFullResponse(BaseModel):
    """Schema de respuesta para un logro del catálogo completo cruzado con su estado de desbloqueo."""
    id: str
    name: str
    description: str
    how_to_unlock: str
    category: str
    icon: str
    medal_name: str
    medal_tier: str
    medal_description: Optional[str] = None
    medal_image_path: Optional[str] = None
    medal_placeholder_emoji: Optional[str] = "🏅"
    is_unlocked: bool
    unlocked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TypologyProgressResponse(BaseModel):
    """Progreso en una tipología específica."""
    typology: str
    best_score: int
    total_sessions: int
    perfect_sessions: int
    is_unlocked: bool
    first_completed_at: Optional[datetime] = None
    last_played_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlayerProgressResponse(BaseModel):
    """Progreso completo del jugador (respuesta de GET /progress/me)."""
    user: UserResponse
    active_slot_id: Optional[int] = None
    total_score: int
    typology_progress: List[TypologyProgressResponse]
    achievements: List[AchievementResponse]
    recent_sessions: List[SessionResponse] = []


# ── Schemas de Administración ────────────────────────────────────────────────

class PlayerSummary(BaseModel):
    """Resumen de un jugador para la vista general del dashboard."""
    id: int
    email: str
    display_name: str
    character: str
    is_active: bool
    total_score: int = 0
    total_sessions: int = 0
    total_achievements: int = 0
    last_played_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminStatsResponse(BaseModel):
    """Estadísticas globales para el dashboard."""
    total_players: int
    active_players: int
    total_sessions: int
    total_points: int
    total_achievements: int
    average_accuracy: float
    sessions_by_typology: dict
    activity_last_7_days: List[dict]


class ResetTypologyRequest(BaseModel):
    """Schema para reiniciar progreso de una tipología (y superiores)."""
    typology: str = Field(..., description="Tipología desde la cual reiniciar (incluida)")
    confirm_email: str = Field(..., description="Email del jugador para confirmar")
    confirm_delete: bool = Field(..., description="El admin debe confirmar explícitamente la eliminación")


class ResetAllRequest(BaseModel):
    """Schema para reiniciar todo el progreso de un jugador."""
    confirm_email: str = Field(..., description="Email del jugador para confirmar")
    confirm_delete: bool = Field(..., description="El admin debe confirmar explícitamente la eliminación")


# ── Schemas del Módulo Logros y Medallas (Dashboard Admin) ───────────────────

class MedalImageHistoryResponse(BaseModel):
    """Entrada del historial de imágenes de una medalla."""
    id: int
    achievement_id: str
    image_path: str
    original_filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    uploaded_by: Optional[int] = None
    uploader_name: Optional[str] = None
    uploaded_at: datetime
    is_current: bool

    class Config:
        from_attributes = True


class AchievementDashboardItem(BaseModel):
    """Logro/medalla enriquecido con estadísticas de desbloqueo para el dashboard."""
    id: str
    name: str
    description: str
    how_to_unlock: str
    category: str
    icon: str
    medal_name: str
    medal_tier: str
    medal_description: Optional[str] = None
    medal_image_path: Optional[str] = None
    medal_placeholder_emoji: Optional[str] = "🏅"
    display_order: int
    is_active: bool
    # Estadísticas de desbloqueo
    unlock_count: int = 0
    total_players: int = 0
    unlock_percentage: float = 0.0
    # Estado para un jugador específico (si se filtra por player_id)
    is_unlocked_by_player: Optional[bool] = None
    unlocked_at_by_player: Optional[datetime] = None

    class Config:
        from_attributes = True


class AchievementPlayerInfo(BaseModel):
    """Info de un jugador que posee un logro."""
    user_id: int
    display_name: str
    email: str
    character: str
    slot_number: int
    slot_label: str
    unlocked_at: datetime

    class Config:
        from_attributes = True


class AchievementDetailResponse(BaseModel):
    """Detalle completo de un logro/medalla para la vista de detalle."""
    id: str
    name: str
    description: str
    how_to_unlock: str
    category: str
    icon: str
    medal_name: str
    medal_tier: str
    medal_description: Optional[str] = None
    medal_image_path: Optional[str] = None
    medal_placeholder_emoji: Optional[str] = "🏅"
    display_order: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Estadísticas
    unlock_count: int = 0
    total_players: int = 0
    unlock_percentage: float = 0.0
    # Jugadores que lo poseen
    players: List[AchievementPlayerInfo] = []
    # Historial de imágenes
    image_history: List[MedalImageHistoryResponse] = []

    class Config:
        from_attributes = True


class AchievementStatsResponse(BaseModel):
    """Estadísticas globales de logros y medallas para el dashboard."""
    total_achievements: int
    total_active: int
    total_unlocks: int
    unique_players_with_unlocks: int
    average_unlock_percentage: float
    distribution_by_category: dict  # {"progreso": 3, "maestría": 4, ...}
    distribution_by_tier: dict  # {"bronce": 2, "plata": 3, ...}
    top_unlocked: List[dict]  # [{id, name, icon, unlock_count, percentage}, ...]
    least_unlocked: List[dict]

