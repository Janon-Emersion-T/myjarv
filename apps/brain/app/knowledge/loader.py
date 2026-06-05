from pathlib import Path

from app.config import settings


class KnowledgeLoader:
    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)

    def list_entries(self, category: str | None = None) -> list[dict]:
        base = self.root_path / category if category else self.root_path
        if not base.exists():
            return []
        files = sorted(path for path in base.rglob("*.md") if path.is_file())
        records: list[dict] = []
        for file in files:
            records.append(
                {
                    "path": str(file.relative_to(self.root_path)),
                    "category": file.relative_to(self.root_path).parts[0],
                    "content": file.read_text(encoding="utf-8"),
                }
            )
        return records

    def retrieve_relevant(self, query: str, limit: int = 5) -> list[dict]:
        query_terms = {part.lower() for part in query.split() if part.strip()}
        scored: list[tuple[int, dict]] = []
        for entry in self.list_entries():
            haystack = f"{entry['path']} {entry['content']}".lower()
            score = sum(1 for term in query_terms if term in haystack)
            if score:
                scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:limit]]


knowledge_loader = KnowledgeLoader(settings.KNOWLEDGE_DIR)
