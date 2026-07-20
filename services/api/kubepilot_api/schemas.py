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


class RuntimeStatusResponse(BaseModel):
    """Redacted runtime status for operators."""

    environment: str
    kubernetes_mode: str
    rag_mode: str
    llm_provider: str
    agent_mode: str
    auth_enabled: bool
    namespace_policy_enabled: bool
    action_policy_enabled: bool
    rate_limit_per_minute: int
    otel_export_enabled: bool


class ChatRequest(BaseModel):
    """A user message submitted to KubePilot."""

    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: object) -> object:
        """Trim surrounding whitespace before validating message length."""

        return value.strip() if isinstance(value, str) else value


class CitationResponse(BaseModel):
    """Citation supporting an answer."""

    title: str
    source: str
    snippet: str


class ChatResponse(BaseModel):
    """KubePilot's response to a chat request."""

    request_id: UUID
    answer: str
    sources: list[str] = Field(default_factory=list)
    citations: list[CitationResponse] = Field(default_factory=list)


class KnowledgeSearchRequest(BaseModel):
    """Knowledge search query submitted to KubePilot."""

    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=3, ge=1, le=10)

    @field_validator("query", mode="before")
    @classmethod
    def normalize_query(cls, value: object) -> object:
        """Trim surrounding whitespace before validating query length."""

        return value.strip() if isinstance(value, str) else value


class KnowledgeSearchResult(BaseModel):
    """One retrieved knowledge result."""

    title: str
    source: str
    snippet: str
    score: float


class KnowledgeSearchResponse(BaseModel):
    """Knowledge search response."""

    results: list[KnowledgeSearchResult] = Field(default_factory=list)


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


class ContainerLogResponse(BaseModel):
    """Container log excerpt returned by diagnosis APIs."""

    namespace: str
    pod_name: str
    container_name: str
    text: str
    previous: bool = False


class DeploymentDiagnosisResponse(BaseModel):
    """Deployment diagnosis response returned by the API."""

    namespace: str
    name: str
    health: WorkloadHealthResponse
    pods: list[PodStatusResponse] = Field(default_factory=list)
    events: list[KubernetesEventResponse] = Field(default_factory=list)
    logs: list[ContainerLogResponse] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class EvidenceItemResponse(BaseModel):
    """One evidence item in an incident report."""

    source: str
    message: str


class IncidentReportResponse(BaseModel):
    """Structured incident report returned by the API."""

    title: str
    severity: Literal["info", "warning", "critical"]
    summary: str
    impacted_resource: str
    evidence: list[EvidenceItemResponse] = Field(default_factory=list)
    timeline: list[EvidenceItemResponse] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class AuditEventResponse(BaseModel):
    """One audit event returned by the API."""

    timestamp: float
    request_id: str
    method: str
    path: str
    status_code: int


class AuditEventsResponse(BaseModel):
    """Recent API audit events."""

    events: list[AuditEventResponse] = Field(default_factory=list)


class TraceSpanResponse(BaseModel):
    """One local trace span returned by the API."""

    trace_id: str
    name: str
    started_at: float
    duration_ms: float
    attributes: dict[str, str] = Field(default_factory=dict)


class TraceSpansResponse(BaseModel):
    """Recent local trace spans."""

    spans: list[TraceSpanResponse] = Field(default_factory=list)
