"""Incident report artifact storage backends."""

from collections import OrderedDict
from functools import lru_cache
from threading import Lock
from typing import Any, Protocol

from kubepilot_api.config import get_settings
from kubepilot_api.schemas import (
    IncidentReportResponse,
    IncidentReportSummaryResponse,
)


class IncidentReportStore(Protocol):
    """Storage interface for generated incident report artifacts."""

    def put(self, report: IncidentReportResponse) -> IncidentReportResponse:
        """Store a generated incident report artifact."""

    def get(self, report_id: str) -> IncidentReportResponse | None:
        """Return one generated report artifact by ID."""

    def list(self, *, limit: int = 20) -> list[IncidentReportSummaryResponse]:
        """Return newest generated report artifacts first."""


class InMemoryIncidentReportStore:
    """Keep recently generated incident reports for local/demo workflows."""

    def __init__(self, *, max_items: int = 50) -> None:
        self._max_items = max_items
        self._reports: OrderedDict[str, IncidentReportResponse] = OrderedDict()
        self._lock = Lock()

    def put(self, report: IncidentReportResponse) -> IncidentReportResponse:
        """Store a report and evict the oldest artifact if needed."""

        with self._lock:
            self._reports[report.report_id] = report
            self._reports.move_to_end(report.report_id)
            while len(self._reports) > self._max_items:
                self._reports.popitem(last=False)
        return report

    def get(self, report_id: str) -> IncidentReportResponse | None:
        """Return one generated report artifact by ID."""

        with self._lock:
            return self._reports.get(report_id)

    def list(self, *, limit: int = 20) -> list[IncidentReportSummaryResponse]:
        """Return newest generated report artifacts first."""

        with self._lock:
            reports = list(reversed(self._reports.values()))[:limit]
        return [
            IncidentReportSummaryResponse(
                report_id=report.report_id,
                generated_at=report.generated_at,
                title=report.title,
                severity=report.severity,
                impacted_resource=report.impacted_resource,
                summary=report.summary,
            )
            for report in reports
        ]


class PostgresIncidentReportStore:
    """Persist generated incident reports in PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._ensure_schema()

    def put(self, report: IncidentReportResponse) -> IncidentReportResponse:
        """Store a report in PostgreSQL."""

        payload = report.model_dump(mode="json")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO incident_reports (
                    report_id,
                    generated_at,
                    title,
                    severity,
                    impacted_resource,
                    summary,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (report_id) DO UPDATE SET
                    generated_at = EXCLUDED.generated_at,
                    title = EXCLUDED.title,
                    severity = EXCLUDED.severity,
                    impacted_resource = EXCLUDED.impacted_resource,
                    summary = EXCLUDED.summary,
                    payload = EXCLUDED.payload
                """,
                (
                    report.report_id,
                    report.generated_at,
                    report.title,
                    report.severity,
                    report.impacted_resource,
                    report.summary,
                    self._json(payload),
                ),
            )
        return report

    def get(self, report_id: str) -> IncidentReportResponse | None:
        """Return one generated report artifact by ID."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM incident_reports WHERE report_id = %s",
                (report_id,),
            ).fetchone()
        if row is None:
            return None
        return IncidentReportResponse.model_validate(row["payload"])

    def list(self, *, limit: int = 20) -> list[IncidentReportSummaryResponse]:
        """Return newest generated report artifacts first."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    report_id,
                    generated_at,
                    title,
                    severity,
                    impacted_resource,
                    summary
                FROM incident_reports
                ORDER BY generated_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return [
            IncidentReportSummaryResponse(
                report_id=row["report_id"],
                generated_at=row["generated_at"],
                title=row["title"],
                severity=row["severity"],
                impacted_resource=row["impacted_resource"],
                summary=row["summary"],
            )
            for row in rows
        ]

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_reports (
                    report_id TEXT PRIMARY KEY,
                    generated_at TIMESTAMPTZ NOT NULL,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    impacted_resource TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload JSONB NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS incident_reports_generated_at_idx
                ON incident_reports (generated_at DESC)
                """
            )

    def _connect(self) -> Any:
        psycopg, dict_row, _ = _load_psycopg()
        return psycopg.connect(
            self._database_url,
            autocommit=True,
            row_factory=dict_row,
        )

    def _json(self, payload: dict[str, Any]) -> Any:
        _, _, json_adapter = _load_psycopg()
        return json_adapter(payload)


@lru_cache
def get_incident_report_store() -> IncidentReportStore:
    """Return the configured incident report store."""

    settings = get_settings()
    if settings.database_url:
        return PostgresIncidentReportStore(settings.database_url)
    return InMemoryIncidentReportStore()


def _load_psycopg() -> tuple[Any, Any, Any]:
    try:
        import psycopg
        from psycopg.rows import dict_row
        from psycopg.types.json import Json
    except ImportError as exc:
        raise RuntimeError(
            "Postgres persistence requires the psycopg package. "
            "Install project dependencies or unset KUBEPILOT_DATABASE_URL."
        ) from exc
    return psycopg, dict_row, Json
