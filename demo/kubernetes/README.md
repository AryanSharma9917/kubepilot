# KubePilot Demo Workloads

These manifests create intentionally unhealthy workloads for local cluster demos.

```bash
kubectl apply -f demo/kubernetes/namespace.yaml
kubectl apply -f demo/kubernetes/checkout-broken.yaml
kubectl apply -f demo/kubernetes/metrics-scraper-broken.yaml
```

Use them with `KUBEPILOT_K8S_MODE=in_cluster` in the Helm deployment or with the
Go `k8s-tool` in `cluster` mode.
