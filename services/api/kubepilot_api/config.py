"""Runtime configuration for the KubePilot API."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuration loaded from environment variables."""

    app_name: str = "KubePilot API"
    environment: str = "development"
    version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide application settings."""

    return Settings(
        app_name=os.getenv("KUBEPILOT_APP_NAME", "KubePilot API"),
        environment=os.getenv("KUBEPILOT_ENVIRONMENT", "development"),
        version=os.getenv("KUBEPILOT_VERSION", "0.1.0"),
    )
