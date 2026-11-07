from abc import ABC, abstractmethod
import uuid


class DocumentKnowledgePipeline(ABC):

    @abstractmethod
    async def process_document_knowledge(
        self,
        document_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
    ) -> None:
        """Process document chunks, ingest vector embeddings, and generate summaries in Qdrant."""
        raise NotImplementedError

    @abstractmethod
    async def delete_document_knowledge(
        self, document_id: uuid.UUID
    ) -> None:
        """Delete all indexed chunks and summary vectors associated with a document from Qdrant."""
        raise NotImplementedError

