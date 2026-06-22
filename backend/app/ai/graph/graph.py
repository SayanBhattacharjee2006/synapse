from langgraph.graph import END, START, StateGraph
from app.ai.graph.state import GraphState
from app.ai.graph.nodes import (
    llm_node,
    summarisation_node,
    retreive_context_node,
    evaluator_node,
    route_after_evaluation,
    web_retrieval_node,
)


def get_graph(postgresCheckpointer):
    builder = StateGraph(GraphState)
    builder.add_node("llm", llm_node)
    builder.add_node("summarisation", summarisation_node)
    builder.add_node("retreiver", retreive_context_node)
    builder.add_node("evaluator", evaluator_node)
    builder.add_node("web", web_retrieval_node)

    
    builder.add_edge(START, "summarisation")
    builder.add_edge("summarisation", "evaluator")
    builder.add_conditional_edges(
        "evaluator", route_after_evaluation, ["retreiver", "web", "llm"]
    )
    builder.add_edge("retreiver", "llm")
    builder.add_edge("web", "llm")
    builder.add_edge("llm", END)

    graph = builder.compile(checkpointer=postgresCheckpointer)
    return graph
