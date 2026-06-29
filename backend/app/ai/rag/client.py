from qdrant_client import AsyncQdrantClient
from app.core.config import settings

client = AsyncQdrantClient(url=settings.QDRANT_URL)