import builtins

from fastapi import FastAPI
from kubepilot_api.config import Settings, get_settings
from kubepilot_api.otel import configure_opentelemetry


def test_otel_is_disabled_without_endpoint() -> None:
    app = FastAPI()

    enabled = configure_opentelemetry(app, Settings())

    assert enabled is False
    assert app.state.otel_enabled is False


def test_otel_config_parses_endpoint_service_name_and_headers(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "KUBEPILOT_OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://otel-collector:4318/v1/traces",
    )
    monkeypatch.setenv("KUBEPILOT_OTEL_SERVICE_NAME", "kubepilot-test")
    monkeypatch.setenv("KUBEPILOT_OTEL_HEADERS", "x-api-key=secret,invalid,tenant=dev")
    get_settings.cache_clear()

    settings = get_settings()

    get_settings.cache_clear()

    assert settings.otel_exporter_otlp_endpoint == "http://otel-collector:4318/v1/traces"
    assert settings.otel_service_name == "kubepilot-test"
    assert settings.otel_headers == (("x-api-key", "secret"), ("tenant", "dev"))


def test_otel_startup_is_graceful_without_optional_dependencies(
    monkeypatch,
) -> None:
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("opentelemetry"):
            raise ImportError("missing opentelemetry")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    app = FastAPI()

    enabled = configure_opentelemetry(
        app,
        Settings(otel_exporter_otlp_endpoint="http://otel-collector:4318/v1/traces"),
    )

    assert enabled is False
    assert app.state.otel_enabled is False
    assert "missing opentelemetry" in app.state.otel_error
