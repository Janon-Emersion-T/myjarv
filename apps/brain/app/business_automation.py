from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.memory import memory_store


class BusinessAutomation:
    DEFAULT_STATE = {
        "leads": [],
        "proposals": [],
        "quotations": [],
        "followups": [],
        "invoice_reminders": [],
        "onboarding": [],
        "blog_drafts": [],
        "competitor_reports": [],
        "monthly_reports": [],
    }

    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database_path = self.root / "business.json"
        if not self.database_path.exists():
            self._save(dict(self.DEFAULT_STATE))

    def create_lead(self, *, name: str, company: str, service_interest: str, budget: float | None = None, channel: str = "website", notes: str | None = None) -> dict[str, Any]:
        payload = self._load()
        score = self._lead_score(service_interest=service_interest, budget=budget, channel=channel)
        lead = {
            "id": str(uuid.uuid4()),
            "name": name,
            "company": company,
            "service_interest": service_interest,
            "budget": budget,
            "channel": channel,
            "notes": notes,
            "status": "captured",
            "score": score,
            "qualified": score >= 65,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        payload["leads"].append(lead)
        self._save(payload)
        memory_store.create(
            scope="client",
            key=f"lead:{lead['id']}",
            value=f"{company} interested in {service_interest}",
            tags=["lead", channel],
            source="business_automation",
            task_id=None,
            summary=notes or service_interest,
            metadata={"company": company, "score": score},
        )
        return lead

    def list_leads(self) -> list[dict[str, Any]]:
        return self._load()["leads"]

    def qualify_lead(self, lead_id: str) -> dict[str, Any]:
        payload = self._load()
        lead = self._find(payload["leads"], lead_id)
        lead["qualified"] = True
        lead["status"] = "qualified"
        lead["updated_at"] = self._now()
        self._save(payload)
        return lead

    def create_proposal(self, *, client_name: str, project_name: str, scope: str, timeline_weeks: int, budget_estimate: float, lead_id: str | None = None) -> dict[str, Any]:
        payload = self._load()
        proposal = {
            "id": str(uuid.uuid4()),
            "lead_id": lead_id,
            "client_name": client_name,
            "project_name": project_name,
            "scope": scope,
            "timeline_weeks": timeline_weeks,
            "budget_estimate": budget_estimate,
            "status": "draft",
            "risks": self._proposal_risks(scope, budget_estimate),
            "sections": [
                "Goals and success criteria",
                "Delivery scope",
                "Timeline and milestones",
                "Assumptions and exclusions",
                "Commercial terms and approvals",
            ],
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        payload["proposals"].append(proposal)
        self._save(payload)
        return proposal

    def list_proposals(self) -> list[dict[str, Any]]:
        return self._load()["proposals"]

    def create_quotation(self, *, proposal_id: str, labor_hours: float, hourly_rate: float, expenses: float = 0.0, discount: float = 0.0) -> dict[str, Any]:
        payload = self._load()
        proposal = self._find(payload["proposals"], proposal_id)
        subtotal = round((labor_hours * hourly_rate) + expenses, 2)
        total = round(max(0.0, subtotal - discount), 2)
        quotation = {
            "id": str(uuid.uuid4()),
            "proposal_id": proposal_id,
            "client_name": proposal["client_name"],
            "project_name": proposal["project_name"],
            "labor_hours": labor_hours,
            "hourly_rate": hourly_rate,
            "expenses": expenses,
            "discount": discount,
            "subtotal": subtotal,
            "total": total,
            "status": "draft",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        payload["quotations"].append(quotation)
        self._save(payload)
        return quotation

    def create_followup(self, *, client_name: str, subject: str, channel: str, context: str, days_since_last_touch: int = 0) -> dict[str, Any]:
        payload = self._load()
        followup = {
            "id": str(uuid.uuid4()),
            "client_name": client_name,
            "subject": subject,
            "channel": channel,
            "context": context,
            "days_since_last_touch": days_since_last_touch,
            "message": f"Hello {client_name}, following up on {subject}. {context}",
            "priority": "high" if days_since_last_touch >= 7 else "normal",
            "created_at": self._now(),
        }
        payload["followups"].append(followup)
        self._save(payload)
        return followup

    def create_invoice_reminder(self, *, client_name: str, invoice_number: str, amount_due: float, days_overdue: int) -> dict[str, Any]:
        payload = self._load()
        escalation = "executive_review" if days_overdue >= 30 else "finance_followup" if days_overdue >= 14 else "gentle_reminder"
        reminder = {
            "id": str(uuid.uuid4()),
            "client_name": client_name,
            "invoice_number": invoice_number,
            "amount_due": amount_due,
            "days_overdue": days_overdue,
            "escalation": escalation,
            "message": f"Invoice {invoice_number} is overdue by {days_overdue} days. Outstanding amount: {amount_due:.2f}.",
            "created_at": self._now(),
        }
        payload["invoice_reminders"].append(reminder)
        self._save(payload)
        return reminder

    def create_onboarding(self, *, client_name: str, project_name: str, service_line: str) -> dict[str, Any]:
        payload = self._load()
        onboarding = {
            "id": str(uuid.uuid4()),
            "client_name": client_name,
            "project_name": project_name,
            "service_line": service_line,
            "checklist": [
                "Collect brand assets and access requirements.",
                "Confirm stakeholders and communication channel.",
                "Approve scope, milestones, and launch assumptions.",
                "Create project kickoff note and memory records.",
            ],
            "created_at": self._now(),
        }
        payload["onboarding"].append(onboarding)
        self._save(payload)
        return onboarding

    def create_blog_draft(self, *, title: str, audience: str, topic: str, call_to_action: str) -> dict[str, Any]:
        payload = self._load()
        draft = {
            "id": str(uuid.uuid4()),
            "title": title,
            "audience": audience,
            "topic": topic,
            "call_to_action": call_to_action,
            "outline": [
                f"Problem framing for {audience}",
                f"Core insight about {topic}",
                "Actionable recommendations",
                f"Closing CTA: {call_to_action}",
            ],
            "intro": f"{title} helps {audience} understand {topic} in practical business terms.",
            "created_at": self._now(),
        }
        payload["blog_drafts"].append(draft)
        self._save(payload)
        return draft

    def competitor_analysis(self, *, competitor_name: str, website: str, focus: str) -> dict[str, Any]:
        payload = self._load()
        report = {
            "id": str(uuid.uuid4()),
            "competitor_name": competitor_name,
            "website": website,
            "focus": focus,
            "channels": ["website", "seo", "social"],
            "strengths": [
                f"Visible positioning around {focus}.",
                "Likely active website content and market messaging.",
            ],
            "gaps": [
                "Differentiate with stronger proof, process clarity, and local trust signals.",
                "Track SEO themes and social cadence for follow-up comparison.",
            ],
            "created_at": self._now(),
        }
        payload["competitor_reports"].append(report)
        self._save(payload)
        return report

    def create_monthly_report(self, *, month: str) -> dict[str, Any]:
        payload = self._load()
        report = {
            "id": str(uuid.uuid4()),
            "month": month,
            "summary": {
                "leads": len(payload["leads"]),
                "qualified_leads": len([item for item in payload["leads"] if item["qualified"]]),
                "proposals": len(payload["proposals"]),
                "quotations": len(payload["quotations"]),
                "invoice_reminders": len(payload["invoice_reminders"]),
                "competitor_reports": len(payload["competitor_reports"]),
            },
            "generated_at": self._now(),
        }
        payload["monthly_reports"].append(report)
        self._save(payload)
        return report

    def analytics(self) -> dict[str, Any]:
        payload = self._load()
        lead_channels = Counter(item["channel"] for item in payload["leads"])
        followup_channels = Counter(item["channel"] for item in payload["followups"])
        return {
            "leads_total": len(payload["leads"]),
            "qualified_leads": len([item for item in payload["leads"] if item["qualified"]]),
            "proposals_total": len(payload["proposals"]),
            "quotations_total": len(payload["quotations"]),
            "followups_total": len(payload["followups"]),
            "invoice_reminders_total": len(payload["invoice_reminders"]),
            "onboarding_total": len(payload["onboarding"]),
            "blog_drafts_total": len(payload["blog_drafts"]),
            "competitor_reports_total": len(payload["competitor_reports"]),
            "monthly_reports_total": len(payload["monthly_reports"]),
            "lead_channels": dict(lead_channels),
            "followup_channels": dict(followup_channels),
            "average_lead_score": round(sum(item["score"] for item in payload["leads"]) / len(payload["leads"]), 2) if payload["leads"] else 0.0,
        }

    def _proposal_risks(self, scope: str, budget_estimate: float) -> list[str]:
        risks = ["Scope clarity and approval timing should be confirmed."]
        if "seo" in scope.lower() or "marketing" in scope.lower():
            risks.append("Content dependency risk may affect turnaround.")
        if budget_estimate > 500000:
            risks.append("Finance approval likely required for premium pricing.")
        return risks

    def _lead_score(self, *, service_interest: str, budget: float | None, channel: str) -> int:
        score = 45
        if budget and budget >= 250000:
            score += 20
        if budget and budget >= 500000:
            score += 10
        if any(keyword in service_interest.lower() for keyword in ["website", "seo", "automation", "retainer", "development"]):
            score += 15
        if channel in {"referral", "linkedin"}:
            score += 10
        return min(score, 100)

    def _find(self, items: list[dict[str, Any]], record_id: str) -> dict[str, Any]:
        for item in items:
            if item["id"] == record_id:
                return item
        raise ValueError(f"Record not found: {record_id}")

    def _load(self) -> dict[str, Any]:
        payload = json.loads(self.database_path.read_text(encoding="utf-8"))
        changed = False
        for key, default in self.DEFAULT_STATE.items():
            if key not in payload:
                payload[key] = list(default)
                changed = True
        if changed:
            self._save(payload)
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        self.database_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()


business_automation = BusinessAutomation(settings.BUSINESS_DIR)
