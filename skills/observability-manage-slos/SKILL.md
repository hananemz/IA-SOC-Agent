---
name: observability-manage-slos
description: >
  Create and manage SLOs in Elastic Observability using the Kibana API. Use when defining
  SLIs, setting error budgets, or managing SLO lifecycle.
metadata:
  author: elastic
  version: 0.2.0`n  qwen_optimized: true
---

# Service-Level Objectives (SLOs)
## System Instructions for Qwen

You are an Elastic observability specialist. Follow these rules:

1. DO_NOT_INVENT: Never fabricate service names, metric values, pod names, or cluster status.
2. VERIFY_FIRST: Run test connections and schema discovery before generating queries.
3. CONFIDENCE_CALIBRATION: Start at high confidence, downgrade for missing evidence.
4. STRUCTURED_OUTPUT: Return structured health assessments with signal categories.
5. COMPETING_HYPOTHESES: List multiple explanations; indicate which evidence disambiguates.

### Investigation Reasoning Framework

- FACTS: Data from OTel telemetry, K8s events, API responses
- OBSERVATIONS: Patterns in utilization, restarts, errors, latency
- HYPOTHESES: Possible root causes
- CONCLUSIONS: Evidence-supported determinations with confidence level

### Confidence Calibration Rules

| Confidence | When to Use                                              |
|------------|----------------------------------------------------------|
| high       | Primary signal clear + corroboration from logs/APM/infra |
| medium     | Primary signal clear but corroboration missing           |
| low        | Only single signal supports hypothesis, or signals conflict |

### Hallucination Guards

| Risk                      | Guard Rail                                              |
|---------------------------|---------------------------------------------------------|
| Inventing pod/container   | Use names only from cluster viewer or query results.    |
| Fabricating metrics       | Use aggregation output values only.                     |
| Wrong failure root cause  | Require corroborating evidence before determining cause.|
| Missing evidence          | Note EVIDENCE_UNAVAILABLE for uncheckable signals.      |



Create and manage SLOs in Elastic Observability. SLOs track service performance against measurable targets using
service-level indicators (SLIs) computed from Elasticsearch data.

## Authentication

SLO operations go through the Kibana API. Authenticate with either an API key or basic auth:

```bash
# API key
curl -H "Authorization: ApiKey <base64-encoded-key>" -H "kbn-xsrf: true" <KIBANA_URL>/api/observability/slos

# Basic auth
curl -u "$KIBANA_USER:$KIBANA_PASSWORD" -H "kbn-xsrf: true" <KIBANA_URL>/api/observability/slos
```

For non-default spaces, prefix the path: `/s/<space_id>/api/observability/slos`.

Include `kbn-xsrf: true` on all POST, PUT, and DELETE requests.

## SLI Types

| Type                    | API value                      | Use case                                    |
| ----------------------- | ------------------------------ | ------------------------------------------- |
| Custom KQL              | `sli.kql.custom`               | Raw logs â€” good/total using KQL queries     |
| Custom metric           | `sli.metric.custom`            | Metric fields â€” equations with aggregations |
| Timeslice metric        | `sli.metric.timeslice`         | Metric fields â€” per-slice threshold check   |
| Histogram metric        | `sli.histogram.custom`         | Histogram fields â€” range/value_count        |
| APM latency             | `sli.apm.transactionDuration`  | APM â€” latency threshold                     |
| APM availability        | `sli.apm.transactionErrorRate` | APM â€” success rate                          |
| Synthetics availability | `sli.synthetics.availability`  | Synthetics monitors â€” uptime percentage     |

## Guidelines

- `objective.target` is a decimal between 0 and 1 (for example `0.995` for 99.5%).
- Timeslice metric indicators require `budgetingMethod: "timeslices"`.
- Updating an SLO resets the underlying transform â€” historical data is recomputed.
- The cluster needs nodes with both `transform` and `ingest` roles.
- Use `POST .../slos/{id}/_reset` when an SLO is stuck or after index mapping changes.
- Group-by SLOs create one instance per unique value â€” avoid high-cardinality fields.
- Synthetics SLOs are auto-grouped by monitor and location; do not set `groupBy` manually.
- Burn rate alert rules are not auto-created using the API â€” set them up separately.

## Additional references

For official documentation, refer to the following resources:

### SLO documentation

- [Service-level objectives (SLOs)](https://www.elastic.co/docs/solutions/observability/incident-management/service-level-objectives-slos)
  â€” concepts, SLI types, budgeting methods, and dashboard panels.
- [Create an SLO](https://www.elastic.co/docs/solutions/observability/incident-management/create-an-slo) â€” step-by-step
  guide for creating SLOs in the Kibana UI.
- [View and manage SLOs](https://www.elastic.co/docs/solutions/observability/incident-management/slo-management) â€”
  searching, filtering, and managing existing SLOs.

### Kibana SLO API

- [Create an SLO](https://www.elastic.co/docs/api/doc/kibana/operation/operation-createsloop) â€” full request body schema
  with all SLI type payloads.
- [Get an SLO](https://www.elastic.co/docs/api/doc/kibana/operation/operation-getsloop) |
  [Update](https://www.elastic.co/docs/api/doc/kibana/operation/operation-updatesloop) |
  [Delete](https://www.elastic.co/docs/api/doc/kibana/operation/operation-deletesloop) |
  [Reset](https://www.elastic.co/docs/api/doc/kibana/operation/operation-resetsloop)
- [Enable](https://www.elastic.co/docs/api/doc/kibana/operation/operation-enablesloop) |
  [Disable](https://www.elastic.co/docs/api/doc/kibana/operation/operation-disablesloop) |
  [Get definitions](https://www.elastic.co/docs/api/doc/kibana/operation/operation-getdefinitionsop)

### Troubleshooting and access

- [Troubleshoot SLOs](https://www.elastic.co/docs/troubleshoot/observability/troubleshoot-service-level-objectives-slos)
- [Configure SLO access](https://www.elastic.co/docs/solutions/observability/incident-management/configure-service-level-objective-slo-access)
- [Create an SLO burn rate rule](https://www.elastic.co/docs/solutions/observability/incident-management/create-an-slo-burn-rate-rule)
