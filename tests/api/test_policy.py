import pytest
from kubepilot_api.policy import NamespaceAccessPolicy


def test_namespace_policy_allows_everything_without_allowlist() -> None:
    policy = NamespaceAccessPolicy()

    policy.ensure_allowed("payments")
    policy.ensure_allowed(None)


def test_namespace_policy_rejects_namespaces_outside_allowlist() -> None:
    policy = NamespaceAccessPolicy(("payments",))

    with pytest.raises(PermissionError, match="platform"):
        policy.ensure_allowed("platform")
