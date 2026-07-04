"""Intent classification for agent workflows."""

from dataclasses import dataclass
from typing import Literal

IntentName = Literal[
    "cluster_health",
    "deployment_diagnosis",
    "incident_report",
    "runbook_answer",
]


@dataclass(frozen=True)
class Intent:
    """Classified user intent."""

    name: IntentName
    confidence: float


def classify_intent(message: str) -> Intent:
    """Classify a user message into a workflow intent."""

    normalized = message.lower()
    if _cluster_health_intent(normalized):
        return Intent(name="cluster_health", confidence=0.95)
    if _incident_report_intent(normalized):
        return Intent(name="incident_report", confidence=0.9)
    if _deployment_diagnosis_intent(normalized):
        return Intent(name="deployment_diagnosis", confidence=0.85)
    return Intent(name="runbook_answer", confidence=0.7)


def _cluster_health_intent(normalized: str) -> bool:
    return (
        "unhealthy workload" in normalized
        or "cluster health" in normalized
        or "unhealthy pod" in normalized
    )


def _incident_report_intent(normalized: str) -> bool:
    return "incident report" in normalized or "incident summary" in normalized


def _deployment_diagnosis_intent(normalized: str) -> bool:
    if "deployment" not in normalized and "rollout" not in normalized:
        return False
    return any(
        term in normalized
        for term in ("fail", "failing", "diagnose", "why", "status", "incident")
    )
