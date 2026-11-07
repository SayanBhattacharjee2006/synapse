import json
from typing import AsyncIterator

from app.features.chat.application.models import ChatEvent


def format_sse_event(event: ChatEvent) -> str:
    """Format a normalized ChatEvent into an SSE string conforming to the frontend contract."""
    if event.event_type in ("tokens", "token"):
        token_str = (
            event.data
            if isinstance(event.data, str)
            else event.data.get("token", "")
        )
        return f"data: {token_str}\n\n"

    elif event.event_type == "done":
        marker = event.data if isinstance(event.data, str) else "[DONE]"
        return f"data: {marker}\n\n"

    elif event.event_type in (
        "status",
        "title",
        "retrieval_found",
        "web_found",
        "error",
    ):
        payload = (
            json.dumps(event.data)
            if not isinstance(event.data, str)
            else event.data
        )
        return f"event: {event.event_type}\ndata: {payload}\n\n"

    else:
        payload = (
            json.dumps(event.data)
            if isinstance(event.data, dict)
            else str(event.data)
        )
        return f"event: {event.event_type}\ndata: {payload}\n\n"


async def format_sse_stream(
    event_stream: AsyncIterator[ChatEvent],
) -> AsyncIterator[str]:
    """Asynchronously transform a stream of ChatEvents into SSE text chunks."""
    async for event in event_stream:
        yield format_sse_event(event)

