from fastapi import FastAPI
from app.features.health.router import router as health_router

app = FastAPI(
    title = "synapse",
    version = "0.1.0"
)

app.include_router(health_router, prefix="/api/v1")