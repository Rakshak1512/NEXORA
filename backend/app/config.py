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

    # Database
    DATABASE_URL: str = "sqlite:///./cicada_saas.db"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Security
    JWT_SECRET_KEY: str = "cicada-2026-super-secret-jwt-key-98127398127"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    COLLECTOR_AUTH_SECRET: str = "secret-collector-token-01"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"
    LOG_LEVEL: str = "INFO"

    @property
    def jwt_secret(self) -> str:
        return self.JWT_SECRET_KEY or self.JWT_SECRET or "cicada-2026-super-secret-jwt-key-98127398127"

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
