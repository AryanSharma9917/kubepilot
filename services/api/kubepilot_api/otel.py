"""Optional OpenTelemetry integration for the API service."""

from typing import Any

from fastapi import FastAPI

from kubepilot_api.config import Settings

_TRACER_PROVIDER: Any | None = None


def configure_opentelemetry(app: FastAPI, settings: Settings) -> bool:
    """Configure OTLP tracing when optional dependencies and config are present."""

    if not settings.otel_exporter_otlp_endpoint:
        app.state.otel_enabled = False
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        app.state.otel_enabled = False
        app.state.otel_error = str(exc)
        return False

    global _TRACER_PROVIDER
    if _TRACER_PROVIDER is None:
        resource = Resource.create(
            {
                "service.name": settings.otel_service_name,
                "deployment.environment": settings.environment,
            }
        )
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            headers=dict(settings.otel_headers),
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _TRACER_PROVIDER = provider

    FastAPIInstrumentor.instrument_app(app, tracer_provider=_TRACER_PROVIDER)
    app.state.otel_enabled = True
    return True
