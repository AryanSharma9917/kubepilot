from agent.tools.kubernetes import ClusterHealth, WorkloadHealth


def test_cluster_health_filters_unhealthy_workloads() -> None:
    healthy = WorkloadHealth(
        namespace="default",
        name="api",
        kind="Deployment",
        desired_replicas=2,
        ready_replicas=2,
        status="Healthy",
        reason="All replicas are ready",
    )
    unhealthy = WorkloadHealth(
        namespace="payments",
        name="checkout",
        kind="Deployment",
        desired_replicas=3,
        ready_replicas=1,
        status="Degraded",
        reason="Two replicas are unavailable",
    )

    health = ClusterHealth(workloads=(healthy, unhealthy))

    assert health.is_healthy is False
    assert health.unhealthy_workloads == (unhealthy,)
    assert unhealthy.display_name == "payments/deployment/checkout"
