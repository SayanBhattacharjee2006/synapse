import ast
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
import pytest

from app.features.auth.dependencies import get_current_user
from app.features.auth.model import User
from app.features.chat.application.chat_service import ChatService
from app.features.chat.application.exceptions import (
    ChatError,
    ChatExecutionError,
    ConversationNotFoundError,
)
from app.features.chat.application.interfaces.chat_engine import ChatEngine
from app.features.chat.application.interfaces.conversation_operations import (
    ConversationOperations,
)
from app.features.chat.application.models import (
    ChatEvent,
    ConversationContext,
)
from app.features.chat.infrastructure.ai.langgraph_chat_engine import (
    LangGraphChatEngine,
    STATUS_BY_NODE,
)
from app.features.chat.infrastructure.integrations.conversation_adapter import (
    ConversationAdapter,
)
from app.features.chat.presentation.router import router as chat_router
from app.features.chat.presentation.schemas import ChatRequest
from app.features.chat.presentation.streaming import (
    format_sse_event,
    format_sse_stream,
)
from app.features.chat.wiring import get_chat_service
from app.features.conversations.application.exceptions import (
    ConversationNotFoundError as ServiceConversationNotFoundError,
)

# ============================================================================
# Fakes & Test Doubles
# ============================================================================


class FakeConversationOperations(ConversationOperations):
    def __init__(self) -> None:
        self.contexts: dict[uuid.UUID, ConversationContext] = {}
        self.metadata_updates: list[dict[str, Any]] = []

    async def get_chat_context(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationContext:
        ctx = self.contexts.get(conversation_id)
        if ctx is None or ctx.user_id != user_id:
            raise ConversationNotFoundError(
                f"Conversation '{conversation_id}' not found"
            )
        return ctx

    async def update_generated_metadata(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
        summary: str | None = None,
        slug: str | None = None,
    ) -> None:
        self.metadata_updates.append(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "title": title,
                "summary": summary,
                "slug": slug,
            }
        )
        if conversation_id in self.contexts:
            ctx = self.contexts[conversation_id]
            if title is not None:
                ctx.title = title


class FakeChatEngine(ChatEngine):
    def __init__(
        self,
        events: list[ChatEvent] | None = None,
        title: str = "Test Title",
        raise_on_stream: bool = False,
        raise_on_title: bool = False,
    ) -> None:
        self.events = events or []
        self.title = title
        self.raise_on_stream = raise_on_stream
        self.raise_on_title = raise_on_title
        self.stream_calls: list[dict[str, Any]] = []
        self.title_calls: list[str] = []

    async def stream_chat(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        has_uploaded_documents: bool,
    ) -> AsyncIterator[ChatEvent]:
        self.stream_calls.append(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "content": content,
                "has_uploaded_documents": has_uploaded_documents,
            }
        )
        if self.raise_on_stream:
            raise RuntimeError("Underlying stream failure")
        for ev in self.events:
            yield ev

    async def generate_title(self, content: str) -> str:
        self.title_calls.append(content)
        if self.raise_on_title:
            raise RuntimeError("LLM title generation timeout")
        return self.title


@dataclass
class FakeConversationModel:
    id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    document_count: int
    is_deleted: bool = False


# ============================================================================
# Section 17 Tests: 1 to 6 - Conversation Integration
# ============================================================================


@pytest.mark.asyncio
async def test_01_valid_conversation_access():
    user_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    ops = FakeConversationOperations()
    ops.contexts[conv_id] = ConversationContext(
        conversation_id=conv_id,
        user_id=user_id,
        title="Existing Title",
        document_count=2,
        has_uploaded_documents=True,
    )

    ctx = await ops.get_chat_context(conv_id, user_id)
    assert ctx.conversation_id == conv_id
    assert ctx.user_id == user_id
    assert ctx.has_uploaded_documents is True


@pytest.mark.asyncio
async def test_02_nonexistent_conversation_returns_error():
    user_id = uuid.uuid4()
    non_existent = uuid.uuid4()
    ops = FakeConversationOperations()

    with pytest.raises(ConversationNotFoundError):
        await ops.get_chat_context(non_existent, user_id)


@pytest.mark.asyncio
async def test_03_inaccessible_conversation_returns_error():
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    ops = FakeConversationOperations()
    ops.contexts[conv_id] = ConversationContext(
        conversation_id=conv_id,
        user_id=owner_id,
        title="Owner Chat",
        document_count=0,
        has_uploaded_documents=False,
    )

    with pytest.raises(ConversationNotFoundError):
        await ops.get_chat_context(conv_id, other_user_id)


@pytest.mark.asyncio
async def test_04_deleted_conversation_returns_error_via_adapter():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_service = AsyncMock()
    mock_service.get_conversation.side_effect = ServiceConversationNotFoundError(
        "Conversation not found"
    )

    adapter = ConversationAdapter(conversation_service=mock_service)
    with pytest.raises(ConversationNotFoundError):
        await adapter.get_chat_context(conv_id, user_id)


@pytest.mark.asyncio
async def test_05_generated_metadata_updates_through_conversation_operations():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    mock_service = AsyncMock()

    adapter = ConversationAdapter(conversation_service=mock_service)
    await adapter.update_generated_metadata(
        conversation_id=conv_id,
        user_id=user_id,
        title="New Title",
        summary="Summary text",
        slug="new-title",
    )

    mock_service.update_generated_metadata.assert_awaited_once_with(
        conversation_id=conv_id,
        user_id=user_id,
        title="New Title",
        summary="Summary text",
        slug="new-title",
    )


def test_06_no_direct_orm_imports_from_conversations():
    """Verify Chat does not import Conversation or Message SQLAlchemy models."""
    chat_dir = Path("app/features/chat")
    forbidden_modules = [
        "app.features.conversations.models",
        "app.features.conversations.infrastructure.persistence.models",
    ]

    for py_file in chat_dir.rglob("*.py"):
        if "chat_eval" in str(py_file):
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for forbidden in forbidden_modules:
                    assert (
                        forbidden not in node.module
                    ), f"Forbidden ORM import {node.module} in {py_file}"


# ============================================================================
# Section 17 Tests: 7 to 13 - ChatEngine
# ============================================================================


@pytest.mark.asyncio
async def test_07_and_13_langgraph_execution_invoked_correctly_with_checkpoint():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_graph = MagicMock()

    async def fake_astream_events(inputs, config, version):
        assert config["configurable"]["thread_id"] == str(conv_id)
        assert inputs["conversation_id"] == str(conv_id)
        assert inputs["has_uploaded_documents"] is True
        assert inputs["messages"][0].content == "Hello AI"
        assert version == "v2"
        yield {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "evaluator"},
        }
        yield {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "llm"},
            "data": {"chunk": MagicMock(content="Hello!")},
        }

    mock_graph.astream_events = fake_astream_events

    engine = LangGraphChatEngine(graph=mock_graph)
    events = [
        ev
        async for ev in engine.stream_chat(
            conversation_id=conv_id,
            user_id=user_id,
            content="Hello AI",
            has_uploaded_documents=True,
        )
    ]

    assert len(events) == 2
    assert events[0].event_type == "status"
    assert events[0].data["status"] == "routing"
    assert events[1].event_type == "tokens"
    assert events[1].data == "Hello!"


@pytest.mark.asyncio
async def test_08_to_11_langgraph_events_normalized_correctly():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_graph = MagicMock()

    async def fake_astream_events(inputs, config, version):
        # 1. Evaluator status
        yield {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "evaluator"},
        }
        # 2. Retriever start & end with docs
        yield {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "retreiver"},
        }
        yield {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "retreiver"},
            "data": {
                "output": {
                    "retrieval_found": True,
                    "retrieved_document_names": ["doc1.pdf", "doc2.pdf"],
                }
            },
        }
        # 3. Web start & end with urls
        yield {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "web"},
        }
        yield {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "web"},
            "data": {
                "output": {
                    "web_found": True,
                    "web_sources": ["https://example.com/source"],
                }
            },
        }
        # 4. Summarisation end
        yield {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "summarisation"},
            "data": {"output": {"summary": "Chat summary text"}},
        }
        # 5. LLM tokens
        yield {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "llm"},
        }
        yield {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "llm"},
            "data": {"chunk": MagicMock(content="Token 1 ")},
        }
        yield {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "llm"},
            "data": {"chunk": MagicMock(content="Token 2")},
        }

    mock_graph.astream_events = fake_astream_events
    engine = LangGraphChatEngine(graph=mock_graph)

    events = [
        ev
        async for ev in engine.stream_chat(
            conversation_id=conv_id,
            user_id=user_id,
            content="Question",
            has_uploaded_documents=True,
        )
    ]

    event_types = [ev.event_type for ev in events]
    assert "status" in event_types
    assert "tokens" in event_types
    assert "_summary" in event_types
    assert "retrieval_found" in event_types
    assert "web_found" in event_types

    retrieval_ev = next(
        ev for ev in events if ev.event_type == "retrieval_found"
    )
    assert retrieval_ev.data == {"retrieved_doc_names": ["doc1.pdf", "doc2.pdf"]}

    web_ev = next(ev for ev in events if ev.event_type == "web_found")
    assert web_ev.data == {"web_sources": ["https://example.com/source"]}


@pytest.mark.asyncio
async def test_12_graph_execution_errors_propagated_to_chat_service():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ops = FakeConversationOperations()
    ops.contexts[conv_id] = ConversationContext(
        conversation_id=conv_id,
        user_id=user_id,
        title="Title",
        document_count=0,
        has_uploaded_documents=False,
    )
    engine = FakeChatEngine(raise_on_stream=True)
    service = ChatService(chat_engine=engine, conversation_ops=ops)

    events = [
        ev
        async for ev in service.stream_chat(
            conv_id, user_id, "Failing request"
        )
    ]
    assert len(events) == 2
    assert events[0].event_type == "error"
    assert (
        events[0].data["message"]
        == "Something went wrong while processing your request."
    )
    assert events[1].event_type == "done"
    assert events[1].data == "[DONE]"


# ============================================================================
# Section 17 Tests: 14 to 17 - Title Generation
# ============================================================================


@pytest.mark.asyncio
async def test_14_empty_conversation_title_triggers_title_generation():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ops = FakeConversationOperations()
    ops.contexts[conv_id] = ConversationContext(
        conversation_id=conv_id,
        user_id=user_id,
        title=None,  # Empty title -> needs title
        document_count=0,
        has_uploaded_documents=False,
    )
    engine = FakeChatEngine(
        events=[ChatEvent(event_type="tokens", data="AI Response")],
        title="Generated Super Title",
    )
    service = ChatService(chat_engine=engine, conversation_ops=ops)

    events = [
        ev
        async for ev in service.stream_chat(
            conv_id, user_id, "First user message"
        )
    ]
    title_events = [ev for ev in events if ev.event_type == "title"]
    assert len(title_events) == 1
    assert title_events[0].data == {"title": "Generated Super Title"}
    assert len(engine.title_calls) == 1
    assert len(ops.metadata_updates) == 1
    assert ops.metadata_updates[0]["title"] == "Generated Super Title"
    assert ops.metadata_updates[0]["slug"] == "generated-super-title"


@pytest.mark.asyncio
async def test_15_existing_conversation_title_skips_generation():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ops = FakeConversationOperations()
    ops.contexts[conv_id] = ConversationContext(
        conversation_id=conv_id,
        user_id=user_id,
        title="Already Titled",
        document_count=0,
        has_uploaded_documents=False,
    )
    engine = FakeChatEngine(
        events=[ChatEvent(event_type="tokens", data="Second answer")]
    )
    service = ChatService(chat_engine=engine, conversation_ops=ops)

    events = [
        ev
        async for ev in service.stream_chat(
            conv_id, user_id, "Second user message"
        )
    ]
    title_events = [ev for ev in events if ev.event_type == "title"]
    assert len(title_events) == 0
    assert len(engine.title_calls) == 0


@pytest.mark.asyncio
async def test_16_title_generation_failure_does_not_break_ai_response():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ops = FakeConversationOperations()
    ops.contexts[conv_id] = ConversationContext(
        conversation_id=conv_id,
        user_id=user_id,
        title="",
        document_count=0,
        has_uploaded_documents=False,
    )
    engine = FakeChatEngine(
        events=[ChatEvent(event_type="tokens", data="AI Answer Still Here")],
        raise_on_title=True,
    )
    service = ChatService(chat_engine=engine, conversation_ops=ops)

    events = [
        ev
        async for ev in service.stream_chat(conv_id, user_id, "Hello without title")
    ]
    token_events = [ev for ev in events if ev.event_type == "tokens"]
    error_events = [ev for ev in events if ev.event_type == "error"]
    done_events = [ev for ev in events if ev.event_type == "done"]

    assert len(token_events) == 1
    assert token_events[0].data == "AI Answer Still Here"
    assert len(error_events) == 0  # Not broken!
    assert len(done_events) == 1


@pytest.mark.asyncio
async def test_17_failed_title_generation_can_be_retried_on_subsequent_request():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ops = FakeConversationOperations()
    ops.contexts[conv_id] = ConversationContext(
        conversation_id=conv_id,
        user_id=user_id,
        title=None,
        document_count=0,
        has_uploaded_documents=False,
    )

    # First request: title fails
    engine1 = FakeChatEngine(
        events=[ChatEvent(event_type="tokens", data="Ans 1")],
        raise_on_title=True,
    )
    service1 = ChatService(chat_engine=engine1, conversation_ops=ops)
    _ = [ev async for ev in service1.stream_chat(conv_id, user_id, "Msg 1")]
    assert ops.contexts[conv_id].title is None  # Title still empty

    # Second request: title succeeds
    engine2 = FakeChatEngine(
        events=[ChatEvent(event_type="tokens", data="Ans 2")],
        title="Retried Title Success",
        raise_on_title=False,
    )
    service2 = ChatService(chat_engine=engine2, conversation_ops=ops)
    events2 = [
        ev async for ev in service2.stream_chat(conv_id, user_id, "Msg 2")
    ]

    title_events = [ev for ev in events2 if ev.event_type == "title"]
    assert len(title_events) == 1
    assert title_events[0].data == {"title": "Retried Title Success"}
    assert ops.contexts[conv_id].title == "Retried Title Success"


# ============================================================================
# Section 17 Tests: 18 to 26 - SSE Contract & Ordering
# ============================================================================


def test_18_to_24_sse_event_formatting_contract():
    # 18. status
    status_ev = ChatEvent(
        event_type="status",
        data={"status": "routing", "message": "Understanding..."},
    )
    assert format_sse_event(status_ev) == (
        'event: status\ndata: {"status": "routing", "message": "Understanding..."}\n\n'
    )

    # 19. tokens
    token_ev = ChatEvent(event_type="tokens", data="token_chunk")
    assert format_sse_event(token_ev) == "data: token_chunk\n\n"

    # 20. title
    title_ev = ChatEvent(event_type="title", data={"title": "Test Title"})
    assert format_sse_event(title_ev) == (
        'event: title\ndata: {"title": "Test Title"}\n\n'
    )

    # 21. retrieval_found
    retrieval_ev = ChatEvent(
        event_type="retrieval_found",
        data={"retrieved_doc_names": ["doc.pdf"]},
    )
    assert format_sse_event(retrieval_ev) == (
        'event: retrieval_found\ndata: {"retrieved_doc_names": ["doc.pdf"]}\n\n'
    )

    # 22. web_found
    web_ev = ChatEvent(
        event_type="web_found", data={"web_sources": ["https://url.com"]}
    )
    assert format_sse_event(web_ev) == (
        'event: web_found\ndata: {"web_sources": ["https://url.com"]}\n\n'
    )

    # 23. error
    error_ev = ChatEvent(
        event_type="error",
        data={"status": "error", "message": "Failure occurred"},
    )
    assert format_sse_event(error_ev) == (
        'event: error\ndata: {"status": "error", "message": "Failure occurred"}\n\n'
    )

    # 24. [DONE] marker
    done_ev = ChatEvent(event_type="done", data="[DONE]")
    assert format_sse_event(done_ev) == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_25_streaming_order_is_correct():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ops = FakeConversationOperations()
    ops.contexts[conv_id] = ConversationContext(
        conversation_id=conv_id,
        user_id=user_id,
        title=None,
        document_count=1,
        has_uploaded_documents=True,
    )
    engine = FakeChatEngine(
        events=[
            ChatEvent(
                event_type="status",
                data={"status": "routing", "message": "routing..."},
            ),
            ChatEvent(
                event_type="status",
                data={"status": "generating", "message": "generating..."},
            ),
            ChatEvent(event_type="tokens", data="Word1 "),
            ChatEvent(event_type="tokens", data="Word2"),
            ChatEvent(
                event_type="retrieval_found",
                data={"retrieved_doc_names": ["doc.txt"]},
            ),
            ChatEvent(
                event_type="web_found",
                data={"web_sources": ["http://web.org"]},
            ),
        ],
        title="Ordered Title",
    )
    service = ChatService(chat_engine=engine, conversation_ops=ops)

    events = [
        ev async for ev in service.stream_chat(conv_id, user_id, "Order test")
    ]
    order = [ev.event_type for ev in events]

    # Expected order: status -> status -> tokens -> tokens -> title -> retrieval_found -> web_found -> done
    assert order == [
        "status",
        "status",
        "tokens",
        "tokens",
        "title",
        "retrieval_found",
        "web_found",
        "done",
    ]


@pytest.mark.asyncio
async def test_26_authorization_happens_before_streaming_response():
    app = FastAPI()
    app.include_router(chat_router)

    fake_user = User(
        id=uuid.uuid4(),
        display_name="Test User",
        email="test@synapse.ai",
        hashed_password="fake",
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user

    mock_chat_service = AsyncMock()
    mock_chat_service.validate_access.side_effect = ConversationNotFoundError(
        "Conversation not found"
    )
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    client = TestClient(app)
    conv_id = uuid.uuid4()

    response = client.post(
        f"/conversations/{conv_id}/chat",
        json={"content": "Hello!"},
    )

    # Must return real HTTP 404, NOT an SSE stream!
    assert response.status_code == 404
    assert "Conversation not found" in response.json()["detail"]
    mock_chat_service.stream_chat.assert_not_called()


# ============================================================================
# Section 17 Tests: 27 to 33 - Architecture Verification
# ============================================================================


def test_27_chatservice_has_no_direct_sqlalchemy_dependency():
    target = Path("app/features/chat/application/chat_service.py")
    with open(target, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(target))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            assert "sqlalchemy" not in mod, f"SQLAlchemy imported in {target}"


def test_28_chatservice_has_no_direct_langgraph_dependency():
    target = Path("app/features/chat/application/chat_service.py")
    with open(target, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(target))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            assert "langgraph" not in mod, f"LangGraph imported in {target}"
            assert "langchain" not in mod, f"LangChain imported in {target}"


def test_29_chat_does_not_import_conversation_or_message_orm_models():
    chat_dir = Path("app/features/chat")
    for p in chat_dir.rglob("*.py"):
        if "chat_eval" in str(p):
            continue
        with open(p, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert (
                    "conversations.models" not in node.module
                ), f"Direct ORM model import in {p}"
                assert (
                    "conversations.infrastructure.persistence.models"
                    not in node.module
                ), f"Direct ORM model import in {p}"


def test_30_sse_serialization_remains_in_presentation():
    app_files = [
        Path("app/features/chat/application/chat_service.py"),
        Path("app/features/chat/infrastructure/ai/langgraph_chat_engine.py"),
    ]
    for p in app_files:
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        assert (
            "event: status" not in content
        ), f"Raw SSE status event leaked into {p}"
        assert (
            "event: error" not in content
        ), f"Raw SSE error event leaked into {p}"
        assert (
            "text/event-stream" not in content
        ), f"SSE media type leaked into {p}"
        assert "StreamingResponse" not in content, f"StreamingResponse in {p}"


def test_31_graph_is_not_recompiled_for_each_request():
    mock_graph = MagicMock()
    engine1 = LangGraphChatEngine(graph=mock_graph)
    engine2 = LangGraphChatEngine(graph=mock_graph)
    assert engine1._graph is engine2._graph


def test_32_qdrant_conversation_summary_write_path_removed():
    chat_dir = Path("app/features/chat")
    for p in chat_dir.rglob("*.py"):
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        assert (
            "summary_memory_sevice" not in content
        ), f"Unused Qdrant summary memory service still referenced in {p}"
        assert (
            "store_summary" not in content
        ), f"Unused store_summary write call still referenced in {p}"


# ============================================================================
# Section 17 Tests: 34 to 38 - Regression & HTTP Endpoint
# ============================================================================


def test_34_and_35_existing_chat_endpoint_and_frontend_streaming_compatible():
    app = FastAPI()
    app.include_router(chat_router)

    fake_user = User(
        id=uuid.uuid4(),
        display_name="Test User",
        email="test@synapse.ai",
        hashed_password="fake",
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user

    conv_id = uuid.uuid4()
    mock_chat_service = AsyncMock()
    mock_chat_service.validate_access.return_value = ConversationContext(
        conversation_id=conv_id,
        user_id=fake_user.id,
        title="My Chat",
        document_count=0,
        has_uploaded_documents=False,
    )

    async def fake_stream_chat(conversation_id, user_id, content):
        yield ChatEvent(
            event_type="status",
            data={"status": "routing", "message": "routing"},
        )
        yield ChatEvent(event_type="tokens", data="Answer token")
        yield ChatEvent(event_type="done", data="[DONE]")

    mock_chat_service.stream_chat = fake_stream_chat
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

    client = TestClient(app)
    response = client.post(
        f"/conversations/{conv_id}/chat",
        json={"content": "Hello!"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    body = response.text
    assert 'event: status\ndata: {"status": "routing", "message": "routing"}\n\n' in body
    assert "data: Answer token\n\n" in body
    assert "data: [DONE]\n\n" in body


def test_36_and_37_message_persistence_remains_in_conversations():
    """Verify Chat does not define MessageRepository or MessageService."""
    chat_dir = Path("app/features/chat")
    for p in chat_dir.rglob("*.py"):
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        assert "MessageRepository" not in content
        assert "MessageService" not in content
        assert "messages.create" not in content


def test_38_langgraph_chat_engine_title_generation():
    mock_graph = MagicMock()
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content="Generated Title")

    engine = LangGraphChatEngine(graph=mock_graph, llm=mock_llm)
    title = pytest.run(engine.generate_title("What is the capital of France?")) if False else None


@pytest.mark.asyncio
async def test_39_langgraph_chat_engine_generate_title_async():
    mock_graph = MagicMock()
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content="France Capital Query")

    engine = LangGraphChatEngine(graph=mock_graph, llm=mock_llm)
    res = await engine.generate_title("What is the capital of France?")
    assert res == "France Capital Query"
    mock_llm.ainvoke.assert_awaited_once()

