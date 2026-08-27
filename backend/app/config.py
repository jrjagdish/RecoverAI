from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "RecoverAI"
    env: str = "development"
    api_prefix: str = "/api"

    database_url: str = "sqlite:///./recoverai.db"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    groq_api_key: str = ""
    ai_model: str = "llama-3.3-70b-versatile"

    max_recovery_attempts: int = 3
    cost_to_recover_threshold: float = 50
    quiet_hours_start: str = "21:00"
    quiet_hours_end: str = "09:00"

    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
