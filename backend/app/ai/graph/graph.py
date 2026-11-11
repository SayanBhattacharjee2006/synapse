from langgraph.graph import END, START, StateGraph

from app.ai.graph.nodes.context import (
    full_context_builder_node,
    llm_node,
)
from app.ai.graph.nodes.conversation import (
    summarisation_node,
)
from app.ai.graph.nodes.document_retrieval import (
    document_summary_retrieval_node,
    retreive_context_node,
)
from app.ai.graph.nodes.routing import (
    evaluator_node,
    route_after_document_summary,
    route_after_evaluation,
)
from app.ai.graph.nodes.web_retrieval import (
    document_aware_web_query_optimizer_node,
    web_retreival_node,
)
from app.ai.graph.state import GraphState


def get_graph(postgresCheckpointer):
    builder = StateGraph(GraphState)

    # Nodes
    builder.add_node("llm", llm_node)
    builder.add_node("summarisation", summarisation_node)
    builder.add_node("evaluator", evaluator_node)
    builder.add_node("doc_summary_retrieval", document_summary_retrieval_node)
    builder.add_node("retreiver", retreive_context_node)
    builder.add_node(
        "doc_aware_web_optimizer", document_aware_web_query_optimizer_node
    )
    builder.add_node("web", web_retreival_node)
    builder.add_node(
        "full_context_builder", full_context_builder_node, defer=True
    )

    # Linear: START → summarisation → evaluator
    builder.add_edge(START, "summarisation")
    builder.add_edge("summarisation", "evaluator")

    # First conditional fan-out after evaluator:
    #   RAG  → doc_summary_retrieval
    #   WEB  → web
    #   BOTH → doc_summary_retrieval
    #   NONE → full_context_builder
    builder.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        ["doc_summary_retrieval", "web", "full_context_builder"],
    )

    # Second conditional fan-out after document summary retrieval:
    #   RAG  → retreiver
    #   BOTH → retreiver + doc_aware_web_optimizer (parallel)
    builder.add_conditional_edges(
        "doc_summary_retrieval",
        route_after_document_summary,
        ["retreiver", "doc_aware_web_optimizer"],
    )

    # Linear: doc_aware_web_optimizer → web
    builder.add_edge("doc_aware_web_optimizer", "web")

    # Convergence: both retrieval paths feed into full_context_builder
    builder.add_edge("retreiver", "full_context_builder")
    builder.add_edge("web", "full_context_builder")

    # Final: full_context_builder → llm → END
    builder.add_edge("full_context_builder", "llm")
    builder.add_edge("llm", END)

    graph = builder.compile(checkpointer=postgresCheckpointer)
    return graph
