from fastapi import APIRouter, HTTPException, Query

from app.agent_loader import get_agent_detail, get_all_agents
from app.logger import logger
from app.memory import memory_store
from app.orchestrator import orchestrate_task
from app.schemas import ApprovalDecisionRequest, MemoryCreateRequest, TaskCreateRequest
from app.task_manager import task_manager


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "Jarvis Brain", "version": "0.2.0"}


@router.get("/agents")
def list_agents() -> dict:
    return {"agents": get_all_agents()}


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
