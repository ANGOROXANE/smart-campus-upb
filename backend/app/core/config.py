import os
from uuid import uuid4
from functools import lru_cache

from pydantic import BaseModel, Field, SecretStr, field_validator


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    app_name: str = Field(default="Smart Campus UPB API")
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = Field(default="INFO")

    mongo_uri: SecretStr = Field(default=SecretStr("mongodb://localhost:27017"))
    mongo_database: str = Field(default="smart_campus")
    influx_url: str = Field(default="http://localhost:8086")
    influx_token: SecretStr | None = None
    influx_org: str = Field(default="smart-campus-upb")
    influx_bucket: str = Field(default="campus")
    jwt_secret: SecretStr | None = None
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)
    redis_url: str | None = Field(default="redis://localhost:6379/0")
    redis_password: SecretStr | None = None
    redis_sentinel_hosts: str | None = None
    redis_sentinel_service: str = Field(default="smart-campus-redis")
    redis_db: int = Field(default=0, ge=0)
    redis_socket_timeout_seconds: float = Field(default=2.0, gt=0)
    cache_ttl_seconds: int = Field(default=60, ge=1)
    latest_measurements_cache_ttl_seconds: int = Field(default=10, ge=1)
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=120, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    node_red_api_key: SecretStr | None = None
    initial_admin_email: str | None = None
    initial_admin_password: SecretStr | None = None
    instance_id: str = Field(default_factory=lambda: f"api-{uuid4().hex[:8]}")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed_levels:
            return "INFO"
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Smart Campus UPB API"),
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=os.getenv("APP_PORT", "8000"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        mongo_database=os.getenv("MONGO_DATABASE", "smart_campus"),
        influx_url=os.getenv("INFLUX_URL", "http://localhost:8086"),
        influx_token=os.getenv("INFLUX_TOKEN"),
        influx_org=os.getenv("INFLUX_ORG", "smart-campus-upb"),
        influx_bucket=os.getenv("INFLUX_BUCKET", "campus"),
        jwt_secret=os.getenv("JWT_SECRET"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_expire_minutes=os.getenv(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
            "30",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        redis_password=os.getenv("REDIS_PASSWORD"),
        redis_sentinel_hosts=os.getenv("REDIS_SENTINEL_HOSTS"),
        redis_sentinel_service=os.getenv(
            "REDIS_SENTINEL_SERVICE",
            "smart-campus-redis",
        ),
        redis_db=os.getenv("REDIS_DB", "0"),
        redis_socket_timeout_seconds=os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", "2"),
        cache_ttl_seconds=os.getenv("CACHE_TTL_SECONDS", "60"),
        latest_measurements_cache_ttl_seconds=os.getenv(
            "LATEST_MEASUREMENTS_CACHE_TTL_SECONDS",
            "10",
        ),
        rate_limit_enabled=_env_bool("RATE_LIMIT_ENABLED", True),
        rate_limit_requests=os.getenv("RATE_LIMIT_REQUESTS", "120"),
        rate_limit_window_seconds=os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"),
        node_red_api_key=os.getenv("NODE_RED_API_KEY"),
        initial_admin_email=os.getenv("INITIAL_ADMIN_EMAIL"),
        initial_admin_password=os.getenv("INITIAL_ADMIN_PASSWORD"),
        instance_id=os.getenv("INSTANCE_ID", f"api-{uuid4().hex[:8]}"),
    )
