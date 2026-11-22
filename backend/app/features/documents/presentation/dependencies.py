from app.features.auth.presentation.dependencies import get_current_user
from app.features.documents.wiring import (
    get_document_processing_service,
    get_document_service,
)

__all__ = [
    "get_current_user",
    "get_document_service",
    "get_document_processing_service",
]

