import uuid
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.core.logging import logger
from app.features.auth.application.interfaces.password_hasher import PasswordHasher
from app.features.auth.application.interfaces.token_service import TokenService
from app.features.auth.application.interfaces.unit_of_work import AuthUnitOfWork
from app.features.auth.infrastructure.persistence.models import User
from app.features.auth.presentation.schemas import (
    AuthResponse,
    UserCreate,
    UserLogin,
)


class AuthService:

    def __init__(
        self,
        uow: AuthUnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._token_service = token_service

    @property
    def token_service(self) -> TokenService:
        return self._token_service

    async def authenticate_user(
        self,
        user_login: UserLogin,
    ) -> User:
        user = await self.get_user_by_email(user_login.email)

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if user is None:
            logger.bind(
                email=user_login.email,
                error_reason="invalid_credentials",
            ).warning("auth.login.failed")
            raise credentials_exception

        is_user_verified = self._password_hasher.verify(
            user_login.password,
            user.hashed_password,
        )

        if not is_user_verified:
            logger.bind(
                email=user_login.email,
                error_reason="invalid_credentials",
            ).warning("auth.login.failed")
            raise credentials_exception

        return user

    async def login_user(
        self,
        user_login: UserLogin,
    ) -> AuthResponse:
        email = user_login.email.lower()
        try:
            logger.bind(
                email=email,
            ).info("auth.login.started")

            user = await self.authenticate_user(user_login)

            access_token = self._token_service.create_access_token(
                {
                    "sub": str(user.id),
                }
            )

            logger.bind(
                user_id=str(user.id),
                email=email,
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
        self,
        user_create: UserCreate,
    ) -> AuthResponse:
        email = user_create.email.lower()

        try:
            logger.bind(
                email=email,
            ).info("auth.register.started")

            user = User(
                email=email,
                hashed_password=self._password_hasher.hash(user_create.password),
                display_name=user_create.display_name,
            )

            await self._uow.users.create(user)
            await self._uow.commit()
            await self._uow.refresh(user)

        except IntegrityError:
            await self._uow.rollback()

            logger.bind(
                email=email,
                error_reason="user_already_exists",
            ).warning("auth.register.failed")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )
        except Exception:
            await self._uow.rollback()
            logger.bind(
                email=email,
            ).exception("auth.register.error")
            raise

        access_token = self._token_service.create_access_token(
            {
                "sub": str(user.id),
            }
        )

        logger.bind(
            user_id=str(user.id),
            email=email,
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
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        return await self._uow.users.get_by_id(user_id)

    async def get_user_by_email(
        self,
        email: str,
    ) -> User | None:
        return await self._uow.users.get_by_email(email.lower())

