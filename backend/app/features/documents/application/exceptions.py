class DocumentNotFoundError(Exception):
    """Raised when a document is not found, soft-deleted, or inaccessible to the user."""
    pass


class DocumentUploadInvalidError(Exception):
    """Raised when an upload request fails validation (extension, size, content type)."""
    pass


class DocumentProcessingError(Exception):
    """Raised when background processing of a document fails."""
    pass


class ObjectNotFoundError(Exception):
    """Raised when an object is not found in object storage."""
    pass


class ConversationAccessError(Exception):
    """Raised when conversation ownership or accessibility check fails."""
    pass

