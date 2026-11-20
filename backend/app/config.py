import os
import json
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "CYNERA"
    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Routing
    BACKEND_URL: str = "http://127.0.0.1:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    API_V1_STR: str = "/api"

    # Database (Supabase PostgreSQL is primary)
    SUPABASE_DB_URL: str = ""
    DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DB_ENGINE: str = "postgresql"
    DB_HOST: str = ""
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = ""
    DB_PASSWORD: str = ""

    # Security & Tokens
    JWT_SECRET_KEY: str = ""
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    COLLECTOR_AUTH_SECRET: str = "secret-collector-token-01"

    # Collector Reference Config
    COLLECTOR_ID: str = "col-prod-core-01"
    COLLECTOR_NAME: str = "Primary Cluster Collector 01"
    TENANT_ID: str = "11111111-1111-1111-1111-111111111111"
    COLLECTOR_CREDENTIAL: str = "secret-collector-token-01"
    COLLECTION_INTERVAL_SECONDS: int = 5
    HEARTBEAT_INTERVAL_SECONDS: int = 15
    LOCAL_QUEUE_PATH: str = "data/local_buffer.db"
    MAX_RETRY_ATTEMPTS: int = 5
    BACKOFF_FACTOR: float = 1.5
    VERSION: str = "1.4.2"
    SIMULATED_MODE: bool = False

    # Email & OTP (Resend API)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""
    RESEND_FROM_NAME: str = "CYNERA"
    RESEND_REPLY_TO: str = "support@cynera.io"
    OTP_EXPIRY_MINUTES: int = 5
    OTP_LENGTH: int = 6
    OTP_REQUIRED: bool = True
    OTP_HASH_SECRET: str = "cynera-otp-salt-98723498237"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"
    LOG_LEVEL: str = "INFO"

    @property
    def jwt_secret(self) -> str:
        key = self.JWT_SECRET_KEY or self.JWT_SECRET
        if not key:
            if "PYTEST_CURRENT_TEST" in os.environ or os.getenv("TESTING") == "true":
                return "cynera-test-secret-key-98127398127"
            return ""
        return key

    def get_active_db_url(self) -> str:
        # Strict precedence: SUPABASE_DB_URL > DATABASE_URL
        raw = (self.SUPABASE_DB_URL or self.DATABASE_URL or "").strip()
        if raw.startswith("postgres://"):
            raw = raw.replace("postgres://", "postgresql://", 1)
        # In automated test runner, use local SQLite test store
        if not raw and ("PYTEST_CURRENT_TEST" in os.environ or os.getenv("TESTING") == "true"):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cynera_db = os.path.join(backend_dir, "cynera.db").replace(os.sep, "/")
            return f"sqlite:///{cynera_db}"
        return raw

    def is_database_configured(self) -> bool:
        url = self.get_active_db_url()
        return bool(url and (url.startswith("postgresql://") or url.startswith("sqlite://")))

    def is_resend_configured(self) -> bool:
        return bool(self.RESEND_API_KEY and not self.RESEND_API_KEY.startswith("re_your") and self.RESEND_FROM_EMAIL)

    def is_jwt_configured(self) -> bool:
        return bool(self.JWT_SECRET_KEY and self.JWT_SECRET_KEY.strip())

    @property
    def algorithm(self) -> str:
        return self.JWT_ALGORITHM or self.ALGORITHM or "HS256"

    def get_cors_origins(self) -> List[str]:
        origins = []
        if self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL.rstrip('/'))
        if isinstance(self.CORS_ORIGINS, list):
            origins.extend(self.CORS_ORIGINS)
        elif isinstance(self.CORS_ORIGINS, str):
            if self.CORS_ORIGINS.startswith("["):
                try:
                    parsed = json.loads(self.CORS_ORIGINS)
                    if isinstance(parsed, list):
                        origins.extend(parsed)
                except Exception:
                    origins.extend([o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()])
            else:
                origins.extend([o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()])

        # Common local dev origins
        dev_defaults = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
        for dev in dev_defaults:
            if dev not in origins:
                origins.append(dev)

        # Deduplicate
        seen = set()
        deduped = []
        for o in origins:
            clean = o.rstrip('/')
            if clean and clean not in seen:
                seen.add(clean)
                deduped.append(clean)
        return deduped

settings = Settings()
