from fastapi import APIRouter, Depends, status
from app.features.auth.application.auth_service import AuthService
from app.features.auth.infrastructure.persistence.models import User
from app.features.auth.presentation.dependencies import get_current_user
from app.features.auth.presentation.schemas import (
    AuthResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.features.auth.wiring import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
async def login(
    user_login: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    return await auth_service.login_user(user_login)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_create: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    return await auth_service.register_user(user_create)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

