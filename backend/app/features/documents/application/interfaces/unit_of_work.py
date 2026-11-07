from abc import ABC, abstractmethod
from typing import Any
from app.features.documents.application.interfaces.document_repository import (
    DocumentRepository,
)


class DocumentUnitOfWork(ABC):
    documents: DocumentRepository

    @abstractmethod
    async def __aenter__(self) -> "DocumentUnitOfWork":
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        """Commit the active transaction."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the active transaction."""
        raise NotImplementedError

    @abstractmethod
    async def refresh(self, instance: Any) -> None:
        """Refresh instance state from the database."""
        raise NotImplementedError

