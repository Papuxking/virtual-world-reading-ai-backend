"""
auth.py — Lógica de autenticación con JWT y bcrypt.
Provee funciones para hashear/verificar contraseñas, crear/decodificar tokens,
y dependencies de FastAPI para proteger endpoints.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User, Workspace

# ── Configuración ────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")
if len(SECRET_KEY.encode("utf-8")) < 32 or "change-in-production" in SECRET_KEY:
    raise RuntimeError("Configura JWT_SECRET_KEY con al menos 32 bytes aleatorios; no se admiten claves de ejemplo")
ALGORITHM = "HS256"
ISSUER = "virtual-world-reading"
AUDIENCE = "virtual-world-api"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
if not 15 <= ACCESS_TOKEN_EXPIRE_MINUTES <= 1440:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES debe estar entre 15 y 1440")
ADMIN_COOKIE = "vw_admin_session"

# ── Hashing de contraseñas ───────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated=["bcrypt"])


def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt."""
    try:
        if not hashed_password.startswith("$bcrypt-sha256$") and len(plain_password.encode("utf-8")) > 72:
            return False
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


# ── JWT Tokens ───────────────────────────────────────────────────────────────

def create_access_token(user_id: int, email: str = "", is_admin: bool = False, session_version: int = 1) -> str:
    """Crea un token JWT con los datos del usuario."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "sv": session_version,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "purpose": "access",
        "iat": now,
        "nbf": now,
        "jti": secrets.token_urlsafe(24),
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica un token JWT. Retorna None si es inválido o expirado."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], issuer=ISSUER, audience=AUDIENCE,
                             options={"require_exp": True, "require_sub": True, "require_iat": True,
                                      "require_nbf": True, "require_iss": True, "require_aud": True})
        sub = payload["sub"]
        if not isinstance(sub, str) or not sub.isascii() or not sub.isdecimal() or not 0 < int(sub) <= 2147483647:
            return None
        if type(payload.get("sv")) is not int or payload.get("purpose") != "access":
            return None
        return payload
    except (JWTError, ValueError, TypeError, KeyError):
        return None


# ── Dependencies de FastAPI ──────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)


def get_authenticated_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency que extrae el usuario autenticado del token JWT.
    Lanza 401 si no hay token, es inválido, o el usuario no existe.
    """
    token = credentials.credentials if credentials else request.cookies.get(ADMIN_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
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

    if payload["sv"] != user.session_version:
        raise HTTPException(409, "SESSION_INVALIDATED")
    request.state.security_user_id = user.id
    if credentials is None:
        if not user.is_admin:
            raise HTTPException(403, "Permisos de administrador requeridos")
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = os.getenv("PUBLIC_ORIGIN", "").rstrip("/")
            if not origin or request.headers.get("origin", "").rstrip("/") != origin:
                raise HTTPException(403, "Origen de la solicitud no permitido")

    # Un jugador solo juega mientras su entorno está activo; los
    # administradores no tienen entorno. El juego trata este 409 como una
    # sesión invalidada: vuelve al login con un aviso.
    if not user.is_admin and not _entorno_activo(db, user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="WORKSPACE_INACTIVE")

    return user


def get_current_user(user: User = Depends(get_authenticated_user)) -> User:
    if user.must_change_password:
        raise HTTPException(403, "PASSWORD_CHANGE_REQUIRED")
    return user


def _entorno_activo(db: Session, user: User) -> bool:
    if user.workspace_id is None:
        return False
    return bool(
        db.query(Workspace.is_active).filter(Workspace.id == user.workspace_id).scalar()
    )


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
