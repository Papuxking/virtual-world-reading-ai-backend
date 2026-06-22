"""
catalog_router.py — Endpoints para gestionar el catálogo de logros y medallas.
Permite listar el catálogo, actualizar logros y subir imágenes de medallas.
"""
import io
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, AchievementCatalog
from schemas import AchievementCatalogResponse, AchievementCatalogUpdate
from auth import get_current_admin

router = APIRouter(prefix="/achievements", tags=["Catálogo de Logros y Medallas"])

MEDALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "medals")


def resize_image_to_256(data: bytes) -> bytes:
    """Redimensiona cualquier imagen a 256x256 píxeles en formato PNG.
    Acepta PNG, JPEG, WebP, BMP y GIF.
    Retorna los bytes de la imagen PNG redimensionada.
    Lanza ValueError si los datos no son una imagen válida.
    """
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(data))
    except Exception:
        raise ValueError("El archivo no es una imagen válida")

    # Convertir a RGBA para mantener transparencia en PNG
    if img.mode not in ("RGBA", "RGB"):
        img = img.convert("RGBA")

    # Redimensionar a 256x256 con alta calidad
    img = img.resize((256, 256), Image.LANCZOS)

    # Guardar como PNG en memoria
    output = io.BytesIO()
    img.save(output, format="PNG", optimize=True)
    return output.getvalue()


# ── Catálogo Público ─────────────────────────────────────────────────────────

@router.get("/catalog", response_model=List[AchievementCatalogResponse])
def get_achievements_catalog(db: Session = Depends(get_db)):
    """Retorna el catálogo completo de logros y medallas (público)."""
    return db.query(AchievementCatalog).filter(AchievementCatalog.is_active == True).order_by(AchievementCatalog.display_order).all()


# ── Administración de Logros y Medallas ─────────────────────────────────────

@router.put("/admin/{achievement_id}", response_model=AchievementCatalogResponse)
def update_catalog_achievement(
    achievement_id: str,
    data: AchievementCatalogUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Actualiza los datos de un logro/medalla en el catálogo."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado en el catálogo")

    # Actualizar campos proporcionados
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(achievement, key, value)

    db.commit()
    db.refresh(achievement)
    return achievement


@router.put("/admin/{achievement_id}/medal-image", response_model=AchievementCatalogResponse)
async def upload_medal_image(
    achievement_id: str,
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Sube una imagen personalizada para una medalla. Se redimensiona automáticamente a 256x256 PNG."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado en el catálogo")

    # 1. Validar extensión y formato
    allowed_extensions = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Se aceptan: PNG, JPG, WebP, BMP, GIF",
        )

    # 2. Leer archivo y validar tamaño máximo (10MB)
    raw_content = await file.read()
    max_size = 10 * 1024 * 1024  # 10 MB para imágenes grandes que serán redimensionadas
    if len(raw_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen excede el límite de tamaño de 10 MB",
        )

    # 3. Redimensionar automáticamente a 256x256 PNG
    try:
        content = resize_image_to_256(raw_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Asegurar que el directorio de medallas existe
    os.makedirs(MEDALS_DIR, exist_ok=True)

    # Guardar archivo físicamente
    filename = f"{achievement_id}.png"
    filepath = os.path.join(MEDALS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # Actualizar la ruta en la base de datos
    # Usaremos una ruta relativa para poder servirla a través de static
    achievement.medal_image_path = f"/static/medals/{filename}"
    db.commit()
    db.refresh(achievement)

    return achievement


@router.delete("/admin/{achievement_id}/medal-image", response_model=AchievementCatalogResponse)
def delete_medal_image(
    achievement_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Elimina la imagen personalizada y vuelve al placeholder automático."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado en el catálogo")

    # Borrar archivo si existe
    if achievement.medal_image_path:
        filename = f"{achievement_id}.png"
        filepath = os.path.join(MEDALS_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"[Error delete image] {e}")

    # Poner en NULL la ruta en la BD
    achievement.medal_image_path = None
    db.commit()
    db.refresh(achievement)

    return achievement
