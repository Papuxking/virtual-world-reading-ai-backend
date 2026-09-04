"""
auth_router.py — Endpoints de autenticación.
Registro, login, datos del usuario actual y refresco de token.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, PlayerTypologyProgress, PlayerSlot
from schemas import UserRegister, UserLogin, UserResponse, TokenResponse, DIFFICULTY_ORDER, ChangePasswordRequest
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(data: UserRegister, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con correo y contraseña."""
    # Verificar si el email ya existe
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo electrónico",
        )

    # Validar contraseña: al menos 1 mayúscula y 1 número
    if not any(c.isupper() for c in data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una letra mayúscula",
        )
    if not any(c.isdigit() for c in data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos un número",
        )

    # Validar personaje
    if data.character not in ("male", "women"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El personaje debe ser 'male' o 'women'",
        )

    # Crear usuario
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        display_name=data.display_name,
        character=data.character,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear slot 1 por defecto
    slot = PlayerSlot(
        user_id=user.id,
        slot_number=1,
        label="Sesión 1",
        is_active=True
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    # Inicializar progreso de tipologías (Narrativo desbloqueado) vinculadas al slot 1
    for typology in DIFFICULTY_ORDER:
        progress = PlayerTypologyProgress(
            user_id=user.id,
            slot_id=slot.id,
            typology=typology,
            is_unlocked=(typology == "Narrativo"),
        )
        db.add(progress)
    db.commit()

    return user


@router.post("/login", response_model=TokenResponse)
def login_user(data: UserLogin, db: Session = Depends(get_db)):
    """Inicia sesión con correo y contraseña, retorna JWT."""
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
        )

    # Sesión única: cada login invalida la anterior.
    # El juego se publica en web y un mismo alumno puede abrirlo desde otro
    # navegador o equipo, donde el cerrojo de pestañas del cliente ya no llega.
    # Al subir session_version, la ventana antigua recibe 409 SESSION_INVALIDATED
    # en su siguiente petición y se cierra sola, de modo que solo una sesión
    # escribe progreso a la vez.
    user.session_version = (user.session_version or 1) + 1

    # Actualizar último login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    # Generar token
    token = create_access_token(user.id, user.email, user.is_admin)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        must_change_password=user.must_change_password,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    display_name: str = None,
    character: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza el perfil del usuario autenticado."""
    if display_name is not None:
        current_user.display_name = display_name
    if character is not None:
        if character not in ("male", "women"):
            raise HTTPException(status_code=400, detail="El personaje debe ser 'male' o 'women'")
        current_user.character = character
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password", status_code=200)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permite al usuario cambiar su contraseña (útil tras un reset del administrador)."""
    # Validar longitud
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres",
        )
    # Validar mayúscula
    if not any(c.isupper() for c in data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una letra mayúscula",
        )
    # Validar número
    if not any(c.isdigit() for c in data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos un número",
        )

    # Actualizar hash y quitar flag de cambio obligatorio
    current_user.hashed_password = hash_password(data.new_password)
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)

    return {"detail": "Contraseña cambiada exitosamente"}
