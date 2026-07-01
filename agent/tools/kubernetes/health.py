"""Cluster health inspection tool."""

from typing import Protocol

from agent.tools.kubernetes.models import ClusterHealth, WorkloadHealth


class ClusterHealthInspector(Protocol):
    """Interface for Kubernetes health inspection implementations."""

    async def inspect(self, namespace: str | None = None) -> ClusterHealth:
        """Return health information for known workloads."""


class InMemoryClusterHealthInspector:
    """Deterministic inspector used until a real Kubernetes client is wired in."""

    def __init__(self, workloads: tuple[WorkloadHealth, ...] | None = None) -> None:
        self._workloads = workloads or default_workloads()

    async def inspect(self, namespace: str | None = None) -> ClusterHealth:
        """Return all fixture workloads or workloads from one namespace."""

        if namespace is None:
            return ClusterHealth(workloads=self._workloads)

        return ClusterHealth(
            workloads=tuple(
                workload for workload in self._workloads if workload.namespace == namespace
            ),
        )


def create_cluster_health_inspector() -> ClusterHealthInspector:
    """Create the default cluster health inspector."""

    return InMemoryClusterHealthInspector()


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
