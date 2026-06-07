from fastapi import APIRouter, Depends
from app.features.auth import service
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from app.core.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    access_token = await service.login_user(db, user_login)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    return await service.register_user(db, user_create)
