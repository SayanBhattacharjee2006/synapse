from sqlalchemy import text
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.database import Base
from app.core.dependencies import get_db

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[ get_db ]= override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

async def create_test_db():
    engine  = create_async_engine(str(settings.TEST_DATABASE_URL).replace("/test", "/postgres"), isolation_level = "AUTOCOMMIT")

    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1 FROM pg_database WHERE datname = 'test'"))
        exists = result.scalar()

        if not exists:
            await connection.execute(text("CREATE DATABASE test"))

    await engine.dispose()

@pytest.fixture(scope="session")
async def test_db():
    await create_test_db()
    engine = create_async_engine(str(settings.TEST_DATABASE_URL))
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(test_db):
    async_session_factory = async_sessionmaker(test_db, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session 



