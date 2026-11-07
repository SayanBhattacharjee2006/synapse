from abc import ABC, abstractmethod


class PasswordHasher(ABC):

    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a plain text password."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, password: str, hashed_password: str) -> bool:
        """Verify that a plain text password matches a hash."""
        raise NotImplementedError

