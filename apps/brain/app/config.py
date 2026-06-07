from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    APP_NAME: str = "Jarvis Brain"
    APP_ENV: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DATABASE_BACKEND: str = "sqlite"
    DATABASE_PATH: str = str(ROOT_DIR / "data" / "jarvis.sqlite3")
    POSTGRES_DSN: str | None = None
    LOG_FILE_PATH: str = str(ROOT_DIR / "data" / "logs" / "jarvis.jsonl")
    TASKS_DIR: str = str(ROOT_DIR / "data" / "tasks")
    APPROVALS_DIR: str = str(ROOT_DIR / "data" / "approvals")
    DEVELOPER_DIR: str = str(ROOT_DIR / "data" / "developer")
    BUSINESS_DIR: str = str(ROOT_DIR / "data" / "business")
    PROJECTS_DIR: str = str(ROOT_DIR / "data" / "projects")
    MEMORY_DIR: str = str(ROOT_DIR / "data" / "memory")
    KNOWLEDGE_DIR: str = str(ROOT_DIR / "data" / "knowledge")
    ROUTING_RULES_PATH: str = str(ROOT_DIR / "packages" / "agents" / "routing-rules.json")
    VOICE_ALLOWED_SPEAKERS: str = "janon,lkp-admin"
    VOICE_EMERGENCY_CONTACT: str = "Janon"
    VOICE_SESSION_TIMEOUT_SECONDS: int = 900
    SECURITY_SECRET_KEY: str = "jarvis-dev-secret-key"
    SECURITY_BOOTSTRAP_ADMIN: str = "janon"
    SECURITY_BOOTSTRAP_PASSWORD: str = "change-me-now"
    SECURITY_REQUIRE_AUTH: bool = False
    SECURITY_RATE_LIMIT_WINDOW_SECONDS: int = 60
    SECURITY_RATE_LIMIT_MAX_REQUESTS: int = 240
    HASHICORP_VAULT_ADDR: str | None = None
    CLOUD_SECRET_MANAGER_ENDPOINT: str | None = None
    BACKUP_DIR: str = str(ROOT_DIR / "data" / "backups")
    PRODUCTION_LOCK_MODE: bool = False
    LOCAL_AUTH_TOKEN: str | None = None
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
        Path(self.DEVELOPER_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.BUSINESS_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.PROJECTS_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.MEMORY_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.KNOWLEDGE_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.BACKUP_DIR).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
