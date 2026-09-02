# Skills RAG layer

This is an offline retrieval layer for the Security Skill Router. It contains
two separate retrievers:

- `skills_rag.py`: Operational Knowledge RAG for complementary investigation
  patterns, troubleshooting, query examples, playbooks, and pitfalls.
- `soc_rag.py`: the SOC Analyst RAG for security reasoning and investigation
  guidance.

The operational RAG and the default SOC mode use deterministic standard-library
lexical retrieval. Their indexes are separate and need no model, database,
credentials, or vector database. SOC can optionally enable the Qdrant/vector
extension described below; it never supplies MCP evidence or selects a platform.

From this directory:

```powershell
py .\skills_rag.py index
py .\skills_rag.py search "suspicious PowerShell execution" --platform elastic --skill security-alert-triage
py .\soc_rag.py index
py .\soc_rag.py search "Investigate suspicious PowerShell execution"
```

Retrieval is advisory operational context. It never selects a platform, invents schema,
overrides the registry, or authorizes an MCP call. Rebuild the index after
changing the operational JSONL corpus.

Retrieval limits are configured in `config.yaml`. Results are selected by
relevance threshold and redundancy filtering, with `max_top_k` and
`max_context_chars` as safety ceilings; the limit is not a fixed evidence
requirement. Skill guidance is section-selected and cached by file mtime.

## SOC Analyst RAG

SOC source records live in `soc-knowledge/documents.jsonl` (the original
backward-compatible corpus) and `soc-knowledge/documents_expanded.jsonl`.
Both are JSONL and the loader combines them automatically. Normalized records
also expose `event_ids`, `log_source`, `mitre_tactic`, `mitre_technique`,
`data_source`, `investigation_phase`, `keywords`, and `related_techniques`.
Unknown future fields are preserved. Source evaluation is recorded in
`soc-knowledge/sources.json`.

The selected corpus is a small, attributed set of local Elastic/Splunk
reasoning guidance and four focused MITRE ATT&CK technique-page summaries.
Intent detection supports TRIAGE, INVESTIGATION, IOC_ANALYSIS, MITRE_MAPPING,
RISK_ASSESSMENT, FALSE_POSITIVE, THREAT_HUNTING, INCIDENT_RESPONSE, DETECTION,
AUTHENTICATION, NETWORK_ANALYSIS, MALWARE_ANALYSIS, WINDOWS_ANALYSIS,
LINUX_ANALYSIS, AI_SECURITY, AI_ALERT_TRIAGE, PROMPT_INJECTION_ANALYSIS,
RAG_SECURITY_ANALYSIS, AI_AGENT_SECURITY, AI_DATA_LEAKAGE, AI_THREAT_HUNTING,
AI_INCIDENT_RESPONSE, AI_DETECTION_ENGINEERING, and GENERAL_SECURITY. Low-confidence queries fall back to general SOC
retrieval. Ranking combines lexical relevance, metadata and technique matches,
intent/category boosts, thresholding, redundancy filtering, deterministic
ordering, and a 4,200-character SOC ceiling.

## Hybrid Security SOC RAG

The lexical SOC retrieval remains the default and is never replaced. When
`qdrant.enabled` is true, the same normalized JSONL chunks are also embedded
with the configured `sentence-transformers` model and upserted into Qdrant.
Qdrant supports a local persistent path or a configured remote URL; credentials
are read only from the configured environment-variable name. The collection
payload retains document/chunk IDs and SOC metadata, including category,
source, tags, platform, techniques, severity, and content hashes.

Use `python .\\soc_rag.py index` to build the lexical index and, when enabled,
idempotently upsert vector points. Retrieval supports `mode=lexical`,
`mode=vector`, `mode=hybrid`, or `auto`; default `auto` preserves lexical-only
behavior while Qdrant is disabled. Hybrid scoring normalizes both result sets,
applies configurable lexical/vector weights, preserves exact lexical matches,
and removes duplicate chunks. Qdrant or embedding failures return
`LEXICAL_FALLBACK` without interrupting SOC retrieval.

Install optional dependencies with:

```powershell
python -m pip install -r .\\requirements-qdrant.txt
```

Compare lexical, vector-only, and hybrid modes with:

```powershell
python .\\benchmark_hybrid_rag.py
```

`context_handoff.build_context(..., soc_result=soc_result)` preserves the
existing positional interface and adds explicit `[USER_REQUEST]`, `[OPERATIONAL_RAG]`,
`[SOC_ANALYST_RAG]`, `[MCP_EVIDENCE]`, and `[MODEL_INSTRUCTIONS]` sections.
SOC records are marked `GUIDANCE_ONLY`; MCP output is the only observed
evidence section. Missing evidence is reported as `Not available from current
evidence.`

Run the local, read-only stage benchmark with:

```powershell
python .\benchmark_security_agent.py
python .\benchmark_soc_rag.py
```

The SOC benchmark runs five repetitions for indexing and four representative
queries. It reports average/minimum/maximum local timings, retrieved document
counts, and final context size. Router, MCP, and Qwen remain
`NOT_MEASURABLE` unless an executable runtime is present. Rebuild the SOC
index after changing `documents.jsonl`:

```powershell
py .\soc_rag.py index
```

To add future SOC knowledge, add one focused attributed JSONL record to the
expanded file. Keep one topic per record, use a unique stable ID, uppercase
allowed intents, valid ATT&CK IDs, and a source URL or `local://` reference.
Include verified event IDs and fields, and keep facts, benign hypotheses,
malicious hypotheses, evidence gaps, and actions distinct. Do not place live
provider results in this corpus.

Rebuild and validate after changes:

```powershell
py .\soc_rag.py index
py .\validate_soc_rag.py
py -m unittest .\test_soc_rag.py .\test_skills_rag.py
```

The generated `.rag/soc-index.json` contains document and chunk counts.
Retrieval weights content and metadata (including event IDs and ATT&CK
fields), then applies intent/category boosts, thresholding, redundancy
filtering, deterministic order, and the context-size ceiling. Verify actual
Elastic, Splunk, or Sentinel mappings before using platform-specific fields.

## Unified recommendations

`recommendations.build_recommendations()` consumes the SOC retrieval result and
optional observed evidence to produce structured, advisory fields: verdict,
confidence, attack status, facts, evidence gaps, hypotheses, investigation and
correlation steps, recommended containment, prioritized recommendations, next
actions, and escalation criteria. The recommendation family is selected from
retrieved category/topic knowledge across traditional and AI alerts; it is not
an AI-only rule set. With no relevant knowledge it returns conservative
clarification and evidence-collection actions rather than invented remediation.
Facts and guidance remain separate, and recommended containment is never an
automatic action. The dashboard exposes the same object under
`recommendations` while retaining the existing narrative `answer` field.

The AI Security corpus in `soc-knowledge/documents_ai_security.jsonl` adds the
`ai_security` category, AI-specific intents, and independent `attack_status`
metadata. Records cover prompt injection and jailbreaks; RAG/vector integrity;
agent tools, permissions, identity, and memory; leakage and cross-tenant
exposure; API/token abuse; supply chain; telemetry; and twelve defensive
playbook topics. Verdict and attack status are evidence-first and independent:
suspicious text is not proof of compromise, successful impact, authorization
failure, or data breach. OWASP LLM identifiers are stored separately from MITRE
ATT&CK fields.

## Operational Knowledge RAG

Records live in `operational-knowledge/documents.jsonl`; the generated index is
`.rag/operational-index.json`. Only this curated corpus is indexed: router files
and `SKILL.md` are deliberately excluded. The router must provide an already
selected platform; an unknown or ambiguous decision returns no context.
Results are advisory and never platform/skill authority, schema, MCP evidence,
or authorization. Near-duplicates against selected `SKILL.md` sections are
removed by `context_handoff` before injection into the LLM context.
