import pytest

from agent.tools.kubernetes import KubernetesServiceClient


def fake_fetch_json(url: str) -> dict[str, object] | None:
    if url.endswith("/api/v1/cluster/health?namespace=payments"):
        return {
            "workloads": [
                {
                    "namespace": "payments",
                    "name": "checkout",
                    "kind": "Deployment",
                    "desired_replicas": 3,
                    "ready_replicas": 1,
                    "status": "Degraded",
                    "reason": "Two replicas are unavailable",
                }
            ]
        }
    if url.endswith("/api/v1/namespaces/payments/deployments/checkout"):
        return {
            "namespace": "payments",
            "name": "checkout",
            "health": {
                "namespace": "payments",
                "name": "checkout",
                "kind": "Deployment",
                "desired_replicas": 3,
                "ready_replicas": 1,
                "status": "Degraded",
                "reason": "Two replicas are unavailable",
            },
            "pods": [
                {
                    "namespace": "payments",
                    "name": "checkout-abc",
                    "phase": "Running",
                    "ready": False,
                    "restart_count": 5,
                    "reason": "CrashLoopBackOff",
                }
            ],
            "events": [
                {
                    "namespace": "payments",
                    "involved_object": "checkout-abc",
                    "reason": "BackOff",
                    "message": "Back-off restarting failed container",
                    "event_type": "Warning",
                }
            ],
            "logs": [
                {
                    "namespace": "payments",
                    "pod_name": "checkout-abc",
                    "container_name": "checkout",
                    "text": "panic: missing PAYMENT_GATEWAY_URL",
                    "previous": True,
                }
            ],
        }
    return None


@pytest.mark.anyio
async def test_service_client_maps_cluster_health_payload() -> None:
    client = KubernetesServiceClient(
        "http://k8s-tool:8081",
        fetch_json=fake_fetch_json,
    )

    deployments = await client.list_deployments(namespace="payments")

    assert len(deployments) == 1
    assert deployments[0].display_name == "payments/deployment/checkout"


@pytest.mark.anyio
async def test_service_client_maps_diagnosis_payload() -> None:
    client = KubernetesServiceClient(
        "http://k8s-tool:8081",
        fetch_json=fake_fetch_json,
    )

    deployment = await client.get_deployment(namespace="payments", name="checkout")
    pods = await client.list_pods_for_deployment(namespace="payments", name="checkout")
    events = await client.list_events_for_deployment(namespace="payments", name="checkout")
    logs = await client.list_logs_for_deployment(namespace="payments", name="checkout")

    assert deployment is not None
    assert deployment.status == "Degraded"
    assert pods[0].reason == "CrashLoopBackOff"
    assert events[0].event_type == "Warning"
    assert logs[0].previous is True
