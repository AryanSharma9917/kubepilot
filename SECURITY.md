# Security Policy

KubePilot is an operator-facing Kubernetes troubleshooting platform. Treat it as
security-sensitive because it can read cluster health, pod metadata, events, and
log excerpts.

## Supported Versions

The `main` branch is the supported development line for this portfolio release.

## Reporting A Vulnerability

Do not open public issues for secrets, authentication bypasses, Kubernetes RBAC
problems, or data-exposure findings. Report privately to the repository owner.

Include:

- affected commit or release
- reproduction steps
- impact
- suggested mitigation if known

## Security Design

- API key authentication can protect `/api/*` routes.
- Namespace and action allowlists constrain Kubernetes inspection access.
- Kubernetes tooling is read-only by default.
- Remediation plans return approval-gated commands; they do not execute writes.
- Secrets are expected to come from Kubernetes Secrets or an external secret
  manager in production deployments.
- Audit events and request IDs are recorded for API activity.

## Production Requirements

Before exposing KubePilot outside a trusted local demo:

1. Enable API authentication.
2. Use namespace and action allowlists.
3. Store API keys, LLM endpoints, and OTLP headers in secrets.
4. Review Kubernetes RBAC for least privilege.
5. Put the service behind TLS.
6. Configure logs and traces according to your data-retention policy.
7. Review runbooks for sensitive internal content before indexing.
