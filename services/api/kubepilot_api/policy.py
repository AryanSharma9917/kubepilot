"""API access policy helpers."""


class NamespaceAccessPolicy:
    """Allowlist policy for namespace-scoped Kubernetes operations."""

    def __init__(self, allowed_namespaces: tuple[str, ...] = ()) -> None:
        self._allowed_namespaces = frozenset(allowed_namespaces)

    def ensure_allowed(self, namespace: str | None) -> None:
        """Raise PermissionError when a namespace is outside the allowlist."""

        if not self._allowed_namespaces or namespace is None:
            return
        if namespace not in self._allowed_namespaces:
            raise PermissionError(f"Namespace is not allowed: {namespace}")
