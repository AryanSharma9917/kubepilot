"""FastAPI application entry point."""

from fastapi import FastAPI, Response

from kubepilot_api.audit import audit_middleware
from kubepilot_api.auth import api_key_auth_middleware
from kubepilot_api.config import get_settings
from kubepilot_api.metrics import metrics_middleware, render_metrics
from kubepilot_api.otel import configure_opentelemetry
from kubepilot_api.rate_limit import rate_limit_middleware
from kubepilot_api.routes.audit import router as audit_router
from kubepilot_api.routes.chat import router as chat_router
from kubepilot_api.routes.cluster import router as cluster_router
from kubepilot_api.routes.knowledge import router as knowledge_router
from kubepilot_api.routes.traces import router as traces_router
from kubepilot_api.schemas import HealthResponse, ServiceInfo
from kubepilot_api.tracing import trace_middleware


def create_app() -> FastAPI:
    """Create and configure the API application."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="API entry point for the KubePilot platform.",
    )
    app.middleware("http")(audit_middleware)
    app.middleware("http")(metrics_middleware)
    app.middleware("http")(trace_middleware)
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(api_key_auth_middleware)
    app.include_router(audit_router)
    app.include_router(chat_router)
    app.include_router(cluster_router)
    app.include_router(knowledge_router)
    app.include_router(traces_router)

    @app.get("/", response_model=ServiceInfo, tags=["service"])
    async def service_info() -> ServiceInfo:
        return ServiceInfo(
            name=settings.app_name,
            version=settings.version,
            environment=settings.environment,
        )

    @app.get("/healthz", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        """Report whether the API process is alive."""

        return HealthResponse(status="ok")

    @app.get("/readyz", response_model=HealthResponse, tags=["health"])
    async def readiness() -> HealthResponse:
        """Report whether the API can accept traffic."""

        return HealthResponse(status="ready")

    @app.get("/metrics", tags=["monitoring"])
    async def metrics() -> Response:
        """Expose Prometheus-style service metrics."""

        return Response(render_metrics(), media_type="text/plain; version=0.0.4")

    configure_opentelemetry(app, settings)
    return app


app = create_app()
