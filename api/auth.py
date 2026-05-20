"""
auth.py — Lógica de autenticación con JWT y bcrypt.
Provee funciones para hashear/verificar contraseñas, crear/decodificar tokens,
y dependencies de FastAPI para proteger endpoints.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User

# ── Configuración ────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# ── Hashing de contraseñas ───────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ───────────────────────────────────────────────────────────────

def create_access_token(user_id: int, email: str, is_admin: bool = False) -> str:
    """Crea un token JWT con los datos del usuario."""
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "is_admin": is_admin,
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica un token JWT. Retorna None si es inválido o expirado."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ── Dependencies de FastAPI ──────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency que extrae el usuario autenticado del token JWT.
    Lanza 401 si no hay token, es inválido, o el usuario no existe.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """
    Dependency que verifica que el usuario actual es administrador.
    Lanza 403 si no tiene permisos de admin.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos de administrador requeridos",
        )
    return user
