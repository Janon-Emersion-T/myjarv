from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.agents.registry import get_agent_by_name, list_agents
from app.agents.schema import Agent
from app.approval_gate import approval_gate
from app.knowledge.loader import knowledge_loader
from app.logger import logger
from app.routing.rules import routing_rules
from app.routing.store import routing_store


INTENT_ORDER = [
    "development",
    "marketing",
    "finance",
    "legal",
    "operations",
    "support",
    "research",
    "creative",
    "infrastructure",
    "general",
]


@dataclass
class CandidateScore:
    agent: Agent
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    def add(self, points: float, reason: str) -> None:
        self.score += points
        self.reasons.append(reason)


class RoutingEngine:
    def __init__(self) -> None:
        self.default_fallback = "Jarvis"

    def route(
        self,
        *,
        message: str,
        requested_action: str | None = None,
        preferred_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
        mode: str = "live",
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        metadata = metadata or {}
        blob = f"{message} {requested_action or ''}".strip()
        text = blob.lower()
        rules = routing_rules.load()
        agent_map = {agent.name: agent for agent in list_agents()}
        candidate_scores = {
            agent.name: CandidateScore(agent=agent) for agent in list_agents() if agent.status not in rules["blacklisted_statuses"]
        }

        knowledge_matches = knowledge_loader.retrieve_relevant(blob, limit=5)
        memory_scopes = self._memory_scopes_from_metadata(metadata)
        framework_hints = self._collect_hints(text, rules.get("framework_routes", {}))
        language_hints = self._collect_hints(text, rules.get("language_routes", {}))
        tool_matches = self._match_tools(text, rules.get("tool_keywords", {}))
        client_context = self._resolve_client_context(text, metadata)
        project_context = self._resolve_project_context(text, metadata)

        intent_category = self._classify_intent(text, rules)
        direct_rule = self._match_direct_route(text, rules.get("direct_routes", []))

        for score in candidate_scores.values():
            self._apply_agent_awareness(score, intent_category, tool_matches, memory_scopes, knowledge_matches)

        if direct_rule:
            self._apply_direct_rule(candidate_scores, direct_rule)

        self._apply_framework_and_language_routes(candidate_scores, rules, framework_hints, language_hints)
        self._apply_override_rules(candidate_scores, text, preferred_agent, metadata, rules)
        self._apply_client_context(candidate_scores, client_context, rules)
        self._apply_blacklist_whitelist(candidate_scores, metadata)

        candidates = self._rank_candidates(candidate_scores)
        primary_name, confidence, is_ambiguous, ambiguity_reason = self._pick_primary(candidates, direct_rule)
        if primary_name not in agent_map:
            primary_name = rules.get("default_fallback_agent", self.default_fallback)

        primary_agent = get_agent_by_name(primary_name)
        priority = self._classify_priority(text, primary_agent)
        risk_level, approval_level = approval_gate.classify(blob, primary_agent.approval_level, requested_action)
        strategy = self._choose_strategy(intent_category, direct_rule, risk_level, metadata, candidates)

        collaborators = self._supporting_agents(
            primary_agent=primary_agent,
            direct_rule=direct_rule,
            intent_category=intent_category,
            rules=rules,
            candidates=candidates,
        )
        fallback_agent = primary_agent.fallback_agent if primary_agent.fallback_agent in agent_map else rules.get(
            "default_fallback_agent", self.default_fallback
        )
        reviewers = self._review_chain(intent_category, direct_rule, rules, risk_level, client_context)
        escalation_chain = self._escalation_chain(intent_category, direct_rule, rules, risk_level)
        duplicate_of_task_id = metadata.get("duplicate_of_task_id")
        retry_recommendation = None
        warnings: list[str] = []

        if not duplicate_of_task_id:
            duplicate_of_task_id = self._detect_duplicate_task(message)
        if duplicate_of_task_id:
            warnings.append(f"Potential duplicate detected: {duplicate_of_task_id}")

        if metadata.get("previous_status") == "blocked":
            retry_recommendation = f"Retry via fallback agent {fallback_agent} with executive review."
            warnings.append("Blocked task recovery path activated.")

        if metadata.get("retry_attempt", 0):
            warnings.append("Retry routing mode enabled.")

        if is_ambiguous:
            warnings.append(ambiguity_reason or "Ambiguous routing decision.")

        if not collaborators and primary_agent.name == fallback_agent and primary_agent.name == rules.get("default_fallback_agent", "Jarvis"):
            warnings.append("Dead-end protection used the Jarvis fallback path.")

        subtasks = self._build_subtasks(intent_category, primary_agent.name, collaborators, reviewers, strategy)
        stages = self._build_stages(primary_agent.name, collaborators, reviewers, strategy)
        route_map = {
            "intake": ["Jarvis"],
            "execution": [primary_agent.name, *collaborators],
            "review": reviewers,
            "escalation": escalation_chain,
        }
        reasoning = self._build_reasoning(
            intent_category=intent_category,
            primary_agent=primary_agent.name,
            confidence=confidence,
            collaborators=collaborators,
            reviewers=reviewers,
            strategy=strategy,
            warnings=warnings,
        )

        decision = {
            "trace_id": trace_id or str(uuid.uuid4()),
            "mode": mode,
            "intent_category": intent_category,
            "confidence": confidence,
            "is_ambiguous": is_ambiguous,
            "ambiguity_reason": ambiguity_reason,
            "selected_agent": primary_agent.name,
            "supporting_agents": collaborators,
            "fallback_agent": fallback_agent,
            "review_chain": reviewers,
            "escalation_chain": escalation_chain,
            "execution_strategy": strategy,
            "stages": stages,
            "subtasks": subtasks,
            "priority": priority,
            "risk_level": risk_level,
            "approval_level": approval_level,
            "client_context": client_context,
            "project_context": project_context,
            "knowledge_matches": [item["path"] for item in knowledge_matches],
            "memory_scopes": memory_scopes,
            "tool_matches": tool_matches,
            "framework_hints": framework_hints,
            "language_hints": language_hints,
            "reviewers_required": reviewers,
            "duplicate_of_task_id": duplicate_of_task_id,
            "retry_recommendation": retry_recommendation,
            "timeout_seconds": self._timeout_for_strategy(strategy, risk_level),
            "route_map": route_map,
            "candidates": candidates[:8],
            "warnings": warnings,
            "reasoning": reasoning,
        }
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        routing_store.record(
            trace_id=decision["trace_id"],
            task_id=metadata.get("task_id"),
            mode=mode,
            message=message,
            requested_action=requested_action,
            preferred_agent=preferred_agent,
            latency_ms=latency_ms,
            decision=decision,
            metadata=metadata,
        )
        logger.log(
            "INFO",
            "routing.decision",
            "Routing decision created.",
            {
                "trace_id": decision["trace_id"],
                "selected_agent": primary_agent.name,
                "intent_category": intent_category,
                "confidence": confidence,
                "strategy": strategy,
            },
        )
        return decision

    def replay(self, trace_id: str) -> dict[str, Any]:
        trace = routing_store.get_trace(trace_id)
        request = trace["input"]
        return self.route(
            message=request["message"],
            requested_action=request.get("requested_action"),
            preferred_agent=request.get("preferred_agent"),
            metadata=request.get("metadata", {}),
            mode="replay",
            trace_id=str(uuid.uuid4()),
        )

    def _classify_intent(self, text: str, rules: dict[str, Any]) -> str:
        best_intent = "general"
        best_score = -1
        for intent in INTENT_ORDER:
            config = rules["intent_categories"].get(intent, {})
            score = sum(2 for keyword in config.get("keywords", []) if keyword in text)
            if score > best_score:
                best_score = score
                best_intent = intent
        return best_intent

    def _apply_agent_awareness(
        self,
        score: CandidateScore,
        intent_category: str,
        tool_matches: list[str],
        memory_scopes: list[str],
        knowledge_matches: list[dict[str, Any]],
    ) -> None:
        agent = score.agent
        if agent.department == intent_category or agent.company_department == intent_category:
            score.add(6, f"department match: {intent_category}")
        if intent_category in agent.knowledge_domains:
            score.add(3, f"knowledge domain match: {intent_category}")
        for tool in tool_matches:
            if tool in {item.lower() for item in agent.tools}:
                score.add(2.5, f"tool match: {tool}")
        for memory_scope in memory_scopes:
            if memory_scope in {item.lower() for item in agent.memory_permissions}:
                score.add(1.5, f"memory scope match: {memory_scope}")
        for knowledge in knowledge_matches:
            category = knowledge["category"].lower()
            if category in {item.lower() for item in agent.knowledge_domains}:
                score.add(1.5, f"knowledge base relevance: {knowledge['path']}")
        if agent.status == "experimental":
            score.add(-1, "experimental agent penalty")

    def _apply_direct_rule(self, scores: dict[str, CandidateScore], direct_rule: dict[str, Any]) -> None:
        primary = direct_rule["primary"]
        if primary in scores:
            scores[primary].add(14, f"direct route: {direct_rule['label']}")
        for collaborator in direct_rule.get("collaborators", []):
            if collaborator in scores:
                scores[collaborator].add(6, f"collaboration route: {direct_rule['label']}")
        for reviewer in direct_rule.get("reviewers", []):
            if reviewer in scores:
                scores[reviewer].add(2, f"review route: {direct_rule['label']}")

    def _apply_framework_and_language_routes(
        self,
        scores: dict[str, CandidateScore],
        rules: dict[str, Any],
        framework_hints: list[str],
        language_hints: list[str],
    ) -> None:
        for framework in framework_hints:
            agent = rules.get("framework_routes", {}).get(framework)
            if agent in scores:
                scores[agent].add(7, f"framework match: {framework}")
        for language in language_hints:
            agent = rules.get("language_routes", {}).get(language)
            if agent in scores:
                scores[agent].add(5, f"language match: {language}")

    def _apply_override_rules(
        self,
        scores: dict[str, CandidateScore],
        text: str,
        preferred_agent: str | None,
        metadata: dict[str, Any],
        rules: dict[str, Any],
    ) -> None:
        if preferred_agent and preferred_agent in scores:
            scores[preferred_agent].add(20, "preferred agent override")
        override_agent = metadata.get("route_override")
        if override_agent and override_agent in scores:
            scores[override_agent].add(25, "metadata route override")
        for phrase, agent in rules.get("routing_overrides", {}).items():
            if phrase in text and agent in scores:
                scores[agent].add(18, f"routing override: {phrase}")

    def _apply_client_context(self, scores: dict[str, CandidateScore], client_context: str | None, rules: dict[str, Any]) -> None:
        if not client_context:
            return
        config = rules.get("client_routes", {}).get(client_context)
        if not config:
            return
        for reviewer in config.get("executive_reviewers", []):
            if reviewer in scores:
                scores[reviewer].add(4, f"client context: {client_context}")

    def _apply_blacklist_whitelist(self, scores: dict[str, CandidateScore], metadata: dict[str, Any]) -> None:
        whitelist = {item for item in metadata.get("agent_whitelist", [])}
        blacklist = {item for item in metadata.get("agent_blacklist", [])}
        for name, candidate in list(scores.items()):
            if whitelist and name not in whitelist:
                candidate.add(-100, "whitelist exclusion")
            if name in blacklist:
                candidate.add(-100, "blacklist exclusion")

    def _rank_candidates(self, scores: dict[str, CandidateScore]) -> list[dict[str, Any]]:
        ranked = [item for item in scores.values() if item.score > -50]
        ranked.sort(key=lambda item: (item.score, item.agent.priority), reverse=True)
        return [
            {
                "agent": item.agent.name,
                "score": round(item.score, 2),
                "reasons": item.reasons[:6],
            }
            for item in ranked
        ]

    def _pick_primary(self, candidates: list[dict[str, Any]], direct_rule: dict[str, Any] | None) -> tuple[str, float, bool, str | None]:
        if not candidates:
            return self.default_fallback, 0.2, True, "No eligible candidates remained after blacklist/whitelist filters."
        top = candidates[0]
        confidence = 0.55 if top["score"] <= 0 else min(0.99, 0.55 + (top["score"] / 40.0))
        ambiguity_reason = None
        is_ambiguous = False
        if len(candidates) > 1:
            delta = top["score"] - candidates[1]["score"]
            if delta < 2.0:
                is_ambiguous = True
                ambiguity_reason = f"Top candidates are close: {top['agent']} vs {candidates[1]['agent']}."
                confidence = min(confidence, 0.72)
        if direct_rule:
            confidence = max(confidence, 0.88)
        return top["agent"], round(confidence, 4), is_ambiguous, ambiguity_reason

    def _supporting_agents(
        self,
        *,
        primary_agent: Agent,
        direct_rule: dict[str, Any] | None,
        intent_category: str,
        rules: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> list[str]:
        names: list[str] = []
        if direct_rule:
            names.extend(direct_rule.get("collaborators", []))
        else:
            for candidate in candidates[1:4]:
                if candidate["agent"] == primary_agent.name:
                    continue
                other = get_agent_by_name(candidate["agent"])
                if other.department == primary_agent.department or intent_category in other.knowledge_domains:
                    names.append(other.name)
        for partner in primary_agent.collaboration_partners:
            if partner != primary_agent.name and partner not in names:
                names.append(partner)
        unique = []
        for name in names:
            if name != primary_agent.name and name not in unique:
                unique.append(name)
        return unique[:4]

    def _review_chain(
        self,
        intent_category: str,
        direct_rule: dict[str, Any] | None,
        rules: dict[str, Any],
        risk_level: str,
        client_context: str | None,
    ) -> list[str]:
        reviewers = list(direct_rule.get("reviewers", [])) if direct_rule else list(
            rules["intent_categories"].get(intent_category, {}).get("reviewers", [])
        )
        if risk_level in {"HIGH", "CRITICAL"} and "Athena" not in reviewers:
            reviewers.append("Athena")
        if client_context == "lkprofessionals" and "Jarvis" not in reviewers:
            reviewers.append("Jarvis")
        return reviewers or list(rules.get("default_reviewers", ["Athena"]))

    def _escalation_chain(
        self,
        intent_category: str,
        direct_rule: dict[str, Any] | None,
        rules: dict[str, Any],
        risk_level: str,
    ) -> list[str]:
        chain = list(direct_rule.get("reviewers", [])) if direct_rule else list(
            rules["intent_categories"].get(intent_category, {}).get("escalation_chain", [])
        )
        if risk_level == "CRITICAL" and "Jarvis" not in chain:
            chain.append("Jarvis")
        if "Athena" not in chain:
            chain.append("Athena")
        return chain

    def _build_subtasks(
        self,
        intent_category: str,
        primary_agent: str,
        collaborators: list[str],
        reviewers: list[str],
        strategy: str,
    ) -> list[dict[str, Any]]:
        subtasks = [
            {
                "title": f"Scope and plan the {intent_category} task",
                "assigned_agent": primary_agent,
                "strategy": "single",
                "depends_on": [],
                "status": "planned",
            }
        ]
        for collaborator in collaborators:
            subtasks.append(
                {
                    "title": f"Collaborate on {intent_category} deliverables",
                    "assigned_agent": collaborator,
                    "strategy": strategy if strategy != "single" else "parallel",
                    "depends_on": [primary_agent],
                    "status": "planned",
                }
            )
        for reviewer in reviewers:
            subtasks.append(
                {
                    "title": "Final review and release recommendation",
                    "assigned_agent": reviewer,
                    "strategy": "sequential",
                    "depends_on": [primary_agent, *collaborators],
                    "status": "planned",
                }
            )
        return subtasks

    def _build_stages(self, primary_agent: str, collaborators: list[str], reviewers: list[str], strategy: str) -> list[dict[str, Any]]:
        return [
            {
                "stage": "intake",
                "assigned_agents": ["Jarvis"],
                "strategy": "single",
                "purpose": "Receive, classify, and validate the task request.",
            },
            {
                "stage": "execution",
                "assigned_agents": [primary_agent, *collaborators],
                "strategy": strategy,
                "purpose": "Deliver the main workstream with collaborator support.",
            },
            {
                "stage": "review",
                "assigned_agents": reviewers,
                "strategy": "sequential",
                "purpose": "Review quality, risk, and business readiness.",
            },
        ]

    def _build_reasoning(
        self,
        *,
        intent_category: str,
        primary_agent: str,
        confidence: float,
        collaborators: list[str],
        reviewers: list[str],
        strategy: str,
        warnings: list[str],
    ) -> str:
        return (
            f"Intent classified as {intent_category}. Selected {primary_agent} with confidence {confidence:.2f}. "
            f"Execution strategy is {strategy}. Collaborators: {', '.join(collaborators) or 'none'}. "
            f"Review chain: {', '.join(reviewers) or 'none'}. "
            f"Warnings: {', '.join(warnings) or 'none'}."
        )

    def _match_direct_route(self, text: str, direct_routes: list[dict[str, Any]]) -> dict[str, Any] | None:
        for route in direct_routes:
            if any(keyword in text for keyword in route.get("match_any", [])):
                return route
        return None

    def _match_tools(self, text: str, tool_keywords: dict[str, list[str]]) -> list[str]:
        matches = []
        for tool, keywords in tool_keywords.items():
            if any(keyword in text for keyword in keywords):
                matches.append(tool)
        return matches

    def _collect_hints(self, text: str, mapping: dict[str, str]) -> list[str]:
        return [key for key in mapping if key in text]

    def _resolve_client_context(self, text: str, metadata: dict[str, Any]) -> str | None:
        client = str(metadata.get("client", "")).strip().lower()
        if client:
            return client
        if "lkprofessionals" in text or "lk professionals" in text or "lkp" in text:
            return "lkprofessionals"
        return None

    def _resolve_project_context(self, text: str, metadata: dict[str, Any]) -> str | None:
        project = str(metadata.get("project", "")).strip()
        if project:
            return project
        if "website" in text or "web app" in text:
            return "website"
        if "seo" in text:
            return "seo"
        if "invoice" in text:
            return "finance"
        return None

    def _memory_scopes_from_metadata(self, metadata: dict[str, Any]) -> list[str]:
        scopes = metadata.get("memory_scopes", [])
        if isinstance(scopes, list):
            return [str(item).lower() for item in scopes]
        return []

    def _classify_priority(self, text: str, agent: Agent) -> int:
        urgency_map = {
            5: {"urgent", "critical", "asap", "outage", "production", "blocked"},
            4: {"today", "important", "deadline", "review"},
            3: {"plan", "prepare", "draft"},
        }
        for priority, keywords in urgency_map.items():
            if any(keyword in text for keyword in keywords):
                return max(priority, agent.priority)
        return max(3, agent.priority)

    def _choose_strategy(
        self,
        intent_category: str,
        direct_rule: dict[str, Any] | None,
        risk_level: str,
        metadata: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> str:
        if metadata.get("execution_strategy") in {"single", "sequential", "parallel"}:
            return metadata["execution_strategy"]
        if direct_rule:
            return direct_rule.get("strategy", "single")
        if risk_level in {"HIGH", "CRITICAL"}:
            return "sequential"
        if intent_category in {"marketing", "creative"} and len(candidates) > 2:
            return "parallel"
        return "single"

    def _timeout_for_strategy(self, strategy: str, risk_level: str) -> int:
        base = {"single": 900, "sequential": 1800, "parallel": 1200}[strategy]
        if risk_level == "CRITICAL":
            return base // 2
        if risk_level == "HIGH":
            return int(base * 0.75)
        return base

    def _detect_duplicate_task(self, message: str) -> str | None:
        trace_candidates = routing_store.list_traces(limit=50)
        normalized = self._normalize(message)
        for trace in trace_candidates:
            if self._normalize(trace["message"]) == normalized and trace.get("task_id"):
                return trace["task_id"]
        return None

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


routing_engine = RoutingEngine()
