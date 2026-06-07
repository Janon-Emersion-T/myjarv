from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings


@dataclass
class AdapterDescriptor:
    name: str
    kind: str
    configured: bool
    mode: str
    description: str


class SQLiteMemoryAdapter:
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name="sqlite",
            kind="primary",
            configured=True,
            mode="read_write",
            description="Default local-first memory adapter backed by the Jarvis SQLite database.",
        )


class PostgreSQLMemoryAdapter:
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name="postgresql",
            kind="relational",
            configured=bool(settings.POSTGRES_DSN),
            mode="standby",
            description="Future-compatible relational memory adapter preserving migration paths beyond SQLite.",
        )


class RedisCacheLayer:
    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name="redis_cache",
            kind="cache",
            configured=False,
            mode="placeholder",
            description="Cache-layer placeholder for hot memory lookup acceleration and cleanup scheduling.",
        )


class VectorMemoryAdapter:
    provider = "vector"

    def descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            name=self.provider,
            kind="vector",
            configured=False,
            mode="placeholder",
            description=f"{self.provider.title()} semantic memory adapter scaffold for future retrieval expansion.",
        )


class QdrantMemoryAdapter(VectorMemoryAdapter):
    provider = "qdrant"


class PineconeMemoryAdapter(VectorMemoryAdapter):
    provider = "pinecone"


class WeaviateMemoryAdapter(VectorMemoryAdapter):
    provider = "weaviate"


class MemoryAdapterRegistry:
    def __init__(self) -> None:
        self.adapters = [
            SQLiteMemoryAdapter(),
            PostgreSQLMemoryAdapter(),
            RedisCacheLayer(),
            QdrantMemoryAdapter(),
            PineconeMemoryAdapter(),
            WeaviateMemoryAdapter(),
        ]

    def describe(self) -> list[dict[str, Any]]:
        return [adapter.descriptor().__dict__ for adapter in self.adapters]


memory_adapter_registry = MemoryAdapterRegistry()
