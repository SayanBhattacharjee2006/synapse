from langchain_core.messages import AIMessage, HumanMessage

def get_system_prompt(summary: str | None) -> str:
    base_prompt ="""You are Synapse, a helpful, knowledgeable AI assistant.
You are clear, concise, and direct in your responses.
You adapt your tone to the user — technical when needed, conversational when appropriate.
You never make up facts. If you don't know something, you say so honestly."""
    
    if not summary:
        return base_prompt
    return f"{base_prompt}\n\nconversation summary:{summary}"


def get_summariser_prompt(summary: str, messages: list[AIMessage | HumanMessage]) -> str:
    return f"""You are a conversation summarizer.You summarize the conversation of the user with the ai assistant using the existing conversation summary and current messages.

    existing conversation summary: {summary}
    messages: {messages}"""

