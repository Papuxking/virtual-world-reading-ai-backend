"""
catalog_router.py — Endpoints para gestionar el catálogo de logros y medallas.
Permite listar el catálogo, actualizar logros y subir imágenes de medallas.
"""
import os
import struct
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, AchievementCatalog
from schemas import AchievementCatalogResponse, AchievementCatalogUpdate
from auth import get_current_admin

router = APIRouter(prefix="/achievements", tags=["Catálogo de Logros y Medallas"])

MEDALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "medals")


def validate_png_256x256(data: bytes) -> bool:
    """Valida que los bytes correspondan a una imagen PNG de 256x256 píxeles leyendo su cabecera IHDR."""
    if len(data) < 24:
        return False
    # Firma estándar de PNG
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return False
    # Chunk IHDR
    if data[12:16] != b'IHDR':
        return False
    # Ancho y alto son enteros de 32 bits big-endian en los bytes 16-23
    width, height = struct.unpack('>II', data[16:24])
    return width == 256 and height == 256


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
    """Sube una imagen personalizada para una medalla (PNG, 256x256, máx 5MB)."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado en el catálogo")

    # 1. Validar extensión y formato MIME
    if not file.filename.lower().endswith(".png"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen debe ser en formato PNG (.png)",
        )

    # 2. Leer archivo y validar tamaño máximo (5MB)
    content = await file.read()
    max_size = 5 * 1024 * 1024  # 5 Megabytes
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen excede el límite de tamaño de 5 MB",
        )

    # 3. Validar dimensiones (256x256)
    if not validate_png_256x256(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dimensiones de imagen inválidas. Debe ser una imagen PNG de exactamente 256x256 píxeles",
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
