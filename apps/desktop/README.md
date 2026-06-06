# Jarvis Desktop

This is the Tauri + React + Tailwind desktop operations console for Jarvis.

## Current Coverage

* routed desktop dashboard
* agent directory
* task management
* approval management
* project pipeline and timeline views
* memory browser
* knowledge browser
* realtime logs and error views
* reports and KPI views
* collaboration session views
* settings and tool management views
* command palette and global search
* websocket dashboard feed
* offline cache hydration
* local operator switching
* dark/light theme and locale toggle

## Backend Dependencies

The desktop app reads live data from the Python brain API, including:

* `/dashboard/*`
* `/agents`
* `/tasks`
* `/memory`
* `/knowledge`
* `/logs`
* `/routing/*`
* `/collaboration/*`
* `/tools`
* `/settings`
