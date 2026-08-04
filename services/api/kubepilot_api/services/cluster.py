"""Cluster application service."""

from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from agent.incidents import build_deployment_incident_report
from agent.tools.kubernetes import (
    ClusterHealthInspector,
    DeploymentDiagnoser,
    DeploymentDiagnosis,
    create_cluster_health_inspector,
    create_deployment_diagnoser,
)
from kubepilot_api.config import get_settings
from kubepilot_api.incident_store import incident_report_store
from kubepilot_api.metrics import record_cluster_tool_call
from kubepilot_api.policy import NamespaceAccessPolicy
from kubepilot_api.schemas import (
    ClusterHealthResponse,
    ContainerLogResponse,
    DeploymentDiagnosisResponse,
    EvidenceItemResponse,
    IncidentReportResponse,
    KubernetesEventResponse,
    PodStatusResponse,
    RemediationActionResponse,
    RemediationPlanResponse,
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
        self._namespace_policy = NamespaceAccessPolicy(
            allowed_namespaces=settings.allowed_namespaces,
            allowed_actions=settings.allowed_actions,
        )

    async def health(self, namespace: str | None = None) -> ClusterHealthResponse:
        """Return workload health from the configured inspector."""

        self._namespace_policy.ensure_operation_allowed(
            namespace=namespace,
            action="cluster:health",
        )
        started = perf_counter()
        try:
            health = await self._inspector.inspect(namespace=namespace)
        except Exception:
            record_cluster_tool_call(
                operation="cluster_health",
                result="error",
                elapsed_seconds=perf_counter() - started,
            )
            raise
        record_cluster_tool_call(
            operation="cluster_health",
            result="healthy" if health.is_healthy else "degraded",
            elapsed_seconds=perf_counter() - started,
        )
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

        self._namespace_policy.ensure_operation_allowed(
            namespace=namespace,
            action="deployment:diagnose",
        )
        started = perf_counter()
        try:
            diagnosis = await self._diagnoser.diagnose(namespace=namespace, name=name)
        except Exception:
            record_cluster_tool_call(
                operation="deployment_diagnose",
                result="error",
                elapsed_seconds=perf_counter() - started,
            )
            raise
        record_cluster_tool_call(
            operation="deployment_diagnose",
            result="found" if diagnosis is not None else "missing",
            elapsed_seconds=perf_counter() - started,
        )
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

        self._namespace_policy.ensure_operation_allowed(
            namespace=namespace,
            action="deployment:incident-report",
        )
        started = perf_counter()
        try:
            diagnosis = await self._diagnoser.diagnose(namespace=namespace, name=name)
        except Exception:
            record_cluster_tool_call(
                operation="deployment_incident_report",
                result="error",
                elapsed_seconds=perf_counter() - started,
            )
            raise
        record_cluster_tool_call(
            operation="deployment_incident_report",
            result="found" if diagnosis is not None else "missing",
            elapsed_seconds=perf_counter() - started,
        )
        if diagnosis is None:
            return None

        report = build_deployment_incident_report(diagnosis)
        incident_response = IncidentReportResponse(
            report_id=str(uuid4()),
            generated_at=datetime.now(UTC),
            title=report.title,
            severity=report.severity,
            summary=report.summary,
            probable_cause=report.probable_cause,
            operator_impact=report.operator_impact,
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
            status_update=report.status_update,
            sources=list(report.sources),
        )
        return incident_report_store.put(incident_response)

    async def remediation_plan(
        self,
        namespace: str,
        name: str,
    ) -> RemediationPlanResponse | None:
        """Return approval-gated remediation commands for one deployment."""

        self._namespace_policy.ensure_operation_allowed(
            namespace=namespace,
            action="deployment:remediation-plan",
        )
        started = perf_counter()
        try:
            diagnosis = await self._diagnoser.diagnose(namespace=namespace, name=name)
        except Exception:
            record_cluster_tool_call(
                operation="deployment_remediation_plan",
                result="error",
                elapsed_seconds=perf_counter() - started,
            )
            raise
        record_cluster_tool_call(
            operation="deployment_remediation_plan",
            result="found" if diagnosis is not None else "missing",
            elapsed_seconds=perf_counter() - started,
        )
        if diagnosis is None:
            return None

        return RemediationPlanResponse(
            namespace=diagnosis.namespace,
            name=diagnosis.name,
            summary=(
                f"{diagnosis.display_name} is {diagnosis.health.status.lower()}: "
                f"{diagnosis.health.reason}. Review and approve before running commands."
            ),
            actions=_remediation_actions(diagnosis),
            rollback=f"kubectl rollout undo deployment/{name} -n {namespace}",
        )


async def get_cluster_service() -> ClusterService:
    """Provide the cluster service to API routes."""

    return ClusterService()


def _remediation_actions(
    diagnosis: DeploymentDiagnosis,
) -> list[RemediationActionResponse]:
    pod_reasons = {pod.reason for pod in diagnosis.pods if pod.reason}
    event_reasons = {event.reason for event in diagnosis.events}
    namespace = diagnosis.namespace
    name = diagnosis.name
    actions = [
        RemediationActionResponse(
            title="Capture rollout evidence",
            command=f"kubectl describe deployment/{name} -n {namespace}",
            risk="low",
            reason="Read-only evidence capture before any operational change.",
        )
    ]
    if "ImagePullBackOff" in pod_reasons:
        actions.append(
            RemediationActionResponse(
                title="Rollback bad image rollout",
                command=f"kubectl rollout undo deployment/{name} -n {namespace}",
                risk="medium",
                reason="Image pull failures often require reverting to the last known-good tag.",
            )
        )
    if "CrashLoopBackOff" in pod_reasons:
        actions.append(
            RemediationActionResponse(
                title="Restart after config fix",
                command=f"kubectl rollout restart deployment/{name} -n {namespace}",
                risk="medium",
                reason="Use only after the failing config, secret, or dependency has been fixed.",
            )
        )
    if "FailedScheduling" in event_reasons or "Unschedulable" in pod_reasons:
        actions.append(
            RemediationActionResponse(
                title="Review pending pod scheduling",
                command=f"kubectl describe pods -n {namespace} -l app={name}",
                risk="low",
                reason="Scheduling failures need capacity, quota, taint, or affinity review.",
            )
        )
    if not diagnosis.health.ready_replicas:
        actions.append(
            RemediationActionResponse(
                title="Hold traffic until ready",
                command=f"kubectl rollout status deployment/{name} -n {namespace}",
                risk="low",
                reason="Do not route traffic to a deployment with zero ready replicas.",
            )
        )
    return actions
