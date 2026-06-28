# Unhealthy workloads

Use this runbook when an operator asks for a cluster or namespace health
summary.

## Checks

1. List Deployments with unavailable replicas.
2. List pods that are not `Running` or `Succeeded`.
3. Review recent warning events.
4. Group findings by namespace and workload.

## Common signals

- Deployment available replicas are lower than desired replicas.
- Pods are stuck in `Pending`, `CrashLoopBackOff`, `ImagePullBackOff`, or
  `ErrImagePull`.
- Events mention failed scheduling, failed mounts, failed image pulls, or probe
  failures.

## Suggested response

Return a concise health summary with the most severe workloads first and include
the command used to inspect each issue.
