"""Local-cluster smoke-test helpers for the API service."""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True, slots=True)
class LocalClusterValidationResult:
    """Summary of the local-cluster validation run."""

    readyz_status: str
    healthz_status: str
    cluster_status: str
    unhealthy_count: int


def validate_local_cluster_client(
    client: httpx.Client,
    *,
    timeout_seconds: float = 120.0,
    poll_interval_seconds: float = 1.0,
) -> LocalClusterValidationResult:
    """Wait for the API to become ready and validate the main service endpoints."""

    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None

    while True:
        try:
            healthz_response = client.get("/healthz")
            healthz_response.raise_for_status()
            healthz_payload = healthz_response.json()

            readyz_response = client.get("/readyz")
            readyz_response.raise_for_status()
            readyz_payload = readyz_response.json()
            if readyz_payload.get("status") != "ready":
                raise RuntimeError(f"/readyz returned unexpected payload: {readyz_payload!r}")

            metrics_response = client.get("/metrics")
            metrics_response.raise_for_status()
            if "kubepilot_http_requests_total" not in metrics_response.text:
                raise RuntimeError("Metrics endpoint did not expose request counters.")

            chat_response = client.post(
                "/api/v1/chat",
                json={"message": "Show unhealthy workloads"},
            )
            chat_response.raise_for_status()
            chat_payload = chat_response.json()
            if "payments/deployment/checkout" not in chat_payload.get("answer", ""):
                raise RuntimeError("Chat endpoint did not return the expected workload context.")

            diagnosis_response = client.get(
                "/api/v1/cluster/namespaces/payments/deployments/checkout/diagnose"
            )
            diagnosis_response.raise_for_status()
            diagnosis_payload = diagnosis_response.json()
            if diagnosis_payload.get("name") != "checkout":
                raise RuntimeError("Deployment diagnosis did not return the expected deployment.")

            incident_response = client.get(
                "/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report"
            )
            incident_response.raise_for_status()
            incident_payload = incident_response.json()
            if not incident_payload.get("title", "").startswith("Deployment incident: "):
                raise RuntimeError("Incident report did not return the expected summary.")

            cluster_response = client.get("/api/v1/cluster/health")
            cluster_response.raise_for_status()
            cluster_payload = cluster_response.json()
            if "status" not in cluster_payload or "unhealthy_count" not in cluster_payload:
                raise RuntimeError(
                    "Cluster health payload is missing required status fields."
                )

            return LocalClusterValidationResult(
                healthz_status=str(healthz_payload.get("status", "")),
                readyz_status=str(readyz_payload.get("status", "")),
                cluster_status=str(cluster_payload["status"]),
                unhealthy_count=int(cluster_payload["unhealthy_count"]),
            )
        except Exception as exc:  # pragma: no cover - exercised through retry loop
            last_error = str(exc)

        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"KubePilot did not become ready within {timeout_seconds:.0f} seconds: {last_error}"
            ) from None
        time.sleep(poll_interval_seconds)


def main() -> None:
    """Run the local-cluster smoke-test validation."""

    parser = argparse.ArgumentParser(description="Validate a running KubePilot API instance.")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:18000",
        help="Base URL for the running API service.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Maximum time to wait for the service to become ready.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Delay between readiness checks in seconds.",
    )
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url, timeout=10.0) as client:
        result = validate_local_cluster_client(
            client,
            timeout_seconds=args.timeout,
            poll_interval_seconds=args.poll_interval,
        )

    print(
        "KubePilot local cluster validation passed: "
        f"healthz={result.healthz_status}, "
        f"readyz={result.readyz_status}, "
        f"cluster={result.cluster_status}, "
        f"unhealthy_count={result.unhealthy_count}"
    )


if __name__ == "__main__":
    main()