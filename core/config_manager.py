import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class FeatureFlags:

    enable_auth: bool = True
    enable_rate_limiting: bool = True
    enable_monitoring: bool = True
    enable_streaming: bool = True
    enable_caching: bool = True
    enable_debug_mode: bool = False
    enable_audit_logging: bool = True

    enable_web_search: bool = True
    enable_rag: bool = True
    enable_research: bool = True
    enable_tools: bool = True

    max_upload_size_mb: int = 50
    max_batch_size: int = 10
    max_query_length: int = 5000


@dataclass
class EnvironmentConfig:

    env: Environment
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    redis_url: Optional[str] = None

    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    cors_origins: list = field(default_factory=lambda: ["http://localhost:8501"])

    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    features: FeatureFlags = field(default_factory=FeatureFlags)


class ConfigManager:

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):

        if self._initialized:
            return

        self._initialized = True

        self._env = self._detect_environment()
        self._config = self._build_config()
        self._overrides: Dict[str, Any] = {}

    def _detect_environment(self) -> Environment:

        env_str = os.getenv("APP_ENV", "development").lower()

        env_map = {
            "development": Environment.DEVELOPMENT,
            "staging": Environment.STAGING,
            "production": Environment.PRODUCTION,
            "testing": Environment.TESTING,
        }

        return env_map.get(env_str, Environment.DEVELOPMENT)

    def _build_config(self) -> EnvironmentConfig:

        is_prod = self._env == Environment.PRODUCTION
        is_test = self._env == Environment.TESTING

        features = FeatureFlags(
            enable_auth=not is_test,
            enable_rate_limiting=is_prod,
            enable_monitoring=not is_test,
            enable_streaming=True,
            enable_caching=not is_test,
            enable_debug_mode=self._env == Environment.DEVELOPMENT,
            enable_audit_logging=is_prod
        )

        return EnvironmentConfig(
            env=self._env,
            debug=self._env == Environment.DEVELOPMENT,
            host=os.getenv("APP_HOST", "0.0.0.0"),
            port=int(os.getenv("APP_PORT", "8000")),
            workers=int(os.getenv("APP_WORKERS", "4" if is_prod else "1")),
            db_pool_size=int(os.getenv("DB_POOL_SIZE", "10" if is_prod else "5")),
            db_max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20" if is_prod else "10")),
            redis_url=os.getenv("REDIS_URL"),
            log_level=os.getenv("LOG_LEVEL", "WARNING" if is_prod else "INFO"),
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:8501").split(","),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_MINUTE", "120" if is_prod else "60")),
            rate_limit_per_hour=int(os.getenv("RATE_LIMIT_HOUR", "5000" if is_prod else "1000")),
            features=features
        )

    @property
    def env(self) -> Environment:
        return self._env

    @property
    def config(self) -> EnvironmentConfig:
        return self._config

    def get(self, key: str, default: Any = None) -> Any:

        if key in self._overrides:
            return self._overrides[key]

        if hasattr(self._config, key):
            return getattr(self._config, key)

        return default

    def set(self, key: str, value: Any):

        self._overrides[key] = value

    def is_production(self) -> bool:
        return self._env == Environment.PRODUCTION

    def is_development(self) -> bool:
        return self._env == Environment.DEVELOPMENT

    def is_testing(self) -> bool:
        return self._env == Environment.TESTING

    def get_cors_origins(self) -> list:

        if self.is_production():
            return os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

        return ["http://localhost:8501", "http://127.0.0.1:8501"]


config_manager = ConfigManager()
