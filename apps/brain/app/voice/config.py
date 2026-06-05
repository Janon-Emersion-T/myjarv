from dataclasses import dataclass


@dataclass(slots=True)
class VoiceConfig:
    stt_provider: str = "whisper_local"
    tts_provider: str = "piper"
    wake_word_provider: str = "porcupine"
    transport: str = "webrtc"
    noise_reduction: str = "rnnoise"

