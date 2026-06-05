from dataclasses import dataclass


@dataclass(slots=True)
class SpeechToTextRequest:
    audio_path: str
    language: str | None = None


@dataclass(slots=True)
class TextToSpeechRequest:
    text: str
    voice: str | None = None


class SpeechToTextProvider:
    def transcribe(self, request: SpeechToTextRequest) -> str:
        raise NotImplementedError


class TextToSpeechProvider:
    def synthesize(self, request: TextToSpeechRequest) -> str:
        raise NotImplementedError

