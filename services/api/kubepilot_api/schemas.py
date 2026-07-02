"""API response models."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ServiceInfo(BaseModel):
    """Public information about the running service."""

    name: str
    version: str
    environment: str


class HealthResponse(BaseModel):
    """Health probe response."""

    status: Literal["ok", "ready"]


class ChatRequest(BaseModel):
    """A user message submitted to KubePilot."""

    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: object) -> object:
        """Trim surrounding whitespace before validating message length."""

        return value.strip() if isinstance(value, str) else value


class ChatResponse(BaseModel):
    """KubePilot's response to a chat request."""

    request_id: UUID
    answer: str
    sources: list[str] = Field(default_factory=list)


class WorkloadHealthResponse(BaseModel):
    """Health response for one Kubernetes workload."""

    namespace: str
    name: str
    kind: str
    desired_replicas: int
    ready_replicas: int
    status: str
    reason: str


class ClusterHealthResponse(BaseModel):
    """Cluster health response returned by the API."""

    status: Literal["healthy", "degraded"]
    unhealthy_count: int
    workloads: list[WorkloadHealthResponse] = Field(default_factory=list)


class PodStatusResponse(BaseModel):
    """Status response for one pod."""

    namespace: str
    name: str
    phase: str
    ready: bool
    restart_count: int
    reason: str | None = None


class KubernetesEventResponse(BaseModel):
    """Kubernetes event returned by diagnosis APIs."""

    namespace: str
    involved_object: str
    reason: str
    message: str
    event_type: str


class DeploymentDiagnosisResponse(BaseModel):
    """Deployment diagnosis response returned by the API."""

    namespace: str
    name: str
    health: WorkloadHealthResponse
    pods: list[PodStatusResponse] = Field(default_factory=list)
    events: list[KubernetesEventResponse] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
