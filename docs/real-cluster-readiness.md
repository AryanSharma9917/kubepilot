# Real Cluster Readiness

KubePilot defaults to fixture mode so the demo is repeatable. Real cluster mode
is available when you want the API to inspect live Kubernetes deployments, pods,
events, and logs.

## Modes

| Mode | Use when | Required setting |
| --- | --- | --- |
| `fixture` | local demo, CI, screenshots | `KUBEPILOT_K8S_MODE=fixture` |
| `kubeconfig` | running API on your laptop against a cluster | `KUBEPILOT_K8S_MODE=kubeconfig` |
| `in_cluster` | running KubePilot inside Kubernetes | `KUBEPILOT_K8S_MODE=in_cluster` |

The Go tool service has its own mode:

| Mode | Use when | Required setting |
| --- | --- | --- |
| `fixture` | deterministic local service output | `KUBEPILOT_K8S_TOOL_MODE=fixture` |
| `cluster` | live cluster reads through the tool service | `KUBEPILOT_K8S_TOOL_MODE=cluster` |

## Kubeconfig Mode

Use this mode when running the API locally against a real cluster.

```bash
export KUBEPILOT_K8S_MODE=kubeconfig
export KUBEPILOT_KUBECONFIG="$HOME/.kube/config"
export KUBEPILOT_ALLOWED_NAMESPACES=payments,platform,notifications
export KUBEPILOT_ALLOWED_ACTIONS=cluster:health,deployment:diagnose,deployment:incident-report,deployment:remediation-plan
uvicorn kubepilot_api.main:app --reload
```

Smoke the live boundary:

```bash
curl http://127.0.0.1:8000/api/v1/status
curl http://127.0.0.1:8000/api/v1/cluster/health
curl http://127.0.0.1:8000/api/v1/cluster/namespaces/payments/deployments/checkout/diagnose
```

## In-cluster Helm Mode

Install KubePilot into a cluster with the Kubernetes client enabled:

```bash
helm upgrade --install kubepilot ./helm/kubepilot \
  --namespace kubepilot \
  --create-namespace \
  --set env.KUBEPILOT_K8S_MODE=in_cluster \
  --set env.KUBEPILOT_ALLOWED_NAMESPACES=payments,platform,notifications \
  --set env.KUBEPILOT_ALLOWED_ACTIONS=cluster:health,deployment:diagnose,deployment:incident-report,deployment:remediation-plan
```

For the local kind demo:

```bash
./scripts/kind-demo.sh
kubectl port-forward service/kubepilot-kubepilot 18000:8000 --namespace kubepilot
```

Then open:

```text
http://127.0.0.1:18000
```

## Production Helm Controls

The chart supports production-shaped controls without enabling them by default:

- `ingress.enabled` for external routing and TLS
- `autoscaling.enabled` for HorizontalPodAutoscaler
- `podDisruptionBudget.enabled` for voluntary disruption protection
- `envFromSecrets` for secret-backed values such as API keys, LLM endpoints, and
  OTLP headers
- `networkPolicy.enabled` for restricted ingress

The production values use `ghcr.io/aryansharma9917/kubepilot-api` with a
commit-based `sha-...` tag. Publish that exact tag before deploying, or override
`image.repository` and `image.tag` with an immutable digest-backed release.

Create the referenced secret without committing its values:

```bash
kubectl create secret generic kubepilot-api-secrets \
  --namespace kubepilot \
  --from-literal=api-keys="$KUBEPILOT_API_KEYS" \
  --from-literal=azure-openai-api-key="$AZURE_OPENAI_API_KEY" \
  --from-literal=azure-openai-endpoint="$AZURE_OPENAI_ENDPOINT" \
  --from-literal=azure-openai-deployment="$AZURE_OPENAI_DEPLOYMENT" \
  --from-literal=otel-endpoint="$KUBEPILOT_OTEL_EXPORTER_OTLP_ENDPOINT" \
  --from-literal=otel-headers="$KUBEPILOT_OTEL_HEADERS"
```

For production, replace this imperative Secret with External Secrets Operator,
Vault, or the cloud provider's secret manager and keep the same secret keys.
Verify the service account's read-only permissions with
`kubectl auth can-i --as=system:serviceaccount:kubepilot:kubepilot-kubepilot`.

Example secret:

```bash
kubectl create secret generic kubepilot-api-secrets \
  --namespace kubepilot \
  --from-literal=api-keys=replace-me \
  --from-literal=llm-endpoint=https://llm.example.com/v1/chat \
  --from-literal=otel-headers=authorization=Bearer-token
```

Render a production-shaped manifest:

```bash
helm template kubepilot ./helm/kubepilot \
  --namespace kubepilot \
  --values helm/kubepilot/values-production.yaml
```

## Policy Examples

Namespace policy:

```bash
export KUBEPILOT_ALLOWED_NAMESPACES=payments,platform
```

Action policy:

```bash
export KUBEPILOT_ALLOWED_ACTIONS=cluster:health,deployment:diagnose,deployment:incident-report,deployment:remediation-plan
```

API key protection:

```bash
export KUBEPILOT_API_KEYS=local-demo-key
curl -H "x-api-key: local-demo-key" http://127.0.0.1:8000/api/v1/cluster/health
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `/readyz` fails | Confirm the API can initialize settings and the Kubernetes mode is valid. |
| `kubeconfig` mode cannot connect | Confirm `KUBEPILOT_KUBECONFIG` points to a readable file and the current context is correct. |
| `in_cluster` mode is forbidden | Check the chart RBAC and service account binding in the `kubepilot` namespace. |
| deployment diagnosis returns not found | Confirm namespace allowlist, deployment name, and workload namespace. |
| logs are missing | Confirm RBAC includes `pods/log` and the pod container is still available. |
| Helm image pull fails | Set `image.repository`, `image.tag`, and `image.pullPolicy` for your registry or kind image. |

## Demo Checklist

1. Run `./scripts/kind-demo.sh`.
2. Port-forward the API service.
3. Open the web console.
4. Ask `Show unhealthy workloads`.
5. Run diagnosis for `payments` / `checkout`.
6. Open the Incident tab and copy the status update.
7. Open Observability and confirm traces, audit events, and agent trail appear.
