from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Jarvis"
    APP_ENV: str = "development"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    OLLAMA_BASE_URL: str = "http://localhost:11434"

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    VECTOR_DB_ENABLED: bool = True

    WHATSAPP_REPORTING_ENABLED: bool = False

    LOG_LEVEL: str = "debug"

    class Config:
        env_file = ".env"


settings = Settings()
