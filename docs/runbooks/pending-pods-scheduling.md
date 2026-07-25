# Pending Pods And Scheduling Failures

Use this runbook when pods remain in `Pending`, show `Unschedulable`, or emit
`FailedScheduling` events.

## Common Causes

- CPU or memory requests exceed available node capacity.
- Namespace `ResourceQuota` or `LimitRange` blocks the requested resources.
- Node taints do not match pod tolerations.
- Node selectors, affinity, or topology spread constraints are too restrictive.
- Required persistent volumes are unavailable.

## Diagnosis Steps

1. Inspect pod events for `FailedScheduling`.
2. Compare pod CPU and memory requests with allocatable node capacity.
3. Check namespace quotas and limit ranges.
4. Review node taints, tolerations, selectors, and affinity rules.
5. Confirm any required volumes or storage classes can bind.

## Remediation

- Reduce requests or increase cluster capacity.
- Adjust quotas or limits if the workload is intentionally sized.
- Add tolerations or relax selectors and affinity where appropriate.
- Scale the node pool or move the workload to a namespace with capacity.
