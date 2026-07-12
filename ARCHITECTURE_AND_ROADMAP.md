# KubePilot

## AI-Powered Kubernetes Operations Platform

KubePilot is a cloud-native AI operations platform designed to assist engineers with Kubernetes troubleshooting, operational knowledge retrieval, deployment diagnostics, and platform automation.

Unlike traditional chatbots, KubePilot combines Retrieval-Augmented Generation (RAG), agentic workflows, Kubernetes-native tooling, GitOps practices, and observability into a unified system capable of reasoning over documentation and interacting with real infrastructure.

The goal is to build a production-style platform that demonstrates modern AI Engineering, Platform Engineering, and DevOps practices in a single repository.

---

# Vision

Modern platform teams spend significant time searching documentation, investigating deployment failures, analyzing logs, and performing repetitive operational tasks.

KubePilot aims to reduce this operational overhead by providing an AI-powered assistant that can:

* Retrieve operational knowledge from internal runbooks
* Diagnose Kubernetes issues
* Analyze deployments and cluster health
* Interact with platform tooling
* Provide contextual recommendations
* Serve as a foundation for future automation workflows

The project is designed to remain fully self-hosted and runnable on local infrastructure while following production-grade engineering practices.

---

# Core Use Cases

## Deployment Troubleshooting

User:

> Why is my deployment failing?

KubePilot should:

1. Retrieve relevant runbooks
2. Inspect deployment status
3. Analyze recent events
4. Fetch pod information
5. Generate a diagnosis
6. Suggest remediation steps

---

## Operational Knowledge Assistant

User:

> How do we perform a rolling restart?

KubePilot should:

1. Search indexed documentation
2. Retrieve relevant context
3. Generate an answer grounded in runbooks

---

## Cluster Visibility

User:

> Show unhealthy workloads in the cluster.

KubePilot should:

1. Query Kubernetes APIs
2. Collect workload status
3. Summarize cluster health

---

## Incident Investigation

User:

> Why did the checkout service restart five times?

KubePilot should:

1. Gather deployment information
2. Retrieve pod events
3. Fetch logs
4. Correlate findings
5. Present a concise explanation

---

# System Architecture

## Agent Layer

Responsibilities:

* User interaction
* Tool orchestration
* Decision making
* Multi-step reasoning

Technology:

* LangGraph
* LangChain
* Python

---

## Knowledge Layer

Responsibilities:

* Document ingestion
* Chunking
* Embedding generation
* Retrieval

Technology:

* FAISS
* Sentence Transformers

---

## Tool Layer

Responsibilities:

* Kubernetes interactions
* Deployment inspection
* Event retrieval
* Log collection

Technology:

* Go
* client-go
* REST APIs

---

## API Layer

Responsibilities:

* Agent access
* Request handling
* Streaming responses

Technology:

* FastAPI

---

## Platform Layer

Responsibilities:

* Container orchestration
* Service deployment
* Configuration management

Technology:

* Docker
* Kubernetes
* Helm

---

## GitOps Layer

Responsibilities:

* Continuous delivery
* Drift detection
* Environment synchronization

Technology:

* ArgoCD
* GitHub Actions

---

## Observability Layer

Responsibilities:

* Metrics
* Dashboards
* Service monitoring

Technology:

* Prometheus
* Grafana

---

# Repository Structure

```text
kubepilot/

├── agent/
│   ├── graph/
│   ├── prompts/
│   ├── tools/
│   └── state/
│
├── rag/
│   ├── loaders/
│   ├── chunking/
│   ├── embeddings/
│   ├── retrieval/
│   └── evaluation/
│
├── services/
│   ├── api/
│   ├── k8s-tool/
│   └── deploy-tool/
│
├── docs/
│   └── runbooks/
│
├── helm/
│
├── gitops/
│
├── monitoring/
│
├── tests/
│
├── scripts/
│
└── PROJECT_VISION.md
```

---

# Engineering Principles

* Local-first development
* Infrastructure as Code
* GitOps-driven deployments
* Testable components
* Modular architecture
* Production-style repository structure
* Clear separation of concerns
* Observable services
* Reproducible environments

---

# Implementation Snapshot

## Already Implemented

- [x] FastAPI service with chat, health, readiness, and metrics endpoints
- [x] Local markdown runbook loading, chunking, and retrieval
- [x] Optional FAISS-backed vector retrieval
- [x] Persisted runbook index generation and loading
- [x] Optional native FAISS sidecar index generation
- [x] Provider-shaped answer synthesis with structured citations
- [x] Self-hosted HTTP JSON LLM provider support
- [x] Knowledge search API for retrieval inspection
- [x] Retrieval evaluation CLI and JSONL benchmark cases
- [x] LangGraph-compatible workflow boundary with intent classification
- [x] Explicit workflow step plans for graph execution
- [x] Graph output review step before returning responses
- [x] Deterministic Kubernetes health, diagnosis, and incident-report tools
- [x] Go Kubernetes tool service with fixture and real cluster modes
- [x] Deployment diagnostics using pod status, events, and log excerpts
- [x] Incident timeline generation for deployment reports
- [x] Streaming chat endpoint using server-sent events
- [x] Namespace allowlist policy for cluster APIs
- [x] Local audit event trail for API requests
- [x] Request ID propagation through audit events and response headers
- [x] Chat response/source/citation metrics
- [x] Docker Compose, Helm chart, Prometheus config, Grafana dashboard, and ArgoCD manifest
- [x] GitHub Actions CI for linting, tests, index build validation, Docker build, and Helm rendering
- [x] Manual GitHub Actions kind smoke workflow
- [x] Local cluster smoke-test script and validation guide

## Still To Build

- [x] Hosted or self-hosted LLM provider implementation
- [ ] Deeper LangGraph workflow with branch-specific retrieval, tool, synthesis, and review nodes
- [x] Go-based Kubernetes tooling/services
- [ ] Auth, RBAC-aware tool execution, and audit logging
- [ ] OpenTelemetry tracing and richer tool metrics
- [ ] Scheduled integration tests against kind or minikube in CI

---

# MVP Definition

The first release of KubePilot is considered successful when:

- [x] Runbooks can be indexed into FAISS
- [x] Questions can be answered through RAG
- [x] LangGraph agent can use tools
- [x] Kubernetes status can be queried through Go services
- [x] FastAPI exposes a chat endpoint
- [x] Services run locally using Docker
- [x] Deployment works on a local Kubernetes cluster
- [x] Basic metrics are exposed
- [x] GitHub Actions validates builds and tests

---

# Future Enhancements

* Multi-cluster support
* Cloud provider integrations
* Automated remediation workflows
* Slack integration
* RBAC-aware agent actions
* Vector database migration
* OpenTelemetry tracing
* Multi-agent architecture
* Production cloud deployment

---

# Long-Term Goal

Build a production-grade AI-powered Kubernetes operations platform that showcases expertise in:

* AI Engineering
* Retrieval-Augmented Generation
* LangGraph
* FastAPI
* Go
* Kubernetes
* Helm
* GitOps
* ArgoCD
* CI/CD
* Observability
* Platform Engineering
* DevOps

```
```
