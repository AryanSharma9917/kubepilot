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
    kubernetes_service_url: str = "http://k8s-tool:8081"
    allowed_namespaces: tuple[str, ...] = ()
    rag_mode: str = "keyword"
    rag_index_path: str | None = None
    llm_provider: str = "deterministic"
    llm_endpoint: str | None = None
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
        kubernetes_service_url=os.getenv(
            "KUBEPILOT_K8S_SERVICE_URL",
            "http://k8s-tool:8081",
        ),
        allowed_namespaces=_split_csv(os.getenv("KUBEPILOT_ALLOWED_NAMESPACES", "")),
        rag_mode=os.getenv("KUBEPILOT_RAG_MODE", "keyword"),
        rag_index_path=os.getenv("KUBEPILOT_RAG_INDEX_PATH"),
        llm_provider=os.getenv("KUBEPILOT_LLM_PROVIDER", "deterministic"),
        llm_endpoint=os.getenv("KUBEPILOT_LLM_ENDPOINT"),
        agent_mode=os.getenv("KUBEPILOT_AGENT_MODE", "deterministic"),
    )


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())
