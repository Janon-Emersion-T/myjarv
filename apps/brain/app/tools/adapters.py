from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolAdapter:
    name: str
    kind: str
    status: str
    description: str


class ToolAdapterRegistry:
    def __init__(self) -> None:
        self.adapters = [
            ToolAdapter("celery", "worker_backend", "scaffolded", "Queued tool execution backend placeholder."),
            ToolAdapter("temporal", "worker_backend", "scaffolded", "Workflow orchestration backend placeholder."),
            ToolAdapter("rabbitmq", "event_bus", "scaffolded", "Message-broker adapter placeholder for tool events."),
            ToolAdapter("nats", "event_bus", "scaffolded", "Realtime event-bus adapter placeholder."),
            ToolAdapter("playwright", "browser_automation", "scaffolded", "Browser automation adapter placeholder."),
            ToolAdapter("selenium", "browser_automation", "scaffolded", "Legacy browser automation adapter placeholder."),
            ToolAdapter("ocr", "vision", "scaffolded", "OCR tool adapter placeholder."),
            ToolAdapter("opencv", "vision", "scaffolded", "OpenCV adapter placeholder."),
            ToolAdapter("yolo", "vision", "scaffolded", "YOLO adapter placeholder."),
            ToolAdapter("whisper", "audio", "scaffolded", "Speech-to-text adapter placeholder."),
            ToolAdapter("elevenlabs", "audio", "scaffolded", "Text-to-speech adapter placeholder."),
            ToolAdapter("openai_tts", "audio", "scaffolded", "OpenAI TTS adapter placeholder."),
            ToolAdapter("webrtc", "transport", "scaffolded", "Realtime transport adapter placeholder."),
            ToolAdapter("porcupine", "wake_word", "scaffolded", "Wake-word adapter placeholder."),
            ToolAdapter("rnnoise", "noise_reduction", "scaffolded", "Noise reduction adapter placeholder."),
            ToolAdapter("docker", "infrastructure", "scaffolded", "Docker management adapter placeholder."),
            ToolAdapter("kubernetes", "infrastructure", "scaffolded", "Kubernetes management adapter placeholder."),
            ToolAdapter("nginx", "infrastructure", "scaffolded", "Nginx management adapter placeholder."),
            ToolAdapter("cloudflare", "infrastructure", "scaffolded", "Cloudflare management adapter placeholder."),
            ToolAdapter("database_admin", "database", "scaffolded", "Database backup and restore adapter placeholder."),
        ]

    def describe(self) -> list[dict[str, Any]]:
        return [item.__dict__ for item in self.adapters]


tool_adapter_registry = ToolAdapterRegistry()
