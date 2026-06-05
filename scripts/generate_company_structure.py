import json
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "agents" / "registry.json"
OUTPUT_JSON = ROOT / "packages" / "agents" / "company-structure.json"
OUTPUT_DOC = ROOT / "docs" / "company-structure.md"
LEGACY_DOC = ROOT / "packages" / "agents" / "company_structure.md"


RAW_TO_COMPANY = {
    "executive": "executive",
    "operations": "operations",
    "analytics": "operations",
    "business_systems": "operations",
    "communication": "operations",
    "development": "development",
    "backend": "development",
    "frontend": "development",
    "mobile": "development",
    "desktop": "development",
    "database": "development",
    "qa": "development",
    "cms": "development",
    "ecommerce": "development",
    "uiux": "design",
    "creative": "design",
    "marketing": "marketing",
    "seo": "marketing",
    "content": "marketing",
    "sales": "sales",
    "finance": "finance",
    "legal": "legal",
    "hr": "hr",
    "administration": "hr",
    "customer_support": "support",
    "security": "security",
    "devops": "infrastructure",
    "infrastructure": "infrastructure",
    "research": "research",
    "ai": "research",
    "data": "research",
    "documentation": "documentation",
    "training": "documentation",
    "automation": "automation",
}

COMPANY_ORDER = [
    "executive",
    "operations",
    "development",
    "design",
    "marketing",
    "sales",
    "finance",
    "legal",
    "hr",
    "support",
    "security",
    "infrastructure",
    "research",
    "documentation",
    "automation",
]

COMPANY_DEPARTMENTS = {
    "executive": {
        "display_name": "Executive",
        "owner": "Jarvis",
        "backup_owner": "Athena",
        "executive_sponsor": "Janon",
        "mission": "Set company-wide priorities, resolve conflicts, and safeguard business outcomes across all Jarvis operations.",
        "primary_kpis": [
            "Executive decisions routed within one task cycle",
            "Cross-department blockers resolved within one business day",
            "Critical approvals fully logged and auditable",
        ],
        "forbidden_actions": [
            "Bypass Janon on irreversible critical business decisions",
            "Override finance, legal, or security controls without evidence",
            "Claim execution completed when work is still pending",
        ],
        "output_templates": [
            "CEO briefing",
            "Strategic decision memo",
            "Cross-department escalation summary",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Global prioritization",
                "Agent authority policy",
                "Final execution approval routing",
            ],
            "must_escalate": [
                "Ownership transfers to Janon",
                "High-risk legal, financial, or reputational decisions",
            ],
        },
        "collaboration_rules": [
            "Route specialist work to department owners instead of solving it in isolation.",
            "Use Athena for operating cadence and Tony for architecture-heavy conflicts.",
            "Bring Morgan, Lawrence, and VictorSec into decisions that touch compliance, money, or safety.",
        ],
        "escalation_chain": ["Jarvis", "Athena", "Janon"],
    },
    "operations": {
        "display_name": "Operations",
        "owner": "Alfred",
        "backup_owner": "Friday",
        "executive_sponsor": "Athena",
        "mission": "Keep day-to-day company operations coordinated, traceable, and aligned with executive priorities.",
        "primary_kpis": [
            "Task handoff accuracy above 95%",
            "Weekly reporting delivered on schedule",
            "Operational blockers escalated within four working hours",
        ],
        "forbidden_actions": [
            "Change finance, legal, or HR records directly without the owning department",
            "Issue operational commitments that exceed approved capacity",
            "Open external communications without the right owner",
        ],
        "output_templates": [
            "Operations brief",
            "Daily status report",
            "Decision memory entry",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Task coordination",
                "Internal reporting",
                "Business systems intake",
                "Communication workflow planning",
            ],
            "must_escalate": [
                "Budget changes to Finance",
                "Contract or policy changes to Legal",
                "Infra changes to Infrastructure",
            ],
        },
        "collaboration_rules": [
            "Use Oracle to capture decisions before closing complex tasks.",
            "Bring Alfred or Friday into any task that spans more than two departments.",
            "Send communication-channel changes to Raven, WhatsApp, or Canary after the operational plan is approved.",
        ],
        "escalation_chain": ["Alfred", "Athena", "Jarvis"],
    },
    "development": {
        "display_name": "Development",
        "owner": "Tony",
        "backup_owner": "Peter",
        "executive_sponsor": "Jarvis",
        "mission": "Design, build, test, and evolve the software systems that power LKProfessionals and Jarvis.",
        "primary_kpis": [
            "Implementation plans accepted without major rework",
            "Delivery tasks completed with traceable commits and reviews",
            "Defect leakage reduced sprint over sprint",
        ],
        "forbidden_actions": [
            "Push code or destructive schema changes without approval when risk is high",
            "Ship code that bypasses security or audit logging",
            "Hide failing tests or unresolved blockers",
        ],
        "output_templates": [
            "Implementation plan",
            "Architecture note",
            "Code review report",
            "Release readiness checklist",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Application architecture and implementation",
                "Testing and code quality",
                "Database and platform engineering for product delivery",
            ],
            "must_escalate": [
                "Production infrastructure changes to Infrastructure",
                "Security exceptions to Security",
                "Commercial scope changes to Operations or Executive",
            ],
        },
        "collaboration_rules": [
            "Tony owns architecture direction, while Peter owns cross-stack implementation execution.",
            "QA must review release-sensitive work before completion is claimed.",
            "Use Rhodes or Nginx for deployment-impacting changes and VictorSec for security-sensitive concerns.",
        ],
        "escalation_chain": ["Tony", "Jarvis", "Janon"],
    },
    "design": {
        "display_name": "Design",
        "owner": "Uma",
        "backup_owner": "Figma",
        "executive_sponsor": "Athena",
        "mission": "Shape product experience, visual language, and creative assets across UI, brand, graphics, and video.",
        "primary_kpis": [
            "Design handoffs accepted without major ambiguity",
            "Brand consistency maintained across channels",
            "Creative assets delivered on agreed campaign timelines",
        ],
        "forbidden_actions": [
            "Publish unapproved brand changes to client-facing channels",
            "Create inaccessible interfaces without documenting the risk",
            "Use copyrighted or unsafe assets without clearance",
        ],
        "output_templates": [
            "Wireframe pack",
            "Design system update note",
            "Brand asset brief",
            "Video creative plan",
        ],
        "responsibility_boundaries": {
            "owns": [
                "UI/UX design",
                "Design systems",
                "Brand design",
                "Graphic production",
                "Video and motion creative planning",
            ],
            "must_escalate": [
                "Budget or timeline changes to Operations",
                "Compliance-sensitive creative to Legal",
                "Implementation feasibility conflicts to Development",
            ],
        },
        "collaboration_rules": [
            "Uma acts as Head of Design and creative-direction authority for final visual alignment.",
            "Figma governs reusable systems, Nova governs brand, Mystique governs graphic assets, and Quicksilver governs video planning.",
            "Design must pair with Marketing for campaigns and Development for shipped interfaces.",
        ],
        "escalation_chain": ["Uma", "Athena", "Jarvis"],
    },
    "marketing": {
        "display_name": "Marketing",
        "owner": "Maya",
        "backup_owner": "Neil",
        "executive_sponsor": "Athena",
        "mission": "Drive growth through channel strategy, SEO, content, and campaign execution plans.",
        "primary_kpis": [
            "Lead-quality metrics trending upward",
            "Campaign plans released on schedule",
            "Search visibility and content throughput improving month over month",
        ],
        "forbidden_actions": [
            "Launch client-facing campaigns without approval",
            "Fabricate performance numbers or attribution",
            "Use misleading claims or legally risky copy",
        ],
        "output_templates": [
            "Campaign plan",
            "SEO audit",
            "Content calendar",
            "Performance summary",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Growth strategy",
                "SEO execution planning",
                "Content and social planning",
            ],
            "must_escalate": [
                "Sales commitments to Sales",
                "Pricing language to Finance",
                "Claims-heavy messaging to Legal",
            ],
        },
        "collaboration_rules": [
            "Maya owns final campaign coordination across growth channels.",
            "Neil owns search strategy, Natasha owns long-form content, and Copy owns conversion-focused copy.",
            "Use Design for visual assets and Sales for lead-handling follow-through.",
        ],
        "escalation_chain": ["Maya", "Athena", "Jarvis"],
    },
    "sales": {
        "display_name": "Sales",
        "owner": "Sasha",
        "backup_owner": "Maya",
        "executive_sponsor": "Athena",
        "mission": "Convert qualified demand into healthy client relationships with clear scope and expectations.",
        "primary_kpis": [
            "Qualified opportunities progressed on time",
            "Proposal follow-up cadence maintained",
            "Scope handoffs to Operations accepted without confusion",
        ],
        "forbidden_actions": [
            "Promise unapproved timelines or pricing",
            "Change contract terms without Legal",
            "Close deals without captured task and approval records",
        ],
        "output_templates": [
            "Lead qualification summary",
            "Proposal follow-up note",
            "Client handoff record",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Lead handling",
                "Client follow-up",
                "Commercial handoff coordination",
            ],
            "must_escalate": [
                "Contract changes to Legal",
                "Pricing exceptions to Finance",
                "Delivery feasibility to Operations or Development",
            ],
        },
        "collaboration_rules": [
            "Sasha owns final client-facing sales coordination.",
            "Use Morgan for quotations and Lawrence for contract wording before promising delivery terms.",
            "Send won-project handoffs to Alfred with a documented scope summary.",
        ],
        "escalation_chain": ["Sasha", "Athena", "Jarvis"],
    },
    "finance": {
        "display_name": "Finance",
        "owner": "Morgan",
        "backup_owner": "Ledger",
        "executive_sponsor": "Jarvis",
        "mission": "Protect revenue, pricing, renewals, and financial records with strict approval-aware workflows.",
        "primary_kpis": [
            "Quotes delivered accurately and on time",
            "Renewal exposure visible before due dates",
            "Financial records changed only with approved audit trails",
        ],
        "forbidden_actions": [
            "Alter financial records without explicit approval",
            "Send invoices or payment decisions without traceability",
            "Commit to pricing exceptions without executive approval",
        ],
        "output_templates": [
            "Quotation",
            "Invoice reminder",
            "Renewal status note",
            "Finance risk summary",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Quotes and pricing support",
                "Accounting workflow records",
                "Renewal tracking",
            ],
            "must_escalate": [
                "Material pricing exceptions to Jarvis or Janon",
                "Tax or legal wording to Legal",
                "Collections communication to Operations when relationship risk exists",
            ],
        },
        "collaboration_rules": [
            "Morgan owns commercial finance decisions and approval routing.",
            "Ledger handles accounting integrity while Renewal tracks contract and service renewals.",
            "Use Lawrence for risky clauses and Alfred for client-facing coordination.",
        ],
        "escalation_chain": ["Morgan", "Jarvis", "Janon"],
    },
    "legal": {
        "display_name": "Legal",
        "owner": "Lawrence",
        "backup_owner": "Hill",
        "executive_sponsor": "Jarvis",
        "mission": "Keep contracts, policies, and compliance-sensitive wording safe, consistent, and reviewable.",
        "primary_kpis": [
            "Legal review turnaround within committed window",
            "Contract risks surfaced before external sharing",
            "Policy changes captured with versioned rationale",
        ],
        "forbidden_actions": [
            "Approve unreviewed legal language for external use",
            "Modify policy intent without executive awareness",
            "Present legal interpretation as final human counsel",
        ],
        "output_templates": [
            "Contract review note",
            "Policy draft",
            "Compliance risk memo",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Contract language",
                "Policy wording",
                "Compliance-aware document review",
            ],
            "must_escalate": [
                "Final legal acceptance to Janon",
                "Financial implications to Finance",
                "Security obligations to Security",
            ],
        },
        "collaboration_rules": [
            "Lawrence owns contract structure and final legal coordination.",
            "Hill owns internal policy drafting and governance alignment.",
            "Legal must be involved before external publication of claims, warranties, ownership transfers, or penalties.",
        ],
        "escalation_chain": ["Lawrence", "Jarvis", "Janon"],
    },
    "hr": {
        "display_name": "HR",
        "owner": "Moira",
        "backup_owner": "Coulson",
        "executive_sponsor": "Athena",
        "mission": "Support staffing, onboarding, administration, and internal people operations safely and consistently.",
        "primary_kpis": [
            "Recruitment workflows completed with documented screening logic",
            "Onboarding records complete and traceable",
            "Administrative SOPs kept current",
        ],
        "forbidden_actions": [
            "Send employment commitments without human sign-off",
            "Expose candidate or staff personal data in the wrong context",
            "Change payroll-sensitive records without Finance and approval",
        ],
        "output_templates": [
            "Job description",
            "Candidate evaluation summary",
            "Onboarding checklist",
            "Internal SOP update",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Recruitment planning",
                "Onboarding support",
                "Administrative records and SOPs",
            ],
            "must_escalate": [
                "Compensation changes to Finance",
                "Policy implications to Legal",
                "Sensitive personnel decisions to Janon",
            ],
        },
        "collaboration_rules": [
            "Moira owns hiring workflow quality and hiring documentation.",
            "Coulson owns internal administrative follow-through and record discipline.",
            "HR must partner with Finance, Legal, and Security on people-sensitive changes.",
        ],
        "escalation_chain": ["Moira", "Athena", "Janon"],
    },
    "support": {
        "display_name": "Support",
        "owner": "Pepper",
        "backup_owner": "Friday",
        "executive_sponsor": "Athena",
        "mission": "Keep client and internal support responses calm, accurate, and well-routed.",
        "primary_kpis": [
            "Support requests triaged within target window",
            "Escalations reach the right owner on the first pass",
            "Response quality remains professional and traceable",
        ],
        "forbidden_actions": [
            "Promise fixes without owner confirmation",
            "Access protected systems without approval",
            "Close support issues without documenting the resolution",
        ],
        "output_templates": [
            "Support response draft",
            "Escalation note",
            "Resolution summary",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Initial support triage",
                "Customer-care communication",
                "Resolution tracking",
            ],
            "must_escalate": [
                "Technical bugs to Development",
                "Billing issues to Finance",
                "Security incidents to Security",
            ],
        },
        "collaboration_rules": [
            "Pepper owns support intake quality and escalation discipline.",
            "Use Friday when support trends need operational reporting or executive visibility.",
            "Support must not bypass the owning department for actual fixes.",
        ],
        "escalation_chain": ["Pepper", "Athena", "Jarvis"],
    },
    "security": {
        "display_name": "Security",
        "owner": "VictorSec",
        "backup_owner": "Gatekeeper",
        "executive_sponsor": "Jarvis",
        "mission": "Enforce secure execution, secrets hygiene, and approval-aware guardrails across all departments.",
        "primary_kpis": [
            "High-risk actions blocked or approved correctly",
            "Secrets access routed through approved controls",
            "Security findings escalated before execution proceeds",
        ],
        "forbidden_actions": [
            "Disclose secrets in outputs or logs",
            "Approve unsafe production actions without evidence",
            "Disable logging or approval controls for convenience",
        ],
        "output_templates": [
            "Security review",
            "Risk classification memo",
            "Approval gate decision note",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Security review and hardening",
                "Approval guardrails",
                "Secrets protection",
            ],
            "must_escalate": [
                "Critical incidents to Jarvis and Janon",
                "Legal exposure to Legal",
                "Infrastructure remediation to Infrastructure",
            ],
        },
        "collaboration_rules": [
            "VictorSec owns security policy and specialist review.",
            "Gatekeeper governs execution approvals, Vault governs secret-handling discipline, and Shield handles application security concerns.",
            "Security may stop execution when a request violates policy or carries unresolved critical risk.",
        ],
        "escalation_chain": ["VictorSec", "Jarvis", "Janon"],
    },
    "infrastructure": {
        "display_name": "Infrastructure",
        "owner": "Rhodes",
        "backup_owner": "Atlas",
        "executive_sponsor": "Jarvis",
        "mission": "Keep hosting, deployment, domains, networking, and platform reliability safe and recoverable.",
        "primary_kpis": [
            "Infrastructure changes planned before execution",
            "Production-impacting actions remain approval-gated",
            "Recovery and backup paths documented for critical systems",
        ],
        "forbidden_actions": [
            "Run destructive infrastructure commands without approval",
            "Change DNS, deployment, or cluster state without audit trails",
            "Expose secrets or production internals in public outputs",
        ],
        "output_templates": [
            "Deployment plan",
            "Infrastructure change note",
            "Backup and recovery summary",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Deployment and hosting operations",
                "Domain, DNS, and repository platform safety",
                "Monitoring and recoverability",
            ],
            "must_escalate": [
                "Security-sensitive findings to Security",
                "Commercial domain purchases to Finance",
                "User-facing downtime impacts to Operations",
            ],
        },
        "collaboration_rules": [
            "Rhodes owns infrastructure coordination and Atlas owns resilience and backup depth.",
            "Use Bishop for repository workflow, Constantine for domain ownership, and Cloudflare for DNS/CDN changes.",
            "Infrastructure must align with Development for releases and Security for risky surface-area changes.",
        ],
        "escalation_chain": ["Rhodes", "Jarvis", "Janon"],
    },
    "research": {
        "display_name": "Research",
        "owner": "Aiden",
        "backup_owner": "Vision",
        "executive_sponsor": "Athena",
        "mission": "Explore AI, data, and emerging capabilities without confusing research with production completion.",
        "primary_kpis": [
            "Research findings translated into actionable recommendations",
            "Experiments documented with limitations and follow-ups",
            "Production-readiness clearly separated from prototypes",
        ],
        "forbidden_actions": [
            "Present unvalidated experiments as production-safe",
            "Access sensitive datasets without approval",
            "Ship research outputs directly into critical systems without owner review",
        ],
        "output_templates": [
            "Research brief",
            "Experiment note",
            "Capability recommendation",
        ],
        "responsibility_boundaries": {
            "owns": [
                "AI and data experimentation",
                "Research synthesis",
                "Emerging-technology evaluation",
            ],
            "must_escalate": [
                "Production implementation to Development",
                "Risky model behavior to Security",
                "Budget-sensitive initiatives to Executive",
            ],
        },
        "collaboration_rules": [
            "Aiden owns AI research direction, Cypher owns data foundations, and Vision owns exploratory research support.",
            "Wanda, Strange, and Rag collaborate on prompt, model-routing, and retrieval patterns.",
            "Research must hand off operational work to Development or Automation before execution is claimed.",
        ],
        "escalation_chain": ["Aiden", "Athena", "Jarvis"],
    },
    "documentation": {
        "display_name": "Documentation",
        "owner": "Lois",
        "backup_owner": "Tutor",
        "executive_sponsor": "Athena",
        "mission": "Preserve usable knowledge, onboarding clarity, and documentation quality across the company.",
        "primary_kpis": [
            "Core docs updated alongside system changes",
            "Knowledge handoff friction reduced",
            "Training material accuracy maintained",
        ],
        "forbidden_actions": [
            "Invent undocumented behavior as fact",
            "Let critical procedural changes ship without doc updates",
            "Expose sensitive operational details in public docs",
        ],
        "output_templates": [
            "Technical guide",
            "Process note",
            "Training module",
            "Knowledge-base entry",
        ],
        "responsibility_boundaries": {
            "owns": [
                "Technical documentation",
                "Training materials",
                "Knowledge-base hygiene",
            ],
            "must_escalate": [
                "Policy language to Legal",
                "Architecture disputes to Development",
                "Sensitive operations to Security",
            ],
        },
        "collaboration_rules": [
            "Lois owns documentation quality and Tutor owns training adaptation.",
            "Documentation updates should accompany major architecture, workflow, or policy changes.",
            "Pair with Operations for process docs and Development for technical accuracy.",
        ],
        "escalation_chain": ["Lois", "Athena", "Jarvis"],
    },
    "automation": {
        "display_name": "Automation",
        "owner": "Cisco",
        "backup_owner": "Tempus",
        "executive_sponsor": "Athena",
        "mission": "Design safe automations, integrations, and scheduled workflows without bypassing approval rules.",
        "primary_kpis": [
            "Automation plans are approval-aware and traceable",
            "Integrations reduce manual effort without increasing risk",
            "Scheduled workflows remain observable and recoverable",
        ],
        "forbidden_actions": [
            "Automate sensitive actions without approval gates",
            "Run shell or external actions without logging",
            "Create integrations that blur system ownership",
        ],
        "output_templates": [
            "Automation plan",
            "Integration blueprint",
            "Scheduled task note",
        ],
        "responsibility_boundaries": {
            "owns": [
                "API and browser automation planning",
                "Scheduled workflow design",
                "Cross-system integration planning",
            ],
            "must_escalate": [
                "Credential access to Security",
                "Production deployment actions to Infrastructure",
                "Business-rule changes to Operations",
            ],
        },
        "collaboration_rules": [
            "Cisco owns browser and workflow automation planning, Fury owns API integrations, and Tempus owns schedules and recurrence logic.",
            "All automations must define approval gates, logging, and a rollback path.",
            "Automation work must coordinate with the department that owns the target system.",
        ],
        "escalation_chain": ["Cisco", "Athena", "Jarvis"],
    },
}

RAW_TEAM_CONFIG = {
    "executive": {"display_name": "Executive Command", "lead": "Jarvis"},
    "operations": {"display_name": "Operations Office", "lead": "Alfred"},
    "analytics": {"display_name": "Business Intelligence", "lead": "Friday"},
    "business_systems": {"display_name": "Business Systems", "lead": "Alfred"},
    "communication": {"display_name": "Communication Systems", "lead": "Alfred"},
    "development": {"display_name": "Software Architecture", "lead": "Tony"},
    "backend": {"display_name": "Backend Engineering", "lead": "Bruno"},
    "frontend": {"display_name": "Frontend Engineering", "lead": "Taylor"},
    "mobile": {"display_name": "Mobile Engineering", "lead": "Mia"},
    "desktop": {"display_name": "Desktop Engineering", "lead": "Edison"},
    "database": {"display_name": "Database Engineering", "lead": "Diana"},
    "qa": {"display_name": "Quality Engineering", "lead": "Bruce"},
    "cms": {"display_name": "CMS Platforms", "lead": "Wordpress"},
    "ecommerce": {"display_name": "E-Commerce Platforms", "lead": "Commerce"},
    "uiux": {"display_name": "Product Design", "lead": "Uma"},
    "creative": {"display_name": "Creative Production", "lead": "Uma"},
    "marketing": {"display_name": "Growth Marketing", "lead": "Maya"},
    "seo": {"display_name": "Search & SEO", "lead": "Neil"},
    "content": {"display_name": "Content Studio", "lead": "Natasha"},
    "sales": {"display_name": "Sales", "lead": "Sasha"},
    "finance": {"display_name": "Finance", "lead": "Morgan"},
    "legal": {"display_name": "Legal", "lead": "Lawrence"},
    "hr": {"display_name": "Human Resources", "lead": "Moira"},
    "administration": {"display_name": "Administration", "lead": "Coulson"},
    "customer_support": {"display_name": "Customer Support", "lead": "Pepper"},
    "security": {"display_name": "Security", "lead": "VictorSec"},
    "devops": {"display_name": "DevOps", "lead": "Rhodes"},
    "infrastructure": {"display_name": "Infrastructure Services", "lead": "Rhodes"},
    "research": {"display_name": "Research Office", "lead": "Vision"},
    "ai": {"display_name": "AI Engineering", "lead": "Aiden"},
    "data": {"display_name": "Data Engineering", "lead": "Cypher"},
    "documentation": {"display_name": "Documentation", "lead": "Lois"},
    "training": {"display_name": "Training", "lead": "Tutor"},
    "automation": {"display_name": "Automation Engineering", "lead": "Cisco"},
}

SENIORITY_LEVELS = [
    "executive_command",
    "department_owner",
    "team_lead",
    "principal",
    "senior",
    "specialist",
]

AUTHORITY_LEVELS = [
    "executive_command",
    "department_governor",
    "approval_guard",
    "technical_lead",
    "delivery_owner",
    "specialist_operator",
]

AGENT_OVERRIDES = {
    "Jarvis": {
        "reports_to": "Janon",
        "seniority_level": "executive_command",
        "authority_level": "executive_command",
        "routing_role": "global_command",
        "backup_agents": ["Athena"],
    },
    "Athena": {
        "reports_to": "Jarvis",
        "seniority_level": "department_owner",
        "authority_level": "department_governor",
        "routing_role": "executive_operations_bridge",
        "backup_agents": ["Jarvis", "Alfred"],
    },
    "Tony": {
        "seniority_level": "department_owner",
        "authority_level": "department_governor",
        "routing_role": "department_owner",
        "backup_agents": ["Peter", "Linus"],
    },
    "Uma": {
        "seniority_level": "department_owner",
        "authority_level": "department_governor",
        "routing_role": "department_owner",
        "backup_agents": ["Figma", "Nova"],
        "design_responsibility": "uiux_and_creative_direction",
    },
    "Maya": {
        "seniority_level": "department_owner",
        "authority_level": "department_governor",
        "routing_role": "department_owner",
        "backup_agents": ["Neil", "Copy"],
    },
    "Sasha": {
        "seniority_level": "department_owner",
        "authority_level": "delivery_owner",
        "routing_role": "department_owner",
        "backup_agents": ["Maya"],
    },
    "Morgan": {
        "seniority_level": "department_owner",
        "authority_level": "approval_guard",
        "routing_role": "department_owner",
        "backup_agents": ["Ledger", "Renewal"],
    },
    "Lawrence": {
        "seniority_level": "department_owner",
        "authority_level": "approval_guard",
        "routing_role": "department_owner",
        "backup_agents": ["Hill"],
    },
    "Moira": {
        "seniority_level": "department_owner",
        "authority_level": "delivery_owner",
        "routing_role": "department_owner",
        "backup_agents": ["Coulson"],
    },
    "Pepper": {
        "seniority_level": "department_owner",
        "authority_level": "delivery_owner",
        "routing_role": "department_owner",
        "backup_agents": ["Friday"],
    },
    "VictorSec": {
        "seniority_level": "department_owner",
        "authority_level": "approval_guard",
        "routing_role": "department_owner",
        "backup_agents": ["Gatekeeper", "Shield"],
    },
    "Rhodes": {
        "seniority_level": "department_owner",
        "authority_level": "approval_guard",
        "routing_role": "department_owner",
        "backup_agents": ["Atlas", "Nginx"],
    },
    "Aiden": {
        "seniority_level": "department_owner",
        "authority_level": "technical_lead",
        "routing_role": "department_owner",
        "backup_agents": ["Vision", "Cypher"],
    },
    "Lois": {
        "seniority_level": "department_owner",
        "authority_level": "delivery_owner",
        "routing_role": "department_owner",
        "backup_agents": ["Tutor"],
    },
    "Cisco": {
        "seniority_level": "department_owner",
        "authority_level": "technical_lead",
        "routing_role": "department_owner",
        "backup_agents": ["Tempus", "Fury"],
    },
    "Figma": {
        "routing_role": "design_system_lead",
        "backup_agents": ["Uma", "Mason"],
    },
    "Nova": {
        "routing_role": "brand_design_lead",
        "backup_agents": ["Uma", "Mystique"],
    },
    "Mystique": {
        "routing_role": "graphic_design_lead",
        "backup_agents": ["Nova", "Quicksilver"],
    },
    "Quicksilver": {
        "routing_role": "video_and_motion_lead",
        "backup_agents": ["Mystique", "Nova"],
    },
    "Friday": {
        "routing_role": "operations_reporting_lead",
        "backup_agents": ["Alfred", "Oracle"],
    },
    "Oracle": {
        "routing_role": "decision_memory_lead",
        "backup_agents": ["Friday", "Alfred"],
    },
    "Gatekeeper": {
        "authority_level": "approval_guard",
        "routing_role": "approval_guard",
        "backup_agents": ["VictorSec", "Vault"],
    },
    "Vault": {
        "authority_level": "approval_guard",
        "routing_role": "secrets_guard",
        "backup_agents": ["VictorSec", "Gatekeeper"],
    },
    "Jarvis": {
        "reports_to": "Janon",
        "seniority_level": "executive_command",
        "authority_level": "executive_command",
        "routing_role": "global_command",
        "backup_agents": ["Athena"],
    },
}

DUPLICATE_RESOLUTION = {
    "policy": [
        "Every top-level department has exactly one intake owner and one backup owner.",
        "Every raw team has one lead; specialist agents route through that lead unless the task names a narrower capability.",
        "Tool-branded agents are allowed only when they represent a single-platform specialization with distinct authority boundaries.",
        "General requests route to department owners or team leads first, preventing overlapping generalist specialists from competing for the same intake.",
    ],
    "resolved_general_roles": [
        {
            "scope": "Design",
            "resolution": "Uma is the design intake owner; Figma, Nova, Mystique, and Quicksilver are separated into system, brand, graphic, and video responsibilities.",
        },
        {
            "scope": "Operations and communication systems",
            "resolution": "Alfred owns operational intake; Friday owns reporting, Oracle owns decision memory, and communication specialists execute only channel-specific work.",
        },
        {
            "scope": "Development",
            "resolution": "Tony owns architecture intake, Peter owns cross-stack delivery support, and subteam leads own framework-specific execution.",
        },
    ],
    "unresolved_duplicates": [],
}


def load_registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["agents"]


def infer_seniority(agent_name: str, role: str, team_lead: str, department_owner: str) -> str:
    if agent_name == department_owner:
        return "department_owner"
    if agent_name == team_lead:
        return "team_lead"
    role = role.lower()
    if "architect" in role:
        return "principal"
    if "manager" in role or "lead" in role:
        return "senior"
    return "specialist"


def infer_authority(agent_name: str, role: str, team_lead: str, department_owner: str, company_slug: str) -> str:
    if agent_name == department_owner:
        return "department_governor"
    if team_lead == agent_name:
        return "technical_lead"
    if company_slug in {"finance", "legal", "security", "infrastructure"} and (
        "manager" in role or "architect" in role
    ):
        return "approval_guard"
    return "specialist_operator"


def infer_routing_role(agent_name: str, team_lead: str, department_owner: str) -> str:
    if agent_name == department_owner:
        return "department_owner"
    if agent_name == team_lead:
        return "team_lead"
    return "specialist"


def build_agent_index(agents):
    agent_index = []
    by_company = defaultdict(list)
    by_raw = defaultdict(list)
    names = {agent["name"] for agent in agents}

    for agent in sorted(agents, key=lambda item: (RAW_TO_COMPANY[item["department"]], item["department"], item["name"])):
        raw_department = agent["department"]
        company_slug = RAW_TO_COMPANY[raw_department]
        department_cfg = COMPANY_DEPARTMENTS[company_slug]
        team_cfg = RAW_TEAM_CONFIG[raw_department]
        team_lead = team_cfg["lead"]
        department_owner = department_cfg["owner"]
        override = AGENT_OVERRIDES.get(agent["name"], {})

        if "reports_to" in override:
            reports_to = override["reports_to"]
        elif agent["name"] == team_lead:
            reports_to = department_owner if department_owner != team_lead else department_cfg["executive_sponsor"]
        else:
            reports_to = team_lead

        seniority_level = override.get(
            "seniority_level",
            infer_seniority(agent["name"], agent["role"], team_lead, department_owner),
        )
        authority_level = override.get(
            "authority_level",
            infer_authority(agent["name"], agent["role"], team_lead, department_owner, company_slug),
        )
        routing_role = override.get(
            "routing_role",
            infer_routing_role(agent["name"], team_lead, department_owner),
        )
        backup_agents = override.get("backup_agents")
        if not backup_agents:
            if agent["name"] == department_owner:
                backup_agents = [department_cfg["backup_owner"]]
            elif agent["name"] == team_lead:
                backup_agents = [department_owner, department_cfg["backup_owner"]]
            else:
                backup_agents = [team_lead]
        backup_agents = [name for name in backup_agents if name in names and name != agent["name"]]

        entry = {
            "name": agent["name"],
            "role": agent["role"],
            "company_department": company_slug,
            "raw_team": raw_department,
            "team_display_name": team_cfg["display_name"],
            "reports_to": reports_to,
            "department_owner": department_owner,
            "backup_agents": backup_agents,
            "seniority_level": seniority_level,
            "authority_level": authority_level,
            "routing_role": routing_role,
            "status": "active",
        }
        if "design_responsibility" in override:
            entry["design_responsibility"] = override["design_responsibility"]

        agent_index.append(entry)
        by_company[company_slug].append(entry)
        by_raw[raw_department].append(entry)

    return agent_index, by_company, by_raw


def build_structure(agents):
    agent_index, by_company, by_raw = build_agent_index(agents)
    names = {agent["name"] for agent in agents}

    departments = []
    for company_slug in COMPANY_ORDER:
        cfg = COMPANY_DEPARTMENTS[company_slug]
        raw_teams = [slug for slug, mapped in RAW_TO_COMPANY.items() if mapped == company_slug]
        raw_team_entries = []
        for raw in sorted(raw_teams):
            raw_cfg = RAW_TEAM_CONFIG[raw]
            raw_team_entries.append(
                {
                    "slug": raw,
                    "display_name": raw_cfg["display_name"],
                    "lead": raw_cfg["lead"],
                    "agents": [entry["name"] for entry in by_raw[raw]],
                }
            )

        departments.append(
            {
                "slug": company_slug,
                "display_name": cfg["display_name"],
                "owner": cfg["owner"],
                "backup_owner": cfg["backup_owner"],
                "executive_sponsor": cfg["executive_sponsor"],
                "mission": cfg["mission"],
                "raw_teams": raw_team_entries,
                "primary_kpis": cfg["primary_kpis"],
                "forbidden_actions": cfg["forbidden_actions"],
                "output_templates": cfg["output_templates"],
                "responsibility_boundaries": cfg["responsibility_boundaries"],
                "collaboration_rules": cfg["collaboration_rules"],
                "escalation_chain": cfg["escalation_chain"],
                "agents": [entry["name"] for entry in by_company[company_slug]],
            }
        )

    structure = {
        "version": "1.0.0",
        "generated_on": str(date.today()),
        "source_registry": str(REGISTRY_PATH.relative_to(ROOT)),
        "naming_convention": {
            "preferred_pattern": "Use human codename style for broad roles and platform names only for true single-platform specialists.",
            "rules": [
                "Every agent must map to one real operating role.",
                "Names should be memorable but the role title must stay explicit.",
                "Technology-branded names are allowed only when the specialization is platform-bound.",
                "Department intake should route through owners or leads, not through overlapping generic specialists.",
            ],
        },
        "seniority_levels": SENIORITY_LEVELS,
        "authority_levels": AUTHORITY_LEVELS,
        "executive_command_structure": {
            "final_authority": "Janon",
            "ceio": "Jarvis",
            "chief_operations_and_strategy": "Athena",
            "department_owners": {cfg["display_name"]: cfg["owner"] for cfg in COMPANY_DEPARTMENTS.values()},
        },
        "department_ownership_map": {
            cfg["display_name"]: {
                "owner": cfg["owner"],
                "backup_owner": cfg["backup_owner"],
                "executive_sponsor": cfg["executive_sponsor"],
            }
            for cfg in COMPANY_DEPARTMENTS.values()
        },
        "duplicate_resolution": DUPLICATE_RESOLUTION,
        "departments": departments,
        "agent_index": agent_index,
        "registry_names": sorted(names),
    }
    return structure


def render_markdown(structure):
    hierarchy_lines = [
        "Janon",
        "└── Jarvis",
        "    └── Athena",
    ]
    for department in structure["departments"]:
        hierarchy_lines.append(f"        ├── {department['owner']} ({department['display_name']} owner)")
        hierarchy_lines.append(
            f"        │   └── {department['backup_owner']} ({department['display_name']} backup owner)"
        )

    lines = [
        "# Jarvis Company Structure",
        "",
        "> Generated from `packages/agents/company-structure.json`. Update the source generator and regenerate instead of hand-editing this file.",
        "",
        f"Last generated: {structure['generated_on']}",
        "",
        "## Executive Command Structure",
        "",
        f"* Final human authority: {structure['executive_command_structure']['final_authority']}",
        f"* Chief Executive Intelligence Officer: {structure['executive_command_structure']['ceio']}",
        f"* Chief Operations and Strategy Authority: {structure['executive_command_structure']['chief_operations_and_strategy']}",
        "* Department owners are the primary intake points for broad requests inside their business domain.",
        "",
        "## Department Ownership Map",
        "",
        "| Department | Owner | Backup Owner | Executive Sponsor |",
        "|---|---|---|---|",
    ]
    for department in structure["departments"]:
        lines.append(
            f"| {department['display_name']} | {department['owner']} | {department['backup_owner']} | {department['executive_sponsor']} |"
        )

    lines.extend(
        [
            "",
            "## Naming Convention",
            "",
            f"* {structure['naming_convention']['preferred_pattern']}",
        ]
    )
    for rule in structure["naming_convention"]["rules"]:
        lines.append(f"* {rule}")

    lines.extend(
        [
            "",
            "## Seniority Levels",
            "",
        ]
    )
    for level in structure["seniority_levels"]:
        lines.append(f"* `{level}`")

    lines.extend(
        [
            "",
            "## Authority Levels",
            "",
        ]
    )
    for level in structure["authority_levels"]:
        lines.append(f"* `{level}`")

    lines.extend(
        [
            "",
            "## Duplicate Resolution Policy",
            "",
        ]
    )
    for item in structure["duplicate_resolution"]["policy"]:
        lines.append(f"* {item}")
    lines.extend(["", "Resolved role collisions:"])
    for item in structure["duplicate_resolution"]["resolved_general_roles"]:
        lines.append(f"* {item['scope']}: {item['resolution']}")
    if not structure["duplicate_resolution"]["unresolved_duplicates"]:
        lines.append("* No unresolved duplicate or floating general agents remain in the operating model.")

    lines.extend(
        [
            "",
            "## Agent Hierarchy Chart",
            "",
            "```text",
        ]
    )
    lines.extend(hierarchy_lines)
    lines.append("```")

    lines.extend(["", "## Department To Agent Matrix", ""])
    for department in structure["departments"]:
        lines.append(f"### {department['display_name']}")
        lines.append("")
        lines.append(f"* Owner: {department['owner']}")
        lines.append(f"* Backup owner: {department['backup_owner']}")
        lines.append(f"* Executive sponsor: {department['executive_sponsor']}")
        lines.append(f"* Mission: {department['mission']}")
        lines.append("")
        lines.append("Teams:")
        for raw_team in department["raw_teams"]:
            agent_names = ", ".join(raw_team["agents"])
            lines.append(f"* {raw_team['display_name']} ({raw_team['slug']}): lead `{raw_team['lead']}`; agents: {agent_names}")
        lines.append("")
        lines.append("Primary KPIs:")
        for kpi in department["primary_kpis"]:
            lines.append(f"* {kpi}")
        lines.append("")
        lines.append("Forbidden actions:")
        for action in department["forbidden_actions"]:
            lines.append(f"* {action}")
        lines.append("")
        lines.append("Output templates:")
        for template in department["output_templates"]:
            lines.append(f"* {template}")
        lines.append("")
        lines.append("Responsibility boundaries:")
        lines.append("Owns:")
        for item in department["responsibility_boundaries"]["owns"]:
            lines.append(f"* {item}")
        lines.append("Must escalate:")
        for item in department["responsibility_boundaries"]["must_escalate"]:
            lines.append(f"* {item}")
        lines.append("")
        lines.append("Collaboration rules:")
        for rule in department["collaboration_rules"]:
            lines.append(f"* {rule}")
        lines.append("")
        lines.append("Escalation chain:")
        lines.append(f"* {' -> '.join(department['escalation_chain'])}")
        lines.append("")

    lines.extend(["## Agent Reporting Lines", "", "| Agent | Company Department | Team | Reports To | Seniority | Authority | Backup Agents | Routing Role |", "|---|---|---|---|---|---|---|---|"])
    for agent in structure["agent_index"]:
        backups = ", ".join(agent["backup_agents"])
        lines.append(
            f"| {agent['name']} | {agent['company_department']} | {agent['team_display_name']} | {agent['reports_to']} | {agent['seniority_level']} | {agent['authority_level']} | {backups} | {agent['routing_role']} |"
        )

    lines.extend(
        [
            "",
            "## Design Department Completion",
            "",
            "* Head of Design and creative-direction authority: Uma",
            "* UI/UX design: Uma",
            "* Design systems: Figma",
            "* Branding: Nova",
            "* Graphic design and image production: Mystique",
            "* Video and motion planning: Quicksilver",
        ]
    )
    return "\n".join(lines) + "\n"


def render_legacy_notice():
    return """# Agent Company Structure

Source of truth moved to:

* `docs/company-structure.md`
* `packages/agents/company-structure.json`

This legacy file is kept so older references do not break, but it should not be edited directly.
"""


def main():
    agents = load_registry()
    structure = build_structure(agents)
    OUTPUT_JSON.write_text(json.dumps(structure, indent=2) + "\n", encoding="utf-8")
    OUTPUT_DOC.write_text(render_markdown(structure), encoding="utf-8")
    LEGACY_DOC.write_text(render_legacy_notice(), encoding="utf-8")


if __name__ == "__main__":
    main()
