import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "agents" / "registry.json"

DEPARTMENT_TOOLS = {
    "executive": ["agent_registry", "task_dashboard", "approval_records", "operational_reports"],
    "operations": ["task_dashboard", "reports", "memory_lookup", "approval_records"],
    "development": ["project_scanner", "code_reviewer", "doc_generator", "safe_shell_plan"],
    "frontend": ["component_review", "design_review", "accessibility_checklist", "code_reviewer"],
    "backend": ["api_planner", "schema_review", "code_reviewer", "safe_shell_plan"],
    "mobile": ["release_checklist", "api_planner", "code_reviewer", "testing_notes"],
    "desktop": ["desktop_build_planner", "code_reviewer", "logging_tools", "release_notes"],
    "database": ["schema_tools", "migration_planner", "query_review", "integrity_checks"],
    "devops": ["deployment_checklist", "log_review", "approval_records", "infrastructure_notes"],
    "qa": ["test_planner", "quality_checklist", "bug_reporting", "release_readiness"],
    "security": ["risk_classifier", "audit_logs", "approval_records", "security_review"],
    "uiux": ["design_system_review", "wireframe_notes", "accessibility_checklist", "handoff_notes"],
    "seo": ["seo_checklist", "content_review", "report_templates", "structured_data_notes"],
    "content": ["content_briefs", "brand_voice_guide", "review_checklist", "publishing_plans"],
    "marketing": ["campaign_planner", "content_calendar", "performance_reports", "audience_notes"],
    "sales": ["lead_tracking", "proposal_templates", "followup_plans", "client_notes"],
    "finance": ["quotation_templates", "invoice_records", "approval_records", "financial_summaries"],
    "legal": ["policy_templates", "approval_records", "contract_review", "risk_summaries"],
    "research": ["trusted_source_research", "knowledge_base", "summary_templates", "risk_notes"],
    "documentation": ["doc_generator", "readme_templates", "knowledge_base", "task_records"],
    "training": ["learning_plans", "knowledge_base", "training_outlines", "task_summaries"],
    "automation": ["workflow_planner", "safe_browser_plan", "safe_shell_plan", "execution_logs"],
    "data": ["pipeline_planner", "schema_tools", "data_validation", "report_templates"],
    "analytics": ["dashboard_specs", "kpi_reports", "data_summaries", "chart_notes"],
    "ai": ["prompt_library", "model_routing_notes", "knowledge_base", "workflow_planner"],
    "cms": ["cms_build_checklist", "seo_checklist", "plugin_review", "content_workflows"],
    "ecommerce": ["checkout_workflows", "catalog_planning", "order_checklist", "report_templates"],
    "business_systems": ["workflow_planner", "approval_records", "schema_tools", "ops_reports"],
    "communication": ["message_templates", "approval_records", "audit_logs", "workflow_plans"],
    "infrastructure": ["dns_notes", "deployment_plans", "approval_records", "audit_logs"],
    "creative": ["creative_briefs", "asset_planning", "review_notes", "campaign_references"],
    "hr": ["recruitment_workflow", "interview_templates", "approval_records", "onboarding_notes"],
    "administration": ["sop_records", "approval_records", "task_records", "ops_checklists"],
    "customer_support": ["support_templates", "client_notes", "task_routing", "escalation_records"],
}

PRIORITY_BY_DEPARTMENT = {
    "executive": 5,
    "security": 5,
    "finance": 5,
    "legal": 5,
    "operations": 4,
    "devops": 4,
    "infrastructure": 4,
    "development": 4,
    "backend": 4,
    "frontend": 4,
    "database": 4,
    "ai": 4,
    "administration": 4,
}

APPROVAL_BY_DEPARTMENT = {
    "executive": "HIGH",
    "security": "HIGH",
    "finance": "HIGH",
    "legal": "HIGH",
    "hr": "HIGH",
    "devops": "HIGH",
    "infrastructure": "HIGH",
    "business_systems": "HIGH",
    "communication": "HIGH",
    "database": "MEDIUM",
    "development": "MEDIUM",
    "backend": "MEDIUM",
    "frontend": "MEDIUM",
    "mobile": "MEDIUM",
    "desktop": "MEDIUM",
    "operations": "MEDIUM",
    "sales": "MEDIUM",
    "automation": "MEDIUM",
    "ai": "MEDIUM",
}

RISK_BY_DEPARTMENT = {
    "executive": "HIGH",
    "security": "CRITICAL",
    "finance": "CRITICAL",
    "legal": "CRITICAL",
    "hr": "HIGH",
    "devops": "HIGH",
    "infrastructure": "HIGH",
    "business_systems": "HIGH",
    "communication": "HIGH",
    "database": "HIGH",
    "development": "MEDIUM",
    "backend": "MEDIUM",
    "frontend": "MEDIUM",
    "mobile": "MEDIUM",
    "desktop": "MEDIUM",
    "operations": "MEDIUM",
    "sales": "MEDIUM",
    "automation": "MEDIUM",
    "ai": "MEDIUM",
}


def build_authority_scope(agent: dict) -> str:
    department = agent["department"]
    role = agent["role"].replace("_", " ")
    if department in {"executive", "operations"}:
        return f"May coordinate and review {role} work within approved company operations but must preserve approval gates for dangerous actions."
    if department in {"security", "finance", "legal", "hr"}:
        return f"May assess and prepare {role} outputs, but irreversible, external, or compliance-sensitive actions require explicit approval."
    return f"May execute routine {role} tasks within approved scope and escalate when the request crosses risk, budget, policy, or authority limits."


def enrich_agent(agent: dict) -> dict:
    department = agent["department"]
    enriched = dict(agent)
    enriched["profile_path"] = f"packages/agents/prompts/{agent['prompt_file']}"
    enriched["priority"] = PRIORITY_BY_DEPARTMENT.get(department, 3)
    enriched["risk_level"] = RISK_BY_DEPARTMENT.get(department, "LOW")
    enriched["approval_level"] = APPROVAL_BY_DEPARTMENT.get(department, "LOW")
    enriched["tools"] = DEPARTMENT_TOOLS.get(department, ["knowledge_base", "task_records", "approval_records"])
    enriched["authority_scope"] = build_authority_scope(agent)
    return enriched


def main() -> None:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    data["agents"] = [enrich_agent(agent) for agent in data["agents"]]
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Enriched {len(data['agents'])} agents.")


if __name__ == "__main__":
    main()
