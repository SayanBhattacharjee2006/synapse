class ConversationNotFoundError(Exception):
    """Raised when a conversation is not found, soft-deleted, or inaccessible to the user."""
    pass


class MessageNotFoundError(Exception):
    """Raised when a message is not found, soft-deleted, or inaccessible to the user."""
    pass

