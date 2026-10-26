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

## Guided development-cluster pilot

Open **Help & tools → Cluster connection** for setup steps and a namespace-specific
check. Configure credentials only on the API host, never in the browser. The page
does not upload credentials or change runtime configuration.

Set `KUBEPILOT_CLUSTER_DISPLAY_NAME` to a recognizable label. This is an operator
label, not independently discovered cluster identity. `/api/v1/status` returns that
label and the application namespace allowlist, but not kubeconfig paths, credentials,
or inspection service addresses.

The check reads deployment health for the namespace you enter. It reports when the
check completed and replaces an earlier successful result on failure. A successful
read does not verify pod logs, all resource permissions, or a complete diagnosis.
Fixture mode is always labelled as demo data. Service mode is explicitly unverified
because the upstream service can use fixtures. No live-cluster readiness claim should
be based only on a configured mode or the API's `/readyz` endpoint.

For a pilot, use a namespace-scoped read-only identity supplied by a cluster
administrator. The following Role is an example for the chosen namespace; it does
not create credentials or a binding. An administrator must bind it to the intended
user or service account in that namespace.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: kubepilot-pilot-reader
rules:
  - apiGroups: [apps]
    resources: [deployments]
    verbs: [get, list]
  - apiGroups: [""]
    resources: [pods, events]
    verbs: [get, list]
  - apiGroups: [""]
    resources: [pods/log]
    verbs: [get]
```

Confirm permissions with the pilot identity using `kubectl auth can-i` for those
resources in the pilot namespace. It should not have write access. Never reuse a
cluster-admin identity to make a pilot work.

**Namespace enforcement:** Set `KUBEPILOT_ALLOWED_NAMESPACES` before restarting
the API. Overview and cluster-health chat aggregate namespace-scoped deployment
lists rather than requesting a cluster-wide list. Both deterministic and graph chat
use the configured Kubernetes connection and shared namespace boundary. Out-of-scope
chat, diagnosis, report creation, and saved report reads/exports are rejected; saved
report lists are filtered before their result limit. Action allowlists also apply to
chat tool intents and report reads. Denied streaming chat requests return 403 before
the event stream begins. Without a namespace allowlist, unrestricted behavior is
preserved. Kubernetes RBAC must still restrict the credential itself; this setting
is defense in depth, not a replacement for cluster authorization.

A pilot must still verify real workload diagnoses, event access, log access, and
missing-resource/error behavior. The fixture and mocked-failure checks validate the
UI workflow, not live cluster permissions. Use a development cluster with an approved
read-only identity; this change does not connect to or modify one automatically.

## Kubeconfig Mode

Use this mode when running the API locally against a real cluster.

```bash
python -m pip install -e ".[dev,kubernetes]"
export KUBEPILOT_CLUSTER_DISPLAY_NAME=development-pilot
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
- `envFromSecrets` for secret-backed values such as LLM endpoints and OTLP
  headers
- `networkPolicy.enabled` for restricted ingress

The production values use `ghcr.io/aryansharma9917/kubepilot-api` with a
commit-based `sha-...` tag. Publish that exact tag before deploying, or override
`image.repository` and `image.tag` with an immutable digest-backed release.

For production, configure External Secrets Operator with the
`ClusterSecretStore` or `SecretStore` named by
`externalSecret.secretStoreRef`. Store the keys listed in
`helm/kubepilot/values-production.yaml` at the configured
`externalSecret.remoteKey`; do not commit their values or create the target
Secret imperatively. Verify the service account's read-only permissions with
`kubectl auth can-i --as=system:serviceaccount:kubepilot:kubepilot-kubepilot`.

After deployment, verify the external secret and workload:

```bash
kubectl get externalsecret kubepilot-kubepilot \
  --namespace kubepilot \
  --output=jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
kubectl rollout status deployment/kubepilot-kubepilot \
  --namespace kubepilot
```

To rotate a credential, update only the corresponding property at the
external provider. Wait for the ExternalSecret refresh interval, confirm the
target Secret's resource version changes, and verify the API or provider
connection. No image rebuild or Helm chart change is required. Record the
rotation and validation result according to the team's audit policy.

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
