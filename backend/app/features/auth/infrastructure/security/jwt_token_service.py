from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, status
from app.features.auth.application.interfaces.token_service import TokenService


class JwtTokenService(TokenService):

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes

    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=self._access_token_expire_minutes)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            user_id = payload.get("sub")
            if not isinstance(user_id, str):
                raise credentials_exception
            return payload
        except InvalidTokenError:
            raise credentials_exception

