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
    impacted_resource: str
    evidence: tuple[EvidenceItem, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
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

    return IncidentReport(
        title=f"Deployment incident: {diagnosis.display_name}",
        severity=severity,
        summary=summary,
        impacted_resource=diagnosis.display_name,
        evidence=evidence,
        next_actions=diagnosis.recommendations,
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
    return tuple(evidence)
