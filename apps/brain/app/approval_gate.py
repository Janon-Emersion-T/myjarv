from app.logger import logger


LEVEL_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}

DANGEROUS_ACTION_RULES = {
    "delete": "CRITICAL",
    "remove": "CRITICAL",
    "rm ": "CRITICAL",
    "push": "HIGH",
    "deploy": "HIGH",
    "email": "HIGH",
    "whatsapp": "HIGH",
    "credential": "HIGH",
    "secret": "HIGH",
    "finance": "HIGH",
    "invoice": "HIGH",
    "legal": "HIGH",
    "shell": "HIGH",
    "command": "MEDIUM",
}


def highest_level(*levels: str) -> str:
    return max(levels, key=lambda level: LEVEL_ORDER[level])


class ApprovalGate:
    def classify(self, text: str, agent_approval_level: str, requested_action: str | None = None) -> tuple[str, str]:
        blob = f"{text} {requested_action or ''}".lower()
        inferred_risk = "LOW"

        for keyword, level in DANGEROUS_ACTION_RULES.items():
            if keyword in blob:
                inferred_risk = highest_level(inferred_risk, level)

        approval_level = highest_level(inferred_risk, agent_approval_level)
        logger.log(
            "INFO",
            "approval.classified",
            "Classified task approval requirement.",
            {
                "risk_level": inferred_risk,
                "approval_level": approval_level,
                "requested_action": requested_action,
            },
        )
        return inferred_risk, approval_level


approval_gate = ApprovalGate()
