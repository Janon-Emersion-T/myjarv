from typing import Any

import httpx

from app.core.model_config import ModelConfig


class OllamaService:
    def __init__(self) -> None:
        self.config = ModelConfig()
        self.base_url = self.config.get_ollama_base_url()

    async def chat_by_model_role(
        self,
        model_role: str,
        user_message: str,
        system_message: str | None = None
    ) -> str:
        model_config = self.config.get_model_by_role(model_role)
        model_name = model_config["name"]
        temperature = model_config.get("temperature", 0.3)

        messages: list[dict[str, str]] = []

        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })

        messages.append({
            "role": "user",
            "content": user_message
        })

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()

        data = response.json()
        return data["message"]["content"]

    async def chat(
        self,
        agent_name: str,
        user_message: str,
        system_message: str | None = None
    ) -> str:
        model_config = self.config.get_model_for_agent(agent_name)
        model_name = model_config["name"]
        temperature = model_config.get("temperature", 0.3)

        messages: list[dict[str, str]] = []

        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })

        messages.append({
            "role": "user",
            "content": user_message
        })

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()

        data = response.json()
        return data["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        model_config = self.config.get_model_by_role("embedding")
        model_name = model_config["name"]

        payload = {
            "model": model_name,
            "input": text
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json=payload
            )
            response.raise_for_status()

        data = response.json()
        embeddings = data.get("embeddings", [])

        if not embeddings:
            return []

        return embeddings[0]