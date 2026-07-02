"""Cluster application service."""

from agent.tools.kubernetes import (
    ClusterHealthInspector,
    DeploymentDiagnoser,
    create_cluster_health_inspector,
    create_deployment_diagnoser,
)
from kubepilot_api.config import get_settings
from kubepilot_api.schemas import (
    ClusterHealthResponse,
    DeploymentDiagnosisResponse,
    KubernetesEventResponse,
    PodStatusResponse,
    WorkloadHealthResponse,
)


class ClusterService:
    """Boundary between the HTTP API and Kubernetes inspection tools."""

    def __init__(
        self,
        inspector: ClusterHealthInspector | None = None,
        diagnoser: DeploymentDiagnoser | None = None,
    ) -> None:
        settings = get_settings()
        self._inspector = inspector or create_cluster_health_inspector(
            mode=settings.kubernetes_mode,
            kubeconfig_path=settings.kubeconfig_path,
        )
        self._diagnoser = diagnoser or create_deployment_diagnoser(
            mode=settings.kubernetes_mode,
            kubeconfig_path=settings.kubeconfig_path,
        )

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

    async def diagnose_deployment(
        self,
        namespace: str,
        name: str,
    ) -> DeploymentDiagnosisResponse | None:
        """Return a diagnosis for one Kubernetes deployment."""

        diagnosis = await self._diagnoser.diagnose(namespace=namespace, name=name)
        if diagnosis is None:
            return None

        health = diagnosis.health
        return DeploymentDiagnosisResponse(
            namespace=diagnosis.namespace,
            name=diagnosis.name,
            health=WorkloadHealthResponse(
                namespace=health.namespace,
                name=health.name,
                kind=health.kind,
                desired_replicas=health.desired_replicas,
                ready_replicas=health.ready_replicas,
                status=health.status,
                reason=health.reason,
            ),
            pods=[
                PodStatusResponse(
                    namespace=pod.namespace,
                    name=pod.name,
                    phase=pod.phase,
                    ready=pod.ready,
                    restart_count=pod.restart_count,
                    reason=pod.reason,
                )
                for pod in diagnosis.pods
            ],
            events=[
                KubernetesEventResponse(
                    namespace=event.namespace,
                    involved_object=event.involved_object,
                    reason=event.reason,
                    message=event.message,
                    event_type=event.event_type,
                )
                for event in diagnosis.events
            ],
            recommendations=list(diagnosis.recommendations),
        )


async def get_cluster_service() -> ClusterService:
    """Provide the cluster service to API routes."""

    return ClusterService()
