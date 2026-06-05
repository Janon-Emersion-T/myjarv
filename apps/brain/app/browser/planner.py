from app.logger import logger


class BrowserAutomationPlanner:
    def create_plan(self, goal: str) -> dict:
        plan = {
            "goal": goal,
            "mode": "planning_only",
            "requires_approval": True,
            "steps": [
                "Inspect the requested browser workflow.",
                "Identify pages, inputs, outputs, and risk points.",
                "Block login, payment, or destructive actions until explicitly approved.",
                "Generate an execution checklist for Playwright or Selenium.",
            ],
        }
        logger.log("INFO", "browser.plan", "Prepared browser automation plan.", {"goal": goal})
        return plan


browser_planner = BrowserAutomationPlanner()

