"""API access policy helpers."""


class NamespaceAccessPolicy:
    """Allowlist policy for namespace-scoped Kubernetes operations."""

    def __init__(
        self,
        allowed_namespaces: tuple[str, ...] = (),
        allowed_actions: tuple[str, ...] = (),
    ) -> None:
        self._allowed_namespaces = frozenset(allowed_namespaces)
        self._allowed_actions = frozenset(allowed_actions)

    def ensure_allowed(self, namespace: str | None) -> None:
        """Raise PermissionError when a namespace is outside the allowlist."""

        if not self._allowed_namespaces or namespace is None:
            return
        if namespace not in self._allowed_namespaces:
            raise PermissionError(f"Namespace is not allowed: {namespace}")

    def ensure_action_allowed(self, action: str) -> None:
        """Raise PermissionError when an action is outside the allowlist."""

        if not self._allowed_actions:
            return
        if action not in self._allowed_actions:
            raise PermissionError(f"Action is not allowed: {action}")

    def ensure_operation_allowed(self, *, namespace: str | None, action: str) -> None:
        """Raise PermissionError when namespace or action policy rejects an operation."""

        self.ensure_allowed(namespace)
        self.ensure_action_allowed(action)
