from .database import session_factory

async def get_db():
    async with session_factory() as session:
        yield session