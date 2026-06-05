# Jarvis Company Structure

> Generated from `packages/agents/company-structure.json`. Update the source generator and regenerate instead of hand-editing this file.

Last generated: 2026-06-06

## Executive Command Structure

* Final human authority: Janon
* Chief Executive Intelligence Officer: Jarvis
* Chief Operations and Strategy Authority: Athena
* Department owners are the primary intake points for broad requests inside their business domain.

## Department Ownership Map

| Department | Owner | Backup Owner | Executive Sponsor |
|---|---|---|---|
| Executive | Jarvis | Athena | Janon |
| Operations | Alfred | Friday | Athena |
| Development | Tony | Peter | Jarvis |
| Design | Uma | Figma | Athena |
| Marketing | Maya | Neil | Athena |
| Sales | Sasha | Maya | Athena |
| Finance | Morgan | Ledger | Jarvis |
| Legal | Lawrence | Hill | Jarvis |
| HR | Moira | Coulson | Athena |
| Support | Pepper | Friday | Athena |
| Security | VictorSec | Gatekeeper | Jarvis |
| Infrastructure | Rhodes | Atlas | Jarvis |
| Research | Aiden | Vision | Athena |
| Documentation | Lois | Tutor | Athena |
| Automation | Cisco | Tempus | Athena |

## Naming Convention

* Use human codename style for broad roles and platform names only for true single-platform specialists.
* Every agent must map to one real operating role.
* Names should be memorable but the role title must stay explicit.
* Technology-branded names are allowed only when the specialization is platform-bound.
* Department intake should route through owners or leads, not through overlapping generic specialists.

## Seniority Levels

* `executive_command`
* `department_owner`
* `team_lead`
* `principal`
* `senior`
* `specialist`

## Authority Levels

* `executive_command`
* `department_governor`
* `approval_guard`
* `technical_lead`
* `delivery_owner`
* `specialist_operator`

## Duplicate Resolution Policy

* Every top-level department has exactly one intake owner and one backup owner.
* Every raw team has one lead; specialist agents route through that lead unless the task names a narrower capability.
* Tool-branded agents are allowed only when they represent a single-platform specialization with distinct authority boundaries.
* General requests route to department owners or team leads first, preventing overlapping generalist specialists from competing for the same intake.

Resolved role collisions:
* Design: Uma is the design intake owner; Figma, Nova, Mystique, and Quicksilver are separated into system, brand, graphic, and video responsibilities.
* Operations and communication systems: Alfred owns operational intake; Friday owns reporting, Oracle owns decision memory, and communication specialists execute only channel-specific work.
* Development: Tony owns architecture intake, Peter owns cross-stack delivery support, and subteam leads own framework-specific execution.
* No unresolved duplicate or floating general agents remain in the operating model.

## Agent Hierarchy Chart

```text
Janon
└── Jarvis
    └── Athena
        ├── Jarvis (Executive owner)
        │   └── Athena (Executive backup owner)
        ├── Alfred (Operations owner)
        │   └── Friday (Operations backup owner)
        ├── Tony (Development owner)
        │   └── Peter (Development backup owner)
        ├── Uma (Design owner)
        │   └── Figma (Design backup owner)
        ├── Maya (Marketing owner)
        │   └── Neil (Marketing backup owner)
        ├── Sasha (Sales owner)
        │   └── Maya (Sales backup owner)
        ├── Morgan (Finance owner)
        │   └── Ledger (Finance backup owner)
        ├── Lawrence (Legal owner)
        │   └── Hill (Legal backup owner)
        ├── Moira (HR owner)
        │   └── Coulson (HR backup owner)
        ├── Pepper (Support owner)
        │   └── Friday (Support backup owner)
        ├── VictorSec (Security owner)
        │   └── Gatekeeper (Security backup owner)
        ├── Rhodes (Infrastructure owner)
        │   └── Atlas (Infrastructure backup owner)
        ├── Aiden (Research owner)
        │   └── Vision (Research backup owner)
        ├── Lois (Documentation owner)
        │   └── Tutor (Documentation backup owner)
        ├── Cisco (Automation owner)
        │   └── Tempus (Automation backup owner)
```

## Department To Agent Matrix

### Executive

* Owner: Jarvis
* Backup owner: Athena
* Executive sponsor: Janon
* Mission: Set company-wide priorities, resolve conflicts, and safeguard business outcomes across all Jarvis operations.

Teams:
* Executive Command (executive): lead `Jarvis`; agents: Athena, Jarvis

Primary KPIs:
* Executive decisions routed within one task cycle
* Cross-department blockers resolved within one business day
* Critical approvals fully logged and auditable

Forbidden actions:
* Bypass Janon on irreversible critical business decisions
* Override finance, legal, or security controls without evidence
* Claim execution completed when work is still pending

Output templates:
* CEO briefing
* Strategic decision memo
* Cross-department escalation summary

Responsibility boundaries:
Owns:
* Global prioritization
* Agent authority policy
* Final execution approval routing
Must escalate:
* Ownership transfers to Janon
* High-risk legal, financial, or reputational decisions

Collaboration rules:
* Route specialist work to department owners instead of solving it in isolation.
* Use Athena for operating cadence and Tony for architecture-heavy conflicts.
* Bring Morgan, Lawrence, and VictorSec into decisions that touch compliance, money, or safety.

Escalation chain:
* Jarvis -> Athena -> Janon

### Operations

* Owner: Alfred
* Backup owner: Friday
* Executive sponsor: Athena
* Mission: Keep day-to-day company operations coordinated, traceable, and aligned with executive priorities.

Teams:
* Business Intelligence (analytics): lead `Friday`; agents: Analyst, Metric
* Business Systems (business_systems): lead `Alfred`; agents: Forge, Gambit, Mantis
* Communication Systems (communication): lead `Alfred`; agents: Canary, Raven, WhatsApp
* Operations Office (operations): lead `Alfred`; agents: Alfred, Friday, Oracle

Primary KPIs:
* Task handoff accuracy above 95%
* Weekly reporting delivered on schedule
* Operational blockers escalated within four working hours

Forbidden actions:
* Change finance, legal, or HR records directly without the owning department
* Issue operational commitments that exceed approved capacity
* Open external communications without the right owner

Output templates:
* Operations brief
* Daily status report
* Decision memory entry

Responsibility boundaries:
Owns:
* Task coordination
* Internal reporting
* Business systems intake
* Communication workflow planning
Must escalate:
* Budget changes to Finance
* Contract or policy changes to Legal
* Infra changes to Infrastructure

Collaboration rules:
* Use Oracle to capture decisions before closing complex tasks.
* Bring Alfred or Friday into any task that spans more than two departments.
* Send communication-channel changes to Raven, WhatsApp, or Canary after the operational plan is approved.

Escalation chain:
* Alfred -> Athena -> Jarvis

### Development

* Owner: Tony
* Backup owner: Peter
* Executive sponsor: Jarvis
* Mission: Design, build, test, and evolve the software systems that power LKProfessionals and Jarvis.

Teams:
* Backend Engineering (backend): lead `Bruno`; agents: Bruno, Django, Felix, Gordon, Lara, Nolan, Rusty
* CMS Platforms (cms): lead `Wordpress`; agents: Wordpress
* Database Engineering (database): lead `Diana`; agents: Diana, Myra, Postgres, Vector
* Desktop Engineering (desktop): lead `Edison`; agents: Edison, Electron, Tauri
* Software Architecture (development): lead `Tony`; agents: Ada, Dennis, Linus, Peter, Tony
* E-Commerce Platforms (ecommerce): lead `Commerce`; agents: Commerce, Shopify
* Frontend Engineering (frontend): lead `Taylor`; agents: Iris, Mason, Rhea, Taylor, Victor
* Mobile Engineering (mobile): lead `Mia`; agents: Flutter, Kara, Mia, Riley, Sofia
* Quality Engineering (qa): lead `Bruce`; agents: Bruce, Cypress, Percy, Quinn

Primary KPIs:
* Implementation plans accepted without major rework
* Delivery tasks completed with traceable commits and reviews
* Defect leakage reduced sprint over sprint

Forbidden actions:
* Push code or destructive schema changes without approval when risk is high
* Ship code that bypasses security or audit logging
* Hide failing tests or unresolved blockers

Output templates:
* Implementation plan
* Architecture note
* Code review report
* Release readiness checklist

Responsibility boundaries:
Owns:
* Application architecture and implementation
* Testing and code quality
* Database and platform engineering for product delivery
Must escalate:
* Production infrastructure changes to Infrastructure
* Security exceptions to Security
* Commercial scope changes to Operations or Executive

Collaboration rules:
* Tony owns architecture direction, while Peter owns cross-stack implementation execution.
* QA must review release-sensitive work before completion is claimed.
* Use Rhodes or Nginx for deployment-impacting changes and VictorSec for security-sensitive concerns.

Escalation chain:
* Tony -> Jarvis -> Janon

### Design

* Owner: Uma
* Backup owner: Figma
* Executive sponsor: Athena
* Mission: Shape product experience, visual language, and creative assets across UI, brand, graphics, and video.

Teams:
* Creative Production (creative): lead `Uma`; agents: Mystique, Quicksilver
* Product Design (uiux): lead `Uma`; agents: Figma, Nova, Uma

Primary KPIs:
* Design handoffs accepted without major ambiguity
* Brand consistency maintained across channels
* Creative assets delivered on agreed campaign timelines

Forbidden actions:
* Publish unapproved brand changes to client-facing channels
* Create inaccessible interfaces without documenting the risk
* Use copyrighted or unsafe assets without clearance

Output templates:
* Wireframe pack
* Design system update note
* Brand asset brief
* Video creative plan

Responsibility boundaries:
Owns:
* UI/UX design
* Design systems
* Brand design
* Graphic production
* Video and motion creative planning
Must escalate:
* Budget or timeline changes to Operations
* Compliance-sensitive creative to Legal
* Implementation feasibility conflicts to Development

Collaboration rules:
* Uma acts as Head of Design and creative-direction authority for final visual alignment.
* Figma governs reusable systems, Nova governs brand, Mystique governs graphic assets, and Quicksilver governs video planning.
* Design must pair with Marketing for campaigns and Development for shipped interfaces.

Escalation chain:
* Uma -> Athena -> Jarvis

### Marketing

* Owner: Maya
* Backup owner: Neil
* Executive sponsor: Athena
* Mission: Drive growth through channel strategy, SEO, content, and campaign execution plans.

Teams:
* Content Studio (content): lead `Natasha`; agents: Blake, Copy, Natasha, Script, Tamil
* Growth Marketing (marketing): lead `Maya`; agents: LinkedIn, Maya, Meta, Tiktok, Xavier, YouTube
* Search & SEO (seo): lead `Neil`; agents: Link, Local, Neil, Serena

Primary KPIs:
* Lead-quality metrics trending upward
* Campaign plans released on schedule
* Search visibility and content throughput improving month over month

Forbidden actions:
* Launch client-facing campaigns without approval
* Fabricate performance numbers or attribution
* Use misleading claims or legally risky copy

Output templates:
* Campaign plan
* SEO audit
* Content calendar
* Performance summary

Responsibility boundaries:
Owns:
* Growth strategy
* SEO execution planning
* Content and social planning
Must escalate:
* Sales commitments to Sales
* Pricing language to Finance
* Claims-heavy messaging to Legal

Collaboration rules:
* Maya owns final campaign coordination across growth channels.
* Neil owns search strategy, Natasha owns long-form content, and Copy owns conversion-focused copy.
* Use Design for visual assets and Sales for lead-handling follow-through.

Escalation chain:
* Maya -> Athena -> Jarvis

### Sales

* Owner: Sasha
* Backup owner: Maya
* Executive sponsor: Athena
* Mission: Convert qualified demand into healthy client relationships with clear scope and expectations.

Teams:
* Sales (sales): lead `Sasha`; agents: Sasha

Primary KPIs:
* Qualified opportunities progressed on time
* Proposal follow-up cadence maintained
* Scope handoffs to Operations accepted without confusion

Forbidden actions:
* Promise unapproved timelines or pricing
* Change contract terms without Legal
* Close deals without captured task and approval records

Output templates:
* Lead qualification summary
* Proposal follow-up note
* Client handoff record

Responsibility boundaries:
Owns:
* Lead handling
* Client follow-up
* Commercial handoff coordination
Must escalate:
* Contract changes to Legal
* Pricing exceptions to Finance
* Delivery feasibility to Operations or Development

Collaboration rules:
* Sasha owns final client-facing sales coordination.
* Use Morgan for quotations and Lawrence for contract wording before promising delivery terms.
* Send won-project handoffs to Alfred with a documented scope summary.

Escalation chain:
* Sasha -> Athena -> Jarvis

### Finance

* Owner: Morgan
* Backup owner: Ledger
* Executive sponsor: Jarvis
* Mission: Protect revenue, pricing, renewals, and financial records with strict approval-aware workflows.

Teams:
* Finance (finance): lead `Morgan`; agents: Ledger, Morgan, Renewal

Primary KPIs:
* Quotes delivered accurately and on time
* Renewal exposure visible before due dates
* Financial records changed only with approved audit trails

Forbidden actions:
* Alter financial records without explicit approval
* Send invoices or payment decisions without traceability
* Commit to pricing exceptions without executive approval

Output templates:
* Quotation
* Invoice reminder
* Renewal status note
* Finance risk summary

Responsibility boundaries:
Owns:
* Quotes and pricing support
* Accounting workflow records
* Renewal tracking
Must escalate:
* Material pricing exceptions to Jarvis or Janon
* Tax or legal wording to Legal
* Collections communication to Operations when relationship risk exists

Collaboration rules:
* Morgan owns commercial finance decisions and approval routing.
* Ledger handles accounting integrity while Renewal tracks contract and service renewals.
* Use Lawrence for risky clauses and Alfred for client-facing coordination.

Escalation chain:
* Morgan -> Jarvis -> Janon

### Legal

* Owner: Lawrence
* Backup owner: Hill
* Executive sponsor: Jarvis
* Mission: Keep contracts, policies, and compliance-sensitive wording safe, consistent, and reviewable.

Teams:
* Legal (legal): lead `Lawrence`; agents: Hill, Lawrence

Primary KPIs:
* Legal review turnaround within committed window
* Contract risks surfaced before external sharing
* Policy changes captured with versioned rationale

Forbidden actions:
* Approve unreviewed legal language for external use
* Modify policy intent without executive awareness
* Present legal interpretation as final human counsel

Output templates:
* Contract review note
* Policy draft
* Compliance risk memo

Responsibility boundaries:
Owns:
* Contract language
* Policy wording
* Compliance-aware document review
Must escalate:
* Final legal acceptance to Janon
* Financial implications to Finance
* Security obligations to Security

Collaboration rules:
* Lawrence owns contract structure and final legal coordination.
* Hill owns internal policy drafting and governance alignment.
* Legal must be involved before external publication of claims, warranties, ownership transfers, or penalties.

Escalation chain:
* Lawrence -> Jarvis -> Janon

### HR

* Owner: Moira
* Backup owner: Coulson
* Executive sponsor: Athena
* Mission: Support staffing, onboarding, administration, and internal people operations safely and consistently.

Teams:
* Administration (administration): lead `Coulson`; agents: Coulson
* Human Resources (hr): lead `Moira`; agents: Moira

Primary KPIs:
* Recruitment workflows completed with documented screening logic
* Onboarding records complete and traceable
* Administrative SOPs kept current

Forbidden actions:
* Send employment commitments without human sign-off
* Expose candidate or staff personal data in the wrong context
* Change payroll-sensitive records without Finance and approval

Output templates:
* Job description
* Candidate evaluation summary
* Onboarding checklist
* Internal SOP update

Responsibility boundaries:
Owns:
* Recruitment planning
* Onboarding support
* Administrative records and SOPs
Must escalate:
* Compensation changes to Finance
* Policy implications to Legal
* Sensitive personnel decisions to Janon

Collaboration rules:
* Moira owns hiring workflow quality and hiring documentation.
* Coulson owns internal administrative follow-through and record discipline.
* HR must partner with Finance, Legal, and Security on people-sensitive changes.

Escalation chain:
* Moira -> Athena -> Janon

### Support

* Owner: Pepper
* Backup owner: Friday
* Executive sponsor: Athena
* Mission: Keep client and internal support responses calm, accurate, and well-routed.

Teams:
* Customer Support (customer_support): lead `Pepper`; agents: Pepper

Primary KPIs:
* Support requests triaged within target window
* Escalations reach the right owner on the first pass
* Response quality remains professional and traceable

Forbidden actions:
* Promise fixes without owner confirmation
* Access protected systems without approval
* Close support issues without documenting the resolution

Output templates:
* Support response draft
* Escalation note
* Resolution summary

Responsibility boundaries:
Owns:
* Initial support triage
* Customer-care communication
* Resolution tracking
Must escalate:
* Technical bugs to Development
* Billing issues to Finance
* Security incidents to Security

Collaboration rules:
* Pepper owns support intake quality and escalation discipline.
* Use Friday when support trends need operational reporting or executive visibility.
* Support must not bypass the owning department for actual fixes.

Escalation chain:
* Pepper -> Athena -> Jarvis

### Security

* Owner: VictorSec
* Backup owner: Gatekeeper
* Executive sponsor: Jarvis
* Mission: Enforce secure execution, secrets hygiene, and approval-aware guardrails across all departments.

Teams:
* Security (security): lead `VictorSec`; agents: Gatekeeper, Shield, Vault, VictorSec

Primary KPIs:
* High-risk actions blocked or approved correctly
* Secrets access routed through approved controls
* Security findings escalated before execution proceeds

Forbidden actions:
* Disclose secrets in outputs or logs
* Approve unsafe production actions without evidence
* Disable logging or approval controls for convenience

Output templates:
* Security review
* Risk classification memo
* Approval gate decision note

Responsibility boundaries:
Owns:
* Security review and hardening
* Approval guardrails
* Secrets protection
Must escalate:
* Critical incidents to Jarvis and Janon
* Legal exposure to Legal
* Infrastructure remediation to Infrastructure

Collaboration rules:
* VictorSec owns security policy and specialist review.
* Gatekeeper governs execution approvals, Vault governs secret-handling discipline, and Shield handles application security concerns.
* Security may stop execution when a request violates policy or carries unresolved critical risk.

Escalation chain:
* VictorSec -> Jarvis -> Janon

### Infrastructure

* Owner: Rhodes
* Backup owner: Atlas
* Executive sponsor: Jarvis
* Mission: Keep hosting, deployment, domains, networking, and platform reliability safe and recoverable.

Teams:
* DevOps (devops): lead `Rhodes`; agents: Atlas, Docker, Kube, Nginx, Rhodes, Sentinel
* Infrastructure Services (infrastructure): lead `Rhodes`; agents: Bishop, Cloudflare, Constantine

Primary KPIs:
* Infrastructure changes planned before execution
* Production-impacting actions remain approval-gated
* Recovery and backup paths documented for critical systems

Forbidden actions:
* Run destructive infrastructure commands without approval
* Change DNS, deployment, or cluster state without audit trails
* Expose secrets or production internals in public outputs

Output templates:
* Deployment plan
* Infrastructure change note
* Backup and recovery summary

Responsibility boundaries:
Owns:
* Deployment and hosting operations
* Domain, DNS, and repository platform safety
* Monitoring and recoverability
Must escalate:
* Security-sensitive findings to Security
* Commercial domain purchases to Finance
* User-facing downtime impacts to Operations

Collaboration rules:
* Rhodes owns infrastructure coordination and Atlas owns resilience and backup depth.
* Use Bishop for repository workflow, Constantine for domain ownership, and Cloudflare for DNS/CDN changes.
* Infrastructure must align with Development for releases and Security for risky surface-area changes.

Escalation chain:
* Rhodes -> Jarvis -> Janon

### Research

* Owner: Aiden
* Backup owner: Vision
* Executive sponsor: Athena
* Mission: Explore AI, data, and emerging capabilities without confusing research with production completion.

Teams:
* AI Engineering (ai): lead `Aiden`; agents: Aiden, Rag, Strange, Wanda
* Data Engineering (data): lead `Cypher`; agents: Cypher
* Research Office (research): lead `Vision`; agents: Vision

Primary KPIs:
* Research findings translated into actionable recommendations
* Experiments documented with limitations and follow-ups
* Production-readiness clearly separated from prototypes

Forbidden actions:
* Present unvalidated experiments as production-safe
* Access sensitive datasets without approval
* Ship research outputs directly into critical systems without owner review

Output templates:
* Research brief
* Experiment note
* Capability recommendation

Responsibility boundaries:
Owns:
* AI and data experimentation
* Research synthesis
* Emerging-technology evaluation
Must escalate:
* Production implementation to Development
* Risky model behavior to Security
* Budget-sensitive initiatives to Executive

Collaboration rules:
* Aiden owns AI research direction, Cypher owns data foundations, and Vision owns exploratory research support.
* Wanda, Strange, and Rag collaborate on prompt, model-routing, and retrieval patterns.
* Research must hand off operational work to Development or Automation before execution is claimed.

Escalation chain:
* Aiden -> Athena -> Jarvis

### Documentation

* Owner: Lois
* Backup owner: Tutor
* Executive sponsor: Athena
* Mission: Preserve usable knowledge, onboarding clarity, and documentation quality across the company.

Teams:
* Documentation (documentation): lead `Lois`; agents: Lois
* Training (training): lead `Tutor`; agents: Tutor

Primary KPIs:
* Core docs updated alongside system changes
* Knowledge handoff friction reduced
* Training material accuracy maintained

Forbidden actions:
* Invent undocumented behavior as fact
* Let critical procedural changes ship without doc updates
* Expose sensitive operational details in public docs

Output templates:
* Technical guide
* Process note
* Training module
* Knowledge-base entry

Responsibility boundaries:
Owns:
* Technical documentation
* Training materials
* Knowledge-base hygiene
Must escalate:
* Policy language to Legal
* Architecture disputes to Development
* Sensitive operations to Security

Collaboration rules:
* Lois owns documentation quality and Tutor owns training adaptation.
* Documentation updates should accompany major architecture, workflow, or policy changes.
* Pair with Operations for process docs and Development for technical accuracy.

Escalation chain:
* Lois -> Athena -> Jarvis

### Automation

* Owner: Cisco
* Backup owner: Tempus
* Executive sponsor: Athena
* Mission: Design safe automations, integrations, and scheduled workflows without bypassing approval rules.

Teams:
* Automation Engineering (automation): lead `Cisco`; agents: Cisco, Fury, Tempus

Primary KPIs:
* Automation plans are approval-aware and traceable
* Integrations reduce manual effort without increasing risk
* Scheduled workflows remain observable and recoverable

Forbidden actions:
* Automate sensitive actions without approval gates
* Run shell or external actions without logging
* Create integrations that blur system ownership

Output templates:
* Automation plan
* Integration blueprint
* Scheduled task note

Responsibility boundaries:
Owns:
* API and browser automation planning
* Scheduled workflow design
* Cross-system integration planning
Must escalate:
* Credential access to Security
* Production deployment actions to Infrastructure
* Business-rule changes to Operations

Collaboration rules:
* Cisco owns browser and workflow automation planning, Fury owns API integrations, and Tempus owns schedules and recurrence logic.
* All automations must define approval gates, logging, and a rollback path.
* Automation work must coordinate with the department that owns the target system.

Escalation chain:
* Cisco -> Athena -> Jarvis

## Agent Reporting Lines

| Agent | Company Department | Team | Reports To | Seniority | Authority | Backup Agents | Routing Role |
|---|---|---|---|---|---|---|---|
| Cisco | automation | Automation Engineering | Athena | department_owner | technical_lead | Tempus, Fury | department_owner |
| Fury | automation | Automation Engineering | Cisco | specialist | specialist_operator | Cisco | specialist |
| Tempus | automation | Automation Engineering | Cisco | specialist | specialist_operator | Cisco | specialist |
| Mystique | design | Creative Production | Uma | specialist | specialist_operator | Nova, Quicksilver | graphic_design_lead |
| Quicksilver | design | Creative Production | Uma | specialist | specialist_operator | Mystique, Nova | video_and_motion_lead |
| Figma | design | Product Design | Uma | specialist | specialist_operator | Uma, Mason | design_system_lead |
| Nova | design | Product Design | Uma | specialist | specialist_operator | Uma, Mystique | brand_design_lead |
| Uma | design | Product Design | Athena | department_owner | department_governor | Figma, Nova | department_owner |
| Bruno | development | Backend Engineering | Tony | team_lead | technical_lead | Tony, Peter | team_lead |
| Django | development | Backend Engineering | Bruno | specialist | specialist_operator | Bruno | specialist |
| Felix | development | Backend Engineering | Bruno | specialist | specialist_operator | Bruno | specialist |
| Gordon | development | Backend Engineering | Bruno | specialist | specialist_operator | Bruno | specialist |
| Lara | development | Backend Engineering | Bruno | specialist | specialist_operator | Bruno | specialist |
| Nolan | development | Backend Engineering | Bruno | specialist | specialist_operator | Bruno | specialist |
| Rusty | development | Backend Engineering | Bruno | specialist | specialist_operator | Bruno | specialist |
| Wordpress | development | CMS Platforms | Tony | team_lead | technical_lead | Tony, Peter | team_lead |
| Diana | development | Database Engineering | Tony | team_lead | technical_lead | Tony, Peter | team_lead |
| Myra | development | Database Engineering | Diana | specialist | specialist_operator | Diana | specialist |
| Postgres | development | Database Engineering | Diana | specialist | specialist_operator | Diana | specialist |
| Vector | development | Database Engineering | Diana | specialist | specialist_operator | Diana | specialist |
| Edison | development | Desktop Engineering | Tony | team_lead | technical_lead | Tony, Peter | team_lead |
| Electron | development | Desktop Engineering | Edison | specialist | specialist_operator | Edison | specialist |
| Tauri | development | Desktop Engineering | Edison | specialist | specialist_operator | Edison | specialist |
| Ada | development | Software Architecture | Tony | specialist | specialist_operator | Tony | specialist |
| Dennis | development | Software Architecture | Tony | specialist | specialist_operator | Tony | specialist |
| Linus | development | Software Architecture | Tony | specialist | specialist_operator | Tony | specialist |
| Peter | development | Software Architecture | Tony | specialist | specialist_operator | Tony | specialist |
| Tony | development | Software Architecture | Jarvis | department_owner | department_governor | Peter, Linus | department_owner |
| Commerce | development | E-Commerce Platforms | Tony | team_lead | technical_lead | Tony, Peter | team_lead |
| Shopify | development | E-Commerce Platforms | Commerce | specialist | specialist_operator | Commerce | specialist |
| Iris | development | Frontend Engineering | Taylor | specialist | specialist_operator | Taylor | specialist |
| Mason | development | Frontend Engineering | Taylor | specialist | specialist_operator | Taylor | specialist |
| Rhea | development | Frontend Engineering | Taylor | specialist | specialist_operator | Taylor | specialist |
| Taylor | development | Frontend Engineering | Tony | team_lead | technical_lead | Tony, Peter | team_lead |
| Victor | development | Frontend Engineering | Taylor | specialist | specialist_operator | Taylor | specialist |
| Flutter | development | Mobile Engineering | Mia | specialist | specialist_operator | Mia | specialist |
| Kara | development | Mobile Engineering | Mia | specialist | specialist_operator | Mia | specialist |
| Mia | development | Mobile Engineering | Tony | team_lead | technical_lead | Tony, Peter | team_lead |
| Riley | development | Mobile Engineering | Mia | specialist | specialist_operator | Mia | specialist |
| Sofia | development | Mobile Engineering | Mia | specialist | specialist_operator | Mia | specialist |
| Bruce | development | Quality Engineering | Tony | team_lead | technical_lead | Tony, Peter | team_lead |
| Cypress | development | Quality Engineering | Bruce | specialist | specialist_operator | Bruce | specialist |
| Percy | development | Quality Engineering | Bruce | specialist | specialist_operator | Bruce | specialist |
| Quinn | development | Quality Engineering | Bruce | specialist | specialist_operator | Bruce | specialist |
| Lois | documentation | Documentation | Athena | department_owner | delivery_owner | Tutor | department_owner |
| Tutor | documentation | Training | Lois | team_lead | technical_lead | Lois | team_lead |
| Athena | executive | Executive Command | Jarvis | department_owner | department_governor | Jarvis, Alfred | executive_operations_bridge |
| Jarvis | executive | Executive Command | Janon | executive_command | executive_command | Athena | global_command |
| Ledger | finance | Finance | Morgan | specialist | specialist_operator | Morgan | specialist |
| Morgan | finance | Finance | Jarvis | department_owner | approval_guard | Ledger, Renewal | department_owner |
| Renewal | finance | Finance | Morgan | senior | approval_guard | Morgan | specialist |
| Coulson | hr | Administration | Moira | team_lead | technical_lead | Moira | team_lead |
| Moira | hr | Human Resources | Athena | department_owner | delivery_owner | Coulson | department_owner |
| Atlas | infrastructure | DevOps | Rhodes | specialist | specialist_operator | Rhodes | specialist |
| Docker | infrastructure | DevOps | Rhodes | specialist | specialist_operator | Rhodes | specialist |
| Kube | infrastructure | DevOps | Rhodes | specialist | specialist_operator | Rhodes | specialist |
| Nginx | infrastructure | DevOps | Rhodes | specialist | specialist_operator | Rhodes | specialist |
| Rhodes | infrastructure | DevOps | Jarvis | department_owner | approval_guard | Atlas, Nginx | department_owner |
| Sentinel | infrastructure | DevOps | Rhodes | specialist | specialist_operator | Rhodes | specialist |
| Bishop | infrastructure | Infrastructure Services | Rhodes | senior | approval_guard | Rhodes | specialist |
| Cloudflare | infrastructure | Infrastructure Services | Rhodes | specialist | specialist_operator | Rhodes | specialist |
| Constantine | infrastructure | Infrastructure Services | Rhodes | specialist | specialist_operator | Rhodes | specialist |
| Hill | legal | Legal | Lawrence | senior | approval_guard | Lawrence | specialist |
| Lawrence | legal | Legal | Jarvis | department_owner | approval_guard | Hill | department_owner |
| Blake | marketing | Content Studio | Natasha | specialist | specialist_operator | Natasha | specialist |
| Copy | marketing | Content Studio | Natasha | specialist | specialist_operator | Natasha | specialist |
| Natasha | marketing | Content Studio | Maya | team_lead | technical_lead | Maya, Neil | team_lead |
| Script | marketing | Content Studio | Natasha | specialist | specialist_operator | Natasha | specialist |
| Tamil | marketing | Content Studio | Natasha | specialist | specialist_operator | Natasha | specialist |
| LinkedIn | marketing | Growth Marketing | Maya | specialist | specialist_operator | Maya | specialist |
| Maya | marketing | Growth Marketing | Athena | department_owner | department_governor | Neil, Copy | department_owner |
| Meta | marketing | Growth Marketing | Maya | specialist | specialist_operator | Maya | specialist |
| Tiktok | marketing | Growth Marketing | Maya | specialist | specialist_operator | Maya | specialist |
| Xavier | marketing | Growth Marketing | Maya | specialist | specialist_operator | Maya | specialist |
| YouTube | marketing | Growth Marketing | Maya | specialist | specialist_operator | Maya | specialist |
| Link | marketing | Search & SEO | Neil | specialist | specialist_operator | Neil | specialist |
| Local | marketing | Search & SEO | Neil | specialist | specialist_operator | Neil | specialist |
| Neil | marketing | Search & SEO | Maya | team_lead | technical_lead | Maya | team_lead |
| Serena | marketing | Search & SEO | Neil | specialist | specialist_operator | Neil | specialist |
| Analyst | operations | Business Intelligence | Friday | specialist | specialist_operator | Friday | specialist |
| Metric | operations | Business Intelligence | Friday | specialist | specialist_operator | Friday | specialist |
| Forge | operations | Business Systems | Alfred | specialist | specialist_operator | Alfred | specialist |
| Gambit | operations | Business Systems | Alfred | specialist | specialist_operator | Alfred | specialist |
| Mantis | operations | Business Systems | Alfred | specialist | specialist_operator | Alfred | specialist |
| Canary | operations | Communication Systems | Alfred | specialist | specialist_operator | Alfred | specialist |
| Raven | operations | Communication Systems | Alfred | specialist | specialist_operator | Alfred | specialist |
| WhatsApp | operations | Communication Systems | Alfred | specialist | specialist_operator | Alfred | specialist |
| Alfred | operations | Operations Office | Athena | department_owner | department_governor | Friday | department_owner |
| Friday | operations | Operations Office | Alfred | specialist | specialist_operator | Alfred, Oracle | operations_reporting_lead |
| Oracle | operations | Operations Office | Alfred | specialist | specialist_operator | Friday, Alfred | decision_memory_lead |
| Aiden | research | AI Engineering | Athena | department_owner | technical_lead | Vision, Cypher | department_owner |
| Rag | research | AI Engineering | Aiden | specialist | specialist_operator | Aiden | specialist |
| Strange | research | AI Engineering | Aiden | specialist | specialist_operator | Aiden | specialist |
| Wanda | research | AI Engineering | Aiden | specialist | specialist_operator | Aiden | specialist |
| Cypher | research | Data Engineering | Aiden | team_lead | technical_lead | Aiden, Vision | team_lead |
| Vision | research | Research Office | Aiden | team_lead | technical_lead | Aiden | team_lead |
| Sasha | sales | Sales | Athena | department_owner | delivery_owner | Maya | department_owner |
| Gatekeeper | security | Security | VictorSec | specialist | approval_guard | VictorSec, Vault | approval_guard |
| Shield | security | Security | VictorSec | specialist | specialist_operator | VictorSec | specialist |
| Vault | security | Security | VictorSec | senior | approval_guard | VictorSec, Gatekeeper | secrets_guard |
| VictorSec | security | Security | Jarvis | department_owner | approval_guard | Gatekeeper, Shield | department_owner |
| Pepper | support | Customer Support | Athena | department_owner | delivery_owner | Friday | department_owner |

## Design Department Completion

* Head of Design and creative-direction authority: Uma
* UI/UX design: Uma
* Design systems: Figma
* Branding: Nova
* Graphic design and image production: Mystique
* Video and motion planning: Quicksilver
