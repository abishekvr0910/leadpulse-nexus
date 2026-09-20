from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "LeadPulse Nexus"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = f"sqlite:///{(BASE_DIR / 'leads.db').as_posix()}"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    auto_create_schema: bool = True

    admin_username: str = ""
    admin_password: SecretStr = SecretStr("")

    agency_name: str = "LeadPulse AI"
    sender_name: str = "LeadPulse AI"
    sender_email: str = ""
    sender_phone: str = ""
    calendly_url: str = ""
    demo_inbound_phone: str = ""
    default_setup_price: str = ""
    default_retainer_price: str = ""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")

    twilio_account_sid: str = ""
    twilio_api_key: str = ""
    twilio_api_secret: SecretStr = SecretStr("")
    twilio_auth_token: SecretStr = SecretStr("")
    twilio_from_phone: str = ""
    vapi_api_key: SecretStr = SecretStr("")
    vapi_assistant_id: str = ""

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url.removeprefix("postgres://")
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url.removeprefix("postgresql://")
        return url

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @property
    def auth_enabled(self) -> bool:
        return bool(self.admin_username and self.admin_password.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()
