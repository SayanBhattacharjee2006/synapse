import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
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

        logger.bind(
            email = user_login.email,
            error_reason = "invalid_credentials",
        ).warning("auth.login.failed")

        raise credentials_exception

    is_user_verified = verify_password(
        user_login.password,
        user.hashed_password,
    )

    if not is_user_verified:

        logger.bind(
            email = user_login.email,
            error_reason = "invalid_credentials",
        ).warning("auth.login.failed")

        raise credentials_exception

    return user

async def login_user(
    db: AsyncSession,
    user_login: UserLogin,
) -> AuthResponse:

    try: 
        email = user_login.email.lower()

        logger.bind(
            email = email,
        ).info("auth.login.started")

        user = await authenticate_user(
            db,
            user_login,
        )

        access_token = create_access_token(
            {
                "sub": str(user.id),
            }
        )

        logger.bind(
            user_id = str(user.id),
            email = email,
        ).info("auth.login.completed")

    except HTTPException:
        raise

    except Exception:
        logger.bind(
            email=email,
        ).exception("auth.login.error")
        raise

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

    email = user_create.email.lower()

    try:
        logger.bind(
            email = email,
        ).info("auth.register.started")

        user = User(
            email=email,
            hashed_password=hash_password(user_create.password),
            display_name=user_create.display_name,
        )

        db.add(user)

        await db.commit()

        await db.refresh(user)

    except IntegrityError:

        await db.rollback()

        logger.bind(
            email = email,
            error_reason = "user_already_exists",
        ).warning("auth.register.failed")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    except Exception:
        await db.rollback()
        logger.bind(
            email=email,
        ).exception("auth.register.error")
        raise

    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    logger.bind(
        user_id = str(user.id),
        email = email,
    ).info("auth.register.completed")
    

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
