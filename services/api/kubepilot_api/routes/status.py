"""Runtime status API routes."""

from fastapi import APIRouter

from kubepilot_api.config import get_settings
from kubepilot_api.schemas import RuntimeStatusResponse

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
