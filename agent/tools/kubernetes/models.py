"""Kubernetes health models used by agent tools."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorkloadHealth:
    """Health summary for one Kubernetes workload."""

    namespace: str
    name: str
    kind: str
    desired_replicas: int
    ready_replicas: int
    status: str
    reason: str

    @property
    def is_healthy(self) -> bool:
        """Return whether the workload currently looks healthy."""

        return self.ready_replicas >= self.desired_replicas and self.status == "Healthy"

    @property
    def display_name(self) -> str:
        """Return a compact workload identifier."""

        return f"{self.namespace}/{self.kind.lower()}/{self.name}"


@dataclass(frozen=True)
class ClusterHealth:
    """Cluster health summary returned by Kubernetes tools."""

    workloads: tuple[WorkloadHealth, ...] = field(default_factory=tuple)

    @property
    def unhealthy_workloads(self) -> tuple[WorkloadHealth, ...]:
        """Return workloads that need operator attention."""

        return tuple(workload for workload in self.workloads if not workload.is_healthy)

    @property
    def is_healthy(self) -> bool:
        """Return whether all known workloads are healthy."""

        return not self.unhealthy_workloads
