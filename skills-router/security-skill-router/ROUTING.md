# Deterministic routing reference

## Task selection

Select the narrowest actual skill after platform identification:

| Task signal | Splunk skill | Elastic skill |
|---|---|---|
| security alert, notable event, Incident Review | `splunk-security-alert-triage` | `security-alert-triage` |
| detection rule, correlation search | `splunk-security-detection-rules` | `security-detection-rule-management` |
| case or investigation record | `splunk-security-case-management` | `security-case-management` |
| SPL/search or ES|QL search | `splunk-search` | `elasticsearch-esql` |
| logs, errors, volume, service investigation | `splunk-logs-search` | `observability-logs-search` |
| audit, `_audit`, `_internal` | `splunk-audit` | `elasticsearch-audit` or `kibana-audit` as applicable |
| authentication | `splunk-authentication` | `elasticsearch-authn` |
| authorization, roles, permissions | `splunk-authorization` | `elasticsearch-authz` |
| dashboards | `splunk-dashboards` | `kibana-dashboards` |
| anomaly detection / MLTK | `splunk-mltk-anomaly-detection` | `kibana-anomaly-detection` |
| saved searches / Splunk alerts | `splunk-alerting` | `kibana-alerting-rules` |
| troubleshooting | `splunk-security-troubleshooting` | `elasticsearch-security-troubleshooting` |

Only names present in `skill-registry.yaml` may be selected. The registry paths are absolute Windows paths and must be checked before execution.

## Cross-platform mode

Use cross-platform mode only for an explicit Elastic + Splunk comparison, correlation, or investigation. Execute separate platform branches, label evidence by platform, preserve each platform's schema, and keep queries isolated. Do not translate queries implicitly. Validate target schemas before any explicitly requested translation.

## Mutation and evidence gates

Read-only verification precedes mutations. Mutating work requires explicit confirmation. A Splunk detection-rule request requires Enterprise Security verification; with the current `NOT VERIFIED` dependency status, return `NOT VERIFIED` and do not claim creation. Alert and case identifiers are candidates until verified.

## Local RAG boundary

The optional local RAG layer is a retrieval aid over local router and skill
files. It runs after deterministic platform/task routing and returns
`rag_status: LOCAL_OPTIONAL` plus local source references when used. The
separate SOC Analyst RAG supplies provider-independent security reasoning and
source-attributed guidance; it does not select a platform or create evidence.
Neither RAG can route an ambiguous request, change the selected skill,
establish backend availability, or replace schema/MCP/dependency verification.
