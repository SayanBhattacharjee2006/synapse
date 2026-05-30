from langgraph.graph import END, START, StateGraph
from app.ai.graph.state import GraphState
from app.ai.graph.nodes import llm_node


def get_graph(postgresCheckpointer):
    builder = StateGraph(GraphState)
    builder.add_node("llm", llm_node)
    builder.add_edge(START, "llm")
    builder.add_edge("llm", END)
    graph = builder.compile(checkpointer=postgresCheckpointer)
    return graph