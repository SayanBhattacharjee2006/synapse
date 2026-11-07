import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.features.auth.application.auth_service import AuthService
from app.features.auth.application.interfaces.password_hasher import PasswordHasher
from app.features.auth.application.interfaces.token_service import TokenService
from app.features.auth.application.interfaces.unit_of_work import AuthUnitOfWork
from app.features.auth.application.interfaces.user_repository import UserRepository
from app.features.auth.infrastructure.persistence.models import User
from app.features.auth.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from app.features.auth.infrastructure.persistence.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.features.auth.infrastructure.security.jwt_token_service import (
    JwtTokenService,
)
from app.features.auth.infrastructure.security.pwdlib_password_hasher import (
    PwdlibPasswordHasher,
)
from app.features.auth.presentation.dependencies import (
    credentials_exception,
    get_current_user,
)
from app.features.auth.presentation.router import router as auth_router
from app.features.auth.presentation.schemas import (
    AuthResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.features.auth.wiring import get_auth_service


# ==============================================================================
# 1 & 4. Password Hashing and Verification
# ==============================================================================

def test_password_hasher():
    hasher = PwdlibPasswordHasher()
    plain = "SuperSecretPassword123"

    hashed = hasher.hash(plain)
    assert hashed != plain
    assert hasher.verify(plain, hashed) is True
    assert hasher.verify("WrongPassword123", hashed) is False


# ==============================================================================
# 5 & 6. JWT Generation and Validation
# ==============================================================================

def test_jwt_token_service_generation_and_validation():
    secret = "test-secret-key-for-auth-testing-12345"
    token_svc = JwtTokenService(
        secret_key=secret,
        algorithm="HS256",
        access_token_expire_minutes=15,
    )

    user_id = str(uuid.uuid4())
    token = token_svc.create_access_token({"sub": user_id})
    assert isinstance(token, str)

    payload = token_svc.decode_access_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload


def test_jwt_token_service_invalid_and_expired():
    secret = "test-secret-key-for-auth-testing-12345"
    token_svc = JwtTokenService(
        secret_key=secret,
        algorithm="HS256",
        access_token_expire_minutes=15,
    )

    # Invalid token
    with pytest.raises(HTTPException) as exc_info:
        token_svc.decode_access_token("not-a-valid-token")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    # Expired token
    expired_token = token_svc.create_access_token(
        {"sub": "user-123"},
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(HTTPException) as exc_info:
        token_svc.decode_access_token(expired_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ==============================================================================
# 11. Repository Operations
# ==============================================================================

@pytest.mark.asyncio
async def test_sqlalchemy_user_repository_operations():
    session = AsyncMock()
    session.add = MagicMock()
    repo = SQLAlchemyUserRepository(session)

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        display_name="Test User",
        hashed_password="hash",
    )

    # Test create
    created = await repo.create(user)
    assert created == user
    session.add.assert_called_once_with(user)

    # Test get_by_id (found)
    mock_result_id = MagicMock()
    mock_result_id.one_or_none.return_value = user
    session.scalars.return_value = mock_result_id
    found_user = await repo.get_by_id(user.id)
    assert found_user == user
    assert session.scalars.call_count == 1

    # Test get_by_id (not found)
    mock_result_none = MagicMock()
    mock_result_none.one_or_none.return_value = None
    session.scalars.return_value = mock_result_none
    not_found = await repo.get_by_id(uuid.uuid4())
    assert not_found is None

    # Test get_by_email
    session.scalars.return_value = mock_result_id
    found_email = await repo.get_by_email("test@example.com")
    assert found_email == user


# ==============================================================================
# 9 & 10. Database Commit and Rollback (Unit of Work)
# ==============================================================================

@pytest.mark.asyncio
async def test_unit_of_work_commit_and_rollback():
    session = AsyncMock()
    uow = SQLAlchemyUnitOfWork(session)

    assert isinstance(uow.users, UserRepository)

    # Commit
    await uow.commit()
    session.commit.assert_awaited_once()

    # Rollback
    await uow.rollback()
    session.rollback.assert_awaited_once()

    # Refresh
    obj = object()
    await uow.refresh(obj)
    session.refresh.assert_awaited_once_with(obj)


@pytest.mark.asyncio
async def test_unit_of_work_context_manager_rollback_on_failure():
    session = AsyncMock()
    uow = SQLAlchemyUnitOfWork(session)

    with pytest.raises(ValueError):
        async with uow:
            raise ValueError("Something broke")

    session.rollback.assert_awaited_once()


# ==============================================================================
# 1, 8, 9, 10. AuthService: Registration, Commit, Rollback, Duplicate User
# ==============================================================================

@pytest.mark.asyncio
async def test_auth_service_register_success():
    uow = AsyncMock(spec=AuthUnitOfWork)
    uow.users = AsyncMock(spec=UserRepository)

    saved_user = None

    async def fake_create(user):
        nonlocal saved_user
        saved_user = user
        user.id = uuid.uuid4()
        user.created_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        return user

    uow.users.create.side_effect = fake_create

    hasher = MagicMock(spec=PasswordHasher)
    hasher.hash.return_value = "hashed_pass_xyz"

    token_svc = MagicMock(spec=TokenService)
    token_svc.create_access_token.return_value = "mocked-jwt-token"

    auth_service = AuthService(
        uow=uow,
        password_hasher=hasher,
        token_service=token_svc,
    )

    create_data = UserCreate(
        email="NewUser@Example.com",
        password="securePassword123",
        display_name="New User",
    )

    response = await auth_service.register_user(create_data)

    assert response.email == "newuser@example.com"
    assert response.display_name == "New User"
    assert response.access_token == "mocked-jwt-token"
    assert response.token_type == "bearer"

    uow.users.create.assert_awaited_once()
    uow.commit.assert_awaited_once()
    uow.refresh.assert_awaited_once()
    hasher.hash.assert_called_once_with("securePassword123")


@pytest.mark.asyncio
async def test_auth_service_register_duplicate_user_triggers_rollback():
    uow = AsyncMock(spec=AuthUnitOfWork)
    uow.users = AsyncMock(spec=UserRepository)
    # Simulate unique constraint violation on commit
    uow.commit.side_effect = IntegrityError("statement", "params", Exception("duplicate key"))

    hasher = MagicMock(spec=PasswordHasher)
    hasher.hash.return_value = "hashed_pass"

    token_svc = MagicMock(spec=TokenService)

    auth_service = AuthService(
        uow=uow,
        password_hasher=hasher,
        token_service=token_svc,
    )

    create_data = UserCreate(
        email="existing@example.com",
        password="securePassword123",
        display_name="Existing User",
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(create_data)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "User already exists"

    uow.rollback.assert_awaited_once()


# ==============================================================================
# 2 & 3. AuthService: Login, Success & Invalid Credentials
# ==============================================================================

@pytest.mark.asyncio
async def test_auth_service_login_success():
    uow = AsyncMock(spec=AuthUnitOfWork)
    uow.users = AsyncMock(spec=UserRepository)

    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    user = User(
        id=user_id,
        email="user@example.com",
        display_name="User Name",
        hashed_password="correct_hash",
        created_at=now,
        updated_at=now,
    )
    uow.users.get_by_email.return_value = user

    hasher = MagicMock(spec=PasswordHasher)
    hasher.verify.return_value = True

    token_svc = MagicMock(spec=TokenService)
    token_svc.create_access_token.return_value = "access_token_123"

    auth_service = AuthService(
        uow=uow,
        password_hasher=hasher,
        token_service=token_svc,
    )

    login_data = UserLogin(email="user@example.com", password="correct_password")
    response = await auth_service.login_user(login_data)

    assert response.id == user_id
    assert response.email == "user@example.com"
    assert response.access_token == "access_token_123"
    assert response.token_type == "bearer"


@pytest.mark.asyncio
async def test_auth_service_login_invalid_password():
    uow = AsyncMock(spec=AuthUnitOfWork)
    uow.users = AsyncMock(spec=UserRepository)

    user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        display_name="User Name",
        hashed_password="correct_hash",
    )
    uow.users.get_by_email.return_value = user

    hasher = MagicMock(spec=PasswordHasher)
    hasher.verify.return_value = False  # Bad password

    token_svc = MagicMock(spec=TokenService)

    auth_service = AuthService(
        uow=uow,
        password_hasher=hasher,
        token_service=token_svc,
    )

    login_data = UserLogin(email="user@example.com", password="wrong_password")

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(login_data)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_auth_service_login_nonexistent_user():
    uow = AsyncMock(spec=AuthUnitOfWork)
    uow.users = AsyncMock(spec=UserRepository)
    uow.users.get_by_email.return_value = None

    hasher = MagicMock(spec=PasswordHasher)
    token_svc = MagicMock(spec=TokenService)

    auth_service = AuthService(
        uow=uow,
        password_hasher=hasher,
        token_service=token_svc,
    )

    login_data = UserLogin(email="unknown@example.com", password="anypassword")

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(login_data)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid credentials"


# ==============================================================================
# 7. Current User Authentication Dependency
# ==============================================================================

@pytest.mark.asyncio
async def test_get_current_user_dependency_success():
    auth_service = AsyncMock(spec=AuthService)
    token_svc = MagicMock(spec=TokenService)
    user_id = uuid.uuid4()
    token_svc.decode_access_token.return_value = {"sub": str(user_id)}
    auth_service.token_service = token_svc

    expected_user = User(
        id=user_id,
        email="current@example.com",
        display_name="Current User",
    )
    auth_service.get_user_by_id.return_value = expected_user

    current_user = await get_current_user(token="valid-token", auth_service=auth_service)
    assert current_user == expected_user
    auth_service.get_user_by_id.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_get_current_user_dependency_user_not_found():
    auth_service = AsyncMock(spec=AuthService)
    token_svc = MagicMock(spec=TokenService)
    user_id = uuid.uuid4()
    token_svc.decode_access_token.return_value = {"sub": str(user_id)}
    auth_service.token_service = token_svc
    auth_service.get_user_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="valid-token", auth_service=auth_service)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid authentication credentials"


# ==============================================================================
# HTTP Routes and FastAPI Dependency Injection
# ==============================================================================

@pytest.mark.asyncio
async def test_auth_router_endpoints():
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")

    mock_service = AsyncMock(spec=AuthService)
    mock_token_svc = MagicMock(spec=TokenService)
    mock_service.token_service = mock_token_svc

    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_auth_response = AuthResponse(
        id=user_id,
        display_name="Integration User",
        email="integration@example.com",
        created_at=now,
        updated_at=now,
        access_token="test-access-token",
        token_type="bearer",
    )
    mock_user = User(
        id=user_id,
        display_name="Integration User",
        email="integration@example.com",
        created_at=now,
        updated_at=now,
    )

    mock_service.register_user.return_value = mock_auth_response
    mock_service.login_user.return_value = mock_auth_response
    mock_service.get_user_by_id.return_value = mock_user
    mock_token_svc.decode_access_token.return_value = {"sub": str(user_id)}

    app.dependency_overrides[get_auth_service] = lambda: mock_service

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # 1. Register endpoint
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "integration@example.com",
                "password": "mypassword123",
                "display_name": "Integration User",
            },
        )
        assert reg_resp.status_code == 201
        data = reg_resp.json()
        assert data["email"] == "integration@example.com"
        assert data["access_token"] == "test-access-token"

        # 2. Login endpoint
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "integration@example.com",
                "password": "mypassword123",
            },
        )
        assert login_resp.status_code == 200
        assert login_resp.json()["access_token"] == "test-access-token"

        # 3. Me endpoint with Authorization header
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer test-access-token"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "integration@example.com"
        assert me_resp.json()["id"] == str(user_id)


# ==============================================================================
# 12. Auth Import Compatibility Verification
# ==============================================================================

def test_auth_backward_compatibility_imports():
    # 1. Model import
    from app.features.auth.model import User as CompatUser
    from app.features.auth.infrastructure.persistence.models import User as CanonUser
    assert CompatUser is CanonUser

    # 2. Router import
    from app.features.auth.router import router as compat_router
    from app.features.auth.presentation.router import router as canon_router
    assert compat_router is canon_router

    # 3. Dependencies import
    from app.features.auth.dependencies import (
        get_current_user as compat_get_user,
        oauth2_scheme as compat_oauth,
        credentials_exception as compat_exc,
    )
    from app.features.auth.presentation.dependencies import (
        get_current_user as canon_get_user,
        oauth2_scheme as canon_oauth,
        credentials_exception as canon_exc,
    )
    assert compat_get_user is canon_get_user
    assert compat_oauth is canon_oauth
    assert compat_exc is canon_exc

    # 4. Schemas import
    from app.features.auth.schemas import (
        UserCreate as CompatUC,
        UserLogin as CompatUL,
        UserResponse as CompatUR,
        TokenResponse as CompatTR,
        AuthResponse as CompatAR,
    )
    from app.features.auth.presentation.schemas import (
        UserCreate as CanonUC,
        UserLogin as CanonUL,
        UserResponse as CanonUR,
        TokenResponse as CanonTR,
        AuthResponse as CanonAR,
    )
    assert CompatUC is CanonUC
    assert CompatUL is CanonUL
    assert CompatUR is CanonUR
    assert CompatTR is CanonTR
    assert CompatAR is CanonAR

    # 5. Service import
    from app.features.auth.service import (
        register_user,
        login_user,
        authenticate_user,
        get_user_by_id,
        get_user_by_email,
        AuthService as CompatAuthService,
    )
    assert callable(register_user)
    assert callable(login_user)
    assert callable(authenticate_user)
    assert callable(get_user_by_id)
    assert callable(get_user_by_email)
    assert CompatAuthService is AuthService


# ==============================================================================
# Alembic Model Discovery Verification
# ==============================================================================

def test_alembic_user_model_discovery():
    from app.features.auth.infrastructure.persistence.models import User
    from app.features.auth.model import User as LegacyUser

    assert User is LegacyUser
    assert User.__tablename__ == "users"

    table = Base.metadata.tables.get("users")
    assert table is not None

    expected_cols = {
        "id",
        "displayName",
        "email",
        "hashedPassword",
        "isDeleted",
        "createdAt",
        "updatedAt",
    }
    actual_cols = {col.name for col in table.columns}
    assert expected_cols.issubset(actual_cols)
