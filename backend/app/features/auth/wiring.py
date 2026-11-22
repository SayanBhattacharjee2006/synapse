from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.dependencies import get_db
from app.features.auth.application.auth_service import AuthService
from app.features.auth.application.interfaces.password_hasher import PasswordHasher
from app.features.auth.application.interfaces.token_service import TokenService
from app.features.auth.application.interfaces.user_repository import UserRepository
from app.features.auth.infrastructure.persistence.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.features.auth.infrastructure.security.jwt_token_service import (
    JwtTokenService,
)
from app.features.auth.infrastructure.security.pwdlib_password_hasher import (
    PwdlibPasswordHasher,
)


def get_password_hasher() -> PasswordHasher:
    return PwdlibPasswordHasher()


def get_token_service() -> TokenService:
    return JwtTokenService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        password_hasher=password_hasher,
        token_service=token_service,
    )
