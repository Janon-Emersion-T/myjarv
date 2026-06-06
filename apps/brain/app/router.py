import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.agent_loader import get_agent_detail, get_all_agents, get_department_groups, get_registry_data
from app.browser.planner import browser_planner
from app.collaboration import collaboration_bus, collaboration_engine, collaboration_store
from app.config import settings
from app.exceptions import ApprovalRequiredError, TaskExecutionError, TaskStateError
from app.knowledge.loader import knowledge_loader
from app.logger import logger
from app.memory import memory_store
from app.orchestrator import orchestrate_task
from app.routing import routing_engine, routing_store
from app.routing.rules import routing_rules
from app.security import enforce_local_auth
from app.schemas import (
    ApprovalDecisionRequest,
    MemoryCreateRequest,
    RoutingSimulationRequest,
    TaskCreateRequest,
    TaskExecutionRequest,
    TaskReassignmentRequest,
)
from app.task_manager import task_manager
from app.tools.registry import tool_registry
from app.workflows.business import BUSINESS_WORKFLOWS
from app.workflows.developer import DEVELOPER_WORKFLOWS


router = APIRouter(dependencies=[Depends(enforce_local_auth)])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "Jarvis Brain", "version": "0.4.0"}


@router.get("/agents")
def list_agents() -> dict:
    return {
        "version": get_registry_data()["version"],
        "generated_on": get_registry_data()["generated_on"],
        "departments": get_department_groups(),
        "agents": get_all_agents(),
    }


@router.get("/agents/registry")
def get_registry() -> dict:
    return get_registry_data()


@router.get("/agents/{name}")
def get_agent(name: str) -> dict:
    try:
        return get_agent_detail(name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tasks")
def create_task(request: TaskCreateRequest) -> dict:
    try:
        task = task_manager.create_task(orchestrate_task(request))
        logger.log("INFO", "api.tasks.create", "Created task via API.", {"task_id": task["id"]})
        return task
    except Exception as exc:
        logger.log("ERROR", "api.tasks.create_failed", "Failed to create task.", {"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tasks")
def list_tasks() -> dict:
    return {"tasks": task_manager.list_tasks()}


@router.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict:
    try:
        return task_manager.get_task(task_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/approve")
def approve_task(task_id: str, request: ApprovalDecisionRequest) -> dict:
    try:
        return task_manager.approve_task(task_id, request.reviewer, request.notes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/reject")
def reject_task(task_id: str, request: ApprovalDecisionRequest) -> dict:
    try:
        return task_manager.reject_task(task_id, request.reviewer, request.notes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/execute")
def execute_task(task_id: str, request: TaskExecutionRequest) -> dict:
    try:
        return task_manager.execute_task(task_id, executor=request.executor, force_retry=request.force_retry)
    except ApprovalRequiredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (TaskStateError, TaskExecutionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.log("ERROR", "api.tasks.execute_failed", "Failed to execute task.", {"task_id": task_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/reassign")
def reassign_task(task_id: str, request: TaskReassignmentRequest) -> dict:
    try:
        return task_manager.reassign_task(task_id, request.reviewer, request.agent, request.reason)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tasks/{task_id}/route-trace")
def get_task_route_trace(task_id: str) -> dict:
    trace = routing_store.get_trace_for_task(task_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"No route trace found for task {task_id}")
    return trace


@router.get("/tasks/{task_id}/collaboration")
def get_task_collaboration(task_id: str) -> dict:
    session = collaboration_store.get_latest_session_for_task(task_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"No collaboration session found for task {task_id}")
    return session


@router.get("/memory")
def list_memory(scope: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"memory": memory_store.list(scope=scope, limit=limit)}


@router.post("/memory")
def create_memory(request: MemoryCreateRequest) -> dict:
    return memory_store.create(
        scope=request.scope,
        key=request.key,
        value=request.value,
        tags=request.tags,
        source=request.source,
        task_id=request.task_id,
    )


@router.get("/logs")
def get_logs(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"logs": logger.read_recent(limit=limit)}


@router.post("/routing/simulate")
def simulate_routing(request: RoutingSimulationRequest) -> dict:
    return routing_engine.route(
        message=request.message,
        preferred_agent=request.preferred_agent,
        requested_action=request.requested_action,
        metadata=request.metadata,
        mode="simulation",
    )


@router.get("/routing/analytics")
def get_routing_analytics() -> dict:
    return routing_store.analytics()


@router.get("/routing/traces")
def list_routing_traces(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"traces": routing_store.list_traces(limit=limit)}


@router.get("/routing/traces/{trace_id}")
def get_routing_trace(trace_id: str) -> dict:
    try:
        return routing_store.get_trace(trace_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/routing/traces/{trace_id}/replay")
def replay_routing_trace(trace_id: str) -> dict:
    try:
        return routing_engine.replay(trace_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/routing/map")
def get_routing_map() -> dict:
    rules = routing_rules.load()
    edges = []
    for label, config in rules.get("intent_categories", {}).items():
        edges.append({"stage": f"intent:{label}", "agents": [config.get("department", "general")]})
    for route in rules.get("direct_routes", []):
        edges.append(
            {
                "stage": f"route:{route['label']}",
                "agents": [route["primary"], *route.get("collaborators", []), *route.get("reviewers", [])],
            }
        )
    return {
        "nodes": sorted({node for edge in edges for node in edge["agents"]}),
        "edges": edges,
    }


@router.get("/collaboration/sessions")
def list_collaboration_sessions(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"sessions": collaboration_store.list_sessions(limit=limit)}


@router.get("/collaboration/sessions/{session_id}")
def get_collaboration_session(session_id: str) -> dict:
    try:
        return collaboration_store.get_session(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/collaboration/sessions/{session_id}/replay")
def replay_collaboration_session(session_id: str) -> dict:
    try:
        return collaboration_engine.replay(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/collaboration/analytics")
def get_collaboration_analytics() -> dict:
    return collaboration_store.analytics()


@router.post("/tasks/{task_id}/collaboration/plan")
def create_task_collaboration_plan(task_id: str) -> dict:
    try:
        task = task_manager.get_task(task_id)
        return collaboration_engine.plan(task, mode="simulation")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.websocket("/ws/collaboration/{session_id}")
async def collaboration_stream(session_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    queue = collaboration_bus.subscribe(session_id)
    try:
        await websocket.send_json({"type": "connected", "session_id": session_id})
        try:
            session = collaboration_store.get_session(session_id)
            await websocket.send_json({"type": "snapshot", "payload": session})
        except Exception:
            pass
        while True:
            message = await asyncio.wait_for(queue.get(), timeout=30)
            await websocket.send_json(message)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        collaboration_bus.unsubscribe(session_id, queue)
        await websocket.close()


@router.get("/knowledge")
def get_knowledge(category: str | None = Query(default=None), query: str | None = Query(default=None)) -> dict:
    if query:
        return {"knowledge": knowledge_loader.retrieve_relevant(query)}
    return {"knowledge": knowledge_loader.list_entries(category=category)}


@router.get("/tools")
def get_tools() -> dict:
    return {"tools": tool_registry.list_tools()}


@router.get("/settings")
def get_settings() -> dict:
    return {
        "app_name": settings.APP_NAME,
        "app_env": settings.APP_ENV,
        "database_backend": settings.DATABASE_BACKEND,
        "postgres_configured": bool(settings.POSTGRES_DSN),
        "production_lock_mode": settings.PRODUCTION_LOCK_MODE,
    }


@router.get("/browser/plan")
def plan_browser_task(goal: str = Query(..., min_length=1)) -> dict:
    return browser_planner.create_plan(goal)


@router.get("/workflows/business")
def get_business_workflows() -> dict:
    return {"workflows": BUSINESS_WORKFLOWS}


@router.get("/workflows/developer")
def get_developer_workflows() -> dict:
    return {"workflows": DEVELOPER_WORKFLOWS}
