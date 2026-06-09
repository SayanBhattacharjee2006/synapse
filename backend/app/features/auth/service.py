import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)

from app.features.auth.model import User
from app.features.auth.schemas import (
    UserCreate,
    UserLogin,
    AuthResponse,
)


async def authenticate_user(
    db: AsyncSession,
    user_login: UserLogin,
) -> User:

    user = await get_user_by_email(
        db,
        user_login.email,
    )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise credentials_exception

    is_user_verified = verify_password(
        user_login.password,
        user.hashed_password,
    )

    if not is_user_verified:
        raise credentials_exception

    return user


async def login_user(
    db: AsyncSession,
    user_login: UserLogin,
) -> AuthResponse:

    user = await authenticate_user(
        db,
        user_login,
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    return AuthResponse(
        id=user.id,
        display_name=user.display_name,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at,
        access_token=access_token,
        token_type="bearer",
    )


async def register_user(
    db: AsyncSession,
    user_create: UserCreate,
) -> AuthResponse:

    user = User(
        email=user_create.email.lower(),
        hashed_password=hash_password(user_create.password),
        display_name=user_create.display_name,
    )

    try:
        db.add(user)

        await db.commit()

        await db.refresh(user)

    except IntegrityError:

        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    return AuthResponse(
        id=user.id,
        display_name=user.display_name,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at,
        access_token=access_token,
        token_type="bearer",
    )


async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:

    stmt = select(User).where(
        User.id == user_id,
        User.is_deleted == False,
    )

    user = (await db.scalars(stmt)).one_or_none()

    return user


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:

    stmt = select(User).where(
        User.email == email,
        User.is_deleted == False,
    )

    user = (await db.scalars(stmt)).one_or_none()

    return user
