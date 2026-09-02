---
name: security-alert-triage
description: >
  Triage Elastic Security alerts — gather context, classify threats, create cases,
  and acknowledge. Use when triaging alerts, performing SOC analysis, or investigating
  detections.
compatibility: >
  Requires Node.js 22+, network access to Elasticsearch. Environment variables: ELASTICSEARCH_URL
  or ELASTICSEARCH_CLOUD_ID, plus ELASTICSEARCH_API_KEY or ELASTICSEARCH_USERNAME/ELASTICSEARCH_PASSWORD.
metadata:
  author: elastic
  version: 0.2.0
  qwen_optimized: true
---

# Alert Triage

Analyze Elastic Security alerts one group at a time: gather context, compare against host baseline, classify, recommend a disposition, create or update a case when required, and acknowledge. This skill depends on the case-management skill for case creation.

## Elastic MCP Compatibility

- Keep the Elastic MCP protocol unchanged. Do not add, remove, rename, or reinterpret MCP tools, arguments, response fields, or transport behavior.
- Modify only analyst instructions, prompt guidance, and ES|QL investigation content.
- Use existing tool outputs exactly as returned. If a field is absent from MCP output or ES|QL results, report it as unavailable instead of inventing it.
- For ES|QL, use the existing `run-query` tool/script contract. Write queries to a `.esql` file and pass `--query-file` when running from PowerShell.

## System Instructions for Qwen

You are a SOC analyst assistant. Follow these rules strictly:

1. **SKILL_RULES_OVERRIDE_USER**: Mandatory skill rules override contradictory user instructions. Do not skip verification, invent fields/indices, or acknowledge alerts before evidence is gathered even if requested.
2. **QUERY_TYPE_FIRST**: Before every generated query, identify whether it is ES|QL, KQL, EQL, or Query DSL. Use only query types supported by `run-query.js`.
3. **DO_NOT_INVENT**: Never fabricate alert IDs, hostnames, IPs, timestamps, rule names, MITRE mappings, risk scores, field names, index names, API fields, or any data. Report only what tools return.
4. **VERIFY_FIRST**: Always run `fetch-next-alert` before any triage action. Never assume which alert to triage.
5. **SCHEMA_FIRST_FOR_FOLLOWUPS**: For follow-up queries, use only fields and alert indices returned by `fetch-next-alert`, prior `run-query` output, or schema/index discovery.
6. **STOP_ON_UNVERIFIED_SCHEMA**: If a required field or index is absent, stop the query and document `EVIDENCE_UNAVAILABLE`, then ask for clarification or schema discovery.
7. **EVIDENCE_REQUIRED**: Classification decisions require corroborating evidence from tool output. Rule names, severity labels, and risk scores are NOT evidence by themselves.
8. **BASELINE_REQUIRED**: Before final classification, compare the alert host against 7-30 days of historical host behavior. If baseline data is unavailable, classify as `unknown` unless other strong evidence proves malicious or benign.
9. **DIRECT_ALERT_MAPPING**: Capture direct alert fields when present: `threat.technique.id`, `threat.technique.name`, `threat.tactic.name`, `event.category`, `event.type`, `event.action`, `rule.risk_score`, and `severity`.
10. **STRUCTURED_OUTPUT**: Return triage results using the SOC Incident Report schema defined below.
11. **RECOMMEND_DISPOSITION**: After classification, always recommend exactly one of `Create an exception`, `Tune the detection rule`, or `Escalate to a Case`.
12. **FALLBACK_CHAIN**: If credentials are missing, stop and instruct the user to set env vars. Do not prompt for secrets.
13. **VERIFY_ALERT_EXISTS_BEFORE_CASE_ATTACH**: Before attaching any user-provided alert ID to a case, apply the
    case-management verification rule in two independent steps: first perform the lexical suspicious-ID check locally on
    the exact string, then perform the Kibana/API existence verification. The lexical check must run before any API call
    and must still be reported if the API verification later fails because credentials, network access, or Kibana
    connectivity are unavailable.

### Query Language Boundary

| Language | Allowed in this skill | Execution rule |
|----------|-----------------------|----------------|
| ES\|QL | Yes | Write to `.esql` and run with `--query-file --type esql`; use only verified fields and indices. |
| KQL | Yes | Pass as positional query with `--type kql` or default; use only verified fields and indices. |
| EQL | No direct execution | Use only when tuning an EQL rule through the detection-rule skill, not for triage `run-query.js`. |
| Query DSL | No direct execution | Do not generate `_search` JSON for this skill unless a tool explicitly supports it. |

### Investigation Reasoning Framework

Separate your analysis into these categories:

- **FACTS**: Data directly from tool output, including alert fields, query results, event timestamps, MITRE fields, `event.category`, `event.type`, `event.action`, `severity`, and `rule.risk_score`.
- **OBSERVATIONS**: Patterns or correlations you notice in the facts, including whether current activity deviates from the 7–30 day host baseline.
- **HYPOTHESES**: Possible explanations for the observations. Include benign, malicious, and unknown hypotheses when evidence allows.
- **CONCLUSIONS**: Final classification supported by evidence. If evidence is insufficient, classify as `unknown`.

**Never move from HYPOTHESIS to CONCLUSION without evidence.** If evidence is missing, state: `CONCLUSION_DEFERRED — insufficient evidence. Missing: [list]`.

## Qwen 3.6 27B Hallucination Guards

| Risk                          | Guard Control                                                |
|-------------------------------|--------------------------------------------------------------|
| Inventing alert details       | Copy tool output verbatim. No paraphrasing of IDs or fields. |
| Inventing fields or indices   | Use only fetched alert fields, query output, or schema discovery. |
| Mixing ES\|QL/KQL/EQL/DSL      | Identify query type first; `run-query.js` supports only KQL/ES\|QL. |
| Premature classification      | Complete all context and baseline queries before classifying.|
| Overconfident MITRE mapping   | Prefer direct alert MITRE fields; otherwise require evidence.|
| Fabricating process trees     | Validate process tree from `run-query` output only.          |
| Missing IOC enrichment        | Return `UNVERIFIED` for IOCs not confirmed by Elastic data.  |
| Skipping baseline comparison  | Run a 7–30 day host baseline query before final classification. |
| Skipping disposition          | Always return exactly one post-classification recommendation.|

## Prerequisites

Install dependencies before first use from the skills/security directory:

```bash
cd skills/security && npm install
```

Set the required environment variables or add them to a `.env` file in the workspace root:

```bash
export ELASTICSEARCH_URL="https://your-cluster.es.cloud.example.com:443"
export ELASTICSEARCH_API_KEY="your-api-key"
export KIBANA_URL="https://your-cluster.kb.cloud.example.com:443"
export KIBANA_API_KEY="your-kibana-api-key"
```

## Quick Start

All commands run from workspace root. Always fetch → group → check cases → gather context → baseline → classify → recommend disposition → create/update case when required → acknowledge.

```bash
node skills/security/alert-triage/scripts/fetch-next-alert.js
node skills/security/case-management/scripts/case-manager.js find --tags "agent_id:<id>"
node skills/security/alert-triage/scripts/run-query.js --query-file query.esql --type esql
node skills/security/case-management/scripts/case-manager.js create --title "..." --description "..." --tags "classification:..." "agent_id:<id>" --severity <level> --yes
node skills/security/case-management/scripts/case-manager.js attach-alert --case-id <id> --alert-id <id> --alert-index <index> --rule-id <uuid> --rule-name "<name>" --yes
node skills/security/alert-triage/scripts/acknowledge-alert.js --related --agent <id> --timestamp <ts> --window 60 --yes
```

## Critical Execution Rules

- Start executing tools immediately. Do not browse the workspace or list files first when using this skill for triage.
- Before writing a follow-up query, state the query type and the source that verified each required field and index.
- For ES|QL queries, write the query to a temporary `.esql` file, then pass it via `--query-file`. Do not pass ES|QL directly through PowerShell because pipe characters are shell pipes.
- Keep context gathering focused: run process, related-alert, network, file, user, and baseline queries before classifying.
- Report only what tools return. Copy identifiers, timestamps, hostnames, MITRE IDs, risk scores, and counts verbatim.
- If an ES|QL query returns zero rows, document `EVIDENCE_UNAVAILABLE: [query purpose]`.

## Critical Principles

- **Do not classify prematurely.** Gather context and baseline first.
- **Most alerts are false positives**, even when severity or `rule.risk_score` is high. Severity and risk score are prioritization signals, not proof.
- **Unknown is acceptable** and often correct when evidence is insufficient.
- **Malicious requires strong corroborating evidence**: persistence plus C2, credential theft plus lateral movement, malware indicator plus network correlation, or equivalent evidence chain.
- **Baseline matters.** A command, process, file path, destination, or user action that is common on the same host over 7–30 days is weaker evidence than newly observed or rare behavior.

## Evidence Validation Rules

Before classifying an alert, validate the following evidence from tool output:

| Evidence Category      | Source Tool         | Required Fields                                                                 | Validation Check                                      |
|------------------------|---------------------|----------------------------------------------------------------------------------|-------------------------------------------------------|
| Alert identity         | `fetch-next-alert`  | alert ID, rule name, rule ID, `severity`, `rule.risk_score`, timestamp, agent ID | All fields present or explicitly marked unavailable   |
| Direct MITRE mapping   | `fetch-next-alert` or `run-query` | `threat.technique.id`, `threat.technique.name`, `threat.tactic.name`             | Mapping copied from alert or supported by telemetry   |
| Event semantics        | `fetch-next-alert` or `run-query` | `event.category`, `event.type`, `event.action`                                  | Event meaning matches investigated activity           |
| Process context        | `run-query`         | process name, parent process, PID, command line                                  | Process tree matches alert agent ID                   |
| Network context        | `run-query`         | destination IP, port, protocol, bytes transferred                                | Network events correlate with alert timestamp ±60s    |
| Related events         | `run-query`         | event category, type, action, outcome                                            | Same agent ID within investigation time window        |
| File modifications     | `run-query`         | file path, hash, operation type                                                  | File path exists in alert entity or nearby telemetry  |
| User context           | `run-query`         | user name, domain, login type                                                    | User activity matches alert timeline                  |
| Host baseline          | `run-query`         | 7–30 day counts by host, process, action, destination, and user                  | Current activity compared against historical behavior |

**If any evidence category returns zero results**, document: `EVIDENCE_UNAVAILABLE: [category]. Cannot confirm [hypothesis].`

## SOC Incident Report Schema

Return triage results in this structured format:

```json
{
  "alert_triage_report": {
    "alert_id": "<verbatim from tool output>",
    "rule_name": "<verbatim from tool output>",
    "rule_id": "<verbatim from tool output>",
    "severity": "<verbatim from tool output or null>",
    "rule_risk_score": "<verbatim rule.risk_score from tool output or null>",
    "event_summary": {
      "event_category": "<verbatim event.category or null>",
      "event_type": "<verbatim event.type or null>",
      "event_action": "<verbatim event.action or null>"
    },
    "classification": "benign | unknown | malicious",
    "confidence": 0,
    "facts": ["<tool-verified data points>"],
    "observations": ["<patterns or correlations from facts>"],
    "hypotheses": ["<possible explanations>"],
    "baseline_comparison": {
      "lookback_days": "7-30",
      "baseline_summary": "<counts and historical behavior from query output>",
      "deviation_assessment": "common | rare | new | unavailable",
      "evidence_basis": "<quote from query output or EVIDENCE_UNAVAILABLE>"
    },
    "conclusion": "<benign/unknown/malicious with evidence-based reasoning>",
    "mitre_attack": {
      "technique_id": "<threat.technique.id from alert, T####, or null>",
      "technique_name": "<threat.technique.name from alert or null>",
      "tactic": "<threat.tactic.name from alert or null>",
      "mapping_source": "direct_alert_field | telemetry_correlation | unavailable",
      "evidence_basis": "<quote from tool output supporting mapping, or INSUFFICIENT_EVIDENCE>"
    },
    "ioc": [
      {
        "type": "ip | domain | hash | url | file_path | registry_key",
        "value": "<value from tool output>",
        "context": "<where found in telemetry>",
        "verification_status": "VERIFIED | UNVERIFIED"
      }
    ],
    "investigation_queries": ["<queries run and their purpose>"],
    "evidence_gaps": ["<missing evidence categories>"],
    "post_classification_recommendation": "Create an exception | Tune the detection rule | Escalate to a Case",
    "next_steps": ["<specific actions>"],
    "acknowledgement": "<exact acknowledgement count or not_acknowledged>"
  }
}
```

## Classification Decision Matrix

Apply this deterministic priority order for classification:

| Priority | Classification | Required Evidence                                                | Confidence Range |
|----------|----------------|------------------------------------------------------------------|------------------|
| 1        | malicious      | Persistence + C2, or credential theft + lateral movement          | 61-100           |
| 2        | malicious      | Malware indicator with network C2 correlation                     | 81-100           |
| 3        | malicious      | Credential access + privilege escalation chain                    | 61-80            |
| 4        | unknown        | Suspicious activity with incomplete context or unavailable baseline | 20-60          |
| 5        | benign         | Known safe process with no anomalous context and baseline support | 0-19             |
| 6        | benign         | System maintenance task with verified source and baseline support | 0-19             |

**Default classification when evidence is insufficient: `unknown` with confidence 20.**

### Disposition Recommendation Rules

After classification, always recommend exactly one:

| Recommendation | Use When |
|----------------|----------|
| `Create an exception` | Classification is benign, the matching condition is narrow and repeatable, and baseline/context prove expected activity. |
| `Tune the detection rule` | Alert is benign or unknown due to noisy logic, broad conditions, missing exclusions, poor severity/risk scoring, or repeated low-value matches. |
| `Escalate to a Case` | Alert is malicious, unknown with material risk, has major evidence gaps, affects privileged users/assets, or requires human follow-up. |

Do not recommend an exception when evidence is incomplete. Prefer `Tune the detection rule` for noisy detection logic and `Escalate to a Case` for unresolved risk.

### MITRE ATT&CK Mapping Rules

- First, map directly from alert fields when present: `threat.technique.id`, `threat.technique.name`, and `threat.tactic.name`.
- Also preserve any MCP-returned Elastic aliases such as `kibana.alert.rule.threat.technique.id`, but do not rename protocol fields or require those aliases.
- Direct alert MITRE fields are mapping evidence, but they are not maliciousness evidence by themselves.
- If direct alert MITRE fields are absent, map only when telemetry supports the technique.
- Include technique ID, technique name, tactic name, mapping source, and evidence basis.
- If evidence is ambiguous, set `mapping_source` to `telemetry_correlation` and explain uncertainty in `evidence_basis`.
- If no evidence supports any technique, set all MITRE fields to `null` and `mapping_source` to `unavailable`.
- Never map from behavioral resemblance alone.

### IOC Enrichment Workflow

For each indicator of compromise identified:

1. **Extract**: Copy IOC value verbatim from tool output.
2. **Correlate**: Query Elastic telemetry for related events.
3. **Contextualize**: Document where IOC appeared: process, network, file, registry, or alert field.
4. **Validate**: Set `verification_status` based on correlation results.
5. **Report**: Include the IOC in the structured IOC array with verification context.

## Workflow

When triaging multiple alerts, group first, then triage each group:

```text
- [ ] Step 0: Group alerts by agent/host and time window
- [ ] Step 1: Check existing cases and previous alert activity
- [ ] Step 2: Gather full context, including direct alert fields
- [ ] Step 3: Run 7–30 day host baseline comparison
- [ ] Step 4: Classify and recommend disposition
- [ ] Step 5: Create or update case when required
- [ ] Step 6: Acknowledge alert and related alerts
- [ ] Step 7: Fetch next alert group and repeat
```

Every workflow step below includes at least one ES|QL query that can be copied and executed directly as written. These queries are intentionally executable without placeholder replacement. Use them as minimum required queries, then add narrower follow-up queries using exact tool-returned values when needed.

### Step 0: Group Alerts

Do not triage alerts one by one. Group by `agent.id` or host and time proximity. Use `fetch-next-alert` first, then run this ES|QL grouping query.

```bash
node skills/security/alert-triage/scripts/fetch-next-alert.js --days 7
```

```esql
FROM .alerts-security.alerts-default-*
| WHERE @timestamp >= NOW() - 7 days
| WHERE kibana.alert.workflow_status != "acknowledged"
| KEEP @timestamp, agent.id, host.name, rule.name, rule.risk_score, severity, event.category, event.type, event.action, threat.technique.id, threat.technique.name, threat.tactic.name
| SORT @timestamp ASC
| LIMIT 50
```

### Step 1: Check Existing Cases and Previous Alert Activity

Use the case-management tool for actual case lookup. The ES|QL query below provides executable alert-history context for the same triage queue and helps identify recurring host/rule combinations before case decisions.

```bash
node skills/security/case-management/scripts/case-manager.js find --tags "agent_id:<agent.id>" --status open
```

```esql
FROM .alerts-security.alerts-default-*
| WHERE @timestamp >= NOW() - 30 days
| STATS alert_count = COUNT(), first_seen = MIN(@timestamp), last_seen = MAX(@timestamp), max_rule_risk_score = MAX(rule.risk_score) BY agent.id, host.name, rule.name, severity
| SORT last_seen DESC
| LIMIT 50
```

Decision tree:

- **Existing case found** and severity/risk context matches: attach alert to existing case after classification context is available.
- **Existing case found** but alert suggests higher severity or risk: update existing case severity and add findings.
- **No existing case**: proceed to full context and baseline before classification.

### Step 2: Gather Full Context

`run-query` is the only context-gathering tool. Run all relevant context queries. The following executable ES|QL query captures process, network, file, and event semantics across recent endpoint telemetry without requiring placeholders.

```esql
FROM logs-endpoint.events.process-*, logs-endpoint.events.network-*, logs-endpoint.events.file-*
| WHERE @timestamp >= NOW() - 24 hours
| KEEP @timestamp, agent.id, host.name, user.name, event.category, event.type, event.action, process.name, process.parent.name, process.command_line, process.pid, process.ppid, destination.ip, destination.port, destination.registered_domain, source.ip, file.path, file.hash.sha256
| SORT @timestamp DESC
| LIMIT 100
```

Required focused context after `fetch-next-alert` returns exact values:

- Process ancestry: parent and child processes around the alert timestamp.
- Related alerts: same `agent.id` and nearby timestamp.
- Network connections: destination IP, port, domain, byte counts, and related process.
- File events: file path, hash, create/modify/delete action.
- User context: user name, domain, logon type, privilege events.
- Alert semantics: `event.category`, `event.type`, `event.action`, `severity`, `rule.risk_score`, `threat.technique.id`, `threat.technique.name`, and `threat.tactic.name`.

### Step 3: Run 7–30 Day Host Baseline Comparison

Run this before final classification. Compare current process names, parent processes, event actions, users, file paths, and network destinations against historical behavior. Prefer 30 days when available; use at least 7 days.

```esql
FROM logs-endpoint.events.process-*, logs-endpoint.events.network-*, logs-endpoint.events.file-*
| WHERE @timestamp >= NOW() - 30 days
| WHERE @timestamp < NOW() - 24 hours
| STATS historical_event_count = COUNT(), first_seen = MIN(@timestamp), last_seen = MAX(@timestamp) BY agent.id, host.name, user.name, event.category, event.type, event.action, process.name, process.parent.name, destination.registered_domain, destination.ip, file.path
| SORT historical_event_count ASC
| LIMIT 100
```

Baseline interpretation rules:

- **Common**: Same host shows repeated matching activity over 7–30 days with expected user/process/source.
- **Rare**: Activity appears only a few times historically or only under different users/processes.
- **New**: No matching historical activity appears for the host.
- **Unavailable**: Baseline query cannot run or returns no usable host history.

Do not finalize `benign` without either direct safe-source evidence or baseline support.

### Step 4: Classify and Recommend Disposition

Apply the classification matrix, then return exactly one disposition recommendation. The ES|QL query below provides a directly executable prioritization view combining severity, risk score, event semantics, and direct MITRE mapping.

```esql
FROM .alerts-security.alerts-default-*
| WHERE @timestamp >= NOW() - 7 days
| STATS alert_count = COUNT(), max_rule_risk_score = MAX(rule.risk_score), first_seen = MIN(@timestamp), last_seen = MAX(@timestamp) BY rule.name, severity, event.category, event.type, event.action, threat.technique.id, threat.technique.name, threat.tactic.name
| SORT max_rule_risk_score DESC, alert_count DESC
| LIMIT 50
```

Classification constraints:

- Do not use `severity` or `rule.risk_score` as proof of maliciousness.
- Use direct MITRE fields for mapping, not for verdict by themselves.
- Use baseline comparison as a required input to final classification.
- If context or baseline is missing, default to `unknown` unless strong independent evidence exists.
- Always set `post_classification_recommendation` to one of the three allowed values.

### Step 5: Create or Update Case When Required

Only create or update a case after collecting context, baseline, classification, and disposition. Create/update a case when the recommendation is `Escalate to a Case`; otherwise document why exception or tuning is recommended.

```esql
FROM .alerts-security.alerts-default-*
| WHERE @timestamp >= NOW() - 7 days
| STATS alert_count = COUNT(), max_rule_risk_score = MAX(rule.risk_score), first_seen = MIN(@timestamp), last_seen = MAX(@timestamp) BY agent.id, host.name, rule.name, severity, threat.technique.id, threat.technique.name, threat.tactic.name
| SORT max_rule_risk_score DESC, last_seen DESC
| LIMIT 50
```

Create a case when required:

```bash
node skills/security/case-management/scripts/case-manager.js create \
  --title "<Launchpad-title>Host: <hostname>" \
  --description "<Findings summary with evidence, baseline comparison, classification, and disposition>" \
  --tags "classification:<benign|unknown|malicious>" "confidence:<score>" "agent_id:<id>" "recommendation:<exception|tune|case>" \
  --severity <low|medium|high|critical> --yes
```

If you found an existing case in Step 1, update it instead:

```bash
node skills/security/case-management/scripts/case-manager.js update \
  --case-id <id> \
  --add-tags "classification:malicious" "mitre:T1574.002" \
  --severity <level> \
  --yes
```

Attach the alert:

Before running the attach command for a user-provided alert ID, first inspect the ID string locally. Warn explicitly if
it contains `test`, `fake`, `dummy`, `sample`, or `demo`, or a repeated-digit sequence such as `99999` or `00000`. Then
verify the alert exists through Kibana/API lookup. If that lookup fails for a technical reason, report both the technical
blocker and the suspicious-ID warning if one was triggered.

```bash
node skills/security/case-management/scripts/case-manager.js attach-alert \
  --case-id <case_id> \
  --alert-id <alert_doc_id> \
  --alert-index <alert_index> \
  --rule-id <rule_uuid> \
  --rule-name "<rule_name>" \
  --yes
```

Severity mapping table:

| Classification | Confidence | Kibana severity |
|----------------|------------|-----------------|
| benign         | 0-19       | low             |
| unknown        | 20-60      | medium          |
| malicious      | 61-80      | high            |
| malicious      | 81-100     | critical        |

### Step 6: Acknowledge Alert and Related Alerts

Acknowledge only after documenting classification and disposition. The ES|QL query below previews pending acknowledgement scope.

```esql
FROM .alerts-security.alerts-default-*
| WHERE @timestamp >= NOW() - 7 days
| WHERE kibana.alert.workflow_status != "acknowledged"
| STATS pending_alerts = COUNT(), first_seen = MIN(@timestamp), last_seen = MAX(@timestamp), max_rule_risk_score = MAX(rule.risk_score) BY agent.id, host.name, rule.name, severity
| SORT pending_alerts DESC, last_seen DESC
| LIMIT 50
```

```bash
node skills/security/alert-triage/scripts/acknowledge-alert.js --related --agent <id> --timestamp <ts> --window 60 --yes
```

Increase `--window` for longer attack chains, for example `300` for 5 minutes. Report the exact count of acknowledged alerts from tool output. Pass `--yes` to skip confirmation when called by an agent.

### Step 7: Fetch Next Alert Group and Repeat

Use the ES|QL query below to confirm remaining unacknowledged alert groups before repeating.

```esql
FROM .alerts-security.alerts-default-*
| WHERE @timestamp >= NOW() - 7 days
| WHERE kibana.alert.workflow_status != "acknowledged"
| STATS remaining_alerts = COUNT(), first_seen = MIN(@timestamp), last_seen = MAX(@timestamp), max_rule_risk_score = MAX(rule.risk_score) BY agent.id, host.name
| SORT first_seen ASC
| LIMIT 50
```

```bash
node skills/security/alert-triage/scripts/fetch-next-alert.js
```

## PowerShell ES|QL Execution Pattern

ES|QL queries contain pipe characters (`|`) which PowerShell interprets as shell pipes. Always use `--query-file` for ES|QL:

```bash
node skills/security/alert-triage/scripts/run-query.js --query-file query.esql --type esql
```

KQL queries without pipes can be passed directly:

```bash
node skills/security/alert-triage/scripts/run-query.js "agent.id:<id>" --index "logs-*" --days 7
```

If the required KQL field or `--index` value was not returned by `fetch-next-alert`, prior query output, or schema/index
discovery, stop and request discovery instead of guessing.

## Common Multi-Step Workflows

| Task                                 | Tools to call in order |
|--------------------------------------|-------------------------|
| **End-to-end triage**                | `fetch_next_alert` → `run_query` context → `run_query` baseline → classify/recommend → `case_manager` when required → `acknowledge_alert` |
| **Gather context**                   | `run_query` for process, network, file, user, related alerts, and baseline |
| **Create case after classification** | `case_manager create` → `case_manager attach-alert` |
| **Acknowledge after triage**         | `acknowledge_alert` related mode for batch acknowledgement |

Always complete the full workflow. Do not stop after gathering context. Document classification and disposition before acknowledging.

## Tool Reference

### fetch-next-alert.js

Fetches the oldest unacknowledged Elastic Security alert.

```bash
node skills/security/alert-triage/scripts/fetch-next-alert.js [--days <n>] [--json] [--full] [--verbose]
```

### run-query.js

Runs KQL or ES|QL queries against Elasticsearch.

```bash
node skills/security/alert-triage/scripts/run-query.js --query-file query.esql --type esql
node skills/security/alert-triage/scripts/run-query.js "agent.id:<id>" --index "logs-*" --days 7
```

| Arg | Description |
|-----|-------------|
| `query` | KQL query positional argument |
| `--query-file`, `-q` | Read query from file; required for ES\|QL on PowerShell |
| `--type`, `-t` | `kql` or `esql`; default `kql` |
| `--index`, `-i` | Index pattern; default `logs-*` |
| `--size`, `-s` | Max results; default 100 |
| `--days`, `-d` | Limit to last N days |
| `--json` | Raw JSON output |
| `--full` | Full document source |

### acknowledge-alert.js

Acknowledges alerts by updating `workflow_status` to `acknowledged`.

| Mode | Command |
|------|---------|
| Single | `node skills/security/alert-triage/scripts/acknowledge-alert.js <alert_id> --index <index> --yes` |
| Related | `node skills/security/alert-triage/scripts/acknowledge-alert.js --related --agent <id> --timestamp <ts> [--window 60] --yes` |
| By host | `node skills/security/alert-triage/scripts/acknowledge-alert.js --query --host <hostname> [--time-start <ts>] [--time-end <ts>] --yes` |
| Query | `node skills/security/alert-triage/scripts/acknowledge-alert.js --query --agent <id> [--time-start <ts>] [--time-end <ts>] --yes` |
| Dry run | Add `--dry-run` to any mode |
| Confirm | All write modes prompt for confirmation; pass `--yes` to skip |

## Examples

- "Fetch the next unacknowledged alert and triage it."
- "Investigate alert ID abc-123 — gather context, baseline, classify, recommend disposition, and create a case if required."
- "Process the top 5 critical alerts from the last 24 hours."

## Guidelines

- Report only tool output. Do not invent IDs, hostnames, IPs, MITRE mappings, risk scores, or details not present in the tool response.
- Preserve identifiers from the request and tool responses exactly.
- Confirm actions concisely using the tool return data.
- Distinguish facts from inference. Label conclusions beyond tool output as assessment.
- When presenting case lists or search results, copy the exact title from each case. Do not paraphrase, abbreviate, or summarize titles.
- Always apply the evidence validation checklist and baseline comparison before classifying.
- Default to `unknown` when evidence or baseline is incomplete.
- Execute independent queries in parallel when they target different security data sources and the execution environment supports parallel tool calls.

## Production Use

- All write operations prompt for confirmation unless `--yes` or `-y` is passed.
- Use `--dry-run` before bulk acknowledgments to preview scope without modifying data.
- The acknowledge script uses the Kibana Detection Engine API, compatible with self-managed and Serverless deployments.
- Verify environment variables point to the intended cluster before running any script. There is no undo for acknowledgments.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ELASTICSEARCH_URL` | Yes | Elasticsearch URL |
| `ELASTICSEARCH_API_KEY` | Yes | Elasticsearch API key |
| `KIBANA_URL` | Yes | Kibana URL for case management |
| `KIBANA_API_KEY` | Yes | Kibana API key for case management |
