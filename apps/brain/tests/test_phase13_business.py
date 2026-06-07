import sys
import unittest
import uuid
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class BusinessPhase13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_lead_capture_qualification_and_proposal_flow(self):
        company = f"Phase13 Co {uuid.uuid4().hex[:6]}"
        lead = self.client.post(
            "/business/leads",
            json={
                "name": "Alicia",
                "company": company,
                "service_interest": "Website redesign and SEO retainer",
                "budget": 350000,
                "channel": "linkedin",
                "notes": "Warm inbound lead.",
            },
        )
        self.assertEqual(lead.status_code, 200)
        lead_payload = lead.json()
        self.assertGreaterEqual(lead_payload["score"], 65)

        qualified = self.client.post(f"/business/leads/{lead_payload['id']}/qualify")
        self.assertEqual(qualified.status_code, 200)
        self.assertEqual(qualified.json()["status"], "qualified")

        proposal = self.client.post(
            "/business/proposals",
            json={
                "client_name": company,
                "project_name": "Growth Sprint",
                "scope": "Website redesign, SEO, and content support",
                "timeline_weeks": 8,
                "budget_estimate": 420000,
                "lead_id": lead_payload["id"],
            },
        )
        self.assertEqual(proposal.status_code, 200)
        proposal_payload = proposal.json()
        self.assertIn("sections", proposal_payload)

        quotation = self.client.post(
            "/business/quotations",
            json={
                "proposal_id": proposal_payload["id"],
                "labor_hours": 120,
                "hourly_rate": 6500,
                "expenses": 25000,
                "discount": 15000,
            },
        )
        self.assertEqual(quotation.status_code, 200)
        self.assertGreater(quotation.json()["total"], 0)

    def test_followups_invoice_onboarding_competitor_and_monthly_report(self):
        followup = self.client.post(
            "/business/followups",
            json={
                "client_name": "Northstar",
                "subject": "proposal review",
                "channel": "email",
                "context": "Wanted to confirm whether the scope needs any changes.",
                "days_since_last_touch": 9,
            },
        )
        self.assertEqual(followup.status_code, 200)
        self.assertEqual(followup.json()["priority"], "high")

        reminder = self.client.post(
            "/business/invoices/reminders",
            json={
                "client_name": "Northstar",
                "invoice_number": "INV-2026-001",
                "amount_due": 95000,
                "days_overdue": 21,
            },
        )
        self.assertEqual(reminder.status_code, 200)
        self.assertEqual(reminder.json()["escalation"], "finance_followup")

        onboarding = self.client.post(
            "/business/onboarding",
            json={
                "client_name": "Northstar",
                "project_name": "Portal Revamp",
                "service_line": "development",
            },
        )
        self.assertEqual(onboarding.status_code, 200)
        self.assertGreaterEqual(len(onboarding.json()["checklist"]), 4)

        competitor = self.client.post(
            "/business/competitors/analyze",
            json={
                "competitor_name": "CompetitorX",
                "website": "https://competitor.example",
                "focus": "SEO services",
            },
        )
        self.assertEqual(competitor.status_code, 200)
        self.assertIn("strengths", competitor.json())

        blog = self.client.post(
            "/business/blog-drafts",
            json={
                "title": "How Sri Lankan brands can improve SEO",
                "audience": "SME founders",
                "topic": "practical SEO improvements",
                "call_to_action": "Book a discovery call",
            },
        )
        self.assertEqual(blog.status_code, 200)
        self.assertIn("outline", blog.json())

        report = self.client.post("/business/reports/monthly", json={"month": "2026-06"})
        self.assertEqual(report.status_code, 200)
        self.assertIn("summary", report.json())

        analytics = self.client.get("/business/analytics")
        self.assertEqual(analytics.status_code, 200)
        self.assertGreaterEqual(analytics.json()["followups_total"], 1)
        self.assertGreaterEqual(analytics.json()["invoice_reminders_total"], 1)
        self.assertGreaterEqual(analytics.json()["blog_drafts_total"], 1)


if __name__ == "__main__":
    unittest.main()
