from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from asyncpg import Pool
from app.db import get_pool
import os

# Конфигурация
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Хеширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer токен
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширует пароль"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        pool: Pool = Depends(get_pool)
) -> dict:
    """Получает текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, username, email, role, is_active FROM users WHERE username = $1",
            username
        )

    if user is None:
        raise credentials_exception

    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован"
        )

    return dict(user)


def require_role(required_role: str):
    """Декоратор для проверки роли"""

    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user['role'] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль: {required_role}"
            )
        return current_user

    return role_checker