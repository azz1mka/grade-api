import os
from typing import Optional

import asyncpg
from asyncpg import Pool
from dotenv import load_dotenv

load_dotenv(override=False)

DATABASE_URL = os.getenv("DATABASE_URL")
_pool: Optional[Pool] = None
async def get_pool() -> Pool:
    global _pool

    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL,min_size=5,max_size=20)
    return _pool

async def close_pool() -> None:
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None