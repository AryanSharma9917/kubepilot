# Readiness Probe Failures

Use this runbook when pods are running but the deployment does not receive ready
replicas.

## Signals

- Pod phase is `Running`, but readiness is false.
- Events mention `Unhealthy` or readiness probe failures.
- Logs show dependency connection errors, timeout errors, or startup drift.
- Service endpoints are missing one or more pods.

## Common Causes

- The application is listening on a different port than the readiness probe.
- A required downstream service, database, cache, or secret is unavailable.
- Startup time exceeds the readiness probe initial delay.
- The probe path returns a non-success HTTP status during warmup.

## Checks

1. Compare the readiness probe path, port, and scheme with the container config.
2. Inspect recent logs for dependency failures before changing probe thresholds.
3. Confirm the service has endpoints for healthy pods.
4. Check whether the deployment recently changed environment variables or
   secrets.
5. Increase readiness thresholds only when the application is healthy but slow
   to warm up.

## Operator Response

Keep the deployment out of service until readiness is restored. If the failure
is caused by a bad rollout, rollback first and continue investigating with the
failed revision preserved for evidence.
