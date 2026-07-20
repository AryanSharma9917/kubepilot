"""Cluster API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from kubepilot_api.schemas import (
    ClusterHealthResponse,
    DeploymentDiagnosisResponse,
    IncidentReportResponse,
)
from kubepilot_api.services.cluster import ClusterService, get_cluster_service

router = APIRouter(prefix="/api/v1/cluster", tags=["cluster"])


@router.get("/health", response_model=ClusterHealthResponse)
async def cluster_health(
    namespace: str | None = Query(default=None, min_length=1),
    service: ClusterService = Depends(get_cluster_service),
) -> ClusterHealthResponse:
    """Return a Kubernetes workload health summary."""

    try:
        return await service.health(namespace=namespace)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get(
    "/namespaces/{namespace}/deployments/{name}/diagnose",
    response_model=DeploymentDiagnosisResponse,
)
async def diagnose_deployment(
    namespace: str,
    name: str,
    service: ClusterService = Depends(get_cluster_service),
) -> DeploymentDiagnosisResponse:
    """Return a deployment diagnosis for a Kubernetes workload."""

    try:
        diagnosis = await service.diagnose_deployment(namespace=namespace, name=name)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if diagnosis is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return diagnosis


@router.get(
    "/namespaces/{namespace}/deployments/{name}/incident-report",
    response_model=IncidentReportResponse,
)
async def deployment_incident_report(
    namespace: str,
    name: str,
    service: ClusterService = Depends(get_cluster_service),
) -> IncidentReportResponse:
    """Return a structured incident report for a Kubernetes deployment."""

    try:
        report = await service.deployment_incident_report(namespace=namespace, name=name)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if report is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return report


@router.get("/namespaces/{namespace}/deployments/{name}/incident-report.md")
async def deployment_incident_report_markdown(
    namespace: str,
    name: str,
    service: ClusterService = Depends(get_cluster_service),
) -> Response:
    """Return a deployment incident report as markdown."""

    try:
        report = await service.deployment_incident_report(namespace=namespace, name=name)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if report is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return Response(
        _incident_report_markdown(report),
        media_type="text/markdown; charset=utf-8",
    )


def _incident_report_markdown(report: IncidentReportResponse) -> str:
    lines = [
        f"# {report.title}",
        "",
        f"- Severity: {report.severity}",
        f"- Impacted resource: {report.impacted_resource}",
        "",
        "## Summary",
        "",
        report.summary,
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- **{item.source}:** {item.message}" for item in report.evidence)
    lines.extend(["", "## Timeline", ""])
    lines.extend(f"- **{item.source}:** {item.message}" for item in report.timeline)
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in report.next_actions)
    if report.sources:
        lines.extend(["", "## Sources", ""])
        lines.extend(f"- {source}" for source in report.sources)
    return "\n".join(lines) + "\n"
