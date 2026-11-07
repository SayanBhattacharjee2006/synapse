from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any


class TokenService(ABC):

    @abstractmethod
    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Generate an access token containing claims."""
        raise NotImplementedError

    @abstractmethod
    def decode_access_token(self, token: str) -> dict[str, Any]:
        """Decode and validate an access token, returning the payload claims."""
        raise NotImplementedError

