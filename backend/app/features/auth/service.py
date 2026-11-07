import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.application.auth_service import AuthService
from app.features.auth.infrastructure.persistence.models import User
from app.features.auth.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from app.features.auth.presentation.schemas import (
    AuthResponse,
    UserCreate,
    UserLogin,
)
from app.features.auth.wiring import (
    get_password_hasher,
    get_token_service,
)


def _create_service_for_session(db: AsyncSession) -> AuthService:
    return AuthService(
        uow=SQLAlchemyUnitOfWork(db),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
    )


async def authenticate_user(
    db: AsyncSession,
    user_login: UserLogin,
) -> User:
    service = _create_service_for_session(db)
    return await service.authenticate_user(user_login)


async def login_user(
    db: AsyncSession,
    user_login: UserLogin,
) -> AuthResponse:
    service = _create_service_for_session(db)
    return await service.login_user(user_login)


async def register_user(
    db: AsyncSession,
    user_create: UserCreate,
) -> AuthResponse:
    service = _create_service_for_session(db)
    return await service.register_user(user_create)


async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> User | None:
    service = _create_service_for_session(db)
    return await service.get_user_by_id(user_id)


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    service = _create_service_for_session(db)
    return await service.get_user_by_email(email)


__all__ = [
    "authenticate_user",
    "login_user",
    "register_user",
    "get_user_by_id",
    "get_user_by_email",
    "AuthService",
]
