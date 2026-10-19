"""
workspaces.py — Entornos de trabajo.

Cada cuenta de jugador es de un entorno y, como mucho, uno está activo: solo
sus jugadores entran al juego. Los administradores no tienen entorno.
"""
import secrets
import string
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import hash_password
from database import get_db
from game_rules import DIFFICULTY_ORDER
from models import PlayerSlot, PlayerTypologyProgress, User, Workspace

# Colores que se pueden elegir para un entorno, en el orden del dashboard.
PALETA = ("#059669", "#d97706", "#2563eb", "#7c3aed", "#db2777", "#0891b2")


def generate_temp_password(length=10) -> str:
    """Genera una contraseña temporal segura con al menos una mayúscula y un número."""
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if any(c.isupper() for c in password) and any(c.isdigit() for c in password):
            return password


def entorno_activo(db: Session) -> Optional[Workspace]:
    """El entorno activo, o None si el juego está cerrado."""
    return db.query(Workspace).filter(Workspace.is_active == True).first()  # noqa: E712


def es_correo_de_admin(db: Session, email: str) -> bool:
    """Ninguna cuenta de jugador puede usar el correo de un administrador: así
    el login nunca duda entre las dos."""
    return (
        db.query(User.id).filter(User.email == email, User.is_admin == True).first()  # noqa: E712
        is not None
    )


def crear_jugador(
    db: Session,
    *,
    workspace_id: int,
    email: str,
    display_name: str,
    password: str,
    must_change_password: bool = False,
    character: str = "male",
) -> User:
    """Cuenta de jugador lista para jugar: con su slot 1 activo y las filas de
    progreso de las 4 tipologías (solo Narrativo abierta). Hace flush, no
    commit: quien llama decide cuándo confirmar."""
    usuario = User(
        workspace_id=workspace_id,
        email=email,
        hashed_password=hash_password(password),
        display_name=display_name,
        character=character,
        must_change_password=must_change_password,
    )
    db.add(usuario)
    db.flush()
    slot = PlayerSlot(user_id=usuario.id, slot_number=1, label="Sesión 1", is_active=True)
    db.add(slot)
    db.flush()
    for typology in DIFFICULTY_ORDER:
        db.add(PlayerTypologyProgress(
            user_id=usuario.id,
            slot_id=slot.id,
            typology=typology,
            is_unlocked=(typology == "Narrativo"),
        ))
    db.flush()
    return usuario


def get_viewed_workspace(
    x_workspace_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Workspace:
    """El entorno que mira el dashboard (cabecera X-Workspace-Id). Lo exigen los
    endpoints de administración que listan o agregan datos de jugadores."""
    try:
        workspace_id = int(x_workspace_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WORKSPACE_REQUIRED")
    entorno = db.get(Workspace, workspace_id)
    if entorno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WORKSPACE_NOT_FOUND")
    return entorno


def ids_jugadores(workspace_id: int):
    """Consulta con los ids de las cuentas de jugador del entorno, para filtrar
    con .in_()."""
    return select(User.id).where(User.workspace_id == workspace_id, User.is_admin == False)  # noqa: E712
