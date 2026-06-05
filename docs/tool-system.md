# Tool System

Tool definitions are stored in `packages/tools/registry.json`.

Each tool defines:

* name
* description
* input schema
* output schema
* risk level
* approval requirement
* mode

The current Python brain exposes tool definitions through `GET /tools`.

