from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class KnowledgePipeline:
    name: str
    kind: str
    status: str
    description: str


class KnowledgePipelineRegistry:
    def __init__(self) -> None:
        self.parsers = [
            KnowledgePipeline("markdown", "parser", "active", "Parses markdown knowledge files with optional front matter."),
            KnowledgePipeline("json", "parser", "active", "Parses structured JSON knowledge payloads with metadata."),
            KnowledgePipeline("pdf", "parser", "scaffolded", "Provides placeholder PDF knowledge entries pending full text extraction."),
        ]
        self.ingestion = [
            KnowledgePipeline("ocr_ingestion", "pipeline", "scaffolded", "Reserves OCR-backed ingestion for scanned documents and low-quality files."),
            KnowledgePipeline("website_ingestion", "pipeline", "scaffolded", "Reserves website capture and normalization for future trusted-source sync."),
            KnowledgePipeline("codebase_ingestion", "pipeline", "scaffolded", "Reserves source-tree knowledge extraction for internal code references."),
            KnowledgePipeline("github_repository_ingestion", "pipeline", "scaffolded", "Reserves repository-backed knowledge synchronization for external code sources."),
            KnowledgePipeline("auto_update_sync", "pipeline", "scaffolded", "Reserves periodic knowledge refresh and synchronization workflows."),
        ]

    def describe(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "parsers": [item.__dict__ for item in self.parsers],
            "pipelines": [item.__dict__ for item in self.ingestion],
        }


knowledge_pipeline_registry = KnowledgePipelineRegistry()
