from fastapi import FastAPI

from app.router import public_router, router as brain_router
from app.security import SecurityMiddleware

app = FastAPI(
    title="Jarvis Brain",
    version="0.4.0",
    description="Local-first autonomous business operating system for LKProfessionals (Pvt) Ltd.",
)

app.add_middleware(SecurityMiddleware)
app.include_router(public_router)
app.include_router(brain_router)
