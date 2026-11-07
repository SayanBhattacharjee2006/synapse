class ChatError(Exception):
    """Base exception for all chat domain errors."""

    pass


class ConversationNotFoundError(ChatError):
    """Raised when a requested conversation is not found, deleted, or inaccessible."""

    pass


class ChatExecutionError(ChatError):
    """Raised when an error occurs during chat engine execution."""

    pass

