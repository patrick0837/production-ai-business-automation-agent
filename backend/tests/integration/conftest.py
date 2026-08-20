from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.services.task_dispatcher import (
    TaskDispatchError,
    get_task_dispatcher,
)


# Ensure ORM models are registered in Base.metadata.
from backend.app.models import BusinessRequest  # noqa: F401


settings = get_settings()

test_engine = create_async_engine(
    settings.test_database_url,
    poolclass=NullPool,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_database():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def override_database(
        db_session: AsyncSession,
):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )


class FakeTaskDispatcher:
    async def enqueue_business_request(
            self,
            task_id: str,
            request_id: str,
            source: str,
            content: str,
    ) -> None:
        return None


class FailingTaskDispatcher:
    async def enqueue_business_request(
            self,
            task_id: str,
            request_id: str,
            source: str,
            content: str,
    ) -> None:
        raise TaskDispatchError(
            "Simulated broker failure"
        )


@pytest.fixture
def override_failing_task_dispatcher(
        override_task_dispatcher,
):
    app.dependency_overrides[get_task_dispatcher] = (
        lambda: FailingTaskDispatcher()
    )

    yield

@pytest.fixture(autouse=True)
def override_task_dispatcher():
    app.dependency_overrides[get_task_dispatcher] = (
        lambda: FakeTaskDispatcher()
    )

    try:
        yield
    finally:
        app.dependency_overrides.pop(
            get_task_dispatcher,
            None,
        )