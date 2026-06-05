from fastapi import FastAPI

from app.router import router as brain_router

app = FastAPI(
    title="Jarvis Brain",
    version="0.2.0",
    description="Local-first autonomous business operating system for LKProfessionals (Pvt) Ltd.",
)

app.include_router(brain_router)
