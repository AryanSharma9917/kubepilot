# Deployment rollout failures

Use this runbook when a Kubernetes Deployment is not becoming available after a
new rollout.

## Symptoms

- `kubectl rollout status deployment/<name>` does not complete.
- New pods remain in `Pending`, `CrashLoopBackOff`, or `ImagePullBackOff`.
- The Deployment reports unavailable replicas.

## Checks

1. Inspect Deployment status and conditions.
2. List ReplicaSets owned by the Deployment.
3. Describe unhealthy pods.
4. Review recent events in the namespace.
5. Check container image names, pull secrets, resource requests, and probes.

## Common causes

- Invalid image tag or missing registry credentials.
- Readiness probe failures.
- Insufficient CPU or memory in the cluster.
- Misconfigured environment variables or secrets.

## Suggested response

Summarize the failed rollout condition, name the most likely cause, and provide
the next `kubectl` commands an operator should run.
