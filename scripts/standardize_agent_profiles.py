import json
import re
from datetime import date
from pathlib import Path

from agent_profile_sections import REQUIRED_SECTIONS


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "agents" / "registry.json"
STRUCTURE_PATH = ROOT / "packages" / "agents" / "company-structure.json"
PROMPTS_DIR = ROOT / "packages" / "agents" / "prompts"

START_MARKER = "<!-- canonical-profile:start -->"
END_MARKER = "<!-- canonical-profile:end -->"
LAST_UPDATED = str(date.today())
VERSION = "3.0.0"


RAW_DEPARTMENT_LABELS = {
    "executive": "Executive Command",
    "operations": "Operations Office",
    "development": "Software Architecture",
    "frontend": "Frontend Engineering",
    "backend": "Backend Engineering",
    "mobile": "Mobile Engineering",
    "desktop": "Desktop Engineering",
    "database": "Database Engineering",
    "devops": "DevOps",
    "qa": "Quality Engineering",
    "security": "Security",
    "uiux": "Product Design",
    "seo": "Search & SEO",
    "content": "Content Studio",
    "marketing": "Growth Marketing",
    "sales": "Sales",
    "finance": "Finance",
    "legal": "Legal",
    "research": "Research Office",
    "documentation": "Documentation",
    "training": "Training",
    "automation": "Automation Engineering",
    "data": "Data Engineering",
    "analytics": "Business Intelligence",
    "ai": "AI Engineering",
    "cms": "CMS Platforms",
    "ecommerce": "E-Commerce Platforms",
    "business_systems": "Business Systems",
    "communication": "Communication Systems",
    "infrastructure": "Infrastructure Services",
    "creative": "Creative Production",
    "hr": "Human Resources",
    "administration": "Administration",
    "customer_support": "Customer Support",
}

COMPANY_DISPLAY_NAMES = {
    "executive": "Executive",
    "operations": "Operations",
    "development": "Development",
    "design": "Design",
    "marketing": "Marketing",
    "sales": "Sales",
    "finance": "Finance",
    "legal": "Legal",
    "hr": "HR",
    "support": "Support",
    "security": "Security",
    "infrastructure": "Infrastructure",
    "research": "Research",
    "documentation": "Documentation",
    "automation": "Automation",
}

KNOWLEDGE_SOURCES = {
    "executive": ["data/knowledge/lkp", "docs/company-structure.md", "docs/vision.md"],
    "operations": ["data/knowledge/operations", "data/knowledge/projects", "docs/company-structure.md"],
    "development": ["data/knowledge/backend", "data/knowledge/frontend", "docs/architecture.md"],
    "design": ["data/knowledge/frontend", "data/knowledge/marketing", "docs/company-structure.md"],
    "marketing": ["data/knowledge/marketing", "data/knowledge/seo", "data/knowledge/clients"],
    "sales": ["data/knowledge/clients", "data/knowledge/operations", "docs/company-structure.md"],
    "finance": ["data/knowledge/finance", "data/knowledge/clients", "docs/approval-system.md"],
    "legal": ["data/knowledge/legal", "docs/security.md", "docs/approval-system.md"],
    "hr": ["data/knowledge/operations", "data/knowledge/lkp", "docs/company-structure.md"],
    "support": ["data/knowledge/clients", "data/knowledge/projects", "docs/company-structure.md"],
    "security": ["docs/security.md", "docs/approval-system.md", "data/knowledge/backend"],
    "infrastructure": ["data/knowledge/backend", "data/knowledge/web", "docs/deployment.md"],
    "research": ["data/knowledge/ai", "data/knowledge/backend", "data/knowledge/projects"],
    "documentation": ["docs/architecture.md", "docs/setup.md", "data/knowledge/lkp"],
    "automation": ["docs/tool-system.md", "data/knowledge/operations", "data/knowledge/backend"],
}

ROLE_NOTES = {
    "global_command": "global executive coordination",
    "executive_operations_bridge": "strategy-to-operations translation",
    "department_owner": "department intake and final specialist direction",
    "team_lead": "team-level execution and technical leadership",
    "design_system_lead": "design-system governance",
    "brand_design_lead": "branding and visual identity direction",
    "graphic_design_lead": "graphic asset and image production direction",
    "video_and_motion_lead": "video and motion planning direction",
    "approval_guard": "approval gate enforcement",
    "secrets_guard": "secrets and secure access control",
    "operations_reporting_lead": "operational reporting",
    "decision_memory_lead": "decision memory stewardship",
    "specialist": "specialist execution",
}

MEMORY_ACCESS = {
    "executive": [
        "Read company, project, decision, mistake, agent, and user preference memory.",
        "Write decision memory for company direction and agent memory for orchestration improvements.",
        "Do not overwrite sensitive records outside approval-aware workflows.",
    ],
    "operations": [
        "Read company, client, project, decision, and agent memory relevant to active operations.",
        "Write decision and project memory when coordination outcomes change delivery state.",
        "Avoid editing finance, legal, or HR-sensitive memory without the owning department.",
    ],
    "development": [
        "Read project, decision, mistake, and agent memory tied to implementation work.",
        "Write decision and mistake memory when engineering tradeoffs or failures should be preserved.",
        "Use client memory only when the request has direct delivery context.",
    ],
    "design": [
        "Read client, project, agent, and user preference memory for design context.",
        "Write project and user preference memory when brand or UX preferences are clarified.",
        "Avoid changing decision memory unless the change affects cross-department delivery.",
    ],
    "marketing": [
        "Read client, project, company, and user preference memory for campaign context.",
        "Write campaign-related project memory and preference memory when brand choices are confirmed.",
        "Do not edit finance or legal memory without escalation.",
    ],
    "sales": [
        "Read client, company, and project memory for lead and proposal context.",
        "Write client and project memory when scope, stage, or handoff facts change.",
        "Escalate any billing or legal memory updates to the owning department.",
    ],
    "finance": [
        "Read client, project, decision, and company memory for pricing and billing context.",
        "Write decision memory for approved commercial changes and client memory for billing-state updates.",
        "Treat all finance-related memory as approval-sensitive and auditable.",
    ],
    "legal": [
        "Read company, client, project, and decision memory when wording or obligations are involved.",
        "Write decision memory only for approved policy or contract interpretations.",
        "Do not alter commercial or personnel memory beyond legal-review notes.",
    ],
    "hr": [
        "Read company, project, and limited client memory only when people operations require it.",
        "Write agent and project memory for onboarding and internal process continuity.",
        "Treat candidate, staff, and personnel-related context as highly restricted.",
    ],
    "support": [
        "Read client, project, company, and agent memory needed to resolve support issues.",
        "Write client and project memory when a case outcome changes status or next steps.",
        "Escalate sensitive finance, legal, or security memory updates immediately.",
    ],
    "security": [
        "Read company, project, decision, mistake, and agent memory for risk assessment.",
        "Write decision and mistake memory for security findings, guardrails, and remediation outcomes.",
        "Never disclose secrets or sensitive findings in broadly accessible memory scopes.",
    ],
    "infrastructure": [
        "Read project, decision, company, and mistake memory for platform operations.",
        "Write decision and mistake memory for deployment, DNS, backup, and incident handling outcomes.",
        "Keep credential or secret details out of general memory entries.",
    ],
    "research": [
        "Read company, project, decision, and mistake memory to avoid repeating failed experiments.",
        "Write decision and mistake memory for validated findings and important experiment outcomes.",
        "Do not treat exploratory notes as production-ready commitments.",
    ],
    "documentation": [
        "Read company, project, decision, agent, and user preference memory to keep docs aligned.",
        "Write agent, project, and decision memory when documentation clarifies system behavior.",
        "Do not rewrite source-of-truth decisions without checking the owning department.",
    ],
    "automation": [
        "Read company, project, decision, mistake, and agent memory before planning automation.",
        "Write decision and mistake memory for automation design, rollbacks, and safety learnings.",
        "Do not persist secrets or unsafe execution details in shared memory.",
    ],
}


def titleize_slug(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("/", "_").split("_"))


def bullets(lines):
    return "\n".join(f"* {line}" for line in lines)


def load_registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["agents"]


def load_structure():
    structure = json.loads(STRUCTURE_PATH.read_text(encoding="utf-8"))
    by_name = {entry["name"]: entry for entry in structure["agent_index"]}
    department_by_slug = {dept["slug"]: dept for dept in structure["departments"]}
    return structure, by_name, department_by_slug


def legacy_first_line(agent):
    content = (PROMPTS_DIR / agent["prompt_file"]).read_text(encoding="utf-8")
    legacy = strip_existing_block(content)
    legacy = re.sub(r"^## Legacy Profile\s*", "", legacy, count=1).strip()
    if not legacy:
        return ""
    for line in legacy.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return legacy.splitlines()[0].strip()


def make_position(agent):
    first_line = legacy_first_line(agent)
    if "—" in first_line:
        return first_line.split("—", 1)[1].strip().rstrip("#").strip()
    return titleize_slug(agent["role"])


def make_department(agent, structure_entry):
    company = COMPANY_DISPLAY_NAMES[structure_entry["company_department"]]
    raw = RAW_DEPARTMENT_LABELS.get(structure_entry["raw_team"], titleize_slug(structure_entry["raw_team"]))
    if company == raw:
        return company
    return f"{company} / {raw}"


def make_collaborators(agent, entry, department_record):
    collaborators = list(entry["backup_agents"])
    if entry["department_owner"] != agent["name"]:
        collaborators.append(entry["department_owner"])
    if department_record["executive_sponsor"] not in {agent["name"], entry["department_owner"]}:
        collaborators.append(department_record["executive_sponsor"])
    if entry["reports_to"] not in {agent["name"], entry["department_owner"], "Janon"}:
        collaborators.append(entry["reports_to"])
    unique = []
    for collaborator in collaborators:
        if collaborator not in unique:
            unique.append(collaborator)
    return unique[:5]


def make_mission(agent, entry, department_record):
    description = agent["description"].rstrip(".")
    responsibility = agent["responsibility"].rstrip(".")
    role_note = ROLE_NOTES.get(entry["routing_role"], "specialist execution")
    return (
        f"{agent['name']} serves as the {description.lower()} for LKProfessionals (Pvt) Ltd. "
        f"The mission is to {responsibility.lower()} while supporting {role_note}, "
        f"staying inside {department_record['display_name']} authority boundaries, and keeping every action traceable."
    )


def make_responsibilities(agent, entry, department_record):
    return [
        agent["responsibility"].rstrip("."),
        f"Operate as the designated {titleize_slug(agent['role']).lower()} inside {department_record['display_name']}.",
        f"Support the {entry['team_display_name'].lower()} function without crossing approval, policy, or ownership boundaries.",
    ]


def make_skills(agent, entry):
    base = [
        titleize_slug(agent["role"]),
        entry["team_display_name"],
        COMPANY_DISPLAY_NAMES[entry["company_department"]],
        agent["model_role"].capitalize() + " reasoning",
    ]
    if entry["authority_level"] == "approval_guard":
        base.append("Risk escalation")
    unique = []
    for item in base:
        if item not in unique:
            unique.append(item)
    return unique[:5]


def make_tools(agent):
    return [tool.replace("_", " ").title() for tool in agent["tools"]]


def make_knowledge_sources(entry):
    sources = KNOWLEDGE_SOURCES.get(entry["company_department"], ["docs/architecture.md", "data/knowledge/lkp"])
    sources = sources + [
        "packages/agents/registry.json",
        "packages/agents/company-structure.json",
    ]
    unique = []
    for source in sources:
        if source not in unique:
            unique.append(source)
    return [f"`{source}`" for source in unique[:5]]


def make_memory_access(entry):
    return MEMORY_ACCESS.get(entry["company_department"], MEMORY_ACCESS["operations"])


def make_tool_access_level(agent, entry):
    if agent["approval_level"] in {"HIGH", "CRITICAL"} or entry["authority_level"] == "approval_guard":
        return (
            "Planning and review by default. Any external, destructive, credentialed, or production-impacting execution "
            "requires explicit approval and audit logging."
        )
    if entry["authority_level"] in {"department_governor", "technical_lead", "delivery_owner"}:
        return (
            "Can prepare and review specialist work autonomously inside approved scope, but execution that crosses "
            "system, client, or policy boundaries must go through the approval gate."
        )
    return (
        "Specialist planning and structured output only. Any real execution must be delegated or approved through the owning workflow."
    )


def make_inputs(agent, entry):
    return [
        "Assigned task from Jarvis, Athena, or an approved department workflow",
        "Relevant project, client, company, or incident context",
        f"Requirements tied to {entry['team_display_name'].lower()} and {titleize_slug(agent['role']).lower()} work",
    ]


def make_input_validation_rules(agent, entry):
    rules = [
        "Confirm the task belongs to this role, department, or approved collaboration scope before proceeding.",
        "Check for missing context, approvals, deadlines, and risk-sensitive constraints before producing a final answer.",
        "Stop and escalate when the request implies production changes, legal exposure, financial impact, or unsafe execution beyond the role limit.",
    ]
    if entry["company_department"] in {"finance", "legal", "hr", "security", "infrastructure"}:
        rules.append("Require explicit traceability for sensitive records, approvals, and decision ownership.")
    return rules


def make_outputs(agent, entry):
    return [
        f"Structured {titleize_slug(agent['role']).lower()} deliverables",
        "Clear status, decision rationale, and next-step guidance",
        "Explicit escalation notes whenever authority, risk, or dependency boundaries are crossed",
    ]


def make_output_quality_checklist(entry):
    return [
        "The output is specific, actionable, and aligned with the assigned department scope.",
        "Assumptions, risks, and approval-sensitive steps are stated clearly.",
        "The response is traceable enough to store in tasks, approvals, or memory without guesswork.",
    ]


def make_review_checklist(entry):
    return [
        "Re-check that the task stayed within the defined reporting line and authority level.",
        "Re-check that collaboration, escalation, and approval requirements are called out explicitly.",
        "Re-check that the final output can be used by the next agent or human without hidden context.",
    ]


def make_decision_authority(agent, entry):
    lines = [
        f"May make routine {titleize_slug(agent['role']).lower()} decisions inside approved task scope and department ownership boundaries.",
        f"Acts with `{entry['authority_level']}` authority and must respect the approval ceiling of `{agent['approval_level']}`.",
    ]
    if entry["company_department"] in {"finance", "legal", "security", "infrastructure"}:
        lines.append("Must escalate irreversible, externally impactful, or compliance-sensitive actions before execution.")
    return lines


def make_approval_level(agent):
    return (
        f"{agent['approval_level']} — this role can prepare work up to the registry approval ceiling of "
        f"`{agent['approval_level']}`, but higher-risk execution still requires the approval gate."
    )


def make_risk_level(agent):
    return (
        f"{agent['risk_level']} — the registry classifies this role at `{agent['risk_level']}` because its work can affect "
        f"business, technical, operational, or compliance outcomes if mishandled."
    )


def make_escalation_rules(agent, entry, department_record):
    rules = [
        f"Escalate to {entry['reports_to']} when the request exceeds this role's authority, confidence, or department scope.",
        "Escalate to Jarvis when the task becomes cross-departmental, politically sensitive, or strategically ambiguous.",
        "Escalate to Security before any risky execution involving secrets, shell commands, production systems, or external access.",
    ]
    if entry["company_department"] != "finance":
        rules.append("Escalate finance-impacting commitments, pricing, or billing implications to Morgan or Finance.")
    if entry["company_department"] != "legal":
        rules.append("Escalate legal wording, ownership language, or contract-sensitive commitments to Lawrence or Legal.")
    return rules


def make_escalation_message_template(agent, entry):
    return (
        f"Escalation from {agent['name']} ({titleize_slug(agent['role'])}). "
        f"Current scope touches authority beyond `{agent['approval_level']}` or leaves critical context unresolved. "
        f"Blocked area: [describe blocker]. Needed reviewer: {entry['reports_to']}. "
        "Recommended next step: [safe next step]."
    )


def make_failure_response(entry):
    return [
        "State clearly what failed, what is missing, and what has been verified so far.",
        "Offer the safest next action instead of improvising around missing approvals or context.",
        "Record reusable lessons in decision or mistake memory when the failure should influence future work.",
    ]


def make_forbidden_actions(agent, department_record):
    actions = list(department_record["forbidden_actions"])
    actions.extend(
        [
            "Do not claim work is complete when it has not been verified.",
            "Do not expose secrets, credentials, or sensitive internal records.",
            "Do not execute destructive or externally impactful actions without the required approval and logging.",
        ]
    )
    unique = []
    for action in actions:
        if action not in unique:
            unique.append(action)
    return unique[:6]


def make_common_mistakes(agent, entry):
    mistakes = [
        "Acting outside the assigned department boundary because the request sounds adjacent.",
        "Skipping approvals or escalation details when the work feels routine but the impact is not.",
        "Producing outputs that are hard for the next agent or human to audit or continue.",
    ]
    if entry["company_department"] == "design":
        mistakes.append("Treating visual preference as final without checking brand, accessibility, or implementation constraints.")
    if entry["company_department"] == "development":
        mistakes.append("Recommending implementation changes without stating rollout, testing, or rollback implications.")
    if entry["company_department"] in {"finance", "legal", "security", "infrastructure"}:
        mistakes.append("Normalizing risky operational changes as if they were low-risk drafting work.")
    return mistakes[:5]


def make_performance_metrics(department_record):
    return department_record["primary_kpis"]


def make_example_tasks(agent, entry):
    role_name = titleize_slug(agent["role"]).lower()
    team_name = entry["team_display_name"].lower()
    return [
        f"Review an incoming request and produce a scoped {role_name} plan for the {team_name} function.",
        f"Prepare a traceable deliverable that stays within {COMPANY_DISPLAY_NAMES[entry['company_department']].lower()} authority boundaries.",
        f"Escalate a high-risk or blocked {role_name} issue with clear next-step guidance.",
    ]


def make_example_good_output(agent, entry):
    return (
        f"Status: scoped. Owner: {agent['name']}. Approval ceiling checked: {agent['approval_level']}. "
        f"Recommendation: produce a {titleize_slug(agent['role']).lower()} deliverable for {entry['team_display_name'].lower()}. "
        f"Risks: documented. Escalation: {entry['reports_to']} only if scope grows."
    )


def make_example_bad_output():
    return (
        "I'll just handle everything now. No approvals needed, no risks to mention, and no need to document next steps."
    )


def build_block(agent, entry, department_record):
    collaborators = make_collaborators(agent, entry, department_record)
    sections = {
        "Position": make_position(agent),
        "Department": make_department(agent, entry),
        "Reports To": entry["reports_to"],
        "Collaborates With": bullets(collaborators),
        "Mission": make_mission(agent, entry, department_record),
        "Responsibilities": bullets(make_responsibilities(agent, entry, department_record)),
        "Skills": bullets(make_skills(agent, entry)),
        "Tools": bullets(make_tools(agent)),
        "Knowledge Sources": bullets(make_knowledge_sources(entry)),
        "Memory Access": bullets(make_memory_access(entry)),
        "Tool Access Level": make_tool_access_level(agent, entry),
        "Inputs": bullets(make_inputs(agent, entry)),
        "Input Validation Rules": bullets(make_input_validation_rules(agent, entry)),
        "Outputs": bullets(make_outputs(agent, entry)),
        "Output Quality Checklist": bullets(make_output_quality_checklist(entry)),
        "Review Checklist": bullets(make_review_checklist(entry)),
        "Decision Authority": bullets(make_decision_authority(agent, entry)),
        "Approval Level": make_approval_level(agent),
        "Risk Level": make_risk_level(agent),
        "Escalation Rules": bullets(make_escalation_rules(agent, entry, department_record)),
        "Escalation Message Template": make_escalation_message_template(agent, entry),
        "Failure Response": bullets(make_failure_response(entry)),
        "Forbidden Actions": bullets(make_forbidden_actions(agent, department_record)),
        "Common Mistakes To Avoid": bullets(make_common_mistakes(agent, entry)),
        "Performance Metrics": bullets(make_performance_metrics(department_record)),
        "Example Tasks": bullets(make_example_tasks(agent, entry)),
        "Example Good Output": make_example_good_output(agent, entry),
        "Example Bad Output": make_example_bad_output(),
        "Version": VERSION,
        "Last Updated": LAST_UPDATED,
    }

    rendered = [START_MARKER, f"# {agent['name']}", ""]
    for section in REQUIRED_SECTIONS:
        rendered.append(f"## {section}")
        rendered.append(sections[section])
        rendered.append("")
    rendered.append(END_MARKER)
    return "\n".join(rendered).rstrip() + "\n"


def strip_existing_block(content):
    pattern = re.compile(rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\s*", re.DOTALL)
    return re.sub(pattern, "", content).lstrip()


def standardize_prompt(agent, structure_by_name, departments_by_slug):
    prompt_path = PROMPTS_DIR / agent["prompt_file"]
    original = prompt_path.read_text(encoding="utf-8")
    remaining = strip_existing_block(original)

    if "## Legacy Profile" in remaining:
        body = remaining
    else:
        body = "## Legacy Profile\n\n" + remaining.lstrip()

    entry = structure_by_name[agent["name"]]
    department_record = departments_by_slug[entry["company_department"]]
    prompt_path.write_text(build_block(agent, entry, department_record) + "\n" + body.rstrip() + "\n", encoding="utf-8")


def main():
    agents = load_registry()
    _, structure_by_name, departments_by_slug = load_structure()
    for agent in agents:
        standardize_prompt(agent, structure_by_name, departments_by_slug)
        print(f"standardized {agent['prompt_file']}")


if __name__ == "__main__":
    main()
