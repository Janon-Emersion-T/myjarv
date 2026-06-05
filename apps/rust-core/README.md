# Jarvis Rust Core

This workspace contains performance-sensitive, system-facing, and security-oriented Rust utilities for Jarvis.

Current crates:

* `jarvis_file_guard`
* `jarvis_command_guard`
* `jarvis_logger`
* `jarvis_system_info`
* `jarvis_text_utils`

The first integration target is CLI usage from Python and shell workflows. Later phases can expose these crates through Python bindings or service wrappers.

