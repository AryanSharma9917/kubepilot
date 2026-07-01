import pytest

from agent.tools.kubernetes import InMemoryClusterHealthInspector, WorkloadHealth


@pytest.mark.anyio
async def test_in_memory_inspector_returns_default_unhealthy_workloads() -> None:
    inspector = InMemoryClusterHealthInspector()

    health = await inspector.inspect()

    assert [workload.display_name for workload in health.unhealthy_workloads] == [
        "payments/deployment/checkout",
        "platform/deployment/metrics-scraper",
    ]


@pytest.mark.anyio
async def test_in_memory_inspector_filters_by_namespace() -> None:
    inspector = InMemoryClusterHealthInspector(
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
            WorkloadHealth(
                namespace="platform",
                name="metrics-scraper",
                kind="Deployment",
                desired_replicas=1,
                ready_replicas=0,
                status="Degraded",
                reason="Readiness probe is failing",
            ),
        ),
    )

    health = await inspector.inspect(namespace="payments")

    assert len(health.workloads) == 1
    assert health.workloads[0].display_name == "payments/deployment/checkout"
