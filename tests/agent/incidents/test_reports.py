from agent.incidents import build_deployment_incident_report
from agent.tools.kubernetes import (
    DeploymentDiagnosis,
    KubernetesEvent,
    PodStatus,
    WorkloadHealth,
)


def test_build_deployment_incident_report_marks_zero_ready_as_critical() -> None:
    diagnosis = DeploymentDiagnosis(
        namespace="payments",
        name="checkout",
        health=WorkloadHealth(
            namespace="payments",
            name="checkout",
            kind="Deployment",
            desired_replicas=3,
            ready_replicas=0,
            status="Degraded",
            reason="Image pull is failing",
        ),
        pods=(
            PodStatus(
                namespace="payments",
                name="checkout-abc",
                phase="Pending",
                ready=False,
                restart_count=0,
                reason="ImagePullBackOff",
            ),
        ),
        events=(
            KubernetesEvent(
                namespace="payments",
                involved_object="pod/checkout-abc",
                reason="Failed",
                message="Failed to pull image",
                event_type="Warning",
            ),
        ),
        recommendations=("Verify image tag and registry credentials.",),
    )

    report = build_deployment_incident_report(
        diagnosis,
        sources=("Deployment rollout failures",),
    )

    assert report.severity == "critical"
    assert report.impacted_resource == "payments/deployment/checkout"
    assert "0/3 replicas ready" in report.summary
    assert report.next_actions == ("Verify image tag and registry credentials.",)
    assert report.sources == ("Deployment rollout failures",)
    assert [item.source for item in report.evidence] == ["deployment", "pod", "event"]


def test_build_deployment_incident_report_marks_healthy_deployment_as_info() -> None:
    diagnosis = DeploymentDiagnosis(
        namespace="default",
        name="kubepilot-api",
        health=WorkloadHealth(
            namespace="default",
            name="kubepilot-api",
            kind="Deployment",
            desired_replicas=2,
            ready_replicas=2,
            status="Healthy",
            reason="All replicas are ready",
        ),
    )

    report = build_deployment_incident_report(diagnosis)

    assert report.severity == "info"
    assert report.summary == (
        "default/deployment/kubepilot-api currently has all desired replicas ready."
    )
