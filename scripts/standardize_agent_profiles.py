import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "agents" / "registry.json"
PROMPTS_DIR = ROOT / "packages" / "agents" / "prompts"

START_MARKER = "<!-- canonical-profile:start -->"
END_MARKER = "<!-- canonical-profile:end -->"


DEPARTMENT_LABELS = {
    "executive": "Executive",
    "operations": "Operations",
    "development": "Development",
    "frontend": "Frontend Engineering",
    "backend": "Backend Engineering",
    "mobile": "Mobile Engineering",
    "desktop": "Desktop Engineering",
    "database": "Database Engineering",
    "devops": "DevOps",
    "qa": "Quality Assurance",
    "security": "Security",
    "uiux": "UI/UX",
    "seo": "SEO",
    "content": "Content",
    "marketing": "Marketing",
    "sales": "Sales",
    "finance": "Finance",
    "legal": "Legal",
    "research": "Research",
    "documentation": "Documentation",
    "training": "Training",
    "automation": "Automation",
    "data": "Data Engineering",
    "analytics": "Analytics",
    "ai": "AI Systems",
    "cms": "CMS Engineering",
    "ecommerce": "E-Commerce",
    "business_systems": "Business Systems",
    "communication": "Communication Systems",
    "infrastructure": "Infrastructure",
    "creative": "Creative",
    "hr": "Human Resources",
    "administration": "Administration",
    "customer_support": "Customer Support",
}

DEPARTMENT_TOOLS = {
    "executive": ["Agent registry", "Task dashboard", "Approval system", "Operational reporting"],
    "operations": ["Task dashboard", "Reporting tools", "Approval records", "Operational memory"],
    "development": ["Repository scanner", "Code reviewer", "Documentation generator", "Safe command planner"],
    "frontend": ["Component library", "Design references", "Code reviewer", "Accessibility checklist"],
    "backend": ["API planner", "Database schema tools", "Code reviewer", "Safe command planner"],
    "mobile": ["API integration planner", "Build checklist", "Code reviewer", "Release notes tools"],
    "desktop": ["Tauri architecture notes", "Code reviewer", "Desktop packaging checklist", "Logging tools"],
    "database": ["Schema tools", "Query review checklist", "Migration planner", "Data integrity checks"],
    "devops": ["Infrastructure checklist", "Deployment plans", "Log review", "Approval system"],
    "qa": ["Test planning", "Quality checklist", "Bug reporting", "Release readiness reports"],
    "security": ["Risk classification", "Approval records", "Audit logs", "Security review checklist"],
    "uiux": ["Wireframing references", "Design system guide", "Accessibility checklist", "Review notes"],
    "seo": ["SEO checklist", "Content review", "Structured data notes", "Reporting templates"],
    "content": ["Content briefs", "Brand voice guide", "Review checklist", "Publishing plans"],
    "marketing": ["Campaign planner", "Content calendar", "Performance reporting", "Audience notes"],
    "sales": ["Lead tracking", "Proposal templates", "Follow-up plans", "Client notes"],
    "finance": ["Quotation templates", "Invoice records", "Approval records", "Financial summaries"],
    "legal": ["Policy templates", "Approval records", "Contract review notes", "Risk summaries"],
    "research": ["Trusted-source research workflow", "Knowledge base", "Summary templates", "Risk notes"],
    "documentation": ["Documentation generator", "README templates", "Knowledge base", "Task records"],
    "training": ["Learning plans", "Knowledge base", "Training outlines", "Task summaries"],
    "automation": ["Workflow planner", "Safe browser planning", "Safe command planner", "Execution logs"],
    "data": ["Pipeline planning", "Schema tools", "Reporting templates", "Validation checklist"],
    "analytics": ["Dashboard specs", "Reporting templates", "Data summaries", "KPI notes"],
    "ai": ["Prompt library", "Model routing notes", "Knowledge base", "Workflow planner"],
    "cms": ["CMS build checklist", "SEO checklist", "Plugin review notes", "Content workflows"],
    "ecommerce": ["Checkout workflow notes", "Catalog planning", "Order system checklist", "Reporting templates"],
    "business_systems": ["Workflow planner", "Approval records", "Schema tools", "Operational reports"],
    "communication": ["Messaging workflow plans", "Template library", "Approval system", "Audit logs"],
    "infrastructure": ["DNS notes", "Deployment plans", "Approval system", "Audit logs"],
    "creative": ["Creative briefs", "Asset planning", "Review notes", "Campaign references"],
    "hr": ["Recruitment workflow", "Interview templates", "Approval records", "Staff onboarding notes"],
    "administration": ["SOP records", "Approval system", "Task records", "Operational checklists"],
    "customer_support": ["Support templates", "Client notes", "Task routing", "Escalation records"],
}

APPROVAL_LEVEL_BY_DEPARTMENT = {
    "executive": "HIGH",
    "operations": "MEDIUM",
    "development": "MEDIUM",
    "frontend": "MEDIUM",
    "backend": "MEDIUM",
    "mobile": "MEDIUM",
    "desktop": "MEDIUM",
    "database": "HIGH",
    "devops": "HIGH",
    "qa": "MEDIUM",
    "security": "HIGH",
    "uiux": "LOW",
    "seo": "LOW",
    "content": "LOW",
    "marketing": "LOW",
    "sales": "MEDIUM",
    "finance": "HIGH",
    "legal": "HIGH",
    "research": "LOW",
    "documentation": "LOW",
    "training": "LOW",
    "automation": "MEDIUM",
    "data": "MEDIUM",
    "analytics": "LOW",
    "ai": "MEDIUM",
    "cms": "MEDIUM",
    "ecommerce": "MEDIUM",
    "business_systems": "HIGH",
    "communication": "HIGH",
    "infrastructure": "HIGH",
    "creative": "LOW",
    "hr": "HIGH",
    "administration": "MEDIUM",
    "customer_support": "MEDIUM",
}


def titleize_slug(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("/", "_").split("_"))


def make_position(agent: dict) -> str:
    prompt_name = Path(agent["prompt_file"]).stem
    legacy = (PROMPTS_DIR / agent["prompt_file"]).read_text(encoding="utf-8")
    first_line = legacy.splitlines()[0].strip() if legacy.strip() else ""
    if "—" in first_line:
        return first_line.split("—", 1)[1].strip().rstrip("#").strip()
    return titleize_slug(agent["role"])


def make_department(agent: dict) -> str:
    return DEPARTMENT_LABELS.get(agent["department"], titleize_slug(agent["department"]))


def make_mission(agent: dict) -> str:
    description = agent["description"].rstrip(".")
    responsibility = agent["responsibility"].rstrip(".")
    return (
        f"{agent['name']} serves as the {description.lower()} for LKProfessionals (Pvt) Ltd. "
        f"The mission is to {responsibility.lower()} while staying within approved authority, "
        f"company policy, and Jarvis orchestration rules."
    )


def make_responsibilities(agent: dict) -> list[str]:
    role_hint = titleize_slug(agent["role"])
    return [
        agent["responsibility"].rstrip("."),
        f"Operate as the designated {role_hint.lower()} within the {make_department(agent)} function.",
        "Produce work that is traceable, reviewable, and aligned with LKProfessionals standards.",
    ]


def make_skills(agent: dict) -> list[str]:
    role_words = [word.capitalize() for word in agent["role"].split("_")[:3]]
    skills = role_words + [make_department(agent), agent["model_role"].capitalize() + " reasoning"]
    seen: list[str] = []
    for skill in skills:
        if skill not in seen:
            seen.append(skill)
    return seen[:5]


def make_tools(agent: dict) -> list[str]:
    tools = DEPARTMENT_TOOLS.get(agent["department"], ["Task records", "Approval system", "Knowledge base"])
    if agent["model_role"] == "coder" and "Code reviewer" not in tools:
        tools = tools + ["Code reviewer"]
    return tools[:5]


def make_inputs(agent: dict) -> list[str]:
    return [
        "Assigned task from Jarvis or an approved workflow",
        "Relevant project, client, or company context",
        f"Specialist requirements related to {titleize_slug(agent['role']).lower()} work",
    ]


def make_outputs(agent: dict) -> list[str]:
    return [
        f"Structured {titleize_slug(agent['role']).lower()} deliverables",
        "Clear status notes and decision rationale",
        "Escalation notes when work crosses authority or risk limits",
    ]


def make_decision_authority(agent: dict) -> list[str]:
    approval_level = APPROVAL_LEVEL_BY_DEPARTMENT.get(agent["department"], "MEDIUM")
    lines = [
        f"May make routine {titleize_slug(agent['role']).lower()} decisions within approved task scope.",
        f"Must remain within an approval ceiling of `{approval_level}` unless a higher authority explicitly delegates otherwise.",
    ]
    if agent["department"] in {"finance", "legal", "security", "devops", "infrastructure", "hr"}:
        lines.append("Must escalate any irreversible, externally impactful, or sensitive action before execution.")
    return lines


def make_escalation_rules(agent: dict) -> list[str]:
    rules = [
        "Escalate to Jarvis when task scope is ambiguous, cross-departmental, or requires final coordination.",
        "Escalate when the task requires tool access, authority, or approvals beyond this role's defined limits.",
    ]
    if agent["department"] not in {"security"}:
        rules.append("Escalate security-sensitive issues to the security department before risky execution.")
    if agent["department"] not in {"finance"}:
        rules.append("Escalate finance-impacting decisions to Morgan or the finance function when cost or billing risk is material.")
    return rules


def make_forbidden_actions(agent: dict) -> list[str]:
    actions = [
        "Do not claim work is complete when it has not been verified.",
        "Do not expose secrets, credentials, or sensitive internal records.",
        "Do not execute destructive or externally impactful actions without the required approval.",
    ]
    if agent["department"] != "legal":
        actions.append("Do not issue legal commitments outside approved legal workflows.")
    if agent["department"] != "finance":
        actions.append("Do not alter financial records or pricing decisions outside approved finance workflows.")
    return actions


def make_example_tasks(agent: dict) -> list[str]:
    role_name = titleize_slug(agent["role"])
    return [
        f"Plan and deliver a task requiring {role_name.lower()} support.",
        f"Review an incoming request and produce a scoped {role_name.lower()} action plan.",
        f"Escalate a high-risk {role_name.lower()} issue with clear reasoning and next steps.",
    ]


def build_block(agent: dict) -> str:
    position = make_position(agent)
    department = make_department(agent)
    mission = make_mission(agent)
    responsibilities = make_responsibilities(agent)
    skills = make_skills(agent)
    tools = make_tools(agent)
    inputs = make_inputs(agent)
    outputs = make_outputs(agent)
    authority = make_decision_authority(agent)
    escalation = make_escalation_rules(agent)
    forbidden = make_forbidden_actions(agent)
    tasks = make_example_tasks(agent)

    def bullets(lines: list[str]) -> str:
        return "\n".join(f"* {line}" for line in lines)

    return f"""{START_MARKER}
# {agent["name"]}

## Position
{position}

## Department
{department}

## Mission
{mission}

## Responsibilities
{bullets(responsibilities)}

## Skills
{bullets(skills)}

## Tools
{bullets(tools)}

## Inputs
{bullets(inputs)}

## Outputs
{bullets(outputs)}

## Decision Authority
{bullets(authority)}

## Escalation Rules
{bullets(escalation)}

## Forbidden Actions
{bullets(forbidden)}

## Example Tasks
{bullets(tasks)}
{END_MARKER}
"""


def strip_existing_block(content: str) -> str:
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\s*",
        re.DOTALL,
    )
    return re.sub(pattern, "", content).lstrip()


def standardize_prompt(agent: dict) -> None:
    prompt_path = PROMPTS_DIR / agent["prompt_file"]
    original = prompt_path.read_text(encoding="utf-8")
    remaining = strip_existing_block(original)

    if "## Legacy Profile" in remaining:
        body = remaining
    else:
        body = "## Legacy Profile\n\n" + remaining.lstrip()

    prompt_path.write_text(build_block(agent) + "\n" + body.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    for agent in registry["agents"]:
        standardize_prompt(agent)
        print(f"standardized {agent['prompt_file']}")


if __name__ == "__main__":
    main()
