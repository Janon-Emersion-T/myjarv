from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import ROOT_DIR, settings


MANIFEST_PATTERNS = {
    "node": {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"},
    "python": {"pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock"},
    "rust": {"Cargo.toml"},
    "php": {"composer.json"},
    "docker": {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"},
}

EXTENSION_LANGUAGES = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".rs": "Rust",
    ".php": "PHP",
    ".json": "JSON",
    ".md": "Markdown",
    ".toml": "TOML",
    ".yml": "YAML",
    ".yaml": "YAML",
}

FRAMEWORK_HINTS = {
    "FastAPI": ["fastapi", "APIRouter(", "FastAPI("],
    "React": ["react", "tsx", "jsx"],
    "Tauri": ["tauri", "@tauri-apps"],
    "Tailwind": ["tailwindcss"],
    "Playwright": ["@playwright/test", "playwright"],
    "Docker": ["Dockerfile", "docker-compose"],
}


class DeveloperMode:
    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path)
        self.output_dir = Path(settings.DEVELOPER_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str | None = None) -> Path:
        candidate = (self.root_path / (path or ".")).resolve()
        if not str(candidate).startswith(str(self.root_path.resolve())):
            raise ValueError("Repository path must stay within the workspace.")
        return candidate

    def analyze_repository(self, path: str | None = None) -> dict[str, Any]:
        repo = self._resolve_path(path)
        ignored_parts = {".git", "venv", "__pycache__", "node_modules", "dist", "build"}
        files = [item for item in repo.rglob("*") if item.is_file() and not ignored_parts.intersection(item.parts)]
        manifests = sorted({item.name for item in files if item.name in {name for names in MANIFEST_PATTERNS.values() for name in names}})
        extensions = Counter(item.suffix.lower() for item in files if item.suffix)
        languages = self._detect_languages(extensions)
        stack = self._detect_stack(files)
        frameworks = self._detect_frameworks(files)
        tests = [item for item in files if self._is_test_file(item)]
        docs = [item for item in files if item.suffix.lower() == ".md"]
        ci_workflows = [item for item in files if ".github" in item.parts and item.suffix.lower() in {".yml", ".yaml"}]
        summary = {
            "path": str(repo.relative_to(self.root_path)),
            "scanned_at": datetime.now(UTC).isoformat(),
            "total_files": len(files),
            "top_extensions": dict(extensions.most_common(12)),
            "languages": languages,
            "stack": stack,
            "frameworks": frameworks,
            "manifests": manifests,
            "test_files": len(tests),
            "doc_files": len(docs),
            "ci_workflows": [str(item.relative_to(repo)) for item in ci_workflows],
            "key_files": self._key_files(files, repo),
            "repositories": self._discover_repositories(repo),
        }
        self._write_snapshot("analysis", summary)
        return summary

    def repository_health(self, path: str | None = None) -> dict[str, Any]:
        analysis = self.analyze_repository(path)
        signals: list[dict[str, Any]] = []
        if analysis["test_files"] == 0:
            signals.append({"severity": "high", "issue": "No test files detected."})
        if not analysis["ci_workflows"]:
            signals.append({"severity": "medium", "issue": "No CI workflow files detected."})
        if "Docker" not in analysis["frameworks"] and any(item in analysis["stack"] for item in ["Node.js", "Python", "Rust"]):
            signals.append({"severity": "low", "issue": "No containerization markers detected."})
        if analysis["doc_files"] < 5:
            signals.append({"severity": "low", "issue": "Documentation footprint is thin."})

        score = 100
        for signal in signals:
            score -= {"high": 18, "medium": 10, "low": 4}[signal["severity"]]
        score = max(20, score)
        return {
            "score": score,
            "grade": self._grade(score),
            "signals": signals,
            "analysis": analysis,
        }

    def detect_errors(self, path: str | None = None) -> dict[str, Any]:
        analysis = self.analyze_repository(path)
        findings: list[dict[str, Any]] = []
        if analysis["test_files"] < 3:
            findings.append({"type": "test_gap", "severity": "medium", "message": "Limited automated test surface detected."})
        if "Python" in analysis["languages"] and "FastAPI" in analysis["frameworks"] and "README.md" not in analysis["key_files"]:
            findings.append({"type": "docs_gap", "severity": "low", "message": "Primary service README not detected in key files."})
        if not analysis["repositories"]:
            findings.append({"type": "indexing", "severity": "medium", "message": "Repository roots could not be segmented cleanly."})
        if "Playwright" in analysis["frameworks"] and analysis["test_files"] < 5:
            findings.append({"type": "e2e_gap", "severity": "low", "message": "Playwright detected but E2E surface appears small."})
        return {
            "path": analysis["path"],
            "generated_at": datetime.now(UTC).isoformat(),
            "findings": findings,
            "top_risk": findings[0] if findings else None,
        }

    def fix_plan(
        self,
        *,
        goal: str,
        path: str | None = None,
        constraints: list[str] | None = None,
        preferred_files: list[str] | None = None,
    ) -> dict[str, Any]:
        analysis = self.analyze_repository(path)
        health = self.repository_health(path)
        errors = self.detect_errors(path)
        files = preferred_files or analysis["key_files"][:6]
        steps = [
            "Reproduce or inspect the issue within the relevant repository slice.",
            "Apply the smallest safe code change in the likely ownership area.",
            "Run focused tests first, then broaden to regression coverage.",
            "Document risk, rollback notes, and any follow-up hardening work.",
        ]
        return {
            "goal": goal,
            "generated_at": datetime.now(UTC).isoformat(),
            "repository_path": analysis["path"],
            "target_files": files,
            "constraints": constraints or [],
            "health_grade": health["grade"],
            "open_findings": errors["findings"],
            "steps": steps,
            "recommended_tests": self._recommended_tests(analysis),
            "deployment_checklist": self.deployment_checklist(path)["items"],
            "changelog_hint": f"Describe the fix for: {goal}",
        }

    def generate_changelog(self, *, title: str, summary: str, changes: list[str], version: str | None = None) -> dict[str, Any]:
        version_label = version or datetime.now(UTC).strftime("%Y.%m.%d")
        body = "\n".join(f"- {item}" for item in changes)
        markdown = f"## {version_label} - {title}\n\n{summary}\n\n### Changes\n{body}\n"
        payload = {
            "title": title,
            "version": version_label,
            "summary": summary,
            "changes": changes,
            "markdown": markdown,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        self._write_snapshot("changelog", payload)
        return payload

    def deployment_checklist(self, path: str | None = None) -> dict[str, Any]:
        analysis = self.analyze_repository(path)
        items = [
            "Confirm required environment variables and secrets are available.",
            "Run focused tests plus a broader regression sweep.",
            "Capture backup and rollback notes before rollout.",
            "Review approval and release window requirements.",
        ]
        if "Docker" in analysis["frameworks"]:
            items.append("Build and verify container artifacts.")
        if "Rust" in analysis["languages"]:
            items.append("Run cargo checks or workspace build validation.")
        if "TypeScript" in analysis["languages"]:
            items.append("Run frontend build validation and smoke tests.")
        return {
            "path": analysis["path"],
            "items": items,
            "risk_summary": f"{analysis['stack']} stack with {analysis['test_files']} test files detected.",
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def analytics(self, path: str | None = None) -> dict[str, Any]:
        analysis = self.analyze_repository(path)
        health = self.repository_health(path)
        errors = self.detect_errors(path)
        return {
            "analysis": analysis,
            "health": {"score": health["score"], "grade": health["grade"]},
            "open_findings": len(errors["findings"]),
            "recommended_tests": self._recommended_tests(analysis),
        }

    def _discover_repositories(self, root: Path) -> list[dict[str, Any]]:
        repos = []
        for candidate in sorted(root.iterdir()):
            if not candidate.is_dir() or candidate.name.startswith("."):
                continue
            files = {item.name for item in candidate.iterdir() if item.is_file()}
            if files.intersection({"package.json", "pyproject.toml", "Cargo.toml", "composer.json"}):
                repos.append({"name": candidate.name, "path": str(candidate.relative_to(root)), "manifests": sorted(files.intersection({"package.json", "pyproject.toml", "Cargo.toml", "composer.json"}))})
        if not repos:
            repos.append({"name": root.name, "path": str(root.relative_to(self.root_path)), "manifests": []})
        return repos

    def _key_files(self, files: list[Path], repo: Path) -> list[str]:
        ranked = []
        preferred_names = {"README.md", "package.json", "pyproject.toml", "Cargo.toml", "Dockerfile", "ROADMAP.md"}
        for item in files:
            relative = str(item.relative_to(repo))
            if item.name in preferred_names or relative.startswith("apps/brain/app/") or relative.startswith("apps/desktop/src/"):
                ranked.append(relative)
        return ranked[:20]

    def _detect_languages(self, extensions: Counter[str]) -> list[str]:
        seen = []
        for extension, _count in extensions.most_common():
            language = EXTENSION_LANGUAGES.get(extension)
            if language and language not in seen:
                seen.append(language)
        return seen

    def _detect_stack(self, files: list[Path]) -> list[str]:
        names = {item.name for item in files}
        stack = []
        if names.intersection(MANIFEST_PATTERNS["node"]):
            stack.append("Node.js")
        if names.intersection(MANIFEST_PATTERNS["python"]):
            stack.append("Python")
        if names.intersection(MANIFEST_PATTERNS["rust"]):
            stack.append("Rust")
        if names.intersection(MANIFEST_PATTERNS["php"]):
            stack.append("PHP")
        if names.intersection(MANIFEST_PATTERNS["docker"]):
            stack.append("Docker")
        return stack

    def _detect_frameworks(self, files: list[Path]) -> list[str]:
        sample_files = files[:250]
        haystacks = []
        for item in sample_files:
            haystacks.append(item.name.lower())
            if item.suffix.lower() in {".json", ".md", ".ts", ".tsx", ".js", ".jsx", ".py", ".toml"}:
                try:
                    haystacks.append(item.read_text(encoding="utf-8", errors="ignore")[:4000].lower())
                except Exception:
                    continue
        blob = "\n".join(haystacks)
        frameworks = [name for name, hints in FRAMEWORK_HINTS.items() if any(hint.lower() in blob for hint in hints)]
        return sorted(frameworks)

    def _is_test_file(self, path: Path) -> bool:
        name = path.name.lower()
        return name.startswith("test_") or name.endswith(".spec.ts") or name.endswith(".spec.tsx") or "/tests/" in str(path).replace("\\", "/")

    def _recommended_tests(self, analysis: dict[str, Any]) -> list[str]:
        tests = []
        if "Python" in analysis["languages"]:
            tests.append("Run targeted Python unit tests.")
        if "TypeScript" in analysis["languages"]:
            tests.append("Run frontend build and focused TypeScript or Playwright checks.")
        if "Rust" in analysis["languages"]:
            tests.append("Run cargo check or targeted Rust tests.")
        return tests or ["Run the narrowest available validation command."]

    def _grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "E"

    def _write_snapshot(self, prefix: str, payload: dict[str, Any]) -> None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = self.output_dir / f"{prefix}-{stamp}-{uuid.uuid4().hex[:8]}.json"
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


developer_mode = DeveloperMode(str(ROOT_DIR))
