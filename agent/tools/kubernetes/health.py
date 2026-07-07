"""Cluster health inspection tool."""

from typing import Protocol

from agent.tools.kubernetes.client import KubernetesClient, create_kubernetes_client
from agent.tools.kubernetes.models import ClusterHealth, WorkloadHealth


class ClusterHealthInspector(Protocol):
    """Interface for Kubernetes health inspection implementations."""

    async def inspect(self, namespace: str | None = None) -> ClusterHealth:
        """Return health information for known workloads."""


class KubernetesClusterHealthInspector:
    """Cluster health inspector backed by a Kubernetes client boundary."""

    def __init__(self, client: KubernetesClient | None = None) -> None:
        self._client = client or create_kubernetes_client()

    async def inspect(self, namespace: str | None = None) -> ClusterHealth:
        """Return deployment health for all namespaces or one namespace."""

        return ClusterHealth(workloads=await self._client.list_deployments(namespace=namespace))


class InMemoryClusterHealthInspector(KubernetesClusterHealthInspector):
    """Deterministic inspector used by local development and tests."""

    def __init__(self, workloads: tuple[WorkloadHealth, ...] | None = None) -> None:
        from agent.tools.kubernetes.client import InMemoryKubernetesClient

        super().__init__(
            InMemoryKubernetesClient(deployments=workloads or default_workloads())
        )


def create_cluster_health_inspector(
    *,
    mode: str = "fixture",
    kubeconfig_path: str | None = None,
    service_url: str = "http://k8s-tool:8081",
) -> ClusterHealthInspector:
    """Create the default cluster health inspector."""

    return KubernetesClusterHealthInspector(
        create_kubernetes_client(
            mode=mode,
            kubeconfig_path=kubeconfig_path,
            service_url=service_url,
        )
    )


def default_workloads() -> tuple[WorkloadHealth, ...]:
    """Return deterministic sample workloads for local development."""

    return (
        WorkloadHealth(
            namespace="default",
            name="kubepilot-api",
            kind="Deployment",
            desired_replicas=2,
            ready_replicas=2,
            status="Healthy",
            reason="All replicas are ready",
        ),
        WorkloadHealth(
            namespace="payments",
            name="checkout",
            kind="Deployment",
            desired_replicas=3,
            ready_replicas=1,
            status="Degraded",
            reason="Two replicas are unavailable",
        ),
        WorkloadHealth(
            namespace="platform",
            name="metrics-scraper",
            kind="Deployment",
            desired_replicas=1,
            ready_replicas=0,
            status="Degraded",
            reason="Readiness probe is failing",
        ),
    )
