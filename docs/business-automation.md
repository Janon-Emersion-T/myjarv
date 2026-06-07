# Business Automation

Roadmap Phase 13 now includes durable business workflow records and API-driven automation helpers.

## Current Capabilities

* lead capture and qualification
* proposal generation
* quotation calculation
* follow-up drafting
* invoice reminder generation
* onboarding checklist creation
* blog draft generation
* competitor analysis snapshots
* monthly business reporting
* KPI-style analytics
* memory integration for captured leads

## Main Endpoints

* `GET /business/analytics`
* `GET /business/leads`
* `POST /business/leads`
* `POST /business/leads/{lead_id}/qualify`
* `GET /business/proposals`
* `POST /business/proposals`
* `POST /business/quotations`
* `POST /business/followups`
* `POST /business/invoices/reminders`
* `POST /business/onboarding`
* `POST /business/competitors/analyze`
* `POST /business/blog-drafts`
* `POST /business/reports/monthly`

## CLI

* `python3 scripts/business_cli.py analytics`
* `python3 scripts/business_cli.py monthly-report 2026-06`
* `python3 scripts/test_business_automation.py`

## Notes

Business workflow records are stored under `data/business/` and treated as runtime artifacts.
