from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.documents.application.interfaces.unit_of_work import (
    DocumentUnitOfWork,
)
from app.features.documents.infrastructure.persistence.sqlalchemy_document_repository import (
    SQLAlchemyDocumentRepository,
)


class SQLAlchemyDocumentUnitOfWork(DocumentUnitOfWork):

    def __init__(
        self, session: AsyncSession, manage_session: bool = False
    ) -> None:
        self._session = session
        self._manage_session = manage_session
        self.documents = SQLAlchemyDocumentRepository(session)

    async def __aenter__(self) -> "SQLAlchemyDocumentUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            if self._manage_session:
                await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, instance: Any) -> None:
        await self._session.refresh(instance)
