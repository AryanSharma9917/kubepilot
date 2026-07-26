"""Incident report generation from diagnostic signals."""

from dataclasses import dataclass, field
from typing import Literal

from agent.tools.kubernetes import DeploymentDiagnosis

IncidentSeverity = Literal["info", "warning", "critical"]


@dataclass(frozen=True)
class EvidenceItem:
    """One signal supporting an incident report conclusion."""

    source: str
    message: str


@dataclass(frozen=True)
class IncidentReport:
    """Structured incident report returned by KubePilot."""

    title: str
    severity: IncidentSeverity
    summary: str
    probable_cause: str
    operator_impact: str
    impacted_resource: str
    evidence: tuple[EvidenceItem, ...] = field(default_factory=tuple)
    timeline: tuple[EvidenceItem, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    status_update: str = ""
    sources: tuple[str, ...] = field(default_factory=tuple)


def build_deployment_incident_report(
    diagnosis: DeploymentDiagnosis,
    *,
    sources: tuple[str, ...] = (),
) -> IncidentReport:
    """Build an incident report from a deployment diagnosis."""

    severity = _severity(diagnosis)
    unhealthy_pods = tuple(pod for pod in diagnosis.pods if not pod.ready)
    evidence = _evidence(diagnosis, unhealthy_pods)
    summary = _summary(diagnosis, unhealthy_pods)
    probable_cause = _probable_cause(diagnosis)
    operator_impact = _operator_impact(diagnosis, unhealthy_pods)

    return IncidentReport(
        title=f"Deployment incident: {diagnosis.display_name}",
        severity=severity,
        summary=summary,
        probable_cause=probable_cause,
        operator_impact=operator_impact,
        impacted_resource=diagnosis.display_name,
        evidence=evidence,
        timeline=_timeline(evidence),
        next_actions=diagnosis.recommendations,
        status_update=_status_update(
            diagnosis=diagnosis,
            severity=severity,
            probable_cause=probable_cause,
        ),
        sources=sources,
    )


def _severity(diagnosis: DeploymentDiagnosis) -> IncidentSeverity:
    if diagnosis.health.ready_replicas == 0 and diagnosis.health.desired_replicas > 0:
        return "critical"
    if not diagnosis.health.is_healthy:
        return "warning"
    return "info"


def _summary(
    diagnosis: DeploymentDiagnosis,
    unhealthy_pods: tuple[object, ...],
) -> str:
    unavailable = diagnosis.health.desired_replicas - diagnosis.health.ready_replicas
    if unavailable > 0:
        return (
            f"{diagnosis.display_name} has {diagnosis.health.ready_replicas}/"
            f"{diagnosis.health.desired_replicas} replicas ready and "
            f"{len(unhealthy_pods)} unhealthy pod(s)."
        )
    return f"{diagnosis.display_name} currently has all desired replicas ready."


def _probable_cause(diagnosis: DeploymentDiagnosis) -> str:
    pod_reasons = {
        pod.reason
        for pod in diagnosis.pods
        if pod.reason
    }
    event_reasons = {
        event.reason
        for event in diagnosis.events
        if event.reason
    }
    event_text = " ".join(event.message.lower() for event in diagnosis.events)
    log_text = " ".join(log.text.lower() for log in diagnosis.logs)

    if "ImagePullBackOff" in pod_reasons:
        return "Container image pull failure or registry authentication issue."
    if "CrashLoopBackOff" in pod_reasons:
        return "Application process crash after startup."
    if "Unschedulable" in pod_reasons or "FailedScheduling" in event_reasons:
        if "insufficient cpu" in event_text or "insufficient memory" in event_text:
            return "Insufficient cluster capacity for the requested pod resources."
        return "Scheduling constraints prevented Kubernetes from placing the pod."
    if "ReadinessProbeFailed" in pod_reasons or "Unhealthy" in event_reasons:
        return "Application readiness endpoint is not passing Kubernetes health checks."
    if "missing" in log_text and "environment variable" in log_text:
        return "Missing runtime configuration required by the container."
    if diagnosis.health.is_healthy:
        return "No active incident cause detected."
    return diagnosis.health.reason


def _operator_impact(
    diagnosis: DeploymentDiagnosis,
    unhealthy_pods: tuple[object, ...],
) -> str:
    unavailable = diagnosis.health.desired_replicas - diagnosis.health.ready_replicas
    if diagnosis.health.is_healthy:
        return "No current operator impact."
    if diagnosis.health.ready_replicas == 0:
        return (
            f"{diagnosis.display_name} has no ready replicas; requests may fail "
            "or queue until capacity is restored."
        )
    return (
        f"{diagnosis.display_name} is partially available with {unavailable} "
        f"replica(s) unavailable and {len(unhealthy_pods)} unhealthy pod(s)."
    )


def _evidence(
    diagnosis: DeploymentDiagnosis,
    unhealthy_pods: tuple[object, ...],
) -> tuple[EvidenceItem, ...]:
    evidence: list[EvidenceItem] = [
        EvidenceItem(
            source="deployment",
            message=(
                f"{diagnosis.health.ready_replicas}/"
                f"{diagnosis.health.desired_replicas} replicas ready: "
                f"{diagnosis.health.reason}"
            ),
        )
    ]

    evidence.extend(
        EvidenceItem(
            source="pod",
            message=(
                f"{pod.name} is {pod.phase}"
                + (f" because {pod.reason}" if pod.reason else "")
            ),
        )
        for pod in unhealthy_pods
    )
    evidence.extend(
        EvidenceItem(
            source="event",
            message=f"{event.reason}: {event.message}",
        )
        for event in diagnosis.events
        if event.event_type == "Warning"
    )
    evidence.extend(
        EvidenceItem(
            source="log",
            message=(
                f"{log.pod_name}/{log.container_name}"
                f"{' previous' if log.previous else ''} log: {log.text}"
            ),
        )
        for log in diagnosis.logs[:3]
    )
    return tuple(evidence)


def _timeline(evidence: tuple[EvidenceItem, ...]) -> tuple[EvidenceItem, ...]:
    ordered_sources = ("deployment", "pod", "event", "log")
    return tuple(
        item
        for source in ordered_sources
        for item in evidence
        if item.source == source
    )


def _status_update(
    *,
    diagnosis: DeploymentDiagnosis,
    severity: IncidentSeverity,
    probable_cause: str,
) -> str:
    return (
        f"{severity.upper()}: {diagnosis.display_name} is {diagnosis.health.status}. "
        f"{diagnosis.health.ready_replicas}/{diagnosis.health.desired_replicas} "
        f"replicas are ready. Probable cause: {probable_cause}"
    )
