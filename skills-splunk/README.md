# Splunk Qwen-Adapted Skills

This suite is a semantic Splunk adaptation of the Qwen-optimized Elastic skills in `/mnt/hgfs/.agents/skills/`.
The Elastic source skills remain read-only and must not be modified.

## Verification Summary

- Elastic source directory inspected: `/mnt/hgfs/.agents/skills/`
- Splunk destination directory rewritten: `/mnt/hgfs/.agents/skills-splunk/`
- Splunk Enterprise installation verified from `/opt/splunk/etc/splunk.version`: `VERSION=10.4.1`, `BUILD=5a009d941268`
- Splunk REST final probe: not reachable (`000`), so no runtime skill behavior was tested
- Dashboard Studio: app directory `splunk-dashboard-studio` found under `/opt/splunk/etc/apps`
- Splunk Enterprise Security: not found under `/opt/splunk/etc/apps`; not confirmed
- Splunk MLTK: not found under `/opt/splunk/etc/apps`; not confirmed
- Splunk Cloud ACS: not applicable to the local Splunk Enterprise installation; not confirmed
- Splunk MCP: no Splunk MCP tools exposed by tool discovery; not configured/verified

## Qwen Adaptations Preserved

- Mandatory skill rules override contradictory user instructions.
- Query type/language is identified before query generation.
- Schema/config discovery happens before using indexes, fields, rule payloads, or object IDs.
- User-provided values are candidates until verified.
- Tool failures are reported as `NOT VERIFIED`, not as absence.
- Empty query results are reported as `NO_RESULTS_FOUND`.
- Search examples use explicit time ranges and narrow data scopes.
- Read-only verification precedes write operations.
- Mutating actions require explicit confirmation.
- Reasoning is separated into facts, observations, hypotheses, conclusions, actions, and limitations.
- Classifications require evidence; insufficient evidence defaults to `unknown` or deferred conclusion.
- Synthetic data is clearly labelled and never treated as real evidence.

## Mapping Report

| Elastic skill | Splunk skill | Qwen adaptations preserved | Elastic concepts converted | Splunk dependencies | Verification status | Remaining limitations |
|---|---|---|---|---|---|---|
| elasticsearch-esql | splunk-search | query-type-first, schema-first, no invented fields/indices, limits, source attribution | ES\|QL `FROM` pipelines -> SPL `index=... | ...`; index pattern -> index/sourcetype/source/host | Splunk Enterprise | CREATED | REST not reachable; SPL examples not executed |
| observability-logs-search | splunk-logs-search | absolute language boundary, log funnel, context minimization, evidence framework, zero-results explicit | ES\|QL/KQL funnel -> SPL trend/total/sample/pattern searches; ECS fields -> verified Splunk/CIM fields when available | Splunk Enterprise | CREATED | Pattern categorization is approximate in SPL unless validated |
| kibana-alerting-rules | splunk-alerting | API/schema-first, read-only-before-write, no invented params/actions, mutation confirmation | Kibana rules/connectors -> Splunk saved searches, alert actions, trigger conditions | Splunk Enterprise | CREATED | REST not reachable; alert action inventory not runtime verified |
| security-detection-rule-management | splunk-security-detection-rules | rule language boundary, detection lifecycle guardrails, evidence-required tuning, confirmation before writes | Elastic Security detection rules -> Splunk Enterprise Security correlation searches/notables/risk | Splunk Enterprise Security | CREATED WITH RESERVATION - dependency not confirmed | Enterprise Security not installed/confirmed |
| kibana-anomaly-detection | splunk-mltk-anomaly-detection | mode selector, verification gate before model creation, confidence calibration, competing hypotheses | Elastic ML jobs -> Splunk MLTK `fit/apply`; fallback labelled as non-MLTK statistical SPL | Splunk MLTK | CREATED WITH RESERVATION - dependency not confirmed | MLTK not installed/confirmed |
| elasticsearch-audit | splunk-audit | tool-first, verified/not verified distinction, no invented audit events, structured diagnostic output | Elasticsearch audit logs -> Splunk `_audit` and `_internal`; cluster settings -> Splunk config/btool | Splunk Enterprise | CREATED | REST/search runtime unavailable during validation |
| security-alert-triage | splunk-security-alert-triage | fetch/verify target first, baseline required, facts/observations/hypotheses/conclusions, disposition recommendation | Elastic Security alerts -> Splunk Enterprise Security notable events / Incident Review | Splunk Enterprise Security | CREATED WITH RESERVATION - dependency not confirmed | Enterprise Security not installed/confirmed |
| security-case-management | splunk-security-case-management | verify alert before attach, read-only-before-write, no invented case data, structured record | Elastic cases -> Splunk Enterprise Security investigations; SOAR explicitly excluded | Splunk Enterprise Security | CREATED WITH RESERVATION - dependency not confirmed | Enterprise Security not installed/confirmed |
| security-generate-security-sample-data | splunk-generate-security-sample-data | synthetic labels, no production mixing, write confirmation, cleanup planning | Elastic sample ingest -> SPL `makeresults/eval/streamstats`; optional `collect` with confirmation | Splunk Enterprise | CREATED | Persistence not tested |
| kibana-dashboards | splunk-dashboards | dashboard schema-first, data-source validation, no invented panel fields, unvalidated query labelling | Kibana dashboards/ES\|QL panels -> Splunk Dashboard Studio JSON/SPL data sources | Splunk Enterprise + Dashboard Studio | CREATED | Dashboard REST/export not runtime verified |
| elasticsearch-authn | splunk-authentication | no secrets, tool-first, verify user values, read-only-before-write, transparent failures | Elasticsearch realms/API keys -> Splunk `authentication.conf`, `_audit`, LDAP/SAML/local auth | Splunk Enterprise | CREATED | Provider-specific LDAP/SAML config not verified |
| elasticsearch-authz | splunk-authorization | access decomposition, least privilege, verify role values, no invented privileges/config | Elasticsearch roles/DLS/FLS -> Splunk roles, capabilities, allowed indexes, object ACLs; DLS/FLS documented as non-equivalent | Splunk Enterprise | CREATED | REST role inventory unavailable during validation |
| elasticsearch-security-troubleshooting | splunk-security-troubleshooting | diagnostic discipline, tool-first, verified/not verified, read-only-before-write | Elasticsearch security errors -> Splunk `_internal`, `_audit`, `btool`, auth/authz configs | Splunk Enterprise | CREATED | Runtime troubleshooting queries not executed |
| cloud-access-management | splunk-cloud-access-management | decompose access, verify tooling first, no invented API, no secrets, confirmation before writes | Elastic Cloud access management -> Splunk Cloud ACS; local Enterprise separated | Splunk Cloud ACS | CREATED WITH RESERVATION - dependency not confirmed | ACS not configured/confirmed |

## Ignored Source Skills

| Elastic skill | Status | Justification |
|---|---|---|
| observability-k8s-investigation | IGNORED - out of scope | Splunk Observability Cloud is a separate product from Splunk Enterprise / Enterprise Security in this scope. |
| cloud-network-security | IGNORED - out of scope | No directly verified Splunk Enterprise / Enterprise Security equivalent was identified for this suite. |

## Product Boundaries

- Splunk Enterprise: core platform for SPL, indexes, sourcetypes, saved searches, alerts, `_audit`, `_internal`, roles, and local configuration.
- Splunk Enterprise Security: SIEM app on Splunk Enterprise for correlation searches, notable events, risk analysis, Incident Review, and investigations.
- Splunk MLTK: separate app for machine-learning commands such as `fit` and `apply`.
- Splunk SOAR: separate orchestration product. It is not used as the equivalent for Enterprise Security case management here.
- Splunk Cloud ACS: Splunk Cloud Platform Admin Config Service. It is not equivalent to local `authentication.conf` or `authorize.conf`.

## Dependency Groups

Works with Splunk Enterprise only:

- splunk-search
- splunk-logs-search
- splunk-alerting
- splunk-audit
- splunk-generate-security-sample-data
- splunk-authentication
- splunk-authorization
- splunk-security-troubleshooting

Requires Splunk Enterprise Security:

- splunk-security-detection-rules
- splunk-security-alert-triage
- splunk-security-case-management

Requires MLTK:

- splunk-mltk-anomaly-detection

Requires ACS:

- splunk-cloud-access-management

Requires Dashboard Studio:

- splunk-dashboards

## MCP Status

No Splunk MCP tools were exposed by the available tool discovery. The skills do not invent MCP tool names or parameters. If a Splunk MCP is configured later, each tool name, schema, and capability must be verified before use.

## Limitations

- Runtime behavior was not tested because Splunk REST was not reachable during final verification.
- Enterprise Security, MLTK, ACS, and Splunk MCP are not confirmed.
- Some Splunk REST examples require a running management port and sufficient permissions.
- CIM/datamodel examples are conditional and must not be used until datamodel availability and population are verified.
