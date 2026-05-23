from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
        Base class for all sql models
    """
    pass

engine = create_async_engine(str(settings.DATABASE_URL))

session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)
