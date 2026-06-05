from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.agents import router as agents_router


app = FastAPI(
    title="Jarvis Brain",
    version="0.1.0",
    description="Local-first autonomous business operating system"
)

app.include_router(health_router)
app.include_router(agents_router)