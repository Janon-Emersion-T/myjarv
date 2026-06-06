from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CollaborationProtocol:
    coordinator: str = "Jarvis"

    def instruction(self, sender: str, recipient: str, task_message: str, stage: str) -> str:
        return f"{sender} instructs {recipient} to contribute to the {stage} stage for: {task_message}"

    def handoff(self, sender: str, recipient: str, summary: str, stage: str) -> str:
        return f"{sender} hands off the {stage} outcome to {recipient}: {summary}"

    def review(self, sender: str, recipient: str, summary: str) -> str:
        return f"{sender} requests quality and risk review from {recipient}: {summary}"

    def escalation(self, sender: str, recipient: str, reason: str) -> str:
        return f"{sender} escalates to {recipient}: {reason}"

    def memory_ref(self, sender: str, recipient: str, scope: str, key: str) -> str:
        return f"{sender} shares {scope} memory '{key}' with {recipient}"

    def knowledge_ref(self, sender: str, recipient: str, path: str) -> str:
        return f"{sender} shares knowledge source {path} with {recipient}"


collaboration_protocol = CollaborationProtocol()
