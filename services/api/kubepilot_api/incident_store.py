"""Process-local incident report artifact store."""

from collections import OrderedDict
from threading import Lock

from kubepilot_api.schemas import (
    IncidentReportResponse,
    IncidentReportSummaryResponse,
)


class IncidentReportStore:
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


incident_report_store = IncidentReportStore()
