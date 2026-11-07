from abc import ABC, abstractmethod
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.features.auth.infrastructure.persistence.models import User


class UserRepository(ABC):

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> "User | None":
        """Retrieve a non-deleted user by UUID."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> "User | None":
        """Retrieve a non-deleted user by email."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, user: "User") -> "User":
        """Add a user to the persistence store."""
        raise NotImplementedError

