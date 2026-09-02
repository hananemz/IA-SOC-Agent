---
name: security-skill-router
description: Deterministically route security requests to the verified Elastic or Splunk skill and MCP boundary. Use before selecting a platform-specific skill, query language, dependency, or MCP capability for security searches, alerts, detections, investigations, logs, cases, dashboards, authentication, or related SOC work.
---

# Security Skill Router

Use this skill as the platform gate for every in-scope security request.

## Required order

1. Identify the platform from explicit indicators or established conversation context.
2. If Elastic and Splunk indicators both occur, enter cross-platform mode only when the user explicitly requests comparison, correlation, or investigation across both.
3. If no safe platform is established, return `platform: unknown`, `status: AMBIGUOUS`, and `required_clarification: true`; ask: “Which platform do you want: Elastic or Splunk?” Do not generate a platform query.
4. Identify the task/domain.
5. Select the most specific actual skill in `skill-registry.yaml`.
6. Verify the selected skill path and `SKILL.md` exist.
7. Verify required dependencies. Splunk Enterprise Security, MLTK, and Dashboard Studio are `NOT VERIFIED`.
8. Select only the corresponding MCP server in `mcp-routing.yaml` and verify the required capability is listed.
9. Optionally retrieve local supporting evidence from `skills-rag`. Retrieval is advisory and must not override platform detection, the registry, schema verification, or MCP gates.
10. Execute only after all required gates pass. A tool failure is `NOT VERIFIED`; an empty verified result is `NO_RESULTS_FOUND`.

## Platform gates

Splunk indicators include Splunk, Splunk Enterprise, Splunk Enterprise Security, SPL, `index=`, `sourcetype=`, saved search, Splunk alert, Dashboard Studio, `_internal`, `_audit`, notable event, Incident Review, and correlation search. Splunk uses SPL and `splunk-mcp-server`.

Elastic indicators include Elastic, Elasticsearch, Kibana, Elastic Security, ES|QL, KQL, Elasticsearch index/query, Kibana rule, Elastic detection rule, Elastic alert, and Elastic case. Elastic uses the verified `elastic` MCP and the query language required by the selected Elastic skill.

Generic terms such as alert, detection, SIEM, security, logs, threat, MITRE, brute force, authentication, investigation, and incident do not establish a platform.

Never use SPL for Elastic or ES|QL/KQL for Splunk. Never invent indices, fields, sourcetypes, saved-search IDs, alert IDs, case IDs, MCP tools, or parameters.

## Decision output

Expose only concise routing metadata, for example:

```json
{"platform":"splunk","task":"security_alert_triage","skill":"splunk-security-alert-triage","query_language":"SPL","mcp":"splunk-mcp-server","mcp_status":"VERIFIED","backend_runtime_status":"NOT_VERIFIED","rag_status":"LOCAL_OPTIONAL"}
```

Do not expose chain-of-thought. Read `ROUTING.md` for detailed mappings and cross-platform isolation rules. Use the YAML registry as the source of truth for paths, dependencies, MCP names, and capabilities.

## Local retrieval

`skills-rag/skills_rag.py` provides deterministic, offline retrieval over curated
operational knowledge after the Agent/Skills decision. It does not discover,
select, or load skills. `skills-rag/soc_rag.py` is a separate
provider-independent retriever for attributed SOC reasoning guidance. Skills
RAG is technical HOW-TO; SOC Analyst RAG is security WHAT/WHY; MCP output is
the only observed evidence. Neither RAG is an authority over platform routing,
schemas, capabilities, or live evidence. Run `py skills_rag.py index` and
`py soc_rag.py index` after source changes.
after changing indexed artifacts.

The SOC RAG also emits unified evidence-first recommendations for traditional
and AI alert categories. Recommendations are advisory structured output and
remain separate from observed MCP evidence, confirmed facts, and automated
actions. Missing or unknown context produces clarification and evidence
collection steps instead of unsupported containment claims.
