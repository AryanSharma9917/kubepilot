import pytest

from agent.tools.kubernetes.scope import NamespaceScopedClient


@pytest.mark.anyio
async def test_rejected_namespace_never_reaches_any_underlying_client_method():
    class NoAccessClient:
        def __getattr__(self, name):
            raise AssertionError(f"Rejected request reached underlying client: {name}")

    client = NamespaceScopedClient(NoAccessClient(), ("payments",))
    for operation in [
        client.list_deployments(namespace="platform"),
        client.get_deployment(namespace="platform", name="secret"),
        client.list_pods_for_deployment(namespace="platform", name="secret"),
        client.list_events_for_deployment(namespace="platform", name="secret"),
        client.list_logs_for_deployment(namespace="platform", name="secret"),
    ]:
        with pytest.raises(PermissionError):
            await operation
