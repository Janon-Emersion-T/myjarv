from pydantic import BaseModel
from fastapi import APIRouter

from app.core.model_config import ModelConfig
from app.services.ollama_service import OllamaService


router = APIRouter(prefix="/models", tags=["Models"])


class ChatRequest(BaseModel):
    agent: str
    message: str
    system_message: str | None = None


class EmbedRequest(BaseModel):
    text: str


@router.get("/routing")
async def get_model_routing():
    config = ModelConfig()
    return config.data


@router.post("/chat")
async def chat_with_model(request: ChatRequest):
    service = OllamaService()

    response = await service.chat(
        agent_name=request.agent,
        user_message=request.message,
        system_message=request.system_message
    )

    return {
        "agent": request.agent,
        "response": response
    }


@router.post("/embed")
async def create_embedding(request: EmbedRequest):
    service = OllamaService()
    embedding = await service.embed(request.text)

    return {
        "dimension": len(embedding),
        "embedding_preview": embedding[:10]
    }