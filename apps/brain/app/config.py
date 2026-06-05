from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    APP_NAME: str = "Jarvis Brain"
    APP_ENV: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DATABASE_PATH: str = str(ROOT_DIR / "data" / "jarvis.sqlite3")
    LOG_FILE_PATH: str = str(ROOT_DIR / "data" / "logs" / "jarvis.jsonl")
    TASKS_DIR: str = str(ROOT_DIR / "data" / "tasks")
    APPROVALS_DIR: str = str(ROOT_DIR / "data" / "approvals")
    MEMORY_DIR: str = str(ROOT_DIR / "data" / "memory")
    KNOWLEDGE_DIR: str = str(ROOT_DIR / "data" / "knowledge")
    DEFAULT_LOG_LIMIT: int = 100

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / "apps" / "brain" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        Path(self.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(self.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(self.TASKS_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.APPROVALS_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.MEMORY_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.KNOWLEDGE_DIR).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
