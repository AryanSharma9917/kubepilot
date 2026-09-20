# Supported Production Deployment Profile

This is the reference deployment target for the first production pilot.

## Platform

- Kubernetes 1.28 or newer
- Helm 3.14 or newer
- One cluster and one KubePilot namespace per environment
- Ingress NGINX or another ingress controller with TLS termination
- Prometheus-compatible metrics collection
- PostgreSQL 15 or newer for incident report persistence
- An OpenTelemetry Collector is optional but recommended

The API runs in-cluster with a dedicated ServiceAccount and read-only
permissions for pods, pod logs, events, and deployments. The chart's
`values-production.yaml` is the starting point for this profile.

## Required Production Controls

- An immutable container tag or image digest
- TLS at the ingress
- An external secret provider, exposed through External Secrets Operator
- OIDC authentication with an issuer, audience, and role claim
- API-key authentication is disabled in the production deployment; API keys
   remain available only for environments that do not require OIDC
- Explicit namespace and action allowlists
- PostgreSQL backups with a tested restore procedure
- Network policy allowing ingress only from the ingress and monitoring
  namespaces, plus egress to PostgreSQL, the LLM endpoint, and telemetry
  collector as required by the environment

The API does not create or execute Kubernetes write actions. Remediation
responses are plans that require a separate approval workflow, which is a
follow-on capability.

## Resource Starting Points

The production values request 500m CPU and 512Mi memory, limit the API to 2
CPU and 2Gi memory, and scale from two to six replicas at 70% CPU. Measure
actual usage during the pilot and revise these values with the SLO review.

## Deployment Procedure

1. Install and configure External Secrets Operator and an OIDC provider.
2. Create a `ClusterSecretStore` or namespace-scoped `SecretStore` named by
   `externalSecret.secretStoreRef`.
3. Store the secret properties listed in
   `helm/kubepilot/values-production.yaml` in the external provider.
4. Render and review the chart, then deploy with the production values:

   ```bash
   helm upgrade --install kubepilot ./helm/kubepilot \
     --namespace kubepilot --create-namespace \
     --values helm/kubepilot/values-production.yaml
   ```

5. Verify the ExternalSecret reaches `Ready`, the API readiness probe passes,
   and the ingress presents the expected certificate.
6. Run the API, Kubernetes RBAC, and restore checks in the production
   checklist before accepting traffic.

## Upgrade And Recovery

Use an immutable image tag for every release. Review Helm output before an
upgrade and keep the previous image tag available for rollback. Back up the
PostgreSQL database according to the team's retention policy and perform a
restore rehearsal before the pilot and after any storage or schema change.

The environment-specific ingress hostname, TLS secret, OIDC issuer, secret
store, database endpoint, LLM endpoint, and backup destination must be
provided through deployment values or external secret configuration. They are
intentionally not committed here.
