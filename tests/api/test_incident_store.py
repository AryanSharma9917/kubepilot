from datetime import UTC, datetime

import pytest
from kubepilot_api.config import get_settings
from kubepilot_api.incident_store import (
    InMemoryIncidentReportStore,
    get_incident_report_store,
)
from kubepilot_api.schemas import IncidentReportResponse


def test_in_memory_incident_store_returns_newest_reports_first() -> None:
    store = InMemoryIncidentReportStore(max_items=2)
    first = _report("report-1", datetime(2026, 8, 12, 10, 0, tzinfo=UTC))
    second = _report("report-2", datetime(2026, 8, 12, 11, 0, tzinfo=UTC))
    third = _report("report-3", datetime(2026, 8, 12, 12, 0, tzinfo=UTC))

    store.put(first)
    store.put(second)
    store.put(third)

    assert store.get("report-1") is None
    assert store.get("report-3") == third
    assert [report.report_id for report in store.list()] == ["report-3", "report-2"]


def test_incident_store_defaults_to_memory_without_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KUBEPILOT_DATABASE_URL", raising=False)
    get_settings.cache_clear()
    get_incident_report_store.cache_clear()

    store = get_incident_report_store()

    assert isinstance(store, InMemoryIncidentReportStore)
    get_incident_report_store.cache_clear()
    get_settings.cache_clear()


def _report(report_id: str, generated_at: datetime) -> IncidentReportResponse:
    return IncidentReportResponse(
        report_id=report_id,
        generated_at=generated_at,
        title=f"Deployment incident: {report_id}",
        severity="warning",
        summary="Deployment is degraded.",
        probable_cause="Readiness probe failure.",
        operator_impact="Requests may fail.",
        impacted_resource="payments/deployment/checkout",
        status_update="WARNING: checkout is degraded.",
    )
