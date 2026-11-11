from abc import ABC, abstractmethod
import uuid

from app.contracts.document_profile import DocumentProfile


class DocumentKnowledgePipeline(ABC):

    @abstractmethod
    async def process_document_knowledge(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
    ) -> DocumentProfile:
        """Process document chunks, ingest vector embeddings, and return generated DocumentProfile."""
        raise NotImplementedError

    @abstractmethod
    async def delete_document_knowledge(
        self, document_id: uuid.UUID
    ) -> None:
        """Delete all indexed chunks and summary vectors associated with a document from Qdrant.

        Must propagate errors if deletion fails.
        """
        raise NotImplementedError
