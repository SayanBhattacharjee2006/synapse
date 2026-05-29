from fastapi import FastAPI
from app.features.health.router import router as health_router
from app.features.conversations.router import router as conversation_router

app = FastAPI(
    title = "synapse",
    version = "0.1.0"
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")