from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import get_db

EMAIL_NOT_VERIFIED_MESSAGE = "Please verify your email before logging in"


class EmailNotVerifiedError(Exception):
    """Raised when credentials are valid but the email is not verified."""


# Contexto para hashear contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token JWT con tiempo de expiración configurable"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """Obtiene el usuario actual desde el token JWT. Lanza excepción si no es válido"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    if not user.is_verified:
        raise EmailNotVerifiedError()

    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    return current_user


def is_manager(user: models.User) -> bool:
    """Comprueba si el usuario tiene rol de gestor/manager/admin"""
    return any(
        role.name.lower() in ["manager", "admin", "gestor"] for role in user.roles
    )


def require_manager(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    """Dependencia que requiere rol de gestor. Lanza 403 si no lo tiene"""
    if not is_manager(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Manager role required"
        )
    return current_user
