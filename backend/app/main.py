from fastapi import FastAPI
from app.features.health.router import router as health_router
from app.features.conversations.router import router as conversation_router
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver # type: ignore
from app.core.config import settings
from app.ai.graph.graph import get_graph
from app.features.chat.router import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(str(settings.DATABASE_URL).replace("+asyncpg", "")) as checkpoint_saver:
        await checkpoint_saver.setup()
        app.state.graph = get_graph(checkpoint_saver)
        yield


app = FastAPI(
    title = "synapse",
    version = "0.1.0",
    lifespan=lifespan
)


app.include_router(health_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")