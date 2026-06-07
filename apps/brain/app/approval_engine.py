from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.logger import logger


ROLE_ORDER = {
    "operator": 1,
    "manager": 2,
    "director": 3,
    "executive": 4,
}

CHANNEL_TRUST = {
    "dashboard": 0.84,
    "api": 0.8,
    "cli": 0.78,
    "mobile": 0.76,
    "email": 0.68,
    "whatsapp": 0.63,
    "voice": 0.6,
}

ACTION_RULES = {
    "finance": {
        "keywords": {"finance", "invoice", "payment", "bank", "salary", "refund", "transaction"},
        "department": "finance",
        "requires_dual": True,
        "needs_written_document": True,
    },
    "deployment": {
        "keywords": {"deploy", "release", "production", "rollback"},
        "department": "engineering",
        "requires_dual": True,
        "needs_written_document": True,
    },
    "filesystem": {
        "keywords": {"delete", "remove", "filesystem", "rm ", "wipe", "purge"},
        "department": "operations",
        "requires_dual": True,
        "needs_written_document": True,
    },
    "communication": {
        "keywords": {"email", "whatsapp", "message", "sms", "client reply"},
        "department": "operations",
        "requires_dual": False,
        "needs_written_document": False,
    },
    "legal": {
        "keywords": {"legal", "contract", "agreement", "nda", "terms"},
        "department": "legal",
        "requires_dual": True,
        "needs_written_document": True,
    },
    "shell": {
        "keywords": {"shell", "command", "bash", "terminal", "sudo"},
        "department": "engineering",
        "requires_dual": True,
        "needs_written_document": True,
    },
    "browser_automation": {
        "keywords": {"browser", "automation", "scrape", "submit form", "login"},
        "department": "operations",
        "requires_dual": False,
        "needs_written_document": False,
    },
    "ai_autonomy": {
        "keywords": {"autonomous", "auto-run", "fully automatic", "without review"},
        "department": "operations",
        "requires_dual": True,
        "needs_written_document": True,
    },
}

APPROVAL_CHANNELS = sorted(CHANNEL_TRUST)


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class ApprovalEngine:
    def derive_context(self, task: dict[str, Any]) -> dict[str, Any]:
        text = f"{task.get('message', '')} {task.get('requested_action') or ''}".lower()
        metadata = task.get("metadata", {})
        domains: set[str] = set()
        required_departments: set[str] = set()
        needs_written_document = task.get("approval_level") == "CRITICAL"
        suspicious_keywords: list[str] = []

        for domain, config in ACTION_RULES.items():
            matched = [keyword for keyword in config["keywords"] if keyword in text]
            if not matched:
                continue
            domains.add(domain)
            required_departments.add(config["department"])
            needs_written_document = needs_written_document or config["needs_written_document"]
            suspicious_keywords.extend(matched)

        domains.update(metadata.get("approval_domains", []))
        if department := metadata.get("approval_department"):
            required_departments.add(str(department))

        return {
            "domains": sorted(domains),
            "required_departments": sorted(required_departments),
            "needs_written_document": needs_written_document,
            "suspicious_keywords": sorted(set(suspicious_keywords)),
        }

    def build_policy(self, task: dict[str, Any]) -> dict[str, Any]:
        context = self.derive_context(task)
        approval_level = task["approval_level"]
        roles = {
            "LOW": [],
            "MEDIUM": ["manager"],
            "HIGH": ["manager", "director"],
            "CRITICAL": ["manager", "director", "executive"],
        }[approval_level]
        channel_allowlist = APPROVAL_CHANNELS.copy()
        if approval_level == "CRITICAL":
            channel_allowlist = [channel for channel in APPROVAL_CHANNELS if channel != "voice"]

        min_confidence = {
            "LOW": 0.0,
            "MEDIUM": 0.7,
            "HIGH": 0.8,
            "CRITICAL": 0.88,
        }[approval_level]
        timeout_seconds = {
            "LOW": 0,
            "MEDIUM": 900,
            "HIGH": 1800,
            "CRITICAL": 3600,
        }[approval_level]

        return {
            "approval_level": approval_level,
            "risk_level": task["risk_level"],
            "human_in_the_loop": approval_level != "LOW",
            "required_roles": roles,
            "min_approvals": len(roles),
            "dual_approval_required": len(roles) >= 2,
            "executive_required": "executive" in roles,
            "written_signoff_required": context["needs_written_document"],
            "allowed_channels": channel_allowlist,
            "required_departments": context["required_departments"],
            "action_domains": context["domains"],
            "minimum_confidence_score": min_confidence,
            "supports_delegation": True,
            "supports_emergency_override": approval_level in {"HIGH", "CRITICAL"},
            "supports_replay_protection": True,
            "supports_revocation": approval_level != "LOW",
            "supports_rollback": approval_level != "LOW",
            "supports_simulation": True,
            "timeout_seconds": timeout_seconds,
            "retry_limit": 3 if approval_level in {"HIGH", "CRITICAL"} else 2,
            "escalation_chain": roles[1:] if len(roles) > 1 else roles,
            "contextual_keywords": context["suspicious_keywords"],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def compute_confidence(
        self,
        *,
        channel: str,
        reviewer_role: str,
        signature: str | None,
        written_document: dict[str, Any] | None,
        delegated_by: str | None,
        evidence: list[dict[str, Any]],
    ) -> float:
        confidence = CHANNEL_TRUST.get(channel, 0.55)
        confidence += 0.04 * max(ROLE_ORDER.get(reviewer_role, 1) - 1, 0)
        if signature:
            confidence += 0.06
        if written_document:
            confidence += 0.06
        if evidence:
            confidence += min(0.05, len(evidence) * 0.02)
        if delegated_by:
            confidence -= 0.04
        return max(0.0, min(0.99, round(confidence, 2)))

    def simulate_decision(
        self,
        task: dict[str, Any],
        existing_approvals: list[dict[str, Any]],
        decision: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        record = self.prepare_decision(task, existing_approvals, decision, payload, simulation=True)
        return {
            "task_id": task["id"],
            "decision": decision,
            "policy": self.build_policy(task),
            "preview": {
                "stage": record["stage_label"],
                "would_fully_approve": record["fully_approved"],
                "confidence_score": record["confidence_score"],
                "suspicious_flags": record["suspicious_flags"],
                "risk_context": record["risk_context"],
            },
        }

    def prepare_decision(
        self,
        task: dict[str, Any],
        existing_approvals: list[dict[str, Any]],
        decision: str,
        payload: dict[str, Any],
        simulation: bool = False,
    ) -> dict[str, Any]:
        policy = self.build_policy(task)
        channel = payload.get("channel") or "dashboard"
        reviewer_role = payload.get("reviewer_role") or "manager"
        reviewer = payload["reviewer"]
        delegated_by = payload.get("delegated_by")
        written_document = payload.get("written_document")
        signature = payload.get("signature")
        department = payload.get("department")
        evidence = payload.get("evidence") or []

        if channel not in APPROVAL_CHANNELS:
            raise ValueError(f"Unsupported approval channel: {channel}")
        if reviewer_role not in ROLE_ORDER:
            raise ValueError(f"Unsupported reviewer role: {reviewer_role}")
        if decision == "approved" and channel not in policy["allowed_channels"]:
            raise ValueError(f"{task['approval_level']} approvals cannot be granted via {channel}.")

        active_approvals = [
            item for item in existing_approvals if item["decision"] == "approved" and item.get("revoked_at") is None
        ]
        rejected_approvals = [
            item for item in existing_approvals if item["decision"] == "rejected" and item.get("revoked_at") is None
        ]
        stage_index = len(active_approvals)
        required_roles = policy["required_roles"]
        required_role = required_roles[min(stage_index, max(len(required_roles) - 1, 0))] if required_roles else "operator"
        expected_rank = ROLE_ORDER.get(required_role, 1)
        actual_rank = ROLE_ORDER.get(reviewer_role, 1)
        if decision == "approved" and actual_rank < expected_rank:
            raise ValueError(f"{task['approval_level']} stage {stage_index + 1} requires at least {required_role} review.")

        if decision == "approved" and policy["written_signoff_required"] and not written_document and not payload.get("emergency_override"):
            raise ValueError("Written signoff is required for this approval.")

        if decision == "approved" and policy["required_departments"] and department not in policy["required_departments"] and reviewer_role != "executive":
            raise ValueError(
                f"Approval department must be one of: {', '.join(policy['required_departments'])}."
            )

        approval_token = payload.get("approval_token") or hashlib.sha256(
            _stable_json(
                {
                    "task_id": task["id"],
                    "reviewer": reviewer,
                    "decision": decision,
                    "channel": channel,
                    "role": reviewer_role,
                    "notes": payload.get("notes") or "",
                }
            ).encode("utf-8")
        ).hexdigest()
        replay_hash = hashlib.sha256(f"{task['id']}:{approval_token}".encode("utf-8")).hexdigest()
        if any(item.get("replay_hash") == replay_hash for item in existing_approvals):
            raise ValueError("Approval replay detected for this task.")

        suspicious_flags: list[str] = []
        if any(item["reviewer"].lower() == reviewer.lower() and item["decision"] == "approved" and item.get("revoked_at") is None for item in existing_approvals):
            suspicious_flags.append("duplicate_reviewer")
        if rejected_approvals and decision == "approved":
            suspicious_flags.append("approval_after_rejection")
        if delegated_by:
            suspicious_flags.append("delegated_approval")
        if payload.get("emergency_override"):
            suspicious_flags.append("emergency_override")
        if channel in {"voice", "whatsapp"} and policy["approval_level"] in {"HIGH", "CRITICAL"}:
            suspicious_flags.append("low_trust_channel")

        confidence_score = self.compute_confidence(
            channel=channel,
            reviewer_role=reviewer_role,
            signature=signature,
            written_document=written_document,
            delegated_by=delegated_by,
            evidence=evidence,
        )
        if decision == "approved" and confidence_score < policy["minimum_confidence_score"]:
            suspicious_flags.append("low_confidence")

        risk_context = {
            "policy_level": policy["approval_level"],
            "domains": policy["action_domains"],
            "required_departments": policy["required_departments"],
            "minimum_confidence_score": policy["minimum_confidence_score"],
            "human_in_the_loop": policy["human_in_the_loop"],
        }
        stage_label = f"stage_{stage_index + 1}_of_{max(policy['min_approvals'], 1)}"
        fully_approved = decision == "approved" and (stage_index + 1) >= policy["min_approvals"]
        signed_payload = {
            "task_id": task["id"],
            "reviewer": reviewer,
            "decision": decision,
            "channel": channel,
            "reviewer_role": reviewer_role,
            "department": department,
            "delegated_by": delegated_by,
            "notes": payload.get("notes"),
            "written_document": written_document,
            "evidence": evidence,
            "simulation": simulation,
        }
        signature_value = signature or hmac.new(
            settings.SECURITY_SECRET_KEY.encode("utf-8"),
            _stable_json(signed_payload).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        immutable_hash = hashlib.sha256(
            _stable_json(
                {
                    "replay_hash": replay_hash,
                    "signature": signature_value,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ).encode("utf-8")
        ).hexdigest()

        logger.log(
            "INFO",
            "approval.prepared",
            "Prepared approval decision payload.",
            {
                "task_id": task["id"],
                "decision": decision,
                "reviewer": reviewer,
                "stage": stage_label,
                "simulation": simulation,
            },
        )

        return {
            "policy": policy,
            "reviewer_role": reviewer_role,
            "department": department,
            "channel": channel,
            "delegated_by": delegated_by,
            "written_document": written_document,
            "evidence": evidence,
            "approval_token": approval_token,
            "replay_hash": replay_hash,
            "confidence_score": confidence_score,
            "suspicious_flags": sorted(set(suspicious_flags)),
            "risk_context": risk_context,
            "chain_step": stage_index + 1,
            "stage_label": stage_label,
            "fully_approved": fully_approved,
            "signature": signature_value,
            "immutable_hash": immutable_hash,
            "simulation": simulation,
        }

    def summarize(self, task: dict[str, Any], approvals: list[dict[str, Any]], emergency_shutdown: dict[str, Any] | None = None) -> dict[str, Any]:
        policy = self.build_policy(task)
        active_approvals = [item for item in approvals if item["decision"] == "approved" and item.get("revoked_at") is None]
        revoked = [item for item in approvals if item.get("revoked_at") is not None]
        rejected = [item for item in approvals if item["decision"] == "rejected" and item.get("revoked_at") is None]
        outstanding_roles = policy["required_roles"][len(active_approvals) :]
        suspicious = sum(1 for item in approvals if item.get("suspicious_flags"))
        return {
            "policy": policy,
            "approved_count": len(active_approvals),
            "rejected_count": len(rejected),
            "revoked_count": len(revoked),
            "outstanding_roles": outstanding_roles,
            "fully_approved": len(active_approvals) >= policy["min_approvals"],
            "suspicious_records": suspicious,
            "emergency_shutdown": emergency_shutdown or {"active": False},
        }


approval_engine = ApprovalEngine()
