# GitOps Deployment

KubePilot includes ArgoCD manifests for a single application and a multi
environment ApplicationSet.

## Files

- `gitops/argocd/kubepilot-application.yaml` installs one KubePilot release.
- `gitops/argocd/kubepilot-applicationset.yaml` creates local, staging, and
  production applications from Helm values files.
- `helm/kubepilot/values-local.yaml` keeps the demo deterministic.
- `helm/kubepilot/values-staging.yaml` enables in-cluster Kubernetes mode,
  FAISS, LangGraph, namespace/action policy, and network policy.
- `helm/kubepilot/values-production.yaml` raises replicas, resources, and API
  rate limits for a production-shaped deployment.

## Apply

Replace `https://github.com/your-org/kubepilot.git` with your repository URL,
then apply one of the manifests:

```bash
kubectl apply -f gitops/argocd/kubepilot-application.yaml
kubectl apply -f gitops/argocd/kubepilot-applicationset.yaml
```

## Promotion Flow

1. Build and publish a new image.
2. Update the target environment value file with the image tag.
3. Open a pull request.
4. Let ArgoCD sync after merge.
5. Verify `/readyz`, `/api/v1/status`, `/api/v1/capabilities`, and `/metrics`.

## Production Notes

Store secrets such as `KUBEPILOT_API_KEYS`, OTLP headers, or LLM credentials in a
Kubernetes Secret or external secret manager. The committed values files only
contain non-secret defaults and operational guardrails.
