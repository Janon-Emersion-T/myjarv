from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings

REQUIRED_PATHS = {
    "web/html.md",
    "web/css.md",
    "web/javascript.md",
    "backend/laravel.md",
    "backend/python.md",
    "backend/fastapi.md",
    "backend/postgresql.md",
    "backend/redis.md",
    "backend/rabbitmq.md",
    "backend/nats.md",
    "frontend/react.md",
    "frontend/tailwind.md",
    "frontend/tauri.md",
    "frontend/wordpress.md",
    "automation/playwright.md",
    "automation/selenium.md",
    "devops/docker.md",
    "devops/kubernetes.md",
    "devops/prometheus.md",
    "devops/grafana.md",
    "security/cybersecurity.md",
    "business/lkp-services.md",
    "business/proposal-writing.md",
    "business/project-estimation.md",
    "finance/accounting-tax.md",
    "legal/sri-lankan-business.md",
    "operations/playbooks.md",
    "operations/sop-library.md",
    "ai/prompt-engineering.md",
    "ai/autonomous-workflows.md",
    "ai/webrtc.md",
    "ai/whisper.md",
    "ai/opencv.md",
    "ai/yolo.md",
    "ai/ocr.md",
    "company/decisions.md",
    "company/lessons-learned.md",
    "templates/proposals.json",
}

TRUSTED_SOURCE_POLICY = {"internal", "mdn", "w3c", "react", "fastapi", "python", "docker", "kubernetes", "postgresql"}


class KnowledgeLoader:
    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)
        self._index_cache: list[dict[str, Any]] | None = None
        self._indexed_at: str | None = None

    def reindex(self) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        for file in sorted(path for path in self.root_path.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".json", ".pdf"}):
            record = self._load_entry(file)
            if record:
                records.append(record)
        self._index_cache = records
        self._indexed_at = self._now()
        return {"indexed": len(records), "indexed_at": self._indexed_at}

    def list_entries(self, category: str | None = None, include_quarantine: bool = True) -> list[dict[str, Any]]:
        entries = self._ensure_index()
        if category:
            entries = [entry for entry in entries if entry["category"] == category]
        if not include_quarantine:
            entries = [entry for entry in entries if entry["status"] != "quarantined"]
        return entries

    def retrieve_relevant(self, query: str, limit: int = 5, category: str | None = None) -> list[dict[str, Any]]:
        return self.search(query=query, category=category, limit=limit, semantic=True)

    def search(self, *, query: str, category: str | None = None, limit: int = 20, semantic: bool = True) -> list[dict[str, Any]]:
        terms = self._tokenize(query)
        if not terms:
            return self.list_entries(category=category)[:limit]
        scored: list[tuple[float, dict[str, Any]]] = []
        for entry in self.list_entries(category=category):
            haystack = self._search_blob(entry)
            score = 0.0
            for term in terms:
                if term in haystack:
                    score += 2.0
                if term in {item.lower() for item in entry["tags"]}:
                    score += 2.5
                if term in {item.lower() for item in entry["frameworks"] + entry["languages"]}:
                    score += 2.0
            if semantic:
                score += entry["confidence_score"] * 0.6
                score += entry["quality_score"] * 0.4
                score += len(set(terms).intersection(set(self._tokenize(entry["summary"])))) * 0.35
            if score > 0:
                payload = dict(entry)
                payload["search_score"] = round(score, 4)
                scored.append((score, payload))
        scored.sort(key=lambda item: (item[0], item[1]["confidence_score"], item[1]["updated_at"]), reverse=True)
        return [item[1] for item in scored[:limit]]

    def analytics(self) -> dict[str, Any]:
        entries = self._ensure_index()
        categories = Counter(entry["category"] for entry in entries)
        departments = Counter(entry["department"] for entry in entries)
        statuses = Counter(entry["status"] for entry in entries)
        sources = Counter(source for entry in entries for source in entry["sources"])
        return {
            "indexed_at": self._indexed_at,
            "total_entries": len(entries),
            "categories": dict(categories),
            "departments": dict(departments),
            "statuses": dict(statuses),
            "trusted_entries": sum(1 for entry in entries if entry["trusted"]),
            "quarantined_entries": sum(1 for entry in entries if entry["status"] == "quarantined"),
            "average_confidence": round(sum(entry["confidence_score"] for entry in entries) / len(entries), 4) if entries else 0,
            "average_quality": round(sum(entry["quality_score"] for entry in entries) / len(entries), 4) if entries else 0,
            "outdated_entries": sum(1 for entry in entries if entry["outdated"]),
            "sources": dict(sources),
        }

    def validate(self) -> dict[str, Any]:
        entries = self._ensure_index()
        issues: list[dict[str, Any]] = []
        for entry in entries:
            if not entry["summary"]:
                issues.append({"path": entry["path"], "issue": "missing_summary"})
            if not entry["sources"]:
                issues.append({"path": entry["path"], "issue": "missing_sources"})
            if entry["confidence_score"] < 0.5:
                issues.append({"path": entry["path"], "issue": "low_confidence"})
            if entry["approval_status"] not in {"approved", "draft", "review"}:
                issues.append({"path": entry["path"], "issue": "invalid_approval_status"})
        gaps = self.missing_knowledge()
        for gap in gaps["missing_paths"]:
            issues.append({"path": gap, "issue": "missing_required_knowledge"})
        return {"valid": len(issues) == 0, "issues": issues}

    def source_report(self) -> dict[str, Any]:
        entries = self._ensure_index()
        return {
            "trusted_source_policy": sorted(TRUSTED_SOURCE_POLICY),
            "by_entry": [{"path": entry["path"], "sources": entry["sources"], "trusted": entry["trusted"]} for entry in entries],
        }

    def quarantine(self) -> list[dict[str, Any]]:
        return [entry for entry in self._ensure_index() if entry["status"] == "quarantined"]

    def relationship_graph(self) -> dict[str, Any]:
        entries = self._ensure_index()
        nodes = [{"id": entry["path"], "category": entry["category"], "department": entry["department"]} for entry in entries]
        edges: list[dict[str, Any]] = []
        for index, left in enumerate(entries):
            for right in entries[index + 1 :]:
                shared = set(left["tags"]).intersection(set(right["tags"]))
                if left["category"] == right["category"]:
                    shared.add(f"category:{left['category']}")
                if not shared:
                    continue
                edges.append({"source": left["path"], "target": right["path"], "relationship": sorted(shared)[:5]})
        return {"nodes": nodes, "edges": edges[:500]}

    def missing_knowledge(self) -> dict[str, Any]:
        indexed = {entry["path"] for entry in self._ensure_index()}
        missing = sorted(REQUIRED_PATHS.difference(indexed))
        return {"missing_paths": missing, "complete": len(missing) == 0}

    def _ensure_index(self) -> list[dict[str, Any]]:
        if self._index_cache is None:
            self.reindex()
        return self._index_cache or []

    def _load_entry(self, file: Path) -> dict[str, Any] | None:
        if file.suffix.lower() == ".md":
            metadata, content = self._parse_markdown(file)
        elif file.suffix.lower() == ".json":
            metadata, content = self._parse_json(file)
        else:
            metadata, content = self._parse_pdf(file)
        relative = str(file.relative_to(self.root_path))
        category = file.relative_to(self.root_path).parts[0]
        tags = self._normalize_list(metadata.get("tags", []))
        sources = self._normalize_list(metadata.get("sources", ["internal"]))
        frameworks = self._normalize_list(metadata.get("frameworks", []))
        languages = self._normalize_list(metadata.get("languages", []))
        domain = str(metadata.get("domain", category))
        department = str(metadata.get("department", self._infer_department(category)))
        summary = str(metadata.get("summary", self._summarize(content)))
        confidence_score = float(metadata.get("confidence", self._default_confidence(file.suffix.lower())))
        quality_score = round(min(1.0, 0.45 + (0.1 if summary else 0) + (0.1 if sources else 0) + min(0.25, len(tags) * 0.03) + min(0.1, len(content) / 4000)), 4)
        trusted = bool(metadata.get("trusted", all(source.lower() in TRUSTED_SOURCE_POLICY for source in sources)))
        approval_status = str(metadata.get("approval_status", "approved" if trusted else "review"))
        version = str(metadata.get("version", "1.0"))
        last_reviewed = str(metadata.get("last_reviewed", self._now_date()))
        outdated = self._is_outdated(last_reviewed)
        verified = bool(metadata.get("verified", trusted and approval_status == "approved"))
        status = "quarantined" if (not verified or not trusted or confidence_score < 0.45) else "active"
        return {
            "path": relative,
            "category": category,
            "title": str(metadata.get("title", file.stem.replace("-", " ").title())),
            "summary": summary,
            "content": content,
            "tags": tags,
            "sources": sources,
            "confidence_score": round(confidence_score, 4),
            "quality_score": quality_score,
            "trusted": trusted,
            "verified": verified,
            "version": version,
            "last_reviewed": last_reviewed,
            "approval_status": approval_status,
            "domain": domain,
            "department": department,
            "frameworks": frameworks,
            "languages": languages,
            "status": status,
            "outdated": outdated,
            "source_type": file.suffix.lower().lstrip("."),
            "metadata": metadata,
            "updated_at": datetime.fromtimestamp(file.stat().st_mtime, UTC).isoformat(),
        }

    def _parse_markdown(self, file: Path) -> tuple[dict[str, Any], str]:
        raw = file.read_text(encoding="utf-8")
        metadata: dict[str, Any] = {}
        content = raw
        if raw.startswith("---\n"):
            _, front, body = raw.split("---\n", 2)
            metadata = self._parse_front_matter(front)
            content = body.strip()
        return metadata, content

    def _parse_json(self, file: Path) -> tuple[dict[str, Any], str]:
        payload = json.loads(file.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            metadata = payload.get("metadata", {})
            content = json.dumps(payload.get("content", payload), ensure_ascii=True, indent=2)
            return metadata, content
        return {}, json.dumps(payload, ensure_ascii=True, indent=2)

    def _parse_pdf(self, file: Path) -> tuple[dict[str, Any], str]:
        return {
            "title": file.stem.replace("-", " ").title(),
            "summary": "PDF ingestion placeholder entry.",
            "sources": ["internal"],
            "confidence": 0.4,
            "verified": False,
            "trusted": False,
            "approval_status": "review",
        }, f"PDF knowledge placeholder for {file.name}"

    def _parse_front_matter(self, front: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        for line in [item.strip() for item in front.splitlines() if item.strip()]:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = self._parse_value(value.strip())
        return metadata

    def _parse_value(self, value: str) -> Any:
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        if value.startswith("[") and value.endswith("]"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [item.strip() for item in value[1:-1].split(",") if item.strip()]
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return value

    def _normalize_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return []

    def _search_blob(self, entry: dict[str, Any]) -> str:
        return " ".join(
            [
                entry["path"].lower(),
                entry["title"].lower(),
                entry["summary"].lower(),
                entry["content"].lower(),
                " ".join(item.lower() for item in entry["tags"]),
                " ".join(item.lower() for item in entry["frameworks"]),
                " ".join(item.lower() for item in entry["languages"]),
            ]
        )

    def _tokenize(self, text: str) -> list[str]:
        return [token for token in "".join(char.lower() if char.isalnum() else " " for char in text).split() if len(token) > 1]

    def _default_confidence(self, suffix: str) -> float:
        return {".md": 0.82, ".json": 0.88, ".pdf": 0.4}.get(suffix, 0.6)

    def _infer_department(self, category: str) -> str:
        return {
            "web": "development",
            "frontend": "development",
            "backend": "development",
            "automation": "development",
            "devops": "infrastructure",
            "security": "security",
            "ai": "research",
            "business": "operations",
            "finance": "finance",
            "legal": "legal",
            "operations": "operations",
            "company": "executive",
            "templates": "operations",
        }.get(category, "operations")

    def _summarize(self, content: str) -> str:
        compact = " ".join(content.split())
        return compact[:157] + "..." if len(compact) > 160 else compact

    def _is_outdated(self, last_reviewed: str) -> bool:
        try:
            reviewed = datetime.fromisoformat(last_reviewed)
        except ValueError:
            try:
                reviewed = datetime.fromisoformat(f"{last_reviewed}T00:00:00+00:00")
            except ValueError:
                return True
        age_days = (datetime.now(UTC) - reviewed.astimezone(UTC)).days
        return age_days > 365

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _now_date(self) -> str:
        return datetime.now(UTC).date().isoformat()


knowledge_loader = KnowledgeLoader(settings.KNOWLEDGE_DIR)
