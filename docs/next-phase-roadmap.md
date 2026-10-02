# KubePilot Next-Phase Roadmap

KubePilot's local-first MVP is complete. The next work is production readiness
and operator adoption, not another broad demo surface. This backlog is ordered
by risk reduction and user value.

## Current Baseline

- The local-first demo includes a web console, FastAPI API, Go Kubernetes tool,
  Postgres-backed incident storage, and deterministic fixture workloads.
- Chat can retrieve Markdown runbooks, answer with source context, inspect
  cluster health, diagnose deployments, and create incident reports. Keyword
  retrieval is the default; optional vector/FAISS and LLM provider paths exist.
- The console includes chat, workload and diagnosis views, incident reports,
  traces, audit events, and runtime/capability status.
- The API includes health/readiness, metrics, chat, knowledge, cluster, status,
  audit, and trace routes. Authentication, role/action checks, namespace policy,
  rate limiting, request IDs, and audit recording are implemented as
  configurable controls.
- Deployment assets include Docker Compose, local/staging/production Helm
  values, External Secrets templates, OIDC configuration, ingress, network
  policy, HPA/PDB settings, Prometheus/Grafana assets, and Argo CD manifests.
- Remediation is currently proposed as a plan; there is no approval-and-execute
  workflow. Multi-cluster routing and outbound incident collaboration are not
  implemented.

### Verification Snapshot

The current workspace checks pass: 96 Python tests, Ruff, Go tests, Go vet, and
default plus monitoring-profile Compose configuration validation. These checks
do not prove that a real OIDC provider, external secret store, production
cluster, backup/restore process, or pilot SLO has been exercised.

### Code Cleanup

The current Python and Go static checks report no lint or vet findings. No
unused functional module has been confirmed, so this pass does not delete
features based only on their being optional. Keep fixture mode for repeatable
local use and keep production integrations optional; remove code only after a
usage check and tests demonstrate that it is genuinely unreachable or
unsupported.

## Implementation Status

| Area | Status | Remaining proof or work |
| --- | --- | --- |
| Local demo and web console | Implemented | Run the full stack smoke test on a clean machine |
| Runbook chat and retrieval | Implemented | Expand evaluation with real, anonymized operator cases |
| Kubernetes health and diagnosis | Implemented | Validate least-privilege access against the supported cluster profile |
| Incident reports and persistence | Implemented | Exercise production database backup and restore |
| Go Kubernetes tool | Implemented | Validate live-cluster errors, timeouts, and RBAC denials |
| Authentication and policy | Implemented foundation | Exercise the chosen OIDC provider and role mappings in deployment |
| External secrets | Deployment integration present | Configure a real secret store and prove credential rotation |
| Metrics, traces, and audit | Implemented foundation | Define SLOs, verify alerts, and validate retention/correlation |
| Production Helm profile | Documented/configured | Deploy from a clean environment and prove upgrade/rollback |
| Approval-gated remediation | Not implemented | Add proposal lifecycle, authorization, approval, execution, and audit |
| Multi-cluster and incident collaboration | Not implemented | Defer until the single-cluster pilot is safe and useful |

## Phase 1: Production Readiness

### 1. Define the supported deployment profile

The initial profile is documented in
[`production-deployment-profile.md`](production-deployment-profile.md): a
single Kubernetes cluster, Helm, Postgres, external identity/secrets, and
Prometheus-compatible monitoring. Confirm and maintain its supported versions,
ingress/storage behavior, resource limits, backup expectations, and upgrade
procedure.

**Status:** Profile documented; clean-environment deployment and rollback still
need to be exercised.

**Done when:** a clean environment can be deployed and upgraded from documented
values, recovery is tested, and the production checklist has no ambiguous
required setting.

### 2. Move secrets to a managed boundary

External Secrets templates and secret-backed Helm environment variables are
present. Configure the target provider and verify LLM credentials, database
credentials, and telemetry secrets are supplied and rotated without rebuilding
the image. Keep Kubernetes service-account credentials in-cluster rather than
copying them into application secrets.

**Status:** Integration pattern implemented; real provider and rotation are not
verified.

**Done when:** production manifests contain no secret values, rotation is
documented, and a rotated credential is verified without rebuilding images.

### 3. Tighten identity and authorization

action allowlists.
OIDC token validation, role-to-action mapping, API-key support, and namespace
and action allowlists exist in the API. Configure the selected identity provider
and prove those decisions remain enforced at every cluster operation boundary.

**Status:** Code and configuration foundation implemented; provider-backed
deployment validation remains.

**Done when:** an unauthorized user cannot call protected routes or tools, and
an authorized read-only user cannot request a write action.

### 4. Establish operational SLOs and recovery checks

Choose targets for API availability, chat latency, diagnosis latency, and
report durability. Confirm dashboards and alerts measure those targets, then
test backup/restore for incident data and configuration.

**Status:** Metrics, traces, audit events, dashboards, and alert assets exist;
SLOs and recovery exercises remain.

**Done when:** the team can demonstrate an alert, inspect correlated traces,
restore a test database, and follow a documented incident procedure.

## Phase 2: Safe Operator Workflows

### 5. Implement approval-gated remediation

Represent proposed actions with an immutable plan, affected resources,
expected impact, expiry, requester, approver, and execution result. Require a
separate approval before any write operation and keep dry-run as the default.

**Done when:** a remediation can be proposed, approved, rejected, expired,
executed, and audited end to end, with no path for silent execution.

### 6. Add multi-cluster context

Introduce named cluster targets and make cluster identity explicit in chat,
diagnosis, audit events, traces, reports, and remediation plans. Preserve the
existing namespace and action policy for every target.

**Done when:** a user can switch between two configured clusters without
cross-cluster data appearing in answers or incident reports.

### 7. Integrate incident collaboration

Add one outbound integration first, preferably Slack or the team's incident
tool. Support posting a reviewed incident summary and linking back to the
KubePilot report; do not automatically post unreviewed model output.

**Done when:** an operator can publish a reviewed update, see delivery status,
and audit who published it and which report was used.

## Phase 3: Intelligence and Scale

### 8. Measure answer quality with real operator cases

Expand the retrieval benchmark with anonymized incidents, expected evidence,
answer correctness, and unsafe-answer cases. Track retrieval quality,
unsupported claims, latency, and provider failure behavior in CI.

**Done when:** quality regressions fail CI and every supported runbook family
has representative evaluation cases.

### 9. Add provider and cloud integrations selectively

Support only the cloud providers and Kubernetes signals required by real pilot
users. Keep provider adapters behind the existing interface and add contract
tests for authentication failures, rate limits, timeouts, and partial results.

**Done when:** each integration has a documented support boundary, tests, and a
fallback behavior that does not fabricate cluster evidence.

### 10. Revisit retrieval and agent architecture

Consider an external vector store or specialist agents only after Phase 2 and
the evaluation baseline are stable. Compare the operational cost and quality
against the current local index and single workflow before migrating.

**Done when:** a measured benchmark justifies the added infrastructure and a
rollback path is documented.

## Suggested First Slice

Start by deploying the documented single-cluster profile in a clean test
environment. Validate OIDC roles, external secret provisioning/rotation,
least-privilege Kubernetes permissions, and Postgres restore there. The code
foundations exist; the main gap is proving the controls together in the target
environment.

Do not treat a hosted demo, cloud integration, external vector database, or
multi-agent workflow as a prerequisite for the first pilot. They are follow-on
work once a real operator workflow and its safety controls are proven.

## Exit Criteria For The Next Milestone

- One documented production deployment target works from a clean environment.
- Secrets are externally managed and rotation has been exercised.
- OIDC roles and Kubernetes permissions are tested for allowed and denied paths.
- A read-only pilot user can answer, diagnose, and export an incident report.
- Metrics, traces, audit events, backup, and restore are validated together.
- The retrieval evaluation includes real pilot cases and runs in CI.