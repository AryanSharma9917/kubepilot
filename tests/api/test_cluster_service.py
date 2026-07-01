import pytest
from kubepilot_api.services.cluster import ClusterService

from agent.tools.kubernetes import ClusterHealth, WorkloadHealth


class FakeInspector:
    async def inspect(self, namespace: str | None = None) -> ClusterHealth:
        assert namespace == "payments"
        return ClusterHealth(
            workloads=(
                WorkloadHealth(
                    namespace="payments",
                    name="checkout",
                    kind="Deployment",
                    desired_replicas=3,
                    ready_replicas=1,
                    status="Degraded",
                    reason="Two replicas are unavailable",
                ),
            ),
        )


@pytest.mark.anyio
async def test_cluster_service_uses_inspector() -> None:
    service = ClusterService(inspector=FakeInspector())

    response = await service.health(namespace="payments")

    assert response.status == "degraded"
    assert response.unhealthy_count == 1
    assert response.workloads[0].name == "checkout"
