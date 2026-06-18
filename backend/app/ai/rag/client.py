from qdrant_client import QdrantClient
from app.core.config import settings
client = QdrantClient(url=settings.QDRANT_URL)