# Local Cluster Validation

KubePilot can run against a local Kubernetes cluster in fixture mode. This
validates the container image, Helm chart, readiness probes, and metrics endpoint
without requiring a live application cluster.

## Prerequisites

- Docker
- kubectl
- Helm
- kind, optional but recommended

## One-command Smoke Test

```bash
./scripts/local-cluster-smoke.sh
```

The script:

1. Builds `kubepilot-api:local`.
2. Loads the image into kind when kind is available.
3. Renders the Helm chart.
4. Installs or upgrades the chart into the `kubepilot` namespace.
5. Waits for rollout completion.
6. Port-forwards the service.
7. Runs the API-side local-cluster validator against `/healthz`, `/readyz`, `/metrics`, and `/api/v1/cluster/health`.

## Manual Flow

```bash
docker build -t kubepilot-api:local .
kind load docker-image kubepilot-api:local
helm template kubepilot ./helm/kubepilot --namespace kubepilot
helm upgrade --install kubepilot ./helm/kubepilot \
  --namespace kubepilot \
  --create-namespace \
  --set image.repository=kubepilot-api \
  --set image.tag=local \
  --set image.pullPolicy=IfNotPresent
kubectl rollout status deployment/kubepilot-kubepilot --namespace kubepilot
kubectl port-forward service/kubepilot-kubepilot 18000:8000 --namespace kubepilot
```

Then in another shell:

```bash
curl http://127.0.0.1:18000/healthz
curl http://127.0.0.1:18000/readyz
curl http://127.0.0.1:18000/metrics
curl http://127.0.0.1:18000/api/v1/cluster/health
```

You can also run the reusable validator directly once the service is reachable:

```bash
PYTHONPATH=services/api python -m kubepilot_api.local_cluster --base-url http://127.0.0.1:18000
```

## Real Cluster Mode

Fixture mode is the default. To use the in-cluster Kubernetes client, set:

```bash
helm upgrade --install kubepilot ./helm/kubepilot \
  --namespace kubepilot \
  --create-namespace \
  --set env.KUBEPILOT_K8S_MODE=in_cluster
```

The chart includes read-only RBAC for deployments, pods, and events. Log access
uses the pods/log subresource when the cluster enforces subresource permissions.
