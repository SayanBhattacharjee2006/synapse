import uuid
from typing import Annotated
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from app.features.auth.application.auth_service import AuthService
from app.features.auth.infrastructure.persistence.models import User
from app.features.auth.wiring import get_auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    try:
        payload = auth_service.token_service.decode_access_token(token)
    except HTTPException:
        raise credentials_exception

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = await auth_service.get_user_by_id(user_uuid)
    if user is None:
        raise credentials_exception

    return user

