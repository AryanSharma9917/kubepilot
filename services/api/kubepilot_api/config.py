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
    kubernetes_mode: str = "fixture"
    kubeconfig_path: str | None = None
    rag_mode: str = "keyword"
    agent_mode: str = "deterministic"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide application settings."""

    return Settings(
        app_name=os.getenv("KUBEPILOT_APP_NAME", "KubePilot API"),
        environment=os.getenv("KUBEPILOT_ENVIRONMENT", "development"),
        version=os.getenv("KUBEPILOT_VERSION", "0.1.0"),
        kubernetes_mode=os.getenv("KUBEPILOT_K8S_MODE", "fixture"),
        kubeconfig_path=os.getenv("KUBEPILOT_KUBECONFIG"),
        rag_mode=os.getenv("KUBEPILOT_RAG_MODE", "keyword"),
        agent_mode=os.getenv("KUBEPILOT_AGENT_MODE", "deterministic"),
    )
