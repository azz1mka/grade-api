import os
import pytest_asyncio
import asyncpg
from httpx import AsyncClient, ASGITransport
from dotenv import load_dotenv


load_dotenv(override=False)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@test.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

USER_USERNAME = os.getenv("TEST_USER_USERNAME", "test_user")
USER_EMAIL = os.getenv("TEST_USER_EMAIL", "user@test.com")
USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "user123")

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
    """Создает admin пользователя ИЗ .env и возвращает токен"""
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    hashed_password = get_password_hash(ADMIN_PASSWORD)  # ← ИЗ .env
    await conn.execute(
        """
        INSERT INTO users (username, email, hashed_password, role)
        VALUES ($1, $2, $3, $4)
        """,
        ADMIN_USERNAME, ADMIN_EMAIL, hashed_password, "admin"  # ← ИЗ .env
    )
    await conn.close()
    return create_access_token(data={"sub": ADMIN_USERNAME})  # ← ИЗ .env


@pytest_asyncio.fixture(scope="function")
async def user_token(clean_db):
    """Создает обычного пользователя ИЗ .env и возвращает токен"""
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    hashed_password = get_password_hash(USER_PASSWORD)  # ← ИЗ .env
    await conn.execute(
        """
        INSERT INTO users (username, email, hashed_password, role)
        VALUES ($1, $2, $3, $4)
        """,
        USER_USERNAME, USER_EMAIL, hashed_password, "user"  # ← ИЗ .env
    )
    await conn.close()
    return create_access_token(data={"sub": USER_USERNAME})  # ИЗ .env


@pytest_asyncio.fixture(scope="function")
async def client(clean_db):
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac