import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

from app.core.database import Base
from app.features.auth.infrastructure.persistence.models import User
from app.features.auth.presentation.dependencies import get_current_user
from app.features.conversations.application.conversation_service import (
    ConversationService,
)
from app.features.conversations.application.enums import SenderEnum
from app.features.conversations.application.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
)
from app.features.conversations.application.interfaces.conversation_repository import (
    ConversationRepository,
)
from app.features.conversations.application.interfaces.message_repository import (
    MessageRepository,
)
from app.features.conversations.application.interfaces.unit_of_work import (
    ConversationsUnitOfWork,
)
from app.features.conversations.application.message_service import (
    MessageService,
)
from app.features.conversations.infrastructure.persistence.models import (
    Conversation,
    Message,
)
from app.features.conversations.infrastructure.persistence.sqlalchemy_conversation_repository import (
    SQLAlchemyConversationRepository,
)
from app.features.conversations.infrastructure.persistence.sqlalchemy_message_repository import (
    SQLAlchemyMessageRepository,
)
from app.features.conversations.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyConversationsUnitOfWork,
)
from app.features.conversations.presentation.router import (
    router as conversation_router,
)
from app.features.conversations.presentation.schemas import (
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.features.conversations.wiring import (
    get_conversation_service,
    get_message_service,
)


# ==============================================================================
# Helper Factories
# ==============================================================================

def make_test_user(user_id: uuid.UUID | None = None) -> User:
    return User(
        id=user_id or uuid.uuid4(),
        email="testuser@example.com",
        display_name="Test User",
        hashed_password="hashed_pw",
        is_deleted=False,
    )


def make_test_conversation(
    conversation_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    title: str = "Test Conversation",
    is_deleted: bool = False,
) -> Conversation:
    cid = conversation_id or uuid.uuid4()
    now = datetime.now(timezone.utc)
    return Conversation(
        id=cid,
        user_id=user_id or uuid.uuid4(),
        slug=str(cid),
        title=title,
        summary=None,
        is_deleted=is_deleted,
        created_at=now,
        updated_at=now,
        document_count=0,
    )


def make_test_message(
    message_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
    content: str = "Hello test",
    sender: SenderEnum = SenderEnum.user,
    is_deleted: bool = False,
) -> Message:
    return Message(
        id=message_id or uuid.uuid4(),
        conversation_id=conversation_id or uuid.uuid4(),
        content=content,
        sender=sender,
        is_deleted=is_deleted,
        created_at=datetime.now(timezone.utc),
    )


# ==============================================================================
# 1-6. Conversation Operations
# ==============================================================================

@pytest.mark.asyncio
async def test_conversation_service_create_conversation():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)

    async def fake_create(conv):
        conv.created_at = datetime.now(timezone.utc)
        conv.updated_at = datetime.now(timezone.utc)
        return conv

    uow.conversations.create.side_effect = fake_create

    service = ConversationService(uow=uow)
    user_id = uuid.uuid4()

    conv = await service.create_conversation(user_id)

    assert conv.user_id == user_id
    assert conv.slug == str(conv.id)
    uow.conversations.create.assert_awaited_once()
    uow.commit.assert_awaited_once()
    uow.refresh.assert_awaited_once_with(conv)


@pytest.mark.asyncio
async def test_conversation_service_get_conversation():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    uow.conversations.get_by_id_and_user.return_value = convo

    service = ConversationService(uow=uow)
    result = await service.get_conversation(convo.id, user_id)

    assert result == convo
    uow.conversations.get_by_id_and_user.assert_awaited_once_with(convo.id, user_id)


@pytest.mark.asyncio
async def test_conversation_service_list_conversations():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)

    user_id = uuid.uuid4()
    conv1 = make_test_conversation(user_id=user_id, title="Conv 1")
    conv2 = make_test_conversation(user_id=user_id, title="Conv 2")
    uow.conversations.list_by_user.return_value = [conv2, conv1]

    service = ConversationService(uow=uow)
    results = await service.list_conversations(user_id)

    assert len(results) == 2
    assert results == [conv2, conv1]
    uow.conversations.list_by_user.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_conversation_service_rename_conversation():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id, title="Old Title")
    uow.conversations.get_by_id_and_user.return_value = convo

    service = ConversationService(uow=uow)
    update_data = ConversationUpdate(title="New Title")

    updated = await service.update_conversation(convo.id, user_id, update_data)

    assert updated.title == "New Title"
    uow.commit.assert_awaited_once()
    uow.refresh.assert_awaited_once_with(convo)


@pytest.mark.asyncio
async def test_conversation_service_delete_conversation():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)
    uow.__aenter__.return_value = uow

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    uow.conversations.get_by_id_and_user.return_value = convo

    service = ConversationService(uow=uow)
    deleted = await service.delete_conversation(convo.id, user_id)

    uow.conversations.soft_delete.assert_awaited_once_with(convo)
    uow.messages.soft_delete_by_conversation.assert_awaited_once_with(convo.id)
    uow.commit.assert_awaited_once()
    uow.refresh.assert_awaited_once_with(convo)


@pytest.mark.asyncio
async def test_conversation_service_user_ownership_validation():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)

    # Return None simulating wrong owner or non-existent conversation
    uow.conversations.get_by_id_and_user.return_value = None

    service = ConversationService(uow=uow)
    user_id = uuid.uuid4()
    other_convo_id = uuid.uuid4()

    with pytest.raises(ConversationNotFoundError):
        await service.get_conversation(other_convo_id, user_id)

    with pytest.raises(ConversationNotFoundError):
        await service.update_conversation(
            other_convo_id, user_id, ConversationUpdate(title="Hacked")
        )

    with pytest.raises(ConversationNotFoundError):
        await service.delete_conversation(other_convo_id, user_id)


# ==============================================================================
# 7-14. Message Operations
# ==============================================================================

@pytest.mark.asyncio
async def test_message_service_create_user_message():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    uow.conversations.get_by_id_and_user.return_value = convo

    async def fake_create(msg):
        msg.id = uuid.uuid4()
        msg.created_at = datetime.now(timezone.utc)
        return msg

    uow.messages.create.side_effect = fake_create

    service = MessageService(uow=uow)
    data = MessageCreate(content="Hello from user", sender=SenderEnum.user)

    msg = await service.create_message(convo.id, user_id, data)

    assert msg.content == "Hello from user"
    assert msg.sender == SenderEnum.user
    assert msg.conversation_id == convo.id
    uow.messages.create.assert_awaited_once()
    uow.commit.assert_awaited_once()
    uow.refresh.assert_awaited_once_with(msg)


@pytest.mark.asyncio
async def test_message_service_create_assistant_message():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    uow.conversations.get_by_id_and_user.return_value = convo

    async def fake_create(msg):
        msg.id = uuid.uuid4()
        msg.created_at = datetime.now(timezone.utc)
        return msg

    uow.messages.create.side_effect = fake_create

    service = MessageService(uow=uow)
    data = MessageCreate(content="Hello from AI", sender=SenderEnum.assistant)

    msg = await service.create_message(convo.id, user_id, data)

    assert msg.content == "Hello from AI"
    assert msg.sender == SenderEnum.assistant
    assert msg.conversation_id == convo.id
    uow.messages.create.assert_awaited_once()
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_message_service_get_messages():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    uow.conversations.get_by_id_and_user.return_value = convo

    msg1 = make_test_message(conversation_id=convo.id, content="First", sender=SenderEnum.user)
    msg2 = make_test_message(conversation_id=convo.id, content="Second", sender=SenderEnum.assistant)
    uow.messages.list_by_conversation.return_value = [msg1, msg2]

    service = MessageService(uow=uow)
    messages = await service.get_messages(convo.id, user_id)

    assert len(messages) == 2
    assert messages == [msg1, msg2]
    uow.conversations.get_by_id_and_user.assert_awaited_once_with(convo.id, user_id)
    uow.messages.list_by_conversation.assert_awaited_once_with(convo.id)


@pytest.mark.asyncio
async def test_message_service_delete_message():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    uow.conversations.get_by_id_and_user.return_value = convo

    msg = make_test_message(conversation_id=convo.id)
    uow.messages.get_by_id_and_conversation.return_value = msg

    service = MessageService(uow=uow)
    deleted = await service.delete_message(msg.id, convo.id, user_id)

    assert deleted == msg
    uow.messages.soft_delete.assert_awaited_once_with(msg)
    uow.commit.assert_awaited_once()
    uow.refresh.assert_awaited_once_with(msg)


@pytest.mark.asyncio
async def test_message_service_reject_access_to_another_user_conversation():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)

    # Another user's conversation (returns None for requesting user)
    uow.conversations.get_by_id_and_user.return_value = None

    service = MessageService(uow=uow)
    user_id = uuid.uuid4()
    other_convo_id = uuid.uuid4()

    with pytest.raises(ConversationNotFoundError):
        await service.get_messages(other_convo_id, user_id)

    with pytest.raises(ConversationNotFoundError):
        await service.create_message(
            other_convo_id,
            user_id,
            MessageCreate(content="hi", sender=SenderEnum.user),
        )

    with pytest.raises(ConversationNotFoundError):
        await service.delete_message(uuid.uuid4(), other_convo_id, user_id)

    # Repository list_by_conversation must NOT be called
    uow.messages.list_by_conversation.assert_not_called()


@pytest.mark.asyncio
async def test_message_service_nonexistent_or_deleted_conversation_raises_404_semantics():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)

    uow.conversations.get_by_id_and_user.return_value = None

    service = MessageService(uow=uow)

    # 12. Nonexistent conversation
    with pytest.raises(ConversationNotFoundError):
        await service.get_messages(uuid.uuid4(), uuid.uuid4())

    # 13. Soft-deleted conversation (repository filters is_deleted == False, returning None)
    with pytest.raises(ConversationNotFoundError):
        await service.get_messages(uuid.uuid4(), uuid.uuid4())

    # 14. Inaccessible conversation (does not leak existence, raises ConversationNotFoundError)
    with pytest.raises(ConversationNotFoundError):
        await service.get_messages(uuid.uuid4(), uuid.uuid4())


# ==============================================================================
# 15-17. Transaction Management
# ==============================================================================

@pytest.mark.asyncio
async def test_transaction_delete_conversation_and_messages_commit_together():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)
    uow.__aenter__.return_value = uow

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    uow.conversations.get_by_id_and_user.return_value = convo

    service = ConversationService(uow=uow)
    await service.delete_conversation(convo.id, user_id)

    # Both soft-deletes called
    uow.conversations.soft_delete.assert_awaited_once_with(convo)
    uow.messages.soft_delete_by_conversation.assert_awaited_once_with(convo.id)
    # Committed together in UoW context
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_transaction_failure_during_deletion_rolls_back_both():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)
    uow.messages = AsyncMock(spec=MessageRepository)
    uow.__aenter__.return_value = uow
    # Commit fails
    uow.commit.side_effect = Exception("DB error on commit")

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    uow.conversations.get_by_id_and_user.return_value = convo

    service = ConversationService(uow=uow)

    with pytest.raises(Exception) as exc_info:
        await service.delete_conversation(convo.id, user_id)

    assert "DB error on commit" in str(exc_info.value)
    uow.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_repositories_do_not_independently_commit():
    session = AsyncMock()
    session.add = MagicMock()

    conv_repo = SQLAlchemyConversationRepository(session)
    msg_repo = SQLAlchemyMessageRepository(session)

    convo = make_test_conversation()
    msg = make_test_message()

    # Call repository write operations
    await conv_repo.create(convo)
    await conv_repo.soft_delete(convo)
    await msg_repo.create(msg)
    await msg_repo.soft_delete(msg)

    # Verify session.commit was NEVER called by repositories
    assert session.commit.call_count == 0


@pytest.mark.asyncio
async def test_unit_of_work_context_manager_rollback_on_failure():
    session = AsyncMock()
    uow = SQLAlchemyConversationsUnitOfWork(session)

    with pytest.raises(RuntimeError):
        async with uow:
            raise RuntimeError("Transaction failure")

    session.rollback.assert_awaited_once()


# ==============================================================================
# 18-20. Compatibility Verification
# ==============================================================================

def test_compatibility_existing_imports():
    # 1. Models import
    from app.features.conversations.models import (
        Conversation as CompatConv,
        Message as CompatMsg,
        SenderEnum as CompatSender,
    )
    from app.features.conversations.infrastructure.persistence.models import (
        Conversation as CanonConv,
        Message as CanonMsg,
    )
    from app.features.conversations.application.enums import (
        SenderEnum as CanonSender,
    )

    assert CompatConv is CanonConv
    assert CompatMsg is CanonMsg
    assert CompatSender is CanonSender

    # 2. Schemas import
    from app.features.conversations.schemas import (
        ConversationCreate,
        ConversationResponse,
        ConversationUpdate,
        MessageCreate,
        MessageResponse,
        SenderEnum,
    )
    assert SenderEnum is CanonSender

    # 3. Router import
    from app.features.conversations.router import router as compat_router
    from app.features.conversations.presentation.router import router as canon_router
    assert compat_router is canon_router

    # 4. Service functions import
    from app.features.conversations.service import (
        create_conversations,
        create_message,
        delete_conversation,
        delete_message,
        get_all_conversations,
        get_conversation_by_id,
        get_messages,
        update_conversations,
    )
    assert callable(create_conversations)
    assert callable(create_message)
    assert callable(delete_conversation)
    assert callable(delete_message)
    assert callable(get_all_conversations)
    assert callable(get_conversation_by_id)
    assert callable(get_messages)
    assert callable(update_conversations)


def test_alembic_model_discovery():
    from app.features.conversations.infrastructure.persistence.models import (
        Conversation,
        Message,
    )

    assert Conversation.__tablename__ == "conversations"
    assert Message.__tablename__ == "messages"

    assert "conversations" in Base.metadata.tables
    assert "messages" in Base.metadata.tables

    conv_cols = set(Base.metadata.tables["conversations"].columns.keys())
    expected_conv_cols = {
        "id",
        "user_id",
        "slug",
        "title",
        "summary",
        "isDeleted",
        "createdAt",
        "updatedAt",
        "documentCount",
    }
    assert expected_conv_cols.issubset(conv_cols)

    msg_cols = set(Base.metadata.tables["messages"].columns.keys())
    expected_msg_cols = {
        "id",
        "content",
        "sender",
        "conversation_id",
        "isDeleted",
        "createdAt",
    }
    assert expected_msg_cols.issubset(msg_cols)


def test_auth_imports_remain_functional():
    from app.features.auth.model import User
    from app.features.auth.dependencies import get_current_user

    assert hasattr(User, "conversations")
    assert callable(get_current_user)


# ==============================================================================
# Cross-Module Operations (Chat & Documents Helpers)
# ==============================================================================

@pytest.mark.asyncio
async def test_cross_module_operations():
    uow = AsyncMock(spec=ConversationsUnitOfWork)
    uow.conversations = AsyncMock(spec=ConversationRepository)

    user_id = uuid.uuid4()
    convo = make_test_conversation(user_id=user_id)
    convo.document_count = 1
    uow.conversations.get_by_id_and_user.return_value = convo

    service = ConversationService(uow=uow)

    # 1. Update generated metadata (Chat)
    updated_meta = await service.update_generated_metadata(
        convo.id, user_id, title="Generated Title", summary="Summary", slug="gen-title"
    )
    assert updated_meta.title == "Generated Title"
    assert updated_meta.summary == "Summary"
    assert updated_meta.slug == "gen-title"

    # 2. Adjust document count (Documents)
    updated_doc_inc = await service.adjust_document_count(convo.id, user_id, delta=1)
    assert updated_doc_inc.document_count == 2

    updated_doc_dec = await service.adjust_document_count(convo.id, user_id, delta=-5)
    assert updated_doc_dec.document_count == 0  # non-negative


# ==============================================================================
# HTTP Presentation Routes (FastAPI TestClient with DI)
# ==============================================================================

@pytest.mark.asyncio
async def test_conversations_router_http_endpoints():
    app = FastAPI()
    app.include_router(conversation_router, prefix="/api/v1")

    user_id = uuid.uuid4()
    test_user = make_test_user(user_id=user_id)

    mock_conv_service = AsyncMock(spec=ConversationService)
    mock_msg_service = AsyncMock(spec=MessageService)

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_conversation_service] = lambda: mock_conv_service
    app.dependency_overrides[get_message_service] = lambda: mock_msg_service

    convo = make_test_conversation(user_id=user_id)
    msg = make_test_message(conversation_id=convo.id)

    mock_conv_service.list_conversations.return_value = [convo]
    mock_conv_service.get_conversation.return_value = convo
    mock_conv_service.create_conversation.return_value = convo
    mock_conv_service.update_conversation.return_value = convo
    mock_conv_service.delete_conversation.return_value = convo

    mock_msg_service.get_messages.return_value = [msg]
    mock_msg_service.create_message.return_value = msg
    mock_msg_service.delete_message.return_value = msg

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. GET /conversations
        resp = await client.get("/api/v1/conversations/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 2. POST /conversations
        resp = await client.post("/api/v1/conversations/", json={})
        assert resp.status_code == 201

        # 3. GET /conversations/{id}
        resp = await client.get(f"/api/v1/conversations/{convo.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(convo.id)

        # 4. PATCH /conversations/{id}
        resp = await client.patch(
            f"/api/v1/conversations/{convo.id}", json={"title": "Patched"}
        )
        assert resp.status_code == 200

        # 5. DELETE /conversations/{id}
        resp = await client.delete(f"/api/v1/conversations/{convo.id}")
        assert resp.status_code == 204

        # 6. GET /conversations/{id}/messages
        resp = await client.get(f"/api/v1/conversations/{convo.id}/messages")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 7. POST /conversations/{id}/messages
        resp = await client.post(
            f"/api/v1/conversations/{convo.id}/messages",
            json={"content": "hello", "sender": "user"},
        )
        assert resp.status_code == 201

        # 8. DELETE /conversations/{id}/messages/{msg_id}
        resp = await client.delete(
            f"/api/v1/conversations/{convo.id}/messages/{msg.id}"
        )
        assert resp.status_code == 204


@pytest.mark.asyncio
async def test_conversations_router_404_handling():
    app = FastAPI()
    app.include_router(conversation_router, prefix="/api/v1")

    user_id = uuid.uuid4()
    test_user = make_test_user(user_id=user_id)

    mock_conv_service = AsyncMock(spec=ConversationService)
    mock_msg_service = AsyncMock(spec=MessageService)

    mock_conv_service.get_conversation.side_effect = ConversationNotFoundError("Conversation not found")
    mock_msg_service.get_messages.side_effect = ConversationNotFoundError("Conversation not found")
    mock_msg_service.delete_message.side_effect = MessageNotFoundError("Message not found")

    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_conversation_service] = lambda: mock_conv_service
    app.dependency_overrides[get_message_service] = lambda: mock_msg_service

    random_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # GET missing convo -> 404
        resp = await client.get(f"/api/v1/conversations/{random_id}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Conversation not found"

        # GET messages for missing convo -> 404
        resp = await client.get(f"/api/v1/conversations/{random_id}/messages")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Conversation not found"

        # DELETE missing message -> 404
        resp = await client.delete(
            f"/api/v1/conversations/{random_id}/messages/{uuid.uuid4()}"
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Message not found"

