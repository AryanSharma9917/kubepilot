"""Cluster API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

from kubepilot_api.schemas import ClusterHealthResponse, DeploymentDiagnosisResponse
from kubepilot_api.services.cluster import ClusterService, get_cluster_service

router = APIRouter(prefix="/api/v1/cluster", tags=["cluster"])


@router.get("/health", response_model=ClusterHealthResponse)
async def cluster_health(
    namespace: str | None = Query(default=None, min_length=1),
    service: ClusterService = Depends(get_cluster_service),
) -> ClusterHealthResponse:
    """Return a Kubernetes workload health summary."""

    return await service.health(namespace=namespace)


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

    diagnosis = await service.diagnose_deployment(namespace=namespace, name=name)
    if diagnosis is None:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return diagnosis
