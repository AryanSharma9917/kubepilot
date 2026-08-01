# Monitoring

KubePilot exposes Prometheus metrics at `/metrics`, stores a local in-memory
trace buffer for the web UI, records audit events for API requests, and can
export OpenTelemetry traces with OTLP.

## Local Prometheus

Use `monitoring/prometheus.yml` to scrape the API:

```bash
docker compose up --build
```

Start Prometheus and Grafana with the optional monitoring profile:

```bash
docker compose --profile monitoring up --build
```

Open:

```text
Prometheus: http://127.0.0.1:9090
Grafana:    http://127.0.0.1:3001
```

Prometheus should scrape:

```text
api:8000/metrics
```

## Alert Rules

`monitoring/alerts.yml` includes starter rules for:

- API scrape failures
- server-side HTTP errors
- Kubernetes tool failures
- trace buffer saturation

Mount the alert rules into Prometheus at `/etc/prometheus/alerts.yml` when
running a full monitoring stack.

## Grafana

Import `monitoring/grafana-dashboard.json` into Grafana and point
`${DS_PROMETHEUS}` to the Prometheus datasource. The dashboard covers request
volume, chat responses, retrieval citations, Kubernetes tool calls, and local
trace-buffer health.

## OTLP Export

Set these variables when sending traces to a collector:

```bash
export KUBEPILOT_OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
export KUBEPILOT_OTEL_SERVICE_NAME=kubepilot-api
export KUBEPILOT_OTEL_HEADERS=authorization=Bearer-token
```

The local UI still shows recent in-memory spans even when OTLP export is off.
