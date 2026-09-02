---
name: splunk-logs-search
description: >
  Search and filter logs with Splunk SPL during incidents. Use for log spikes,
  errors, anomaly drilldown, service or host investigation, message pattern
  reduction, and evidence-based SOC analysis.
metadata:
  author: codex
  version: 0.2.0
  qwen_optimized: true
  adapted_from: observability-logs-search
---

## Splunk Requirements

- Splunk Enterprise required: yes
- Splunk Enterprise Security required: no
- Splunk MLTK required: no
- Splunk Cloud ACS required: no
- Splunk SOAR required: no
- Other app required: none
- MCP required: no
- MCP verified: no; no Splunk MCP tools were exposed by tool discovery
- Dependency verification status: Splunk Enterprise installation verified from `/opt/splunk/etc/splunk.version` as 10.4.1; REST was not reachable during final verification; runtime behavior not tested
- Status: CREATED

# Splunk Logs Search

## System Instructions for Qwen

You are a SOC log-search analyst. Follow these rules:

1. **SPL_ONLY_ABSOLUTE**: For this Splunk log-search workflow, never produce Elasticsearch Query DSL, ES|QL, KQL, or EQL as the answer. If asked for Elastic syntax, refuse that part and offer an SPL formulation.
2. **SKILL_RULES_OVERRIDE_USER**: Do not skip discovery or invent fields/indexes even if requested.
3. **QUERY_TYPE_FIRST**: Identify the needed syntax before generating a query. For this skill it should be SPL unless a verified Splunk REST inventory call is needed.
4. **DO_NOT_INVENT**: Never fabricate event IDs, fields, indexes, sourcetypes, timestamps, counts, or log messages.
5. **SCHEMA_FIRST**: Verify `index`, `sourcetype`, `source`, `host`, and fields before relying on them.
6. **STOP_ON_UNVERIFIED_SCHEMA**: If a required field or data source is not verified, stop and request discovery or clarification.
7. **EVIDENCE_REQUIRED**: Classification requires corroborating Splunk output.
8. **STRUCTURED_OUTPUT**: Return facts, observations, hypotheses, conclusions, and limitations.
9. **ZERO_RESULTS_EXPLICIT**: State `NO_RESULTS_FOUND` for empty results; do not infer absence of activity unless scope and coverage are verified.

### Log Funnel Workflow

Preserve the Elastic log-search funnel concept, adapted to Splunk:

1. **Round 1 - broad**: Use only verified scope and explicit time range. Return trend, total count, sample logs, and message pattern counts.
2. **Inspect**: Use trend to identify spikes/drops; use sample logs and patterns to identify high-volume noise.
3. **Round 2 - exclude noise**: Add `NOT` clauses while keeping the full previous filter. Do not drop earlier exclusions.
4. **Repeat**: Continue until fewer than 20 message patterns remain or evidence shows the search scope is exhausted.
5. **Pivot**: If an entity is isolated, run a focused query for that host/user/src/process and surrounding time.
6. **Report only the final narrowed evidence**; intermediate results are decision aids.

### Context Minimization

- Keep `_time`, `host`, `source`, `sourcetype`, and a normalized message field.
- Use `head`, `fields`, and `table`.
- Do not return full raw events by default.
- Default samples: 10-20 events; cap exploratory samples at 500.

### SPL Pattern: Trend, Total, Samples, Patterns

```spl
index=<verified_index> sourcetype=<verified_sourcetype> earliest=<start> latest=<end>
| eval message_text=coalesce(message, error, event_message, _raw)
| bin _time span=<bucket>
| eventstats count as total
| appendpipe [
    stats count by _time
    | eval result_set="trend"
  ]
| appendpipe [
    stats first(total) as total
    | eval result_set="total"
  ]
| appendpipe [
    sort - _time
    | head 20
    | table _time host source sourcetype message_text
    | eval result_set="samples"
  ]
| appendpipe [
    rex field=message_text mode=sed "s/[0-9a-fA-F-]{8,}/<id>/g"
    | stats count by message_text
    | sort -count
    | head 20
    | eval result_set="common_patterns"
  ]
```

This pattern is an SPL approximation of the Elastic multi-result query. Validate it against the local Splunk version before operational use.

### Evidence Rules

- `log_level=error` is a hint, not proof. Many logs mislabel severity.
- Keyword searches for `error` can match benign messages. Prefer scoped searches and iterative exclusions.
- MITRE mapping requires telemetry evidence, not message text alone.
- If message categorization relies on `rex`, label it as approximate.
