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


@pytest_asyncio.fixture(scope="function")
async def clean_db():
    db._pool = None
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    async with conn.transaction():
        await conn.execute("TRUNCATE TABLE grades, students RESTART IDENTITY CASCADE")
    await conn.close()
    db._pool = None
    yield
    db._pool = None

@pytest_asyncio.fixture(scope="function")
async def client(clean_db):
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac