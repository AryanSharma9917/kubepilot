# Pod restarts

Use this runbook when a workload has restarted unexpectedly or repeatedly.

## Symptoms

- A pod shows a restart count greater than zero.
- Containers enter `CrashLoopBackOff`.
- Application availability drops after a recent deployment.

## Checks

1. Inspect pod status and container restart counts.
2. Read the previous container logs.
3. Describe the pod and review warning events.
4. Check liveness probes and application startup time.
5. Compare the restart time with recent deployments or configuration changes.

## Common causes

- Application process exits with an error.
- Liveness probe is too aggressive.
- Memory limit causes OOM kills.
- Missing configuration, secret, or dependency.

## Suggested response

Explain whether the restart looks application-driven, probe-driven, or
resource-driven. Recommend checking previous logs before current logs.
