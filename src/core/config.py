from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Production Data Platform"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+pysqlite:///./data_platform.db"
    redis_url: str = "redis://localhost:6379/0"
    process_async: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    jwt_secret_key: str = ("dev-only-change-this-jwt-secret-key-123456789")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    analytics_cache_ttl_seconds: int = 60
    auth_rate_limit_requests: int = 10
    auth_rate_limit_window_seconds: int = 60

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
