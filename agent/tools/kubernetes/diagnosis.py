"""Deployment diagnosis tool."""

from typing import Protocol

from agent.tools.kubernetes.client import KubernetesClient, create_kubernetes_client
from agent.tools.kubernetes.models import DeploymentDiagnosis


class DeploymentDiagnoser(Protocol):
    """Interface for deployment diagnosis implementations."""

    async def diagnose(self, namespace: str, name: str) -> DeploymentDiagnosis | None:
        """Diagnose one Kubernetes deployment."""


class KubernetesDeploymentDiagnoser:
    """Diagnose deployments using a Kubernetes client boundary."""

    def __init__(self, client: KubernetesClient | None = None) -> None:
        self._client = client or create_kubernetes_client()

    async def diagnose(self, namespace: str, name: str) -> DeploymentDiagnosis | None:
        """Collect deployment, pod, and event signals into a diagnosis."""

        deployment = await self._client.get_deployment(namespace=namespace, name=name)
        if deployment is None:
            return None

        pods = await self._client.list_pods_for_deployment(namespace=namespace, name=name)
        events = await self._client.list_events_for_deployment(namespace=namespace, name=name)
        logs = await self._client.list_logs_for_deployment(namespace=namespace, name=name)
        return DeploymentDiagnosis(
            namespace=namespace,
            name=name,
            health=deployment,
            pods=pods,
            events=events,
            logs=logs,
            recommendations=_recommendations(deployment.reason, pods, events, logs),
        )


def create_deployment_diagnoser(
    *,
    mode: str = "fixture",
    kubeconfig_path: str | None = None,
    service_url: str = "http://k8s-tool:8081",
) -> DeploymentDiagnoser:
    """Create a deployment diagnoser for the requested Kubernetes mode."""

    return KubernetesDeploymentDiagnoser(
        create_kubernetes_client(
            mode=mode,
            kubeconfig_path=kubeconfig_path,
            service_url=service_url,
        )
    )


def _recommendations(
    reason: str,
    pods: object,
    events: object,
    logs: object,
) -> tuple[str, ...]:
    pod_reasons = {
        pod.reason
        for pod in pods
        if getattr(pod, "reason", None)
    }
    event_reasons = {
        event.reason
        for event in events
        if getattr(event, "reason", None)
    }
    log_text = "\n".join(
        log.text.lower()
        for log in logs
        if getattr(log, "text", None)
    )
    recommendations: list[str] = []

    if "ImagePullBackOff" in pod_reasons or "Failed" in event_reasons:
        recommendations.append("Verify the image name, tag, registry credentials, and pull secret.")
    if "CrashLoopBackOff" in pod_reasons:
        recommendations.append("Inspect previous container logs and recent configuration changes.")
    if "missing" in log_text and "environment variable" in log_text:
        recommendations.append(
            "Compare required environment variables against the deployment manifest."
        )
    if "Readiness probe is failing" in reason:
        recommendations.append(
            "Check readiness probe path, port, timeout, and application startup logs."
        )
    if not recommendations:
        recommendations.append("Inspect rollout status, pod events, and recent deployment changes.")

    return tuple(recommendations)
