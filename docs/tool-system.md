# Tool System

Tool definitions are stored in `packages/tools/registry.json` and validated against `packages/tools/schema.json`.

Each tool defines:

* name
* aliases
* category
* description
* input schema
* output schema
* risk level
* approval requirement
* mode
* permissions
* rate and timeout controls
* lifecycle metadata

The Python brain now supports:

* registry validation and capability discovery
* approval-aware tool execution
* queued and chained workflow execution
* execution history, replay, analytics, and health views
* CLI inspection through `scripts/tool_cli.py`
* stress verification through `scripts/test_tools.py`

Key endpoints:

* `GET /tools`
* `GET /tools/capabilities`
* `GET /tools/compatibility`
* `GET /tools/adapters`
* `GET /tools/history`
* `GET /tools/analytics`
* `GET /tools/health`
* `POST /tools/execute`
* `POST /tools/workflows`
* `POST /tools/queue/process`
* `POST /tools/replay/{execution_id}`
