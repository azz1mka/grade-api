import os
from typing import Optional
import asyncpg
from asyncpg import Pool
from dotenv import load_dotenv

load_dotenv(override=False)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Переменная окружения DATABASE_URL не найдена в .env файле!")

_pool: Optional[Pool] = None


async def get_pool() -> Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=30.0
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


# ← ДОБАВЬТЕ ЭТУ ФУНКЦИЮ
async def ensure_admin() -> None:
    """Создаёт администратора, если его ещё нет."""
    from app.auth import get_password_hash

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Проверяем, есть ли уже админ
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE username = $1",
            admin_username
        )

        if not existing:
            hashed_password = get_password_hash(admin_password)
            await conn.execute(
                """
                INSERT INTO users (username, email, hashed_password, role, is_active)
                VALUES ($1, $2, $3, 'admin', true)
                """,
                admin_username, admin_email, hashed_password
            )
            print(f"✅ Администратор '{admin_username}' создан")
        else:
            print(f"ℹ️ Администратор '{admin_username}' уже существует")