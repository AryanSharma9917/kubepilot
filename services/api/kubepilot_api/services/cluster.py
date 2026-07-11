"""Cluster application service."""

from agent.incidents import build_deployment_incident_report
from agent.tools.kubernetes import (
    ClusterHealthInspector,
    DeploymentDiagnoser,
    create_cluster_health_inspector,
    create_deployment_diagnoser,
)
from kubepilot_api.config import get_settings
from kubepilot_api.policy import NamespaceAccessPolicy
from kubepilot_api.schemas import (
    ClusterHealthResponse,
    ContainerLogResponse,
    DeploymentDiagnosisResponse,
    EvidenceItemResponse,
    IncidentReportResponse,
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
            service_url=settings.kubernetes_service_url,
        )
        self._diagnoser = diagnoser or create_deployment_diagnoser(
            mode=settings.kubernetes_mode,
            kubeconfig_path=settings.kubeconfig_path,
            service_url=settings.kubernetes_service_url,
        )
        self._namespace_policy = NamespaceAccessPolicy(settings.allowed_namespaces)

    async def health(self, namespace: str | None = None) -> ClusterHealthResponse:
        """Return workload health from the configured inspector."""

        self._namespace_policy.ensure_allowed(namespace)
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

        self._namespace_policy.ensure_allowed(namespace)
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
            logs=[
                ContainerLogResponse(
                    namespace=log.namespace,
                    pod_name=log.pod_name,
                    container_name=log.container_name,
                    text=log.text,
                    previous=log.previous,
                )
                for log in diagnosis.logs
            ],
            recommendations=list(diagnosis.recommendations),
        )

    async def deployment_incident_report(
        self,
        namespace: str,
        name: str,
    ) -> IncidentReportResponse | None:
        """Return a structured incident report for one deployment."""

        self._namespace_policy.ensure_allowed(namespace)
        diagnosis = await self._diagnoser.diagnose(namespace=namespace, name=name)
        if diagnosis is None:
            return None

        report = build_deployment_incident_report(diagnosis)
        return IncidentReportResponse(
            title=report.title,
            severity=report.severity,
            summary=report.summary,
            impacted_resource=report.impacted_resource,
            evidence=[
                EvidenceItemResponse(source=item.source, message=item.message)
                for item in report.evidence
            ],
            timeline=[
                EvidenceItemResponse(source=item.source, message=item.message)
                for item in report.timeline
            ],
            next_actions=list(report.next_actions),
            sources=list(report.sources),
        )


async def get_cluster_service() -> ClusterService:
    """Provide the cluster service to API routes."""

    return ClusterService()
