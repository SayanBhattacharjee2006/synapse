import uuid
from typing import Annotated
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.core.security import decode_access_token
from app.features.auth.model import User
from app.features.auth import service


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
    db: AsyncSession = Depends(get_db),
) -> User:

    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if not isinstance(user_id, str):
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)

    except ValueError:
        raise credentials_exception

    user = await service.get_user_by_id(
        db,
        user_uuid,
    )

    print(user)

    if user is None:
        raise credentials_exception

    return user
