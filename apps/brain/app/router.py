import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect

from app.agent_loader import get_agent_detail, get_all_agents, get_department_groups, get_registry_data
from app.approval_bus import approval_bus
from app.browser.planner import browser_planner
from app.collaboration import collaboration_bus, collaboration_engine, collaboration_store
from app.config import settings
from app.dashboard import (
    get_dashboard_activity,
    get_dashboard_errors,
    get_dashboard_kpis,
    get_dashboard_pipeline,
    get_dashboard_reports,
    get_dashboard_summary,
    search_dashboard,
)
from app.exceptions import ApprovalRequiredError, TaskExecutionError, TaskStateError
from app.knowledge.loader import knowledge_loader
from app.knowledge.pipelines import knowledge_pipeline_registry
from app.logger import logger
from app.memory_adapters import memory_adapter_registry
from app.memory import memory_store
from app.orchestrator import orchestrate_task
from app.routing import routing_engine, routing_store
from app.routing.rules import routing_rules
from app.secops import security_engine
from app.security import enforce_local_auth
from app.schemas import (
    ApiKeyCreateRequest,
    ApprovalEmergencyShutdownRequest,
    AuthLoginRequest,
    AuthMfaVerifyRequest,
    AuthLogoutRequest,
    BackupCreateRequest,
    BackupRestoreRequest,
    ApprovalDecisionRequest,
    ApprovalRevokeRequest,
    ApprovalRollbackRequest,
    ApprovalSimulationRequest,
    IncidentCreateRequest,
    LockdownRequest,
    MemoryCreateRequest,
    MemoryImportRequest,
    MemorySnapshotRequest,
    OfflineModeRequest,
    RoutingSimulationRequest,
    ScanRunRequest,
    SecretCreateRequest,
    TaskCreateRequest,
    TaskExecutionRequest,
    TaskReassignmentRequest,
    ToolExecuteRequest,
    ToolWorkflowRequest,
    VoiceCommandRequest,
    VoiceSessionCreateRequest,
)
from app.task_manager import task_manager
from app.tools.adapters import tool_adapter_registry
from app.tools.engine import tool_execution_engine
from app.tools.registry import tool_registry
from app.tools.store import tool_execution_store
from app.voice.bus import voice_bus
from app.voice.devices import voice_device_manager
from app.voice.engine import voice_engine
from app.voice.store import voice_store
from app.workflows.business import BUSINESS_WORKFLOWS
from app.workflows.developer import DEVELOPER_WORKFLOWS


public_router = APIRouter()
router = APIRouter(dependencies=[Depends(enforce_local_auth)])


@public_router.post("/auth/login")
def auth_login(request: AuthLoginRequest) -> dict:
    session = security_engine.login(request.username, request.password)
    if request.mfa_code:
        security_engine.verify_mfa(request.username, request.mfa_code)
    return session


@public_router.post("/auth/logout")
def auth_logout(request: AuthLogoutRequest) -> dict:
    return security_engine.logout(request.token)


@public_router.post("/auth/mfa/verify")
def auth_mfa_verify(request: AuthMfaVerifyRequest) -> dict:
    return security_engine.verify_mfa(request.username, request.code)


@public_router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "Jarvis Brain",
        "version": "0.4.0",
        "lockdown_active": security_engine.is_lockdown_active(),
        "offline_mode": security_engine.is_offline_mode(),
    }


@router.get("/auth/me")
def auth_me(request: Request) -> dict:
    return {"subject": getattr(request.state, "security_subject", None)}


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
        return task_manager.approve_task(task_id, request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/reject")
def reject_task(task_id: str, request: ApprovalDecisionRequest) -> dict:
    try:
        return task_manager.reject_task(task_id, request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tasks/{task_id}/approvals/policy")
def get_task_approval_policy(task_id: str) -> dict:
    try:
        return task_manager.get_approval_policy(task_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/approvals/simulate")
def simulate_task_approval(task_id: str, request: ApprovalSimulationRequest) -> dict:
    try:
        return task_manager.simulate_approval(task_id, request.model_dump(), decision=request.decision)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/approvals/{approval_id}/revoke")
def revoke_task_approval(task_id: str, approval_id: str, request: ApprovalRevokeRequest) -> dict:
    try:
        return task_manager.revoke_approval(task_id, approval_id, request.actor, request.reason)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/approvals/rollback")
def rollback_task_approval(task_id: str, request: ApprovalRollbackRequest) -> dict:
    try:
        return task_manager.rollback_task(task_id, request.actor, request.reason)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/approvals/queue")
def list_approval_queue(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"queue": task_manager.list_approval_queue(limit=limit)}


@router.get("/approvals/history")
def list_approval_history(limit: int = Query(default=100, ge=1, le=1000), task_id: str | None = Query(default=None)) -> dict:
    return {"approvals": task_manager.list_approval_history(limit=limit, task_id=task_id)}


@router.get("/approvals/metrics")
def get_approval_metrics() -> dict:
    return task_manager.approval_metrics()


@router.get("/approvals/quarantine")
def get_approval_quarantine(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"artifacts": task_manager.list_approval_artifacts("quarantine", limit=limit)}


@router.get("/approvals/archive")
def get_approval_archive(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"artifacts": task_manager.list_approval_artifacts("archive", limit=limit)}


@router.get("/approvals/channels")
def get_approval_channels() -> dict:
    return {
        "channels": ["dashboard", "api", "cli", "mobile", "email", "whatsapp", "voice"],
        "roles": ["operator", "manager", "director", "executive"],
    }


@router.post("/approvals/emergency-shutdown")
def set_approval_emergency_shutdown(request: ApprovalEmergencyShutdownRequest) -> dict:
    return task_manager.set_emergency_shutdown(request.active, request.actor, request.reason)


@router.get("/approvals/emergency-shutdown")
def get_approval_emergency_shutdown() -> dict:
    return task_manager.get_emergency_shutdown()


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
def list_memory(
    scope: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    include_expired: bool = Query(default=False),
) -> dict:
    return {"memory": memory_store.list(scope=scope, limit=limit, include_expired=include_expired)}


@router.post("/memory")
def create_memory(request: MemoryCreateRequest) -> dict:
    return memory_store.create(
        scope=request.scope,
        key=request.key,
        value=request.value,
        tags=request.tags,
        source=request.source,
        task_id=request.task_id,
        summary=request.summary,
        metadata=request.metadata,
        confidence_score=request.confidence_score,
        importance_score=request.importance_score,
        access_level=request.access_level,
        sensitivity=request.sensitivity,
        department=request.department,
        expires_at=request.expires_at,
        encrypted=request.encrypted,
        status=request.status,
    )


@router.get("/memory/search")
def search_memory(query: str = Query(..., min_length=1), scope: str | None = Query(default=None), semantic: bool = Query(default=True)) -> dict:
    return {"memory": memory_store.search(query=query, scope=scope, semantic=semantic)}


@router.get("/memory/summary")
def summarize_memory(scope: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    return memory_store.summarize(scope=scope, limit=limit)


@router.get("/memory/analytics")
def memory_analytics() -> dict:
    return memory_store.analytics()


@router.get("/memory/adapters")
def memory_adapters() -> dict:
    return {"adapters": memory_adapter_registry.describe()}


@router.get("/memory/export")
def export_memory(scope: str | None = Query(default=None)) -> dict:
    return memory_store.export_records(scope=scope)


@router.post("/memory/import")
def import_memory(request: MemoryImportRequest) -> dict:
    records = [item.model_dump() for item in request.records]
    return memory_store.import_records(records, merge=request.merge)


@router.get("/memory/duplicates")
def memory_duplicates() -> dict:
    return {"duplicates": memory_store.detect_duplicates()}


@router.get("/memory/{record_id}/related")
def related_memory(record_id: str, limit: int = Query(default=10, ge=1, le=100)) -> dict:
    try:
        return {"memory": memory_store.related(record_id, limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/memory/snapshots")
def create_memory_snapshot(request: MemorySnapshotRequest) -> dict:
    return memory_store.create_snapshot(request.label)


@router.get("/memory/snapshots")
def list_memory_snapshots() -> dict:
    return {"snapshots": memory_store.list_snapshots()}


@router.post("/memory/backups")
def create_memory_backup(request: BackupCreateRequest) -> dict:
    return memory_store.create_backup(request.label)


@router.get("/memory/backups")
def list_memory_backups() -> dict:
    return {"backups": memory_store.list_backups()}


@router.post("/memory/backups/restore")
def restore_memory_backup(request: BackupRestoreRequest) -> dict:
    return memory_store.restore_backup(request.backup_id)


@router.post("/memory/cleanup")
def cleanup_memory() -> dict:
    return memory_store.cleanup_expired()


@router.get("/memory/corrupted")
def corrupted_memory() -> dict:
    return {"corrupted": memory_store.detect_corrupted()}


@router.post("/memory/repair")
def repair_memory() -> dict:
    return memory_store.repair()


@router.get("/logs")
def get_logs(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"logs": logger.read_recent(limit=limit)}


@router.get("/security/dashboard")
def get_security_dashboard() -> dict:
    return security_engine.dashboard()


@router.get("/security/events")
def get_security_events(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"events": security_engine.list_events(limit=limit)}


@router.get("/security/events/{event_id}")
def replay_security_event(event_id: str) -> dict:
    try:
        return security_engine.replay_event(event_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/security/users")
def list_security_users() -> dict:
    return {"users": security_engine.list_users()}


@router.get("/security/compliance")
def get_security_compliance() -> dict:
    return security_engine.compliance_report()


@router.get("/security/api-keys")
def list_security_api_keys() -> dict:
    return {"api_keys": security_engine.list_api_keys()}


@router.post("/security/api-keys")
def create_security_api_key(request: ApiKeyCreateRequest) -> dict:
    return security_engine.create_api_key(request.owner, request.label, request.role_scope, request.attributes)


@router.get("/security/secrets")
def list_security_secrets() -> dict:
    return {"secrets": security_engine.list_secrets()}


@router.post("/security/secrets")
def create_security_secret(request: SecretCreateRequest) -> dict:
    return security_engine.put_secret(request.name, request.value, request.provider)


@router.get("/security/agent-permissions/{agent_name}")
def get_agent_permissions(agent_name: str, requested_action: str | None = Query(default=None)) -> dict:
    return security_engine.check_agent_permissions(agent_name, requested_action)


@router.get("/security/backups")
def list_security_backups() -> dict:
    return {"backups": security_engine.list_backups()}


@router.post("/security/backups")
def create_security_backup(request: BackupCreateRequest) -> dict:
    return security_engine.create_backup(request.label)


@router.post("/security/backups/restore")
def restore_security_backup(request: BackupRestoreRequest) -> dict:
    return security_engine.restore_backup(request.backup_id)


@router.get("/security/scans")
def list_security_scans() -> dict:
    return {"scans": security_engine.list_scans()}


@router.post("/security/scans")
def run_security_scan(request: ScanRunRequest) -> dict:
    return security_engine.run_scan(request.scan_type)


@router.get("/security/incidents")
def list_security_incidents() -> dict:
    return {"incidents": security_engine.list_incidents()}


@router.post("/security/incidents")
def create_security_incident(request: IncidentCreateRequest) -> dict:
    return security_engine.create_incident(request.title, request.details, request.severity)


@router.post("/security/lockdown")
def activate_security_lockdown(request: LockdownRequest) -> dict:
    return security_engine.lockdown(request.reason)


@router.post("/security/unlock")
def release_security_lockdown(request: LockdownRequest) -> dict:
    return security_engine.unlock(request.reason)


@router.post("/security/offline-mode")
def set_security_offline_mode(request: OfflineModeRequest) -> dict:
    return security_engine.set_offline_mode(request.enabled, request.reason)


@router.get("/security/metrics", response_model=None)
def get_security_metrics(format: str = Query(default="json")):
    if format == "prometheus":
        return Response(content=security_engine.prometheus_metrics(), media_type="text/plain; version=0.0.4")
    return security_engine.metrics()


@router.get("/security/audit-integrity")
def get_security_audit_integrity() -> dict:
    return security_engine.verify_audit_log_integrity()


@router.get("/security/vault/providers")
def get_security_vault_providers() -> dict:
    return {"providers": security_engine.list_vault_providers()}


@router.post("/security/backups/{backup_id}/test-restore")
def test_security_backup_restore(backup_id: str) -> dict:
    return security_engine.test_backup_restore(backup_id)


@router.get("/voice/config")
def get_voice_config() -> dict:
    return voice_engine.dashboard()["config"]


@router.get("/voice/devices")
def get_voice_devices() -> dict:
    return voice_device_manager.list_devices()


@router.get("/voice/analytics")
def get_voice_analytics() -> dict:
    return voice_store.analytics()


@router.get("/voice/dashboard")
def get_voice_dashboard() -> dict:
    return voice_engine.dashboard()


@router.get("/voice/sessions")
def list_voice_sessions(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    return {"sessions": voice_store.list_sessions(limit=limit)}


@router.get("/voice/sessions/{session_id}")
def get_voice_session(session_id: str) -> dict:
    try:
        return voice_store.get_session(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/voice/sessions")
def create_voice_session(request: VoiceSessionCreateRequest) -> dict:
    return voice_engine.create_session(
        mode=request.mode,
        locale=request.locale,
        speaker_id=request.speaker_id,
        text=request.text,
        device_input=request.device_input,
        device_output=request.device_output,
        metadata=request.metadata,
    )


@router.post("/voice/sessions/{session_id}/command")
def handle_voice_command(session_id: str, request: VoiceCommandRequest) -> dict:
    try:
        return voice_engine.handle_command(
            session_id,
            text=request.text,
            requested_action=request.requested_action,
            locale=request.locale,
            speaker_id=request.speaker_id,
            confidence=request.confidence,
            metadata=request.metadata,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/voice/sessions/{session_id}/interrupt")
def interrupt_voice_session(session_id: str) -> dict:
    try:
        return voice_engine.interrupt(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/voice/sessions/{session_id}/resume")
def resume_voice_session(session_id: str) -> dict:
    try:
        return voice_engine.resume(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/voice/sessions/{session_id}/replay")
def replay_voice_session(session_id: str) -> dict:
    try:
        return voice_engine.replay(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/dashboard/summary")
def dashboard_summary() -> dict:
    return get_dashboard_summary()


@router.get("/dashboard/errors")
def dashboard_errors() -> dict:
    return get_dashboard_errors()


@router.get("/dashboard/activity")
def dashboard_activity() -> dict:
    return get_dashboard_activity()


@router.get("/dashboard/reports")
def dashboard_reports() -> dict:
    return get_dashboard_reports()


@router.get("/dashboard/kpis")
def dashboard_kpis() -> dict:
    return get_dashboard_kpis()


@router.get("/dashboard/pipeline")
def dashboard_pipeline() -> dict:
    return get_dashboard_pipeline()


@router.get("/dashboard/search")
def dashboard_search(query: str = Query(..., min_length=1)) -> dict:
    return search_dashboard(query)


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


@router.websocket("/ws/dashboard")
async def dashboard_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(
                {
                    "type": "dashboard_snapshot",
                    "payload": {
                        "summary": get_dashboard_summary(),
                        "activity": get_dashboard_activity(),
                        "errors": get_dashboard_errors(),
                        "kpis": get_dashboard_kpis(),
                    },
                }
            )
            await asyncio.sleep(10)
    except (WebSocketDisconnect, RuntimeError):
        await websocket.close()


@router.websocket("/ws/approvals")
async def approvals_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = approval_bus.subscribe()
    try:
        await websocket.send_json(
            {
                "type": "snapshot",
                "payload": {
                    "queue": task_manager.list_approval_queue(limit=100),
                    "metrics": task_manager.approval_metrics(),
                    "shutdown": task_manager.get_emergency_shutdown(),
                },
            }
        )
        while True:
            message = await asyncio.wait_for(queue.get(), timeout=30)
            await websocket.send_json(message)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        approval_bus.unsubscribe(queue)
        await websocket.close()


@router.websocket("/ws/voice/{session_id}")
async def voice_stream(session_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    queue = voice_bus.subscribe(session_id)
    try:
        await websocket.send_json({"type": "connected", "session_id": session_id})
        try:
            await websocket.send_json({"type": "snapshot", "payload": voice_store.get_session(session_id)})
        except Exception:
            pass
        while True:
            message = await asyncio.wait_for(queue.get(), timeout=30)
            await websocket.send_json(message)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        voice_bus.unsubscribe(session_id, queue)
        await websocket.close()


@router.get("/knowledge")
def get_knowledge(category: str | None = Query(default=None), query: str | None = Query(default=None), limit: int = Query(default=20, ge=1, le=200)) -> dict:
    if query:
        return {"knowledge": knowledge_loader.retrieve_relevant(query, limit=limit, category=category)}
    return {"knowledge": knowledge_loader.list_entries(category=category)[:limit]}


@router.get("/knowledge/search")
def search_knowledge(query: str = Query(..., min_length=1), category: str | None = Query(default=None), limit: int = Query(default=20, ge=1, le=200)) -> dict:
    return {"knowledge": knowledge_loader.search(query=query, category=category, limit=limit, semantic=True)}


@router.get("/knowledge/analytics")
def knowledge_analytics() -> dict:
    return knowledge_loader.analytics()


@router.get("/knowledge/validate")
def validate_knowledge() -> dict:
    return knowledge_loader.validate()


@router.get("/knowledge/sources")
def knowledge_sources() -> dict:
    return knowledge_loader.source_report()


@router.get("/knowledge/quarantine")
def knowledge_quarantine() -> dict:
    return {"knowledge": knowledge_loader.quarantine()}


@router.get("/knowledge/graph")
def knowledge_graph() -> dict:
    return knowledge_loader.relationship_graph()


@router.get("/knowledge/gaps")
def knowledge_gaps() -> dict:
    return knowledge_loader.missing_knowledge()


@router.get("/knowledge/pipelines")
def knowledge_pipelines() -> dict:
    return knowledge_pipeline_registry.describe()


@router.post("/knowledge/reindex")
def reindex_knowledge() -> dict:
    return knowledge_loader.reindex()


@router.get("/tools")
def get_tools() -> dict:
    return {"tools": tool_registry.list_tools(), "validation": tool_registry.validate(), "capabilities": tool_registry.capabilities()}


@router.get("/tools/capabilities")
def get_tool_capabilities() -> dict:
    return tool_registry.capabilities()


@router.get("/tools/compatibility")
def get_tool_compatibility() -> dict:
    return tool_registry.compatibility_matrix()


@router.get("/tools/adapters")
def get_tool_adapters() -> dict:
    return {"adapters": tool_adapter_registry.describe()}


@router.get("/tools/validate")
def validate_tools() -> dict:
    return tool_registry.validate()


@router.get("/tools/history")
def get_tool_history(tool_name: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=500)) -> dict:
    return {"executions": tool_execution_store.list(tool_name=tool_name, limit=limit)}


@router.get("/tools/analytics")
def get_tool_analytics() -> dict:
    return tool_execution_store.analytics()


@router.get("/tools/health")
def get_tool_health() -> dict:
    return tool_execution_store.health()


@router.get("/tools/metrics", response_model=None)
def get_tool_metrics(format: str = Query(default="json")):
    if format == "prometheus":
        return Response(content=tool_execution_engine.prometheus_metrics(), media_type="text/plain; version=0.0.4")
    return tool_execution_store.analytics()


@router.get("/tools/{name}")
def get_tool(name: str) -> dict:
    try:
        return tool_registry.get_tool(name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tools/execute")
def execute_tool(request: ToolExecuteRequest) -> dict:
    try:
        return tool_execution_engine.execute(
            tool_name=request.tool_name,
            input_payload=request.input,
            actor=request.actor,
            agent_name=request.agent_name,
            task_id=request.task_id,
            approved=request.approved,
            async_mode=request.async_mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tools/workflows")
def execute_tool_workflow(request: ToolWorkflowRequest) -> dict:
    return tool_execution_engine.execute_workflow([step.model_dump() for step in request.steps], actor=request.actor, approved=request.approved)


@router.post("/tools/queue/process")
def process_tool_queue(limit: int = Query(default=10, ge=1, le=100)) -> dict:
    return tool_execution_engine.process_queue(limit=limit)


@router.post("/tools/replay/{execution_id}")
def replay_tool_execution(execution_id: str, approved: bool = Query(default=False)) -> dict:
    try:
        return tool_execution_engine.replay(execution_id, approved=approved)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
