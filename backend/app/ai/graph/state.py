from langgraph.graph import MessagesState


class GraphState(MessagesState):
    summary: str = ""
    last_summarised_msg_id: str | None
