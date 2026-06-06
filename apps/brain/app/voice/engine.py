from __future__ import annotations

import re
from typing import Any

from app.approval_gate import approval_gate
from app.audit_logger import audit_logger
from app.config import settings
from app.personality import apply_personality
from app.voice.bus import voice_bus
from app.voice.config import VoiceConfig
from app.voice.devices import voice_device_manager
from app.voice.store import voice_store


EMERGENCY_KEYWORDS = {"shutdown", "emergency", "panic", "stop all", "lockdown", "freeze operations"}
COMMAND_KEYWORDS = {"open", "run", "execute", "create", "approve", "reject", "deploy", "scan", "status"}
WAKE_WORDS = {"jarvis", "hey jarvis"}


class VoiceEngine:
    def __init__(self) -> None:
        self.voice_config = VoiceConfig()

    def create_session(
        self,
        *,
        mode: str,
        locale: str,
        speaker_id: str,
        text: str | None = None,
        device_input: str | None = None,
        device_output: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = metadata or {}
        now = voice_store.now()
        initial_text = text or ""
        session = voice_store.create_session(
            {
                "id": voice_store.next_id(),
                "mode": mode,
                "locale": locale,
                "speaker_id": speaker_id,
                "speaker_authorized": self._speaker_authorized(speaker_id),
                "wake_word_detected": self._wake_word_detected(initial_text),
                "wake_word": self._detected_wake_word(initial_text),
                "transport": self.voice_config.transport,
                "stt_provider": self.voice_config.stt_provider,
                "tts_provider": self.voice_config.tts_provider,
                "noise_reduction": self.voice_config.noise_reduction,
                "input_device": device_input or "default-mic",
                "output_device": device_output or "default-speaker",
                "status": "listening",
                "current_task_id": None,
                "last_transcript": initial_text or None,
                "last_response_text": None,
                "conversation_memory": [initial_text] if initial_text else [],
                "analytics": {
                    "latency_budget_ms": 300,
                    "streaming_stt": True,
                    "streaming_tts": True,
                    "webrtc_ready": True,
                    "rnnoise_ready": True,
                    "multilingual": locale != "en",
                },
                "metadata": metadata | {"created_via": "api"},
                "created_at": now,
                "updated_at": now,
            }
        )
        self._event(session["id"], "session_started", f"Voice session started in {mode} mode.", {"locale": locale})
        return session

    def handle_command(
        self,
        session_id: str,
        *,
        text: str,
        requested_action: str | None,
        locale: str,
        speaker_id: str,
        confidence: float | None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = voice_store.get_session(session_id)
        metadata = metadata or {}
        normalized = self._normalize_text(text)
        detected_mode = self._detected_mode(session["mode"], normalized)
        intent = self._intent(normalized)
        transcript_confidence = confidence if confidence is not None else self._confidence(normalized, locale)
        risk_level, approval_level = approval_gate.classify(normalized, "LOW", requested_action)
        if detected_mode == "emergency":
            risk_level, approval_level = "CRITICAL", "CRITICAL"
        response = self._response_text(
            session=session,
            text=text,
            intent=intent,
            detected_mode=detected_mode,
            confidence=transcript_confidence,
            risk_level=risk_level,
            approval_level=approval_level,
        )
        interruption_handled = "stop" in normalized or "interrupt" in normalized
        interaction = voice_store.add_interaction(
            {
                "id": voice_store.next_id(),
                "session_id": session_id,
                "speaker_id": speaker_id,
                "input_text": text,
                "normalized_text": normalized,
                "detected_mode": detected_mode,
                "intent": intent,
                "confidence": transcript_confidence,
                "risk_level": risk_level,
                "approval_level": approval_level,
                "response_text": response,
                "interruption_handled": interruption_handled,
                "created_at": voice_store.now(),
            }
        )
        updated_memory = [*session["conversation_memory"], f"user:{text}", f"jarvis:{response}"][-20:]
        updated = voice_store.update_session(
            session_id,
            status="responding" if not interruption_handled else "interrupted",
            last_transcript=text,
            last_response_text=response,
            conversation_memory=updated_memory,
            speaker_authorized=self._speaker_authorized(speaker_id),
            wake_word_detected=self._wake_word_detected(text),
            analytics=session["analytics"]
            | {
                "last_confidence": transcript_confidence,
                "last_intent": intent,
                "silence_detection": True,
                "vad_enabled": True,
                "echo_cancellation": True,
                "accent_adaptation": locale != "en",
                "risk_level": risk_level,
                "approval_level": approval_level,
            },
            metadata=session["metadata"] | metadata,
        )
        self._event(
            session_id,
            "voice_command",
            f"Voice command handled in {detected_mode} mode.",
            {"intent": intent, "confidence": transcript_confidence, "risk_level": risk_level, "approval_level": approval_level},
        )
        if detected_mode == "emergency":
            self._event(
                session_id,
                "emergency_workflow",
                "Emergency workflow activated.",
                {"contact": settings.VOICE_EMERGENCY_CONTACT, "command": normalized},
            )
        packet = {"type": "interaction", "payload": {"session": updated, "interaction": interaction}}
        voice_bus.publish(session_id, packet)
        audit_logger.record(
            "voice_command",
            "Voice command handled.",
            {"session_id": session_id, "intent": intent, "risk_level": risk_level, "approval_level": approval_level},
        )
        return {"session": updated, "interaction": interaction}

    def interrupt(self, session_id: str) -> dict[str, Any]:
        session = voice_store.update_session(session_id, status="interrupted")
        self._event(session_id, "interrupted", "Voice session interrupted by operator.", {})
        voice_bus.publish(session_id, {"type": "session", "payload": session})
        return session

    def resume(self, session_id: str) -> dict[str, Any]:
        session = voice_store.update_session(session_id, status="listening")
        self._event(session_id, "resumed", "Voice session resumed.", {})
        voice_bus.publish(session_id, {"type": "session", "payload": session})
        return session

    def replay(self, session_id: str) -> dict[str, Any]:
        session = voice_store.get_session(session_id)
        replay = self.create_session(
            mode=session["mode"],
            locale=session["locale"],
            speaker_id=session["speaker_id"],
            text=session["last_transcript"],
            device_input=session["input_device"],
            device_output=session["output_device"],
            metadata=session["metadata"] | {"replay_of": session_id},
        )
        self._event(replay["id"], "replay", "Voice session replay prepared.", {"source_session_id": session_id})
        return voice_store.get_session(replay["id"])

    def dashboard(self) -> dict[str, Any]:
        devices = voice_device_manager.list_devices()
        analytics = voice_store.analytics()
        sessions = voice_store.list_sessions(limit=20)
        return {
            "config": {
                "stt_provider": self.voice_config.stt_provider,
                "tts_provider": self.voice_config.tts_provider,
                "wake_word_provider": self.voice_config.wake_word_provider,
                "transport": self.voice_config.transport,
                "noise_reduction": self.voice_config.noise_reduction,
            },
            "devices": devices,
            "analytics": analytics,
            "sessions": sessions,
            "modes": ["command", "conversation", "desktop_assistant", "emergency"],
        }

    def _speaker_authorized(self, speaker_id: str) -> bool:
        allowed = {item.strip().lower() for item in settings.VOICE_ALLOWED_SPEAKERS.split(",") if item.strip()}
        return speaker_id.lower() in allowed

    def _wake_word_detected(self, text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in WAKE_WORDS)

    def _detected_wake_word(self, text: str) -> str:
        lowered = text.lower()
        for word in WAKE_WORDS:
            if word in lowered:
                return word
        return "jarvis"

    def _detected_mode(self, current_mode: str, normalized: str) -> str:
        if any(keyword in normalized for keyword in EMERGENCY_KEYWORDS):
            return "emergency"
        if current_mode == "desktop_assistant":
            return "desktop_assistant"
        if current_mode == "conversation" and not any(keyword in normalized for keyword in COMMAND_KEYWORDS):
            return "conversation"
        if current_mode == "command":
            return "command"
        return current_mode

    def _intent(self, normalized: str) -> str:
        if any(keyword in normalized for keyword in EMERGENCY_KEYWORDS):
            return "emergency_control"
        if "approve" in normalized:
            return "approval"
        if "status" in normalized or "report" in normalized:
            return "status_report"
        if any(keyword in normalized for keyword in {"search", "find", "show"}):
            return "lookup"
        if any(keyword in normalized for keyword in {"open", "run", "execute", "create", "plan"}):
            return "command_execution"
        return "conversation"

    def _confidence(self, normalized: str, locale: str) -> float:
        base = 0.86 if locale == "en" else 0.78
        if len(normalized.split()) > 8:
            base -= 0.05
        if any(char.isdigit() for char in normalized):
            base -= 0.03
        return round(max(0.55, min(base, 0.97)), 4)

    def _response_text(
        self,
        *,
        session: dict[str, Any],
        text: str,
        intent: str,
        detected_mode: str,
        confidence: float,
        risk_level: str,
        approval_level: str,
    ) -> str:
        personality = apply_personality("Voice response")
        intro = "Jarvis here."
        if detected_mode == "emergency":
            return (
                f"{intro} Emergency mode engaged. I will prioritize safe shutdown guidance, alert {settings.VOICE_EMERGENCY_CONTACT}, "
                f"and require manual confirmation for any destructive action."
            )
        if detected_mode == "command":
            return (
                f"{intro} Command received with {confidence:.0%} confidence. "
                f"Intent is {intent}. Risk is {risk_level} and approval requirement is {approval_level}. "
                f"I'll stay direct, approval-aware, and keep the action traceable."
            )
        if detected_mode == "desktop_assistant":
            return (
                f"{intro} Desktop assistant mode is active. I can guide workspace actions, surface reports, and help without blocking your flow."
            )
        return (
            f"{intro} Conversation mode is active. I understood '{text}'. "
            f"My speaking style stays {personality['stance']} with memory-aware follow-up and calm pacing."
        )

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()

    def _event(self, session_id: str, event_type: str, message: str, payload: dict[str, Any]) -> None:
        event = voice_store.add_event(
            {
                "id": voice_store.next_id(),
                "session_id": session_id,
                "event_type": event_type,
                "message": message,
                "payload": payload,
                "created_at": voice_store.now(),
            }
        )
        voice_bus.publish(session_id, {"type": "event", "payload": event})


voice_engine = VoiceEngine()
