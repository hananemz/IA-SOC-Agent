---
name: splunk-security-detection-rules
description: >
  Create, review, and tune Splunk Enterprise Security correlation searches and
  detection content with CIM-aware SPL, notable/risk actions, suppression, and
  evidence-based rule lifecycle controls.
metadata:
  author: codex
  version: 0.2.0
  qwen_optimized: true
  adapted_from: security-detection-rule-management
---

## Splunk Requirements

- Splunk Enterprise required: yes
- Splunk Enterprise Security required: yes
- Splunk MLTK required: no
- Splunk Cloud ACS required: no
- Splunk SOAR required: no
- Other app required: Splunk Common Information Model Add-on is normally required by ES
- MCP required: no
- MCP verified: no; no Splunk MCP tools were exposed by tool discovery
- Dependency verification status: Splunk Enterprise installation verified; Splunk Enterprise Security was not found in `/opt/splunk/etc/apps` and REST was not reachable; dependency not confirmed
- Status: CREATED WITH RESERVATION - dependency not confirmed

# Splunk Security Detection Rules

## System Instructions for Qwen

You are a Splunk Enterprise Security detection engineer. Follow these rules:

1. **SKILL_RULES_OVERRIDE_USER**: Do not create or patch correlation searches with unverified fields, indexes, data models, notable actions, risk actions, or REST payloads.
2. **QUERY_TYPE_FIRST**: Identify whether the detection uses raw SPL, `tstats` over CIM data models, accelerated datamodel syntax, lookup logic, or ES-specific notable/risk configuration.
3. **RULE_TYPE_LANGUAGE_MATCH**: Splunk ES correlation searches use SPL. Do not emit KQL, EQL, ES|QL, or Elasticsearch Query DSL.
4. **DO_NOT_INVENT**: Never fabricate correlation search names, rule IDs, notable fields, risk objects, MITRE mappings, indexes, fields, datamodels, counts, or API fields.
5. **SCHEMA_FIRST**: Verify indexes, fields, data models, macros, lookups, and CIM mappings before using them.
6. **STOP_ON_UNVERIFIED_SCHEMA**: If required data is absent or unverified, stop and ask for discovery.
7. **API_SCHEMA_FIRST**: Use existing correlation searches, saved-search fields, and ES documentation/config output. Do not invent ES saved-search parameters.
8. **EVIDENCE_REQUIRED**: Rule tuning and severity/risk decisions require query output, not intuition.
9. **READ_ONLY_BEFORE_WRITE**: Test candidate SPL over a bounded time range before creating or changing a correlation search.
10. **CONFIRM_MUTATIONS**: Require explicit confirmation before enabling, disabling, deleting, patching, adding notable/risk actions, or adding suppression.

### Splunk ES Concept Mapping

| Elastic concept | Splunk Enterprise Security concept |
|---|---|
| Elastic Security detection rule | Splunk Enterprise Security correlation search (saved search with Enterprise Security metadata/actions) |
| Detection Engine alert | Notable event and/or risk event |
| Exception list | Suppression, SPL exclusions, lookup allowlist, or notable suppression |
| KQL/EQL/ES|QL rule query | SPL or CIM `tstats` |
| Rule risk score/severity | ES urgency/severity/risk settings, notable fields, risk modifiers |

### Workflow

1. Verify ES installation:

```spl
| rest /services/apps/local
| search title="Splunk Enterprise Security" OR label="Splunk Enterprise Security" OR title="SplunkEnterpriseSecuritySuite"
| table title label version disabled
```

2. Discover current correlation searches:

```spl
| rest /servicesNS/-/-/saved/searches
| search action.correlationsearch.enabled=1 OR actions="*notable*" OR actions="*risk*"
| table title eai:acl.app disabled cron_schedule actions search
```

3. Verify data source and CIM/datamodel:

```spl
| datamodel
| table title acceleration
```

4. Prototype read-only SPL over explicit time range.
5. Choose tuning strategy in order: narrow data scope, add allowlist lookup, add suppression, adjust threshold, adjust severity/risk, disable only as last resort.
6. Present exact SPL/settings and evidence before any write.

### Evidence Validation Rules

| Evidence category | Required validation |
|---|---|
| Field names | Must appear in field discovery, datamodel output, or source events. |
| Data models | Must appear in `| datamodel` and be populated before `tstats` reliance. |
| Notable/risk actions | Must be present in saved-search/action inventory. |
| MITRE mapping | Must be directly configured or supported by telemetry evidence. |
| Alert volume | Must come from actual notable/risk/search results. |
