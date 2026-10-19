"""
workspaces_router.py — Entornos de trabajo para el dashboard.
Crear, editar, activar (uno solo), apagar y eliminar entornos, y agregar
jugadores a un entorno con contraseña temporal.
"""
from typing import List, Optional

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func as sqlfunc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import get_current_admin
from database import get_db
from models import User, Workspace
from schemas import (
    PlayerAdded, PlayerSkipped, PlayersAddRequest, PlayersAddResult,
    WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate,
)
from workspaces import crear_jugador, es_correo_de_admin, generate_temp_password

router = APIRouter(prefix="/admin/workspaces", tags=["Entornos"])

NOMBRE_REPETIDO = "Ya existe un entorno con ese nombre."


def _lista(db: Session) -> List[WorkspaceResponse]:
    """Todos los entornos, por orden de creación, con sus cuentas de jugador."""
    cuentas = dict(
        db.query(User.workspace_id, sqlfunc.count(User.id))
        .filter(User.workspace_id.isnot(None), User.is_admin == False)  # noqa: E712
        .group_by(User.workspace_id)
        .all()
    )
    return [_respuesta(w, cuentas.get(w.id, 0)) for w in db.query(Workspace).order_by(Workspace.id).all()]


def _respuesta(entorno: Workspace, jugadores: int) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=entorno.id,
        name=entorno.name,
        color=entorno.color,
        is_active=entorno.is_active,
        player_count=jugadores,
        created_at=entorno.created_at,
    )


def _jugadores(db: Session, entorno: Workspace) -> int:
    return (
        db.query(sqlfunc.count(User.id))
        .filter(User.workspace_id == entorno.id, User.is_admin == False)  # noqa: E712
        .scalar()
    ) or 0


def _entorno(db: Session, workspace_id: int) -> Workspace:
    entorno = db.get(Workspace, workspace_id)
    if entorno is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entorno no encontrado")
    return entorno


def _nombre_libre(db: Session, nombre: str, salvo: Optional[int] = None) -> None:
    """409 si otro entorno ya se llama así, sin distinguir mayúsculas."""
    consulta = db.query(Workspace.id).filter(sqlfunc.lower(Workspace.name) == nombre.lower())
    if salvo is not None:
        consulta = consulta.filter(Workspace.id != salvo)
    if consulta.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NOMBRE_REPETIDO)


def _confirmar(db: Session) -> None:
    """Commit; si el índice único del nombre salta (dos admins a la vez), 409."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NOMBRE_REPETIDO)


# ── Entornos ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Lista los entornos con cuántas cuentas de jugador tiene cada uno."""
    return _lista(db)


@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    data: WorkspaceCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Crea un entorno. Nace inactivo: nadie pierde el acceso al juego."""
    _nombre_libre(db, data.name)
    entorno = Workspace(name=data.name, color=data.color, is_active=False)
    db.add(entorno)
    _confirmar(db)
    db.refresh(entorno)
    return _respuesta(entorno, 0)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Cambia el nombre y/o el color de un entorno."""
    entorno = _entorno(db, workspace_id)
    if data.name is not None:
        _nombre_libre(db, data.name, salvo=entorno.id)
        entorno.name = data.name
    if data.color is not None:
        entorno.color = data.color
    _confirmar(db)
    db.refresh(entorno)
    return _respuesta(entorno, _jugadores(db, entorno))


@router.post("/{workspace_id}/activate", response_model=List[WorkspaceResponse])
def activate_workspace(
    workspace_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Activa un entorno y apaga el que lo estuviera. Los jugadores del otro
    quedan fuera en su siguiente petición (409 WORKSPACE_INACTIVE)."""
    entorno = _entorno(db, workspace_id)
    # Primero apagar y luego encender: el índice único no admite dos activos
    # ni por un instante.
    db.query(Workspace).filter(Workspace.is_active == True).update(  # noqa: E712
        {Workspace.is_active: False}, synchronize_session=False,
    )
    db.flush()
    entorno.is_active = True
    db.commit()
    return _lista(db)


@router.post("/{workspace_id}/deactivate", response_model=List[WorkspaceResponse])
def deactivate_workspace(
    workspace_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Apaga un entorno. Sin entorno activo, el juego queda cerrado para los
    estudiantes."""
    entorno = _entorno(db, workspace_id)
    entorno.is_active = False
    db.commit()
    return _lista(db)


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(
    workspace_id: int,
    confirm_name: str = Query(..., description="Nombre exacto del entorno, para confirmar"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Elimina un entorno inactivo y, en cascada, sus cuentas con todo lo suyo.
    No se puede deshacer."""
    entorno = _entorno(db, workspace_id)
    if entorno.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se puede eliminar el entorno activo.")
    if db.query(sqlfunc.count(Workspace.id)).scalar() <= 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se puede eliminar el último entorno.")
    if confirm_name != entorno.name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre no coincide.")
    # La base borra las cuentas y todo lo que cuelga de ellas (ON DELETE CASCADE).
    db.query(Workspace).filter(Workspace.id == entorno.id).delete(synchronize_session=False)
    db.commit()
    return Response(status_code=204)


# ── Alta de jugadores ────────────────────────────────────────────────────────

@router.post("/{workspace_id}/players", response_model=PlayersAddResult)
def add_players(
    workspace_id: int,
    data: PlayersAddRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Agrega jugadores al entorno, esté activo o no. Cada uno recibe una
    contraseña temporal que el juego le pide cambiar al entrar; solo viaja en
    esta respuesta. Los que no se pueden agregar se devuelven con el motivo."""
    entorno = _entorno(db, workspace_id)
    creados: List[PlayerAdded] = []
    saltados: List[PlayerSkipped] = []
    vistos: set = set()

    for jugador in data.players:
        escrito = jugador.email.strip()
        email = _correo_normalizado(escrito)
        motivo = None
        if email is None:
            motivo = "el correo no es válido"
        elif email in vistos:
            motivo = "está repetido en la lista"
        elif db.query(User.id).filter(User.email == email, User.workspace_id == entorno.id).first():
            motivo = "ya tiene cuenta en este entorno"
        elif es_correo_de_admin(db, email):
            motivo = "es el correo de un administrador"
        if email is not None:
            vistos.add(email)
        if motivo:
            saltados.append(PlayerSkipped(email=escrito, reason=motivo))
            continue

        nombre = ((jugador.display_name or "").strip() or email.split("@")[0])[:100]
        clave = generate_temp_password()
        usuario = crear_jugador(
            db,
            workspace_id=entorno.id,
            email=email,
            display_name=nombre,
            password=clave,
            must_change_password=True,
        )
        creados.append(PlayerAdded(id=usuario.id, email=email, display_name=nombre, temp_password=clave))

    db.commit()
    return PlayersAddResult(created=creados, skipped=saltados)


def _correo_normalizado(email: str) -> Optional[str]:
    """El correo tal como lo guarda el registro (EmailStr normaliza igual), o
    None si no es válido."""
    try:
        return validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        return None
