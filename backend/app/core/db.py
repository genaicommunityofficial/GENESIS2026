import asyncpg
from .config import settings

pool: asyncpg.Pool | None = None

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(settings.database_url, min_size=5, max_size=30)

async def close_pool():
    if pool: await pool.close()
