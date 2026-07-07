"""Kubernetes client boundary used by operational tools."""

import asyncio
import json
from collections.abc import Callable
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from agent.tools.kubernetes.models import (
    ContainerLog,
    KubernetesEvent,
    PodStatus,
    WorkloadHealth,
)


class KubernetesClient(Protocol):
    """Minimal Kubernetes operations needed by KubePilot tools."""

    async def list_deployments(self, namespace: str | None = None) -> tuple[WorkloadHealth, ...]:
        """Return deployment health summaries."""

    async def get_deployment(self, namespace: str, name: str) -> WorkloadHealth | None:
        """Return one deployment health summary."""

    async def list_pods_for_deployment(self, namespace: str, name: str) -> tuple[PodStatus, ...]:
        """Return pods that belong to a deployment."""

    async def list_events_for_deployment(
        self,
        namespace: str,
        name: str,
    ) -> tuple[KubernetesEvent, ...]:
        """Return events relevant to a deployment."""

    async def list_logs_for_deployment(
        self,
        namespace: str,
        name: str,
        *,
        tail_lines: int = 50,
    ) -> tuple[ContainerLog, ...]:
        """Return recent logs for pods related to a deployment."""


class InMemoryKubernetesClient:
    """Deterministic Kubernetes client used for local development and tests."""

    def __init__(
        self,
        deployments: tuple[WorkloadHealth, ...],
        pods: dict[tuple[str, str], tuple[PodStatus, ...]] | None = None,
        events: dict[tuple[str, str], tuple[KubernetesEvent, ...]] | None = None,
        logs: dict[tuple[str, str], tuple[ContainerLog, ...]] | None = None,
    ) -> None:
        self._deployments = deployments
        self._pods = pods or {}
        self._events = events or {}
        self._logs = logs or {}

    async def list_deployments(self, namespace: str | None = None) -> tuple[WorkloadHealth, ...]:
        """Return all fixture deployments or deployments from one namespace."""

        if namespace is None:
            return self._deployments

        return tuple(
            deployment
            for deployment in self._deployments
            if deployment.namespace == namespace
        )

    async def get_deployment(self, namespace: str, name: str) -> WorkloadHealth | None:
        """Return one fixture deployment if it exists."""

        for deployment in self._deployments:
            if deployment.namespace == namespace and deployment.name == name:
                return deployment
        return None

    async def list_pods_for_deployment(self, namespace: str, name: str) -> tuple[PodStatus, ...]:
        """Return fixture pods for a deployment."""

        return self._pods.get((namespace, name), ())

    async def list_events_for_deployment(
        self,
        namespace: str,
        name: str,
    ) -> tuple[KubernetesEvent, ...]:
        """Return fixture events for a deployment."""

        return self._events.get((namespace, name), ())

    async def list_logs_for_deployment(
        self,
        namespace: str,
        name: str,
        *,
        tail_lines: int = 50,
    ) -> tuple[ContainerLog, ...]:
        """Return fixture logs for a deployment."""

        return self._logs.get((namespace, name), ())


class KubernetesPythonClient:
    """Adapter around the official Kubernetes Python client.

    The dependency is imported lazily so fixture mode works without installing
    Kubernetes client libraries.
    """

    def __init__(self, *, mode: str = "kubeconfig", kubeconfig_path: str | None = None) -> None:
        try:
            from kubernetes import client, config
        except ImportError as exc:
            raise RuntimeError(
                "KUBEPILOT_K8S_MODE requires the optional 'kubernetes' package."
            ) from exc

        if mode == "in_cluster":
            config.load_incluster_config()
        else:
            config.load_kube_config(config_file=kubeconfig_path)

        self._apps = client.AppsV1Api()
        self._core = client.CoreV1Api()

    async def list_deployments(self, namespace: str | None = None) -> tuple[WorkloadHealth, ...]:
        """Return deployment health from the configured cluster."""

        if namespace is None:
            response = self._apps.list_deployment_for_all_namespaces()
        else:
            response = self._apps.list_namespaced_deployment(namespace=namespace)

        return tuple(_deployment_to_health(item) for item in response.items)

    async def get_deployment(self, namespace: str, name: str) -> WorkloadHealth | None:
        """Return one deployment from the configured cluster."""

        try:
            deployment = self._apps.read_namespaced_deployment(name=name, namespace=namespace)
        except Exception:
            return None
        return _deployment_to_health(deployment)

    async def list_pods_for_deployment(self, namespace: str, name: str) -> tuple[PodStatus, ...]:
        """Return pods matching the deployment selector."""

        deployment = self._apps.read_namespaced_deployment(name=name, namespace=namespace)
        selector = deployment.spec.selector.match_labels or {}
        label_selector = ",".join(f"{key}={value}" for key, value in selector.items())
        response = self._core.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector,
        )
        return tuple(_pod_to_status(item) for item in response.items)

    async def list_events_for_deployment(
        self,
        namespace: str,
        name: str,
    ) -> tuple[KubernetesEvent, ...]:
        """Return warning and normal events mentioning the deployment name."""

        response = self._core.list_namespaced_event(namespace=namespace)
        events: list[KubernetesEvent] = []
        for item in response.items:
            involved = getattr(item.involved_object, "name", "")
            if name in involved:
                events.append(
                    KubernetesEvent(
                        namespace=namespace,
                        involved_object=involved,
                        reason=item.reason or "Unknown",
                        message=item.message or "",
                        event_type=item.type or "Normal",
                    )
                )
        return tuple(events)

    async def list_logs_for_deployment(
        self,
        namespace: str,
        name: str,
        *,
        tail_lines: int = 50,
    ) -> tuple[ContainerLog, ...]:
        """Return recent and previous logs for pods matching the deployment selector."""

        pods = await self.list_pods_for_deployment(namespace=namespace, name=name)
        logs: list[ContainerLog] = []
        for pod in pods:
            try:
                text = self._core.read_namespaced_pod_log(
                    name=pod.name,
                    namespace=namespace,
                    tail_lines=tail_lines,
                )
            except Exception:
                text = ""
            if text:
                logs.append(
                    ContainerLog(
                        namespace=namespace,
                        pod_name=pod.name,
                        container_name="default",
                        text=text,
                    )
                )
            if pod.restart_count > 0:
                try:
                    previous_text = self._core.read_namespaced_pod_log(
                        name=pod.name,
                        namespace=namespace,
                        previous=True,
                        tail_lines=tail_lines,
                    )
                except Exception:
                    previous_text = ""
                if previous_text:
                    logs.append(
                        ContainerLog(
                            namespace=namespace,
                            pod_name=pod.name,
                            container_name="default",
                            text=previous_text,
                            previous=True,
                        )
                    )
        return tuple(logs)


class KubernetesServiceClient:
    """HTTP client for the Go-based Kubernetes tool service."""

    def __init__(
        self,
        base_url: str,
        *,
        fetch_json: Callable[[str], dict[str, Any] | None] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._fetch_json = fetch_json or _fetch_json
        self._fetch_in_thread = fetch_json is None

    async def list_deployments(self, namespace: str | None = None) -> tuple[WorkloadHealth, ...]:
        """Return deployment health from the k8s-tool service."""

        query = f"?{urlencode({'namespace': namespace})}" if namespace else ""
        payload = await self._get(f"/api/v1/cluster/health{query}")
        if payload is None:
            return ()
        return tuple(
            _workload_from_payload(item)
            for item in payload.get("workloads", [])
        )

    async def get_deployment(self, namespace: str, name: str) -> WorkloadHealth | None:
        """Return one deployment health summary from the k8s-tool service."""

        payload = await self._deployment_payload(namespace=namespace, name=name)
        if payload is None:
            return None
        return _workload_from_payload(payload["health"])

    async def list_pods_for_deployment(self, namespace: str, name: str) -> tuple[PodStatus, ...]:
        """Return pod status from the k8s-tool service."""

        payload = await self._deployment_payload(namespace=namespace, name=name)
        if payload is None:
            return ()
        return tuple(_pod_from_payload(item) for item in payload.get("pods", []))

    async def list_events_for_deployment(
        self,
        namespace: str,
        name: str,
    ) -> tuple[KubernetesEvent, ...]:
        """Return deployment events from the k8s-tool service."""

        payload = await self._deployment_payload(namespace=namespace, name=name)
        if payload is None:
            return ()
        return tuple(_event_from_payload(item) for item in payload.get("events", []))

    async def list_logs_for_deployment(
        self,
        namespace: str,
        name: str,
        *,
        tail_lines: int = 50,
    ) -> tuple[ContainerLog, ...]:
        """Return deployment logs from the k8s-tool service."""

        payload = await self._deployment_payload(namespace=namespace, name=name)
        if payload is None:
            return ()
        return tuple(_log_from_payload(item) for item in payload.get("logs", []))

    async def _deployment_payload(self, namespace: str, name: str) -> dict[str, Any] | None:
        return await self._get(f"/api/v1/namespaces/{namespace}/deployments/{name}")

    async def _get(self, path: str) -> dict[str, Any] | None:
        url = f"{self._base_url}{path}"
        if self._fetch_in_thread:
            return await asyncio.to_thread(self._fetch_json, url)
        return self._fetch_json(url)


def create_kubernetes_client(
    *,
    mode: str = "fixture",
    kubeconfig_path: str | None = None,
    service_url: str = "http://k8s-tool:8081",
) -> KubernetesClient:
    """Create a Kubernetes client for the requested runtime mode."""

    if mode == "fixture":
        return create_fixture_kubernetes_client()
    if mode == "service":
        return KubernetesServiceClient(service_url)
    if mode in {"kubeconfig", "in_cluster"}:
        return KubernetesPythonClient(mode=mode, kubeconfig_path=kubeconfig_path)
    raise ValueError(f"Unsupported Kubernetes mode: {mode}")


def create_fixture_kubernetes_client() -> KubernetesClient:
    """Create the deterministic local Kubernetes fixture."""

    checkout = WorkloadHealth(
        namespace="payments",
        name="checkout",
        kind="Deployment",
        desired_replicas=3,
        ready_replicas=1,
        status="Degraded",
        reason="Two replicas are unavailable",
    )
    metrics = WorkloadHealth(
        namespace="platform",
        name="metrics-scraper",
        kind="Deployment",
        desired_replicas=1,
        ready_replicas=0,
        status="Degraded",
        reason="Readiness probe is failing",
    )
    return InMemoryKubernetesClient(
        deployments=(
            WorkloadHealth(
                namespace="default",
                name="kubepilot-api",
                kind="Deployment",
                desired_replicas=2,
                ready_replicas=2,
                status="Healthy",
                reason="All replicas are ready",
            ),
            checkout,
            metrics,
        ),
        pods={
            ("payments", "checkout"): (
                PodStatus(
                    namespace="payments",
                    name="checkout-7d8f5b9c6c-abc12",
                    phase="Running",
                    ready=False,
                    restart_count=5,
                    reason="CrashLoopBackOff",
                ),
                PodStatus(
                    namespace="payments",
                    name="checkout-7d8f5b9c6c-def34",
                    phase="Pending",
                    ready=False,
                    restart_count=0,
                    reason="ImagePullBackOff",
                ),
            )
        },
        events={
            ("payments", "checkout"): (
                KubernetesEvent(
                    namespace="payments",
                    involved_object="checkout-7d8f5b9c6c-def34",
                    reason="Failed",
                    message="Failed to pull image registry.example.com/checkout:bad-tag",
                    event_type="Warning",
                ),
            )
        },
        logs={
            ("payments", "checkout"): (
                ContainerLog(
                    namespace="payments",
                    pod_name="checkout-7d8f5b9c6c-abc12",
                    container_name="checkout",
                    text="panic: missing PAYMENT_GATEWAY_URL environment variable",
                    previous=True,
                ),
            )
        },
    )


def _deployment_to_health(deployment: Any) -> WorkloadHealth:
    namespace = deployment.metadata.namespace
    name = deployment.metadata.name
    desired = deployment.spec.replicas or 0
    ready = deployment.status.ready_replicas or 0
    unavailable = deployment.status.unavailable_replicas or 0
    status = "Healthy" if ready >= desired and unavailable == 0 else "Degraded"
    reason = (
        "All replicas are ready"
        if status == "Healthy"
        else f"{unavailable} replicas unavailable"
    )
    return WorkloadHealth(
        namespace=namespace,
        name=name,
        kind="Deployment",
        desired_replicas=desired,
        ready_replicas=ready,
        status=status,
        reason=reason,
    )


def _pod_to_status(pod: Any) -> PodStatus:
    container_statuses = pod.status.container_statuses or []
    restart_count = sum(status.restart_count or 0 for status in container_statuses)
    ready = bool(container_statuses) and all(status.ready for status in container_statuses)
    reason = pod.status.reason
    waiting_reasons = [
        status.state.waiting.reason
        for status in container_statuses
        if status.state and status.state.waiting and status.state.waiting.reason
    ]
    if waiting_reasons:
        reason = ", ".join(waiting_reasons)
    return PodStatus(
        namespace=pod.metadata.namespace,
        name=pod.metadata.name,
        phase=pod.status.phase or "Unknown",
        ready=ready,
        restart_count=restart_count,
        reason=reason,
    )


def _fetch_json(url: str) -> dict[str, Any] | None:
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=5.0) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def _workload_from_payload(payload: dict[str, Any]) -> WorkloadHealth:
    return WorkloadHealth(
        namespace=str(payload["namespace"]),
        name=str(payload["name"]),
        kind=str(payload["kind"]),
        desired_replicas=int(payload["desired_replicas"]),
        ready_replicas=int(payload["ready_replicas"]),
        status=str(payload["status"]),
        reason=str(payload["reason"]),
    )


def _pod_from_payload(payload: dict[str, Any]) -> PodStatus:
    return PodStatus(
        namespace=str(payload["namespace"]),
        name=str(payload["name"]),
        phase=str(payload["phase"]),
        ready=bool(payload["ready"]),
        restart_count=int(payload["restart_count"]),
        reason=payload.get("reason"),
    )


def _event_from_payload(payload: dict[str, Any]) -> KubernetesEvent:
    return KubernetesEvent(
        namespace=str(payload["namespace"]),
        involved_object=str(payload["involved_object"]),
        reason=str(payload["reason"]),
        message=str(payload["message"]),
        event_type=str(payload.get("event_type", "Normal")),
    )


def _log_from_payload(payload: dict[str, Any]) -> ContainerLog:
    return ContainerLog(
        namespace=str(payload["namespace"]),
        pod_name=str(payload["pod_name"]),
        container_name=str(payload["container_name"]),
        text=str(payload["text"]),
        previous=bool(payload.get("previous", False)),
    )
