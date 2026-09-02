---
name: elasticsearch-audit
description: >
  Enable, configure, and query Elasticsearch security audit logs. Use when the task
  involves audit logging setup, event filtering, or investigating security incidents
  like failed logins.
metadata:
  author: elastic
  version: 0.1.0`n  qwen_optimized: true
---

# Elasticsearch Audit Logging
## System Instructions for Qwen

You are a SOC analyst specialist. Follow these rules:

1. DO_NOT_INVENT: Never fabricate event IDs, field names, metric values, timestamps, settings, privilege names, APIs, mappings, or security configuration. Unknown values must be verified or clearly marked as assumptions.
2. TOOL_FIRST: Always attempt verification with available MCP tools, Elasticsearch APIs, Kibana APIs, mappings, or cluster metadata before concluding or generating configuration. If no verification is possible, state that explicitly.
3. TOOL_CALL_DISCIPLINE: Validate MCP argument structure before calling tools. Do not send JSON as a string when an object is expected, do not retry identical malformed requests, and do not interpret malformed-request failures as Elasticsearch behavior.
4. VERIFY_USER_VALUES: Treat user-provided index names, field names, event actions, privilege names, APIs, IDs, and configuration values as untrusted until verified. If verification fails, state that the value remains unverified.
5. SCHEMA_FIRST: Always validate field existence before using fields in queries. Run schema discovery.
6. STOP_ON_UNVERIFIED_SCHEMA: Do not generate ES|QL, Query DSL, mappings, ingest pipelines, enrich processors, or DLS queries from unverified fields. If schema verification failed technically, say so.
7. TRANSPARENCY_ON_TOOL_FAILURE: If verification fails technically, distinguish VERIFIED, VERIFIED ABSENT, and NOT VERIFIED; never convert NOT VERIFIED into absence. Assumption-based config must say "This configuration assumes ..." and "Please verify before applying in production."
8. DIAGNOSTIC_DISCIPLINE: Separate verified observations, assumptions, possible causes, and recommended verification steps. Never state a diagnosis as confirmed without evidence.
9. STRUCTURED_OUTPUT: Return results using structured format with facts, observations, hypotheses, conclusions.
10. ZERO_RESULTS_EXPLICIT: State NO_RESULTS_FOUND when queries return empty. Do not speculate.

### Investigation Reasoning Framework

- FACTS: Data directly from tool or query output
- OBSERVATIONS: Patterns or correlations identified in facts
- HYPOTHESES: Possible explanations (label as speculative)
- CONCLUSIONS: Evidence-supported determination requiring >=2 corroborating facts

### Hallucination Guards

| Risk                        | Guard Rail                                              |
|-----------------------------|---------------------------------------------------------|
| Inventing field names       | Schema discovery mandatory before generating queries.   |
| Inventing security config   | Use only verified or documented settings and privileges. |
| Tool failure as evidence    | Mark failed checks NOT VERIFIED, not VERIFIED ABSENT.   |
| Malformed MCP calls         | Fix parameter shape before retrying; never retry same bad payload. |
| Unverified user values      | Verify user-provided names, APIs, IDs, and actions first. |
| Overconfident classification| Default to unknown when evidence is insufficient.       |
| Fabricating metrics         | Use only values from aggregation results.               |
| Speculative MITRE mapping   | Map only with evidence support from telemetry.          |
| Missing source attribution  | Cite schema discovery output for all field references.  |
| Environment failure         | Separate MCP, auth, network, local, unsupported API, and ES config errors. |

### Evidence Validation Rules

| Evidence Category | Validation Check                          |
|-------------------|-------------------------------------------|
| Field names       | Must appear in schema output              |
| Index names       | Must appear in index list output          |
| User values       | Must be verified before use               |
| Tool status       | Technical failure means NOT VERIFIED      |
| Metric values     | Must come from aggregation results        |
| Timestamps        | Must match @timestamp from event source   |
| Alerts            | Must reference real alert IDs from API    |



Enable and configure security audit logging for Elasticsearch via the cluster settings API. Audit logs record security
events such as authentication attempts, access grants and denials, role changes, and API key operations â€” essential for
compliance and incident investigation.

For Kibana audit logging (saved object access, login/logout, space operations), see **kibana-audit**. For authentication
and API key management, see **elasticsearch-authn**. For roles and user management, see **elasticsearch-authz**. For
diagnosing security errors, see **elasticsearch-security-troubleshooting**.

For detailed API endpoints and event types, see [references/api-reference.md](references/api-reference.md).

> **Deployment note:** Audit logging configuration differs across deployment types. See
> [Deployment Compatibility](#deployment-compatibility) for details.

## Jobs to Be Done

- Enable or disable security audit logging on a cluster
- Select which security events to record (authentication, access, config changes)
- Create filter policies to reduce audit log noise
- Query audit logs for failed authentication attempts
- Investigate unauthorized access or privilege escalation incidents
- Set up compliance-focused audit configuration
- Detect brute-force login patterns from audit data
- Configure audit output to an index for programmatic querying

## Prerequisites

| Item                   | Description                                                                |
| ---------------------- | -------------------------------------------------------------------------- |
| **Elasticsearch URL**  | Cluster endpoint (e.g. `https://localhost:9200` or a Cloud deployment URL) |
| **Authentication**     | Valid credentials (see the elasticsearch-authn skill)                      |
| **Cluster privileges** | `manage` cluster privilege to update cluster settings                      |
| **License**            | Audit logging requires a gold, platinum, enterprise, or trial license      |

Prompt the user for any missing values.

## Enable Audit Logging

Enable audit logging dynamically without a restart:

```bash
curl -X PUT "${ELASTICSEARCH_URL}/_cluster/settings" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "xpack.security.audit.enabled": true
    }
  }'
```

To disable, set `xpack.security.audit.enabled` to `false`. Verify current state:

```bash
curl "${ELASTICSEARCH_URL}/_cluster/settings?include_defaults=true&flat_settings=true" \
  <auth_flags> | jq '.defaults | with_entries(select(.key | startswith("xpack.security.audit")))'
```

## Audit Output

Audit events can be written to two outputs. Both can be active simultaneously.

| Output      | Setting value | Description                                                    |
| ----------- | ------------- | -------------------------------------------------------------- |
| **logfile** | `logfile`     | Written to `<ES_HOME>/logs/<cluster>_audit.json`. Default.     |
| **index**   | `index`       | Written to `.security-audit-*` indices. Queryable via the API. |

### Configure output via API

```bash
curl -X PUT "${ELASTICSEARCH_URL}/_cluster/settings" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "xpack.security.audit.enabled": true,
      "xpack.security.audit.outputs": ["index", "logfile"]
    }
  }'
```

The `index` output is required for programmatic querying of audit events. The `logfile` output is useful for shipping to
external SIEM tools via Filebeat.

> **Note:** On self-managed clusters, `xpack.security.audit.outputs` may require a static setting in `elasticsearch.yml`
> on older versions (pre-8.x). On 8.x+, prefer the cluster settings API.

## Select Events to Record

Control which event types are included or excluded. By default, all events are recorded when audit is enabled.

### Include specific events only

```bash
curl -X PUT "${ELASTICSEARCH_URL}/_cluster/settings" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "xpack.security.audit.logfile.events.include": [
        "authentication_failed",
        "access_denied",
        "access_granted",
        "anonymous_access_denied",
        "tampered_request",
        "run_as_denied",
        "connection_denied"
      ]
    }
  }'
```

### Exclude noisy events

```bash
curl -X PUT "${ELASTICSEARCH_URL}/_cluster/settings" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "xpack.security.audit.logfile.events.exclude": [
        "access_granted"
      ]
    }
  }'
```

Excluding `access_granted` significantly reduces log volume on busy clusters â€” use this when only failures matter.

### Event types reference

| Event                     | Fires when                                                 |
| ------------------------- | ---------------------------------------------------------- |
| `authentication_failed`   | Credentials were rejected                                  |
| `authentication_success`  | User authenticated successfully                            |
| `access_granted`          | An authorized action was performed                         |
| `access_denied`           | An action was denied due to insufficient privileges        |
| `anonymous_access_denied` | An unauthenticated request was rejected                    |
| `tampered_request`        | A request was detected as tampered with                    |
| `connection_granted`      | A node joined the cluster (transport layer)                |
| `connection_denied`       | A node connection was rejected                             |
| `run_as_granted`          | A run-as impersonation was authorized                      |
| `run_as_denied`           | A run-as impersonation was denied                          |
| `security_config_change`  | A security setting was changed (role, user, API key, etc.) |

See [references/api-reference.md](references/api-reference.md) for the complete event type list with field details.

## Filter Policies

Filter policies let you suppress specific audit events by user, realm, role, or index without disabling the event type
globally. Multiple policies can be active â€” an event is logged only if **no** policy filters it out.

### Ignore system and internal users

```bash
curl -X PUT "${ELASTICSEARCH_URL}/_cluster/settings" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "xpack.security.audit.logfile.events.ignore_filters": {
        "system_users": {
          "users": ["_xpack_security", "_xpack", "elastic/fleet-server"],
          "realms": ["_service_account"]
        }
      }
    }
  }'
```

### Ignore health-check traffic on specific indices

```bash
curl -X PUT "${ELASTICSEARCH_URL}/_cluster/settings" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "xpack.security.audit.logfile.events.ignore_filters": {
        "health_checks": {
          "users": ["monitoring-user"],
          "indices": [".monitoring-*"]
        }
      }
    }
  }'
```

### Filter policy fields

| Field     | Type          | Description                                          |
| --------- | ------------- | ---------------------------------------------------- |
| `users`   | array[string] | Usernames to exclude (supports wildcards)            |
| `realms`  | array[string] | Realm names to exclude                               |
| `roles`   | array[string] | Role names to exclude                                |
| `indices` | array[string] | Index names or patterns to exclude (supports `*`)    |
| `actions` | array[string] | Action names to exclude (e.g. `indices:data/read/*`) |

An event is filtered out if it matches **all** specified fields within a single policy.

### Remove a filter policy

Set the policy to `null`:

```bash
curl -X PUT "${ELASTICSEARCH_URL}/_cluster/settings" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "xpack.security.audit.logfile.events.ignore_filters.health_checks": null
    }
  }'
```

## Query Audit Events

When the `index` output is enabled, audit events are stored in `.security-audit-*` indices and can be queried.

### Search for failed authentication attempts

```bash
curl -X POST "${ELASTICSEARCH_URL}/.security-audit-*/_search" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "term": { "event.action": "authentication_failed" } },
          { "range": { "@timestamp": { "gte": "now-24h" } } }
        ]
      }
    },
    "sort": [{ "@timestamp": { "order": "desc" } }],
    "size": 50
  }'
```

### Search for access denied events on a specific index

```bash
curl -X POST "${ELASTICSEARCH_URL}/.security-audit-*/_search" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "term": { "event.action": "access_denied" } },
          { "term": { "indices": "logs-*" } },
          { "range": { "@timestamp": { "gte": "now-7d" } } }
        ]
      }
    },
    "sort": [{ "@timestamp": { "order": "desc" } }],
    "size": 20
  }'
```

### Search for security configuration changes

```bash
curl -X POST "${ELASTICSEARCH_URL}/.security-audit-*/_search" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "term": { "event.action": "security_config_change" } },
          { "range": { "@timestamp": { "gte": "now-7d" } } }
        ]
      }
    },
    "sort": [{ "@timestamp": { "order": "desc" } }],
    "size": 50
  }'
```

This captures role creation/deletion, user changes, API key operations, and role mapping updates.

### Count events by type and detect brute-force patterns

Use `terms` aggregations on `event.action` (with `size: 0`) to count events by type over a time window. To detect
brute-force attempts, aggregate `authentication_failed` events by `source.ip` with `min_doc_count: 5`. See
[references/api-reference.md](references/api-reference.md) for full aggregation query examples.

## Correlate with Kibana Audit Logs

Kibana has its own audit log covering application-layer events that Elasticsearch does not see (saved object CRUD,
Kibana logins, space operations). When a user performs an action in Kibana, Kibana makes requests to Elasticsearch on
the user's behalf. Both systems record the same `trace.id` (passed via the `X-Opaque-Id` header), which serves as the
primary correlation key.

> **Prerequisite:** Kibana audit must be enabled separately in `kibana.yml`. See the **kibana-audit** skill for setup
> instructions, event types, and Kibana-specific filter policies.

### Find ES audit events triggered by a Kibana action

Given a `trace.id` from a Kibana audit event, search the ES audit index to see the underlying Elasticsearch operations:

```bash
curl -X POST "${ELASTICSEARCH_URL}/.security-audit-*/_search" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "term": { "trace.id": "'"${TRACE_ID}"'" } },
          { "range": { "@timestamp": { "gte": "now-24h" } } }
        ]
      }
    },
    "sort": [{ "@timestamp": { "order": "asc" } }]
  }'
```

### Correlate by user and time window

When `trace.id` is unavailable (e.g. direct API calls), fall back to user + time-window correlation:

```bash
curl -X POST "${ELASTICSEARCH_URL}/.security-audit-*/_search" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "term": { "user.name": "'"${USERNAME}"'" } },
          { "range": { "@timestamp": { "gte": "now-5m" } } }
        ]
      }
    },
    "sort": [{ "@timestamp": { "order": "asc" } }]
  }'
```

Secondary correlation fields: `user.name`, `source.ip`, and `@timestamp`.

### Unified querying

Ship Kibana audit logs to Elasticsearch via Filebeat (see **kibana-audit** for the Filebeat config) so that both
`.security-audit-*` (ES) and `kibana-audit-*` (Kibana) indices can be searched together in a single multi-index query
filtered by `trace.id`.

## Examples

### Enable audit logging for compliance

**Request:** "Enable audit logging and record all failed access and authentication events."

```bash
curl -X PUT "${ELASTICSEARCH_URL}/_cluster/settings" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "xpack.security.audit.enabled": true,
      "xpack.security.audit.logfile.events.include": [
        "authentication_failed",
        "access_denied",
        "anonymous_access_denied",
        "run_as_denied",
        "connection_denied",
        "tampered_request",
        "security_config_change"
      ]
    }
  }'
```

This captures all denial and security change events while excluding high-volume success events.

### Investigate a suspected unauthorized access attempt

**Request:** "Someone may have tried to access the `secrets-*` index. Check the audit logs."

```bash
curl -X POST "${ELASTICSEARCH_URL}/.security-audit-*/_search" \
  <auth_flags> \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "terms": { "event.action": ["access_denied", "authentication_failed"] } },
          { "wildcard": { "indices": "secrets-*" } },
          { "range": { "@timestamp": { "gte": "now-48h" } } }
        ]
      }
    },
    "sort": [{ "@timestamp": { "order": "desc" } }],
    "size": 100
  }'
```

Review `user.name`, `source.ip`, and `event.action` in the results to identify the actor and pattern.

### Reduce audit noise on a busy cluster

**Request:** "Audit logs are too large. Filter out monitoring traffic and successful reads."

Exclude `access_granted` from event types, then add a filter policy for monitoring users and indices. See
[Filter Policies](#filter-policies) for the full syntax.

## Guidelines

### Prefer index output for programmatic access

Enable the `index` output to make audit events queryable. The `logfile` output is better for shipping to external SIEM
tools via Filebeat but cannot be queried through the Elasticsearch API.

### Start restrictive, then widen

Begin with failure events only (`authentication_failed`, `access_denied`, `security_config_change`). Add success events
only when needed â€” they generate high volume.

### Use filter policies instead of disabling events

Suppress specific users or indices with filter policies rather than excluding entire event types.

### Monitor audit index size

Set up an ILM policy to roll over and delete old `.security-audit-*` indices. A 30-90 day retention is typical.

### Enable Kibana audit for full coverage

For application-layer events (saved object access, Kibana logins, space operations), enable Kibana audit logging as
well. See the **kibana-audit** skill for setup. Use `trace.id` to correlate â€” see
[Correlate with Kibana Audit Logs](#correlate-with-kibana-audit-logs) above.

### Avoid superuser credentials

Use a dedicated admin user or API key with `manage` privileges. Reserve `elastic` for emergency recovery only.

## Deployment Compatibility

| Capability                           | Self-managed | ECH          | Serverless    |
| ------------------------------------ | ------------ | ------------ | ------------- |
| ES audit via cluster settings        | Yes          | Yes          | Not available |
| ES logfile output                    | Yes          | Via Cloud UI | Not available |
| ES index output                      | Yes          | Yes          | Not available |
| Filter policies via cluster settings | Yes          | Yes          | Not available |
| Query `.security-audit-*`            | Yes          | Yes          | Not available |

**ECH notes:** ES audit is configured via the cluster settings API. Logfile output is accessible through the Cloud
console deployment logs. Index output works the same as self-managed.

**Serverless notes:**

- Audit logging is not user-configurable on Serverless. Security events are managed by Elastic as part of the platform.
- If a user asks about auditing on Serverless, direct them to the Elastic Cloud console or their account team.
