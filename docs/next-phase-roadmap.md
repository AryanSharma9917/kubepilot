# KubePilot Next-Phase Roadmap

KubePilot's local-first MVP is complete. The next work is production readiness
and operator adoption, not another broad demo surface. This backlog is ordered
by risk reduction and user value.

## Current Baseline

- The local fixture demo, RAG pipeline, agent workflow, Kubernetes inspection
  boundary, incident reports, web console, observability, and CI checks are in
  place.
- Real-cluster use remains environment-specific and requires an explicit review
  of permissions, authentication, secrets, network policy, and retention.
- Write actions are represented as proposed remediation plans; they are not
  yet executed through an approval workflow.

## Phase 1: Production Readiness

### 1. Define the supported deployment profile

Document one reference deployment target first, such as a single Kubernetes
cluster with Helm, Postgres, an external LLM endpoint, and Prometheus. Record
the supported Kubernetes versions, required ingress and storage behavior,
resource limits, backup expectations, and upgrade procedure.

**Done when:** a clean environment can be deployed from documented values and
the production checklist has no ambiguous required setting.

### 2. Move secrets to a managed boundary

Replace plaintext or environment-only production secret handling with a
secret-manager integration or an external-secrets pattern. Cover LLM keys,
API keys, database credentials, and kubeconfig or service-account material.

**Done when:** production manifests contain no secret values, rotation is
documented, and a rotated credential is verified without rebuilding images.

### 3. Tighten identity and authorization

Add real user identity through the selected SSO/OIDC provider and map users or
groups to read-only, incident-operator, and administrator roles. Enforce the
same policy at the API and Kubernetes tool boundaries, including namespace and
action allowlists.

**Done when:** an unauthorized user cannot call protected routes or tools, and
an authorized read-only user cannot request a write action.

### 4. Establish operational SLOs and recovery checks

Choose targets for API availability, chat latency, diagnosis latency, and
report durability. Add dashboards and alerts for those targets, plus a backup
and restore test for incident data and configuration.

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

Start with the reference deployment profile, managed secret boundary, and the
OIDC role model. These decisions constrain multi-cluster support,
approval-gated writes, incident integrations, and production operations.

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