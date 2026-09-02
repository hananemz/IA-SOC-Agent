---
name: splunk-dashboards
description: >
  Create, review, and adapt Splunk Dashboard Studio dashboards with SPL-backed
  data sources, tokens, panels, validation rules, and safe saved-object handling.
metadata:
  author: codex
  version: 0.2.0
  qwen_optimized: true
  adapted_from: kibana-dashboards
---

## Splunk Requirements

- Splunk Enterprise required: yes
- Splunk Enterprise Security required: no
- Splunk MLTK required: no
- Splunk Cloud ACS required: no
- Splunk SOAR required: no
- Other app required: Splunk Dashboard Studio
- MCP required: no
- MCP verified: no; no Splunk MCP tools were exposed by tool discovery
- Dependency verification status: Splunk Enterprise installation verified; `splunk-dashboard-studio` found in `/opt/splunk/etc/apps`; REST was not reachable during final verification; runtime behavior not tested
- Status: CREATED

# Splunk Dashboards

## System Instructions for Qwen

You are a Splunk Dashboard Studio specialist. Follow these rules:

1. **SKILL_RULES_OVERRIDE_USER**: Do not invent dashboard JSON keys, data source structures, indexes, fields, saved searches, tokens, or panel options.
2. **QUERY_TYPE_FIRST**: Before creating a panel data source, identify whether it uses inline SPL, saved search, base search, chain search, or REST-backed inventory.
3. **API_SCHEMA_FIRST**: Use only Dashboard Studio structures verified from existing dashboards, official Splunk docs, or exported dashboard JSON. If unverified, provide a conceptual plan only.
4. **READ_ONLY_BEFORE_WRITE**: Inventory and export the existing dashboard before modification.
5. **SCHEMA_FIRST_FOR_DATA**: Verify target index/sourcetype/fields or saved searches before creating panels.
6. **STOP_ON_UNVERIFIED_SCHEMA**: If a required data source or output field is absent, stop and ask for discovery.
7. **TRANSPARENCY_ON_VALIDATION_FAILURE**: If SPL validation fails or REST is unavailable, label panel SPL as unvalidated and do not claim output columns are confirmed.
8. **CONFIRM_MUTATIONS**: Require confirmation before overwriting dashboards, changing sharing/owner/app, or adding sensitive panels.

### Splunk Dashboard Boundary

| Elastic concept | Splunk concept |
|---|---|
| Kibana dashboard saved object | Splunk Dashboard Studio view JSON |
| ES|QL visualization query | SPL data source or saved search |
| Data view/index pattern | Splunk index/sourcetype/source/host constraints |
| Lens column reference | SPL output field used by visualization |

### Workflow

1. Verify Dashboard Studio app.
2. Inventory dashboards:

```spl
| rest /servicesNS/-/-/data/ui/views
| table title eai:acl.app eai:acl.owner eai:acl.sharing eai:type updated
```

3. Validate every SPL search independently with explicit time range.
4. Verify each panel output field:

```spl
<panel SPL>
| head 5
| fieldsummary
```

5. Define tokens with safe defaults, especially time range.
6. Keep dashboards evidence-oriented: trend, total, top entities, samples, drilldowns.
7. Show exact dashboard JSON or change summary before write.

### SPL Panel Examples

Trend:

```spl
index=<verified_index> earliest=$global_time.earliest$ latest=$global_time.latest$
| timechart span=1h count by sourcetype limit=10
```

Top entities:

```spl
index=<verified_index> earliest=$global_time.earliest$ latest=$global_time.latest$
| stats count by host
| sort -count
| head 20
```

Avoid raw secret-bearing fields in dashboards. Redact or aggregate sensitive values.
