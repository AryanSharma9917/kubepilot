"""Cluster application service."""

from agent.tools.kubernetes import (
    ClusterHealthInspector,
    create_cluster_health_inspector,
)
from kubepilot_api.schemas import ClusterHealthResponse, WorkloadHealthResponse


class ClusterService:
    """Boundary between the HTTP API and Kubernetes inspection tools."""

    def __init__(self, inspector: ClusterHealthInspector | None = None) -> None:
        self._inspector = inspector or create_cluster_health_inspector()

    async def health(self, namespace: str | None = None) -> ClusterHealthResponse:
        """Return workload health from the configured inspector."""

        health = await self._inspector.inspect(namespace=namespace)
        unhealthy = health.unhealthy_workloads
        return ClusterHealthResponse(
            status="healthy" if health.is_healthy else "degraded",
            unhealthy_count=len(unhealthy),
            workloads=[
                WorkloadHealthResponse(
                    namespace=workload.namespace,
                    name=workload.name,
                    kind=workload.kind,
                    desired_replicas=workload.desired_replicas,
                    ready_replicas=workload.ready_replicas,
                    status=workload.status,
                    reason=workload.reason,
                )
                for workload in unhealthy
            ],
        )


async def get_cluster_service() -> ClusterService:
    """Provide the cluster service to API routes."""

    return ClusterService()
