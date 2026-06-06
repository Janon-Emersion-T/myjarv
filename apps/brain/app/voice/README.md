# Voice Engine

This module provides the Jarvis voice interaction foundation.

## Responsibilities

* create and manage voice sessions
* simulate STT and TTS orchestration
* manage desktop assistant, command, conversation, and emergency modes
* enforce speaker authorization and emergency restrictions
* track voice events, interactions, and analytics
* expose websocket-ready realtime updates
* support replay, interruption, and resume workflows

## Current Runtime Scope

* Whisper-style STT orchestration path
* offline STT fallback semantics
* OpenAI and ElevenLabs-ready TTS selection path
* wake-word and speaker authorization checks
* command-mode and conversation-mode parsing
* emergency escalation workflow hooks
* desktop assistant voice control support
* mobile and cross-device architecture placeholders through transport-ready session design
