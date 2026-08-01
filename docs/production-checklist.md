# Production Readiness Checklist

Use this checklist before presenting KubePilot as production-ready for a team or
customer environment.

## Access Control

- [ ] `KUBEPILOT_API_KEYS` is enabled.
- [ ] `KUBEPILOT_ALLOWED_NAMESPACES` is scoped to approved namespaces.
- [ ] `KUBEPILOT_ALLOWED_ACTIONS` includes only required read/planning actions.
- [ ] Kubernetes RBAC is reviewed for least privilege.
- [ ] Ingress uses TLS and a trusted identity layer.

## Runtime

- [ ] API runs with resource requests and limits.
- [ ] Production values enable HPA and PodDisruptionBudget.
- [ ] Health and readiness probes are passing.
- [ ] Container image tag is immutable.
- [ ] Secrets are not committed to Git.

## AI And Retrieval

- [ ] Runbooks are reviewed for sensitive content.
- [ ] Retrieval evaluation passes for expected cases.
- [ ] LLM provider failure behavior is tested.
- [ ] Generated answers show sources and workflow steps.
- [ ] Remediation remains approval-gated.

## Observability

- [ ] Prometheus scrapes `/metrics`.
- [ ] Grafana dashboard is provisioned.
- [ ] Alert rules are loaded.
- [ ] OTLP export is configured if central tracing is required.
- [ ] Audit events are retained according to policy.

## Validation

- [ ] `ruff check .` passes.
- [ ] `pytest` passes.
- [ ] `go test ./...` passes for `services/k8s-tool`.
- [ ] `docker compose config` passes.
- [ ] `docker compose --profile monitoring config` passes.
- [ ] Helm renders default, local, staging, and production values.
- [ ] `./scripts/local-cluster-smoke.sh` passes on kind.
