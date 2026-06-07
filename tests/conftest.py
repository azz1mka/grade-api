import os
import pytest_asyncio
import asyncpg
from httpx import AsyncClient, ASGITransport
from dotenv import load_dotenv

load_dotenv(override=False)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.main import app
from app import db
from app.auth import create_access_token, get_password_hash


@pytest_asyncio.fixture(scope="function")
async def clean_db():
    db._pool = None
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    async with conn.transaction():
        await conn.execute("TRUNCATE TABLE grades, students, users RESTART IDENTITY CASCADE")
    await conn.close()
    db._pool = None
    yield
    db._pool = None


@pytest_asyncio.fixture(scope="function")
async def admin_token(clean_db):
    """Создает admin пользователя и возвращает токен"""
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    hashed_password = get_password_hash("admin123")
    await conn.execute(
        """
        INSERT INTO users (username, email, hashed_password, role)
        VALUES ($1, $2, $3, $4)
        """,
        "admin", "admin@test.com", hashed_password, "admin"
    )
    await conn.close()
    return create_access_token(data={"sub": "admin"})


@pytest_asyncio.fixture(scope="function")
async def user_token(clean_db):
    """Создает обычного пользователя и возвращает токен"""
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    hashed_password = get_password_hash("user123")
    await conn.execute(
        """
        INSERT INTO users (username, email, hashed_password, role)
        VALUES ($1, $2, $3, $4)
        """,
        "user", "user@test.com", hashed_password, "user"
    )
    await conn.close()
    return create_access_token(data={"sub": "user"})


@pytest_asyncio.fixture(scope="function")
async def client(clean_db):
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac