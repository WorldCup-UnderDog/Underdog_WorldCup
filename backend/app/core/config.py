"""Application settings sourced from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _split_csv(value: str) -> list[str]:
    parts = [item.strip() for item in value.split(",")]
    return [item for item in parts if item]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "DarkHorse Prediction API")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    cors_origins_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    @property
    def cors_origins(self) -> list[str]:
        return _split_csv(self.cors_origins_raw)


settings = Settings()

