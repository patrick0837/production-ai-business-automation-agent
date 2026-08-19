from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.core.config import get_settings


async def test_test_database_connection():
    settings = get_settings()

    engine = create_async_engine(
        settings.test_database_url,
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))

            assert result.scalar_one() == 1
    finally:
        await engine.dispose()