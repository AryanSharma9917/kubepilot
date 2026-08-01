"""Runtime status API routes."""

from fastapi import APIRouter

from kubepilot_api.config import get_settings
from kubepilot_api.schemas import (
    PlatformCapabilitiesResponse,
    PlatformCapability,
    RuntimeStatusResponse,
)

router = APIRouter(prefix="/api/v1", tags=["status"])


@router.get("/status", response_model=RuntimeStatusResponse)
async def runtime_status() -> RuntimeStatusResponse:
    """Return redacted runtime feature and mode status."""

    settings = get_settings()
    return RuntimeStatusResponse(
        environment=settings.environment,
        kubernetes_mode=settings.kubernetes_mode,
        rag_mode=settings.rag_mode,
        llm_provider=settings.llm_provider,
        agent_mode=settings.agent_mode,
        auth_enabled=bool(settings.api_keys),
        namespace_policy_enabled=bool(settings.allowed_namespaces),
        action_policy_enabled=bool(settings.allowed_actions),
        rate_limit_per_minute=settings.rate_limit_per_minute,
        otel_export_enabled=bool(settings.otel_exporter_otlp_endpoint),
    )


@router.get("/capabilities", response_model=PlatformCapabilitiesResponse)
async def platform_capabilities() -> PlatformCapabilitiesResponse:
    """Return the implemented KubePilot platform capability map."""

    settings = get_settings()
    return PlatformCapabilitiesResponse(
        capabilities=[
            PlatformCapability(
                name="Agentic orchestration",
                status=settings.agent_mode,
                description=(
                    "Classifies intent, retrieves context, calls Kubernetes tools, "
                    "synthesizes answers, and exposes workflow steps."
                ),
            ),
            PlatformCapability(
                name="Runbook RAG",
                status=settings.rag_mode,
                description=(
                    "Loads markdown runbooks, chunks knowledge, supports keyword "
                    "retrieval, persisted vector indexes, and optional FAISS."
                ),
            ),
            PlatformCapability(
                name="Kubernetes diagnosis",
                status=settings.kubernetes_mode,
                description=(
                    "Inspects workload health, deployment status, pods, events, "
                    "and logs through a bounded Kubernetes client."
                ),
            ),
            PlatformCapability(
                name="Incident reporting",
                status="ready",
                description=(
                    "Generates severity, probable cause, operator impact, evidence "
                    "timeline, next actions, and markdown handoff reports."
                ),
            ),
            PlatformCapability(
                name="Observability",
                status="ready",
                description=(
                    "Exposes Prometheus metrics, local traces, audit events, request "
                    "IDs, and optional OTLP trace export."
                ),
            ),
            PlatformCapability(
                name="Platform deployment",
                status="ready",
                description=(
                    "Ships Docker, Docker Compose, Helm, kind smoke tests, "
                    "Prometheus, Grafana, and ArgoCD manifests."
                ),
            ),
        ]
    )
