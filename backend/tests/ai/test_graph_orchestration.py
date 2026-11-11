from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
import pytest

from app.ai.graph.graph import get_graph
from app.ai.graph.nodes import (
    document_aware_web_query_optimizer_node,
    document_summary_retrieval_node,
    evaluator_node,
    full_context_builder_node,
    llm_node,
    retreive_context_node,
    route_after_document_summary,
    route_after_evaluation,
    summarisation_node,
    web_retreival_node,
)
from app.ai.graph.state import GraphState
from app.ai.schema import (
    DocumentAwareWebQuerySchema,
    DocumentSummarySchema,
    EvaluatorResponseSchema,
    RouterType,
)
from app.features.chat.infrastructure.ai.langgraph_chat_engine import (
    STATUS_BY_NODE,
)


def test_graph_node_registration_and_exact_names():
    """Verify that all required nodes are registered in the graph with exact names."""
    saver = MemorySaver()
    graph = get_graph(saver)

    expected_nodes = {
        "llm",
        "summarisation",
        "evaluator",
        "doc_summary_retrieval",
        "retreiver",
        "doc_aware_web_optimizer",
        "web",
        "full_context_builder",
    }

    graph_nodes = set(graph.nodes.keys())
    for node in expected_nodes:
        assert (
            node in graph_nodes
        ), f"Expected node '{node}' not found in compiled graph nodes: {graph_nodes}"


def test_route_after_evaluation_branches():
    """Verify conditional routing logic after query evaluation."""
    assert route_after_evaluation({"router": RouterType.RAG}) == [
        "doc_summary_retrieval"
    ]
    assert route_after_evaluation({"router": RouterType.WEB}) == ["web"]
    assert route_after_evaluation({"router": RouterType.BOTH}) == [
        "doc_summary_retrieval"
    ]
    assert route_after_evaluation({"router": RouterType.NONE}) == [
        "full_context_builder"
    ]


def test_route_after_document_summary_branches():
    """Verify conditional fan-out after document summary retrieval (including parallel execution)."""
    assert route_after_document_summary({"router": RouterType.RAG}) == [
        "retreiver"
    ]
    assert route_after_document_summary({"router": RouterType.BOTH}) == [
        "retreiver",
        "doc_aware_web_optimizer",
    ]


def test_graph_state_preserves_all_fields_and_defaults():
    """Verify GraphState preserves all expected attributes and types."""
    annotations = GraphState.__annotations__
    required_fields = [
        "summary",
        "last_summarised_msg_id",
        "conversation_id",
        "retrieved_context",
        "retrieval_found",
        "retrieved_document_names",
        "web_context",
        "web_sources",
        "web_found",
        "has_uploaded_documents",
        "router",
        "optimized_rag_query",
        "optimized_web_query",
        "document_summaries",
        "document_summary_found",
        "document_summary_names",
        "document_aware_web_query",
        "full_context",
    ]

    for field in required_fields:
        assert field in annotations, f"Field '{field}' missing from GraphState"


@pytest.mark.asyncio
async def test_evaluator_node_execution():
    state: GraphState = {
        "messages": [HumanMessage(content="What is quarterly revenue?")],
        "conversation_id": "conv-123",
        "has_uploaded_documents": True,
    }

    mock_response = EvaluatorResponseSchema(
        router=RouterType.RAG,
        rag_query="quarterly revenue 2026",
        web_query="quarterly revenue",
    )

    with patch("app.ai.graph.nodes.routing.router_llm") as mock_router_llm:
        mock_router_llm.ainvoke = AsyncMock(return_value=mock_response)
        result = await evaluator_node(state)

        assert result["router"] == RouterType.RAG
        assert result["optimized_rag_query"] == "quarterly revenue 2026"
        assert result["optimized_web_query"] == "quarterly revenue"
        mock_router_llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_summarisation_node_short_conversation():
    state: GraphState = {
        "messages": [
            HumanMessage(content="Short query"),
            AIMessage(content="Short response"),
        ],
        "conversation_id": "conv-123",
    }
    with patch(
        "app.ai.graph.nodes.conversation.count_tokens_approximately",
        return_value=150,
    ):
        result = await summarisation_node(state)
        assert result == {}


@pytest.mark.asyncio
async def test_summarisation_node_long_conversation():
    messages = [HumanMessage(content=f"Msg {i}", id=f"id-{i}") for i in range(15)]
    state: GraphState = {
        "messages": messages,
        "conversation_id": "conv-123",
        "summary": "Initial summary",
        "last_summarised_msg_id": None,
    }

    mock_summary_response = AIMessage(content="Updated summary text")
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_summary_response)

    with patch(
        "app.ai.graph.nodes.conversation.count_tokens_approximately",
        return_value=3000,
    ), patch("app.ai.graph.nodes.conversation.llm", mock_llm):
        result = await summarisation_node(state)
        assert result["summary"] == "Updated summary text"
        assert result["last_summarised_msg_id"] == "id-4"
        assert len(result["messages"]) == 5  # Removes messages older than last 10


@pytest.mark.asyncio
async def test_document_summary_retrieval_node():
    state: GraphState = {
        "messages": [HumanMessage(content="Doc question")],
        "optimized_rag_query": "Optimized doc question",
        "conversation_id": "conv-123",
    }

    mock_doc_summary = DocumentSummarySchema(
        document_id=uuid.uuid4(),
        conversation_id="conv-123",
        user_id=uuid.uuid4(),
        summary="Doc summary text",
        topics=["finance"],
        filename="report.pdf",
    )

    with patch(
        "app.ai.graph.nodes.document_retrieval.retrieve_document_summaries",
        new=AsyncMock(return_value=[mock_doc_summary]),
    ):
        result = await document_summary_retrieval_node(state)
        assert result["document_summary_found"] is True
        assert len(result["document_summaries"]) == 1
        assert result["document_summary_names"] == ["report.pdf"]


@pytest.mark.asyncio
async def test_retreive_context_node():
    state: GraphState = {
        "messages": [HumanMessage(content="Query")],
        "optimized_rag_query": "Optimized query",
        "document_summaries": [],
        "conversation_id": "conv-123",
    }

    with patch(
        "app.ai.graph.nodes.document_retrieval.retreive_context",
        new=AsyncMock(
            return_value=("Retrieved context body", True, ["report.pdf"])
        ),
    ):
        result = await retreive_context_node(state)
        assert result["retrieved_context"] == "Retrieved context body"
        assert result["retrieval_found"] is True
        assert result["retrieved_document_names"] == ["report.pdf"]
        assert result["retieved_document_names"] == ["report.pdf"]


@pytest.mark.asyncio
async def test_document_aware_web_query_optimizer_node_passthrough():
    state: GraphState = {
        "messages": [HumanMessage(content="Search query")],
        "optimized_web_query": "web query",
        "document_summaries": [],
        "conversation_id": "conv-123",
    }

    result = await document_aware_web_query_optimizer_node(state)
    assert result == {"document_aware_web_query": "web query"}


@pytest.mark.asyncio
async def test_document_aware_web_query_optimizer_node_with_summaries():
    mock_doc_summary = DocumentSummarySchema(
        document_id=uuid.uuid4(),
        conversation_id="conv-123",
        user_id=uuid.uuid4(),
        summary="Quarterly figures",
        topics=["finance"],
        filename="q1.pdf",
    )
    state: GraphState = {
        "messages": [HumanMessage(content="Search query")],
        "optimized_web_query": "q1 revenue",
        "document_summaries": [mock_doc_summary],
        "conversation_id": "conv-123",
    }

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(
        return_value=DocumentAwareWebQuerySchema(
            web_query="q1 revenue company comparison"
        )
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm

    with patch("app.ai.graph.nodes.web_retrieval.llm", mock_llm):
        result = await document_aware_web_query_optimizer_node(state)
        assert (
            result["document_aware_web_query"]
            == "q1 revenue company comparison"
        )


@pytest.mark.asyncio
async def test_web_retreival_node():
    state: GraphState = {
        "messages": [HumanMessage(content="Search query")],
        "document_aware_web_query": "refined query",
        "conversation_id": "conv-123",
    }

    mock_search_res = {
        "results": [{"url": "https://example.com/source", "content": "Sample"}]
    }

    with patch(
        "app.ai.graph.nodes.web_retrieval.search_tavily",
        new=AsyncMock(return_value=mock_search_res),
    ), patch(
        "app.ai.graph.nodes.web_retrieval.create_search_response",
        return_value="Formatted search summary",
    ):
        result = await web_retreival_node(state)
        assert result["web_context"] == "Formatted search summary"
        assert result["web_found"] is True
        assert result["web_sources"] == ["https://example.com/source"]


@pytest.mark.asyncio
async def test_full_context_builder_node_variants():
    # 1. NONE
    res_none = await full_context_builder_node(
        {"router": RouterType.NONE, "conversation_id": "1"}
    )
    assert res_none == {"full_context": ""}

    # 2. RAG
    res_rag = await full_context_builder_node(
        {
            "router": RouterType.RAG,
            "retrieved_context": "Doc context",
            "conversation_id": "1",
        }
    )
    assert res_rag == {
        "full_context": "DOCUMENT KNOWLEDGE BASE:\nDoc context"
    }

    # 3. WEB
    res_web = await full_context_builder_node(
        {
            "router": RouterType.WEB,
            "web_context": "Web context",
            "conversation_id": "1",
        }
    )
    assert res_web == {"full_context": "WEB KNOWLEDGE BASE:\nWeb context"}

    # 4. BOTH
    res_both = await full_context_builder_node(
        {
            "router": RouterType.BOTH,
            "retrieved_context": "Doc context",
            "web_context": "Web context",
            "conversation_id": "1",
        }
    )
    assert (
        "DOCUMENT KNOWLEDGE BASE:\nDoc context\n\nWEB KNOWLEDGE BASE:\nWeb context"
        in res_both["full_context"]
    )


@pytest.mark.asyncio
async def test_llm_node():
    state: GraphState = {
        "messages": [HumanMessage(content="Hello AI")],
        "summary": "Previous summary",
        "full_context": "Context information",
        "router": RouterType.RAG,
        "conversation_id": "conv-123",
    }

    mock_ai_response = AIMessage(content="Generated answer")
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_ai_response)

    with patch("app.ai.graph.nodes.context.llm", mock_llm):
        result = await llm_node(state)
        assert result["messages"] == [mock_ai_response]


def test_chat_module_status_by_node_matches_graph_nodes():
    """Verify that all node names in Chat's STATUS_BY_NODE exist in the graph (except virtual 'error')."""
    saver = MemorySaver()
    graph = get_graph(saver)
    graph_node_names = set(graph.nodes.keys())

    for node_name in STATUS_BY_NODE.keys():
        if node_name == "error":
            continue
        assert (
            node_name in graph_node_names
        ), f"STATUS_BY_NODE expects node '{node_name}' which is not in graph nodes: {graph_node_names}"
