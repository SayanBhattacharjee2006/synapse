from abc import ABC, abstractmethod
from typing import Any


class ObjectStorage(ABC):

    @abstractmethod
    async def generate_presigned_upload_url(
        self, key: str, content_type: str, expires_in: int = 900
    ) -> str:
        """Generate a presigned PUT URL for direct client upload."""
        raise NotImplementedError

    @abstractmethod
    async def get_object_metadata(self, key: str) -> dict[str, Any]:
        """Retrieve object metadata (HeadObject), returning size and content_type."""
        raise NotImplementedError

    @abstractmethod
    async def download_file(self, key: str, destination_path: str) -> str:
        """Download an S3 object to a local temporary path."""
        raise NotImplementedError

    @abstractmethod
    async def delete_object(self, key: str) -> None:
        """Delete an object from S3 idempotently (no error if absent)."""
        raise NotImplementedError

