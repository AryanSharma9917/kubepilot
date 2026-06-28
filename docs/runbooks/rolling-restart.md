# Rolling restart

Use this runbook when an operator asks how to restart a Kubernetes workload
without deleting it manually.

## Standard command

```bash
kubectl rollout restart deployment/<name> -n <namespace>
```

## Follow-up checks

1. Watch the rollout status.
2. Confirm new pods become ready.
3. Verify the old ReplicaSet scales down.
4. Check application metrics or smoke tests after the rollout.

## Suggested response

Provide the rollout restart command, mention the namespace flag, and remind the
operator to monitor rollout status afterward.
