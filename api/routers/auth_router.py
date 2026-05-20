"""
auth_router.py — Endpoints de autenticación.
Registro, login, datos del usuario actual y refresco de token.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, PlayerTypologyProgress
from schemas import UserRegister, UserLogin, UserResponse, TokenResponse, DIFFICULTY_ORDER
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

    # Inicializar progreso de tipologías (Narrativo desbloqueado)
    for typology in DIFFICULTY_ORDER:
        progress = PlayerTypologyProgress(
            user_id=user.id,
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

    # Actualizar último login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    # Generar token
    token = create_access_token(user.id, user.email, user.is_admin)

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
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
