"""
achievements_admin_router.py — Endpoints administrativos para el módulo de Logros y Medallas.
Dashboard con filtros avanzados, detalle, historial de imágenes, exportación CSV/Excel.
Todos los endpoints requieren rol de administrador.
"""
import csv
import io
import os
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc, Integer, distinct

from database import get_db
from models import (
    User, PlayerAchievement, AchievementCatalog, MedalImageHistory, PlayerSlot,
    Workspace,
)
from schemas import (
    AchievementDashboardItem, AchievementDetailResponse,
    AchievementStatsResponse, AchievementPlayerInfo,
    MedalImageHistoryResponse,
)
from auth import get_current_admin
from workspaces import get_viewed_workspace, ids_jugadores

router = APIRouter(prefix="/admin/achievements", tags=["Admin — Logros y Medallas"])

MEDALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "medals")
MEDALS_HISTORY_DIR = os.path.join(MEDALS_DIR, "history")


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


def _get_total_non_admin_players(db: Session, workspace_id: int) -> int:
    """Retorna el número de jugadores activos del entorno."""
    return (
        db.query(sqlfunc.count(distinct(User.id)))
        .filter(User.is_admin == False, User.is_active == True, User.workspace_id == workspace_id)
        .scalar()
    ) or 1  # Evitar divisiones por cero


def _get_unlock_counts(db: Session, workspace_id: int) -> dict:
    """Retorna un dict {achievement_id: count} con el número de desbloqueos
    únicos por logro entre los jugadores del entorno."""
    rows = (
        db.query(
            PlayerAchievement.achievement_id,
            sqlfunc.count(distinct(PlayerAchievement.user_id)).label("count"),
        )
        .filter(PlayerAchievement.user_id.in_(ids_jugadores(workspace_id)))
        .group_by(PlayerAchievement.achievement_id)
        .all()
    )
    return {row.achievement_id: row.count for row in rows}


# ── Lista de Logros y Medallas con Filtros ───────────────────────────────────

@router.get("", response_model=List[AchievementDashboardItem])
def list_achievements_dashboard(
    q: str = Query("", description="Buscar por nombre de logro o medalla"),
    category: Optional[str] = Query(None, description="Filtrar por categoría (progreso, maestría, etc.)"),
    tier: Optional[str] = Query(None, description="Filtrar por tier (bronce, plata, oro, platino)"),
    player_id: Optional[int] = Query(None, description="Filtrar por jugador específico"),
    unlock_status: Optional[str] = Query(None, description="Estado: unlocked/locked (requiere player_id)"),
    sort: str = Query("display_order", description="Ordenar por: name, display_order, unlock_count, medal_tier"),
    order: str = Query("asc", description="asc o desc"),
    include_inactive: bool = Query(False, description="Incluir logros inactivos"),
    admin: User = Depends(get_current_admin),
    entorno: Workspace = Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Lista todos los logros/medallas con filtros avanzados y estadísticas de desbloqueo."""
    query = db.query(AchievementCatalog)

    if not include_inactive:
        query = query.filter(AchievementCatalog.is_active == True)

    # Filtro por búsqueda de texto
    if q:
        search = f"%{q}%"
        query = query.filter(
            (AchievementCatalog.name.ilike(search)) |
            (AchievementCatalog.medal_name.ilike(search)) |
            (AchievementCatalog.description.ilike(search))
        )

    # Filtro por categoría
    if category:
        query = query.filter(AchievementCatalog.category == category)

    # Filtro por tier
    if tier:
        query = query.filter(AchievementCatalog.medal_tier == tier)

    # Obtener todos los logros base
    achievements = query.all()

    # Estadísticas de desbloqueo
    total_players = _get_total_non_admin_players(db, entorno.id)
    unlock_counts = _get_unlock_counts(db, entorno.id)

    # Si hay filtro por jugador, obtener sus logros desbloqueados
    player_unlocks = {}
    if player_id:
        player_achievements = (
            db.query(PlayerAchievement)
            .filter(PlayerAchievement.user_id == player_id)
            .all()
        )
        for pa in player_achievements:
            if pa.achievement_id not in player_unlocks:
                player_unlocks[pa.achievement_id] = pa.unlocked_at
            elif pa.unlocked_at and (player_unlocks[pa.achievement_id] is None or pa.unlocked_at < player_unlocks[pa.achievement_id]):
                player_unlocks[pa.achievement_id] = pa.unlocked_at

    # Construir resultado
    result = []
    for ach in achievements:
        count = unlock_counts.get(ach.id, 0)
        pct = round(count / total_players * 100, 1) if total_players > 0 else 0.0

        is_unlocked = None
        unlocked_at = None
        if player_id is not None:
            is_unlocked = ach.id in player_unlocks
            unlocked_at = player_unlocks.get(ach.id)

        # Filtrar por estado de desbloqueo si se especificó
        if unlock_status and player_id is not None:
            if unlock_status == "unlocked" and not is_unlocked:
                continue
            elif unlock_status == "locked" and is_unlocked:
                continue

        result.append(AchievementDashboardItem(
            id=ach.id,
            name=ach.name,
            description=ach.description,
            how_to_unlock=ach.how_to_unlock,
            category=ach.category,
            icon=ach.icon,
            medal_name=ach.medal_name,
            medal_tier=ach.medal_tier,
            medal_description=ach.medal_description,
            medal_image_path=ach.medal_image_path,
            medal_placeholder_emoji=ach.medal_placeholder_emoji,
            display_order=ach.display_order,
            is_active=ach.is_active,
            unlock_count=count,
            total_players=total_players,
            unlock_percentage=pct,
            is_unlocked_by_player=is_unlocked,
            unlocked_at_by_player=unlocked_at,
        ))

    # Ordenamiento
    tier_order = {"bronce": 0, "plata": 1, "oro": 2, "platino": 3}
    sort_keys = {
        "name": lambda x: x.name.lower(),
        "display_order": lambda x: x.display_order,
        "unlock_count": lambda x: x.unlock_count,
        "medal_tier": lambda x: tier_order.get(x.medal_tier, 99),
        "category": lambda x: x.category.lower(),
    }
    key_fn = sort_keys.get(sort, sort_keys["display_order"])
    result.sort(key=key_fn, reverse=(order == "desc"))

    return result


# ── Estadísticas Globales de Logros y Medallas ──────────────────────────────

@router.get("/stats", response_model=AchievementStatsResponse)
def get_achievements_stats(
    admin: User = Depends(get_current_admin),
    entorno: Workspace = Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Retorna estadísticas globales de logros y medallas."""
    total_achievements = db.query(sqlfunc.count(AchievementCatalog.id)).scalar() or 0
    total_active = (
        db.query(sqlfunc.count(AchievementCatalog.id))
        .filter(AchievementCatalog.is_active == True)
        .scalar()
    ) or 0
    del_entorno = PlayerAchievement.user_id.in_(ids_jugadores(entorno.id))
    total_unlocks = db.query(sqlfunc.count(PlayerAchievement.id)).filter(del_entorno).scalar() or 0
    unique_players = (
        db.query(sqlfunc.count(distinct(PlayerAchievement.user_id))).filter(del_entorno).scalar()
    ) or 0

    total_players = _get_total_non_admin_players(db, entorno.id)
    unlock_counts = _get_unlock_counts(db, entorno.id)

    # % de desbloqueo promedio
    if total_active > 0 and total_players > 0:
        avg_pct = round(
            sum(unlock_counts.get(a.id, 0) / total_players * 100
                for a in db.query(AchievementCatalog).filter(AchievementCatalog.is_active == True).all())
            / total_active,
            1,
        )
    else:
        avg_pct = 0.0

    # Distribución por categoría
    cat_rows = (
        db.query(AchievementCatalog.category, sqlfunc.count(AchievementCatalog.id))
        .filter(AchievementCatalog.is_active == True)
        .group_by(AchievementCatalog.category)
        .all()
    )
    dist_category = {cat: cnt for cat, cnt in cat_rows}

    # Distribución por tier
    tier_rows = (
        db.query(AchievementCatalog.medal_tier, sqlfunc.count(AchievementCatalog.id))
        .filter(AchievementCatalog.is_active == True)
        .group_by(AchievementCatalog.medal_tier)
        .all()
    )
    dist_tier = {tier: cnt for tier, cnt in tier_rows}

    # Top 5 más desbloqueados
    all_active = db.query(AchievementCatalog).filter(AchievementCatalog.is_active == True).all()
    items_with_counts = []
    for a in all_active:
        cnt = unlock_counts.get(a.id, 0)
        pct = round(cnt / total_players * 100, 1) if total_players > 0 else 0.0
        items_with_counts.append({
            "id": a.id, "name": a.name, "icon": a.icon,
            "unlock_count": cnt, "percentage": pct,
        })
    items_with_counts.sort(key=lambda x: x["unlock_count"], reverse=True)

    return AchievementStatsResponse(
        total_achievements=total_achievements,
        total_active=total_active,
        total_unlocks=total_unlocks,
        unique_players_with_unlocks=unique_players,
        average_unlock_percentage=avg_pct,
        distribution_by_category=dist_category,
        distribution_by_tier=dist_tier,
        top_unlocked=items_with_counts[:5],
        least_unlocked=list(reversed(items_with_counts))[:5],
    )


# ── Detalle de un Logro/Medalla ─────────────────────────────────────────────

@router.get("/{achievement_id}", response_model=AchievementDetailResponse)
def get_achievement_detail(
    achievement_id: str,
    admin: User = Depends(get_current_admin),
    entorno: Workspace = Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Retorna el detalle completo de un logro/medalla."""
    achievement = (
        db.query(AchievementCatalog)
        .options(joinedload(AchievementCatalog.image_history))
        .filter(AchievementCatalog.id == achievement_id)
        .first()
    )
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado")

    total_players = _get_total_non_admin_players(db, entorno.id)

    # Jugadores que poseen el logro
    player_achievements = (
        db.query(PlayerAchievement, User, PlayerSlot)
        .join(User, PlayerAchievement.user_id == User.id)
        .join(PlayerSlot, PlayerAchievement.slot_id == PlayerSlot.id)
        .filter(PlayerAchievement.achievement_id == achievement_id, User.workspace_id == entorno.id)
        .order_by(PlayerAchievement.unlocked_at.desc())
        .all()
    )

    # Deduplicate by user (keep earliest unlock)
    seen_users = set()
    players = []
    for pa, user, slot in player_achievements:
        if user.id not in seen_users:
            seen_users.add(user.id)
            players.append(AchievementPlayerInfo(
                user_id=user.id,
                display_name=user.display_name,
                email=user.email,
                character=user.character,
                slot_number=slot.slot_number,
                slot_label=slot.label,
                unlocked_at=pa.unlocked_at,
            ))

    unlock_count = len(seen_users)
    pct = round(unlock_count / total_players * 100, 1) if total_players > 0 else 0.0

    # Historial de imágenes con nombre del uploader
    image_history = []
    for hist in achievement.image_history:
        uploader_name = None
        if hist.uploaded_by:
            uploader = db.query(User).filter(User.id == hist.uploaded_by).first()
            if uploader:
                uploader_name = uploader.display_name
        image_history.append(MedalImageHistoryResponse(
            id=hist.id,
            achievement_id=hist.achievement_id,
            image_path=hist.image_path,
            original_filename=hist.original_filename,
            file_size_bytes=hist.file_size_bytes,
            uploaded_by=hist.uploaded_by,
            uploader_name=uploader_name,
            uploaded_at=hist.uploaded_at,
            is_current=hist.is_current,
        ))

    return AchievementDetailResponse(
        id=achievement.id,
        name=achievement.name,
        description=achievement.description,
        how_to_unlock=achievement.how_to_unlock,
        category=achievement.category,
        icon=achievement.icon,
        medal_name=achievement.medal_name,
        medal_tier=achievement.medal_tier,
        medal_description=achievement.medal_description,
        medal_image_path=achievement.medal_image_path,
        medal_placeholder_emoji=achievement.medal_placeholder_emoji,
        display_order=achievement.display_order,
        is_active=achievement.is_active,
        created_at=achievement.created_at,
        updated_at=achievement.updated_at,
        unlock_count=unlock_count,
        total_players=total_players,
        unlock_percentage=pct,
        players=players,
        image_history=image_history,
    )


# ── Jugadores de un Logro ───────────────────────────────────────────────────

@router.get("/{achievement_id}/players", response_model=List[AchievementPlayerInfo])
def get_achievement_players(
    achievement_id: str,
    q: str = Query("", description="Buscar por nombre o email"),
    admin: User = Depends(get_current_admin),
    entorno: Workspace = Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Lista los jugadores que poseen un logro específico."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado")

    query = (
        db.query(PlayerAchievement, User, PlayerSlot)
        .join(User, PlayerAchievement.user_id == User.id)
        .join(PlayerSlot, PlayerAchievement.slot_id == PlayerSlot.id)
        .filter(PlayerAchievement.achievement_id == achievement_id, User.workspace_id == entorno.id)
    )

    if q:
        search = f"%{q}%"
        query = query.filter(
            (User.display_name.ilike(search)) | (User.email.ilike(search))
        )

    results = query.order_by(PlayerAchievement.unlocked_at.desc()).all()

    seen_users = set()
    players = []
    for pa, user, slot in results:
        if user.id not in seen_users:
            seen_users.add(user.id)
            players.append(AchievementPlayerInfo(
                user_id=user.id,
                display_name=user.display_name,
                email=user.email,
                character=user.character,
                slot_number=slot.slot_number,
                slot_label=slot.label,
                unlocked_at=pa.unlocked_at,
            ))

    return players


# ── Historial de Imágenes ───────────────────────────────────────────────────

@router.get("/{achievement_id}/image-history", response_model=List[MedalImageHistoryResponse])
def get_image_history(
    achievement_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retorna el historial de imágenes de una medalla."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado")

    history = (
        db.query(MedalImageHistory)
        .filter(MedalImageHistory.achievement_id == achievement_id)
        .order_by(MedalImageHistory.uploaded_at.desc())
        .all()
    )

    result = []
    for hist in history:
        uploader_name = None
        if hist.uploaded_by:
            uploader = db.query(User).filter(User.id == hist.uploaded_by).first()
            if uploader:
                uploader_name = uploader.display_name
        result.append(MedalImageHistoryResponse(
            id=hist.id,
            achievement_id=hist.achievement_id,
            image_path=hist.image_path,
            original_filename=hist.original_filename,
            file_size_bytes=hist.file_size_bytes,
            uploaded_by=hist.uploaded_by,
            uploader_name=uploader_name,
            uploaded_at=hist.uploaded_at,
            is_current=hist.is_current,
        ))

    return result


# ── Subir Nueva Imagen de Medalla (con historial) ──────────────────────────

@router.put("/{achievement_id}/medal-image")
async def upload_medal_image_with_history(
    achievement_id: str,
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Sube nueva imagen de medalla. La anterior se archiva automáticamente en el historial."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado en el catálogo")

    # Validar extensión
    allowed_extensions = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Se aceptan: PNG, JPG, WebP, BMP, GIF",
        )

    # Leer y validar tamaño
    raw_content = await file.read()
    max_size = 10 * 1024 * 1024  # 10 MB para imágenes grandes que serán redimensionadas
    if len(raw_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen excede el límite de tamaño de 10 MB",
        )

    # Redimensionar automáticamente a 256x256 PNG
    try:
        content = resize_image_to_256(raw_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Asegurar directorios
    os.makedirs(MEDALS_DIR, exist_ok=True)
    os.makedirs(MEDALS_HISTORY_DIR, exist_ok=True)

    # Si ya hay una imagen actual, archivarla en el historial
    if achievement.medal_image_path:
        current_filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            achievement.medal_image_path.lstrip("/")
        )
        if os.path.exists(current_filepath):
            # Copiar a historial con timestamp
            ts = int(time.time())
            history_filename = f"{achievement_id}_{ts}.png"
            history_filepath = os.path.join(MEDALS_HISTORY_DIR, history_filename)
            import shutil
            shutil.copy2(current_filepath, history_filepath)

            # Marcar anteriores como no-current
            db.query(MedalImageHistory).filter(
                MedalImageHistory.achievement_id == achievement_id,
                MedalImageHistory.is_current == True,
            ).update({MedalImageHistory.is_current: False})

            # Registrar en historial
            hist_entry = MedalImageHistory(
                achievement_id=achievement_id,
                image_path=f"/static/medals/history/{history_filename}",
                original_filename=f"{achievement_id}.png",
                file_size_bytes=os.path.getsize(current_filepath),
                uploaded_by=None,  # No sabemos quién subió la anterior
                is_current=False,
            )
            db.add(hist_entry)

    # Guardar nueva imagen
    ts_new = int(time.time())
    filename = f"{achievement_id}.png"
    filepath = os.path.join(MEDALS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # Actualizar la ruta con cache-buster
    achievement.medal_image_path = f"/static/medals/{filename}?v={ts_new}"

    # Marcar anteriores como no-current
    db.query(MedalImageHistory).filter(
        MedalImageHistory.achievement_id == achievement_id,
        MedalImageHistory.is_current == True,
    ).update({MedalImageHistory.is_current: False})

    # Registrar la nueva imagen como current en el historial
    new_hist = MedalImageHistory(
        achievement_id=achievement_id,
        image_path=f"/static/medals/{filename}?v={ts_new}",
        original_filename=file.filename,
        file_size_bytes=len(content),
        uploaded_by=admin.id,
        is_current=True,
    )
    db.add(new_hist)

    db.commit()
    db.refresh(achievement)

    return {
        "detail": "Imagen actualizada exitosamente",
        "medal_image_path": achievement.medal_image_path,
        "achievement_id": achievement_id,
    }


# ── Restaurar Imagen desde Historial ────────────────────────────────────────

@router.post("/{achievement_id}/restore-image/{history_id}")
def restore_medal_image(
    achievement_id: str,
    history_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Restaura una imagen de medalla desde el historial."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado")

    hist_entry = (
        db.query(MedalImageHistory)
        .filter(MedalImageHistory.id == history_id, MedalImageHistory.achievement_id == achievement_id)
        .first()
    )
    if not hist_entry:
        raise HTTPException(status_code=404, detail="Imagen del historial no encontrada")

    # Obtener la ruta real del archivo del historial (sin query params)
    hist_path_clean = hist_entry.image_path.split("?")[0]
    hist_filepath = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        hist_path_clean.lstrip("/")
    )
    if not os.path.exists(hist_filepath):
        raise HTTPException(status_code=404, detail="El archivo de imagen del historial no existe en el servidor")

    # Copiar la imagen del historial a la ubicación principal
    import shutil
    ts = int(time.time())
    dest_filename = f"{achievement_id}.png"
    dest_filepath = os.path.join(MEDALS_DIR, dest_filename)
    shutil.copy2(hist_filepath, dest_filepath)

    # Actualizar la ruta con cache-buster
    achievement.medal_image_path = f"/static/medals/{dest_filename}?v={ts}"

    # Marcar todas las entradas como no-current
    db.query(MedalImageHistory).filter(
        MedalImageHistory.achievement_id == achievement_id,
    ).update({MedalImageHistory.is_current: False})

    # Marcar la restaurada como current
    hist_entry.is_current = True

    db.commit()

    return {
        "detail": "Imagen restaurada exitosamente",
        "medal_image_path": achievement.medal_image_path,
    }


# ── Eliminar Imagen del Historial ───────────────────────────────────────────

@router.delete("/{achievement_id}/image-history/{history_id}")
def delete_history_image(
    achievement_id: str,
    history_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Elimina una imagen del historial (con confirmación desde frontend)."""
    hist_entry = (
        db.query(MedalImageHistory)
        .filter(MedalImageHistory.id == history_id, MedalImageHistory.achievement_id == achievement_id)
        .first()
    )
    if not hist_entry:
        raise HTTPException(status_code=404, detail="Imagen del historial no encontrada")

    if hist_entry.is_current:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la imagen actualmente en uso. Sube una nueva primero.",
        )

    # Eliminar archivo físico
    hist_path_clean = hist_entry.image_path.split("?")[0]
    filepath = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        hist_path_clean.lstrip("/")
    )
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"[Error delete history image] {e}")

    db.delete(hist_entry)
    db.commit()

    return {"detail": "Imagen del historial eliminada exitosamente"}


# ── Exportación CSV ─────────────────────────────────────────────────────────

@router.get("/export/csv")
def export_achievements_csv(
    category: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
    entorno: Workspace = Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Exporta todos los logros y medallas en formato CSV."""
    query = db.query(AchievementCatalog).filter(AchievementCatalog.is_active == True)
    if category:
        query = query.filter(AchievementCatalog.category == category)
    if tier:
        query = query.filter(AchievementCatalog.medal_tier == tier)

    achievements = query.order_by(AchievementCatalog.display_order).all()
    total_players = _get_total_non_admin_players(db, entorno.id)
    unlock_counts = _get_unlock_counts(db, entorno.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Nombre", "Descripción", "Condición de Desbloqueo", "Categoría",
        "Medalla", "Tier", "Descripción Medalla", "Jugadores Desbloqueados",
        "Total Jugadores", "% Desbloqueo", "Orden", "Activo",
    ])

    for ach in achievements:
        cnt = unlock_counts.get(ach.id, 0)
        pct = round(cnt / total_players * 100, 1) if total_players > 0 else 0.0
        writer.writerow([
            ach.id, ach.name, ach.description, ach.how_to_unlock, ach.category,
            ach.medal_name, ach.medal_tier, ach.medal_description or "",
            cnt, total_players, pct, ach.display_order, "Sí" if ach.is_active else "No",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=logros_medallas.csv"},
    )


# ── Exportación Excel ───────────────────────────────────────────────────────

@router.get("/export/excel")
def export_achievements_excel(
    category: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
    entorno: Workspace = Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Exporta todos los logros y medallas en formato Excel (.xlsx)."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl no está instalado. Instálalo con: pip install openpyxl",
        )

    query = db.query(AchievementCatalog).filter(AchievementCatalog.is_active == True)
    if category:
        query = query.filter(AchievementCatalog.category == category)
    if tier:
        query = query.filter(AchievementCatalog.medal_tier == tier)

    achievements = query.order_by(AchievementCatalog.display_order).all()
    total_players = _get_total_non_admin_players(db, entorno.id)
    unlock_counts = _get_unlock_counts(db, entorno.id)

    wb = Workbook()
    ws = wb.active
    ws.title = "Logros y Medallas"

    # Estilos
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    headers = [
        "ID", "Nombre", "Descripción", "Condición de Desbloqueo", "Categoría",
        "Medalla", "Tier", "Descripción Medalla", "Jugadores Desbloqueados",
        "Total Jugadores", "% Desbloqueo", "Orden",
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    for row_idx, ach in enumerate(achievements, 2):
        cnt = unlock_counts.get(ach.id, 0)
        pct = round(cnt / total_players * 100, 1) if total_players > 0 else 0.0
        values = [
            ach.id, ach.name, ach.description, ach.how_to_unlock, ach.category,
            ach.medal_name, ach.medal_tier, ach.medal_description or "",
            cnt, total_players, pct, ach.display_order,
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            cell.border = thin_border

    # Auto-ajustar anchos
    for col in ws.columns:
        max_len = 0
        for cell in col:
            try:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=logros_medallas.xlsx"},
    )


# ── Exportar Jugadores de un Logro ──────────────────────────────────────────

@router.get("/{achievement_id}/players/export/csv")
def export_achievement_players_csv(
    achievement_id: str,
    admin: User = Depends(get_current_admin),
    entorno: Workspace = Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Exporta la lista de jugadores que poseen un logro en formato CSV."""
    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado")

    results = (
        db.query(PlayerAchievement, User, PlayerSlot)
        .join(User, PlayerAchievement.user_id == User.id)
        .join(PlayerSlot, PlayerAchievement.slot_id == PlayerSlot.id)
        .filter(PlayerAchievement.achievement_id == achievement_id, User.workspace_id == entorno.id)
        .order_by(PlayerAchievement.unlocked_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Jugador", "Email", "Personaje", "Slot", "Fecha Desbloqueo"])

    seen = set()
    for pa, user, slot in results:
        if user.id not in seen:
            seen.add(user.id)
            writer.writerow([
                user.display_name, user.email, user.character,
                f"{slot.label} (#{slot.slot_number})",
                pa.unlocked_at.strftime("%Y-%m-%d %H:%M") if pa.unlocked_at else "",
            ])

    output.seek(0)
    safe_name = achievement_id.replace(" ", "_")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=jugadores_{safe_name}.csv"},
    )


@router.get("/{achievement_id}/players/export/excel")
def export_achievement_players_excel(
    achievement_id: str,
    admin: User = Depends(get_current_admin),
    entorno: Workspace = Depends(get_viewed_workspace),
    db: Session = Depends(get_db),
):
    """Exporta la lista de jugadores que poseen un logro en formato Excel."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl no está instalado")

    achievement = db.query(AchievementCatalog).filter(AchievementCatalog.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Logro no encontrado")

    results = (
        db.query(PlayerAchievement, User, PlayerSlot)
        .join(User, PlayerAchievement.user_id == User.id)
        .join(PlayerSlot, PlayerAchievement.slot_id == PlayerSlot.id)
        .filter(PlayerAchievement.achievement_id == achievement_id, User.workspace_id == entorno.id)
        .order_by(PlayerAchievement.unlocked_at.desc())
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = f"Jugadores - {achievement.name[:25]}"

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    headers = ["Jugador", "Email", "Personaje", "Slot", "Fecha Desbloqueo"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border

    seen = set()
    row_idx = 2
    for pa, user, slot in results:
        if user.id not in seen:
            seen.add(user.id)
            values = [
                user.display_name, user.email, user.character,
                f"{slot.label} (#{slot.slot_number})",
                pa.unlocked_at.strftime("%Y-%m-%d %H:%M") if pa.unlocked_at else "",
            ]
            for col, val in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col, value=val)
                cell.border = thin_border
            row_idx += 1

    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    safe_name = achievement_id.replace(" ", "_")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=jugadores_{safe_name}.xlsx"},
    )


# ── Estadísticas de Logros por Jugador ──────────────────────────────────────

@router.get("/players/{player_id}/stats")
def get_player_achievement_stats(
    player_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retorna estadísticas de logros de un jugador específico."""
    user = db.query(User).filter(User.id == player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Logros del jugador
    player_achievements = (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.user_id == player_id)
        .all()
    )

    # Total del catálogo
    total_catalog = (
        db.query(sqlfunc.count(AchievementCatalog.id))
        .filter(AchievementCatalog.is_active == True)
        .scalar()
    ) or 0

    unique_achievements = set(pa.achievement_id for pa in player_achievements)

    # Distribución por categoría de logros obtenidos
    achievement_ids = list(unique_achievements)
    cat_dist = {}
    if achievement_ids:
        cats = (
            db.query(AchievementCatalog.category, sqlfunc.count(AchievementCatalog.id))
            .filter(AchievementCatalog.id.in_(achievement_ids))
            .group_by(AchievementCatalog.category)
            .all()
        )
        cat_dist = {cat: cnt for cat, cnt in cats}

    # Distribución por tier
    tier_dist = {}
    if achievement_ids:
        tiers = (
            db.query(AchievementCatalog.medal_tier, sqlfunc.count(AchievementCatalog.id))
            .filter(AchievementCatalog.id.in_(achievement_ids))
            .group_by(AchievementCatalog.medal_tier)
            .all()
        )
        tier_dist = {tier: cnt for tier, cnt in tiers}

    return {
        "player_id": player_id,
        "display_name": user.display_name,
        "email": user.email,
        "total_unlocked": len(unique_achievements),
        "total_catalog": total_catalog,
        "completion_percentage": round(len(unique_achievements) / total_catalog * 100, 1) if total_catalog > 0 else 0,
        "distribution_by_category": cat_dist,
        "distribution_by_tier": tier_dist,
        "achievements": [
            {
                "achievement_id": pa.achievement_id,
                "achievement_name": pa.achievement_name,
                "slot_id": pa.slot_id,
                "unlocked_at": pa.unlocked_at.isoformat() if pa.unlocked_at else None,
            }
            for pa in player_achievements
        ],
    }
