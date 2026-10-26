"""Namespace boundaries shared by API and chat Kubernetes tools."""

from typing import TYPE_CHECKING

from agent.tools.kubernetes.models import ContainerLog, KubernetesEvent, PodStatus, WorkloadHealth

if TYPE_CHECKING:
    from agent.tools.kubernetes.client import KubernetesClient


class NamespaceScopedClient:
    """Reject out-of-scope reads before invoking the underlying client."""

    def __init__(self, client: "KubernetesClient", namespaces: tuple[str, ...]) -> None:
        self._client = client
        self._namespaces = namespaces

    def _ensure_allowed(self, namespace: str) -> None:
        if namespace not in self._namespaces:
            raise PermissionError(f"Namespace is not allowed: {namespace}")

    async def list_deployments(
        self, namespace: str | None = None
    ) -> tuple[WorkloadHealth, ...]:
        if namespace is not None:
            self._ensure_allowed(namespace)
            return tuple(
                item for item in await self._client.list_deployments(namespace=namespace)
                if item.namespace == namespace
            )
        results = []
        for allowed in self._namespaces:
            results.extend(await self.list_deployments(namespace=allowed))
        return tuple(results)

    async def get_deployment(self, namespace: str, name: str) -> WorkloadHealth | None:
        self._ensure_allowed(namespace)
        item = await self._client.get_deployment(namespace=namespace, name=name)
        return item if item is not None and item.namespace == namespace else None

    async def list_pods_for_deployment(
        self, namespace: str, name: str
    ) -> tuple[PodStatus, ...]:
        self._ensure_allowed(namespace)
        return tuple(
            item for item in await self._client.list_pods_for_deployment(
                namespace=namespace, name=name
            )
            if item.namespace == namespace
        )

    async def list_events_for_deployment(
        self, namespace: str, name: str
    ) -> tuple[KubernetesEvent, ...]:
        self._ensure_allowed(namespace)
        return tuple(
            item for item in await self._client.list_events_for_deployment(
                namespace=namespace, name=name
            )
            if item.namespace == namespace
        )

    async def list_logs_for_deployment(
        self, namespace: str, name: str
    ) -> tuple[ContainerLog, ...]:
        self._ensure_allowed(namespace)
        return tuple(
            item for item in await self._client.list_logs_for_deployment(
                namespace=namespace, name=name
            )
            if item.namespace == namespace
        )
