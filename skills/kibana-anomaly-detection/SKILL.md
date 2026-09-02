---
name: kibana-anomaly-detection
description: Elastic ML anomaly detection skill â€” investigation/RCA, score explanation,
  job operations (create, datafeed, start/stop, results), and troubleshooting (missing
  docs, memory limits, datafeed health, lifecycle). Operates against Kibana Agent
  Builder MCP tools (`ad_*`) on `.ml-anomalies-*`, `.ml-config`, `.ml-notifications-*`,
  `.ml-annotations-*`. Use when answering "what broke?"/"which entity?"/RCA, "why
  is score high/low?"/renormalization, "datafeed stopped"/"memory limit", or any request
  to set up or configure an ML anomaly detection job.
metadata:
  author: elastic
  version: 0.2.0`n  qwen_optimized: true
  qwen_optimized: true
compatibility: Kibana 8.xâ€“9.x with Agent Builder and Workflows; Elasticsearch 8.xâ€“9.x
  with machine learning
---

# Elastic ML Anomaly Detection
## System Instructions for Qwen

You are an Elastic observability specialist. Follow these rules:

1. DO_NOT_INVENT: Never fabricate service names, metric values, pod names, or cluster status.
2. VERIFY_FIRST: Run test connections and schema discovery before generating queries.
3. CONFIDENCE_CALIBRATION: Start at high confidence, downgrade for missing evidence.
4. STRUCTURED_OUTPUT: Return structured health assessments with signal categories.
5. COMPETING_HYPOTHESES: List multiple explanations; indicate which evidence disambiguates.
6. VERIFICATION_MUST_GATE_ACTION: For job creation or modification tasks, a negative source-data verification is a
   persistent hard gate for the entire task. If any verification returns `buckets: []`, `0 buckets`, `empty`, `no data`,
   zero hits, missing required fields, or another negative result, immediately set and keep:
   `verification_status: failed/empty`, `blocking_verification_result: <exact result>`, and
   `blocked_action: ml_job_build_or_create`. This gate applies to every later step in the same task, including query or
   script construction, job/datafeed JSON preparation, validation, preview, presentation for approval, creation, opening,
   starting, or modification. Other successful checks (connection, mappings, permissions, unrelated indices, alternate
   fields, or generic metadata) do not clear this gate and must not justify phrases like "Excellent" or "data is
   available". Only an explicit revalidation of the same requested data scope can clear it: same source index/pattern,
   same time window, same required metric, same entity split/grouping, and non-empty buckets/documents proving the job
   has data. When the gate is set, state it before each critical step and stop instead of continuing automatically.

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



Single skill covering all anomaly detection work against **Kibana Agent Builder** MCP at
`{KIBANA_URL}/api/agent_builder/mcp`. Use the **Mode Selector** below to pick the right approach for the user's question
â€” modes share the same tool surface and concepts.

## Platform

- Read path: ES|QL against `.ml-anomalies-*`, `.ml-config`, `.ml-notifications-*`, `.ml-annotations-*`
- Always-available: `platform.core.execute_esql` (plus additional platform tools for search, index mapping, and
  documentation â€” see `scripts/agent_builder_constants.json`)
- ML API spec (if available): `.kibana_ai_openapi_spec_elasticsearch` â€” see
  [references/anomaly-detection-openapi-spec-discover.md](references/anomaly-detection-openapi-spec-discover.md) for
  discovery pattern.
- **Run `ad_validate_ml_tool_permissions` first** when tools return empty/misleading results â€” missing privileges are
  the most common cause of false negatives. Full permissions matrix:
  [references/permissions-matrix.md](references/permissions-matrix.md).

## Mode Selector

| User intent                                                                   | Mode                                                                                                   |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| "What broke?" / RCA / cross-job / blast radius / influencers / log categories | **Investigate**                                                                                        |
| "Why score high/low?" / renormalization / model bounds / forecasts            | **Explain**                                                                                            |
| Missing docs / memory limit / datafeed stopped / CCS / lifecycle / calendars  | **Troubleshoot**                                                                                       |
| Create a job / configure a datafeed / start analysis / retrieve results       | **Manage**                                                                                             |
| Security framing (attack chains, MITRE, exfil)                                | Investigate + [references/security-anomaly-expert.md](references/security-anomaly-expert.md)           |
| Observability/SRE framing (degradation, capacity, deployment regression)      | Investigate + [references/observability-anomaly-expert.md](references/observability-anomaly-expert.md) |

When a question spans modes: **Investigate â†’ Explain â†’ Troubleshoot**. Don't blend mode logic â€” finish one before moving
on.

---

## Score Quick Reference

- `record_score` bands: **>75** critical Â· **50â€“75** warning Â· **25â€“50** minor Â· **<25** informational
- `multi_bucket_impact â‰¥ 3` â†’ sustained shift (not a transient spike)
- `initial_record_score >> record_score` â†’ renormalization (model saw worse anomalies later)
- `actual << typical` with `count`/`low_count`/`low_mean` â†’ absence/outage, not just low value
- Low scores across many jobs > one high score â€” composite cross-job signal often beats single-detector severity

> Full score definitions, renormalization mechanics, and `anomaly_score_explanation` components:
> [references/score-reference.md](references/score-reference.md).

## Core concepts

Treat `.ml-anomalies-*` as three layers, accessed via `result_type`:

- **`bucket`** â€” bucket-level unusualness per `bucket_span`. `anomaly_score` is the aggregate across all detectors.
- **`record`** â€” finest-grained rows with `actual` vs `typical`, `probability`, `record_score`,
  `anomaly_score_explanation`.
- **`influencer`** â€” entity contributions ranked within a bucket (`influencer_score`).

Read scores this way:

- `anomaly_score` / `record_score` = **current normalized** values (move as the model sees new extremes).
- `initial_anomaly_score` / `initial_record_score` = **immutable snapshots** from detection time.
- Compare `actual` to `typical`; use `probability` for raw likelihood.
- Map entities via `partition_field_value` / `by_field_value` / `over_field_value`.
- Read `multi_bucket_impact` (-5 to +5) to separate single-bucket spikes from sustained trends.

---

## Mode: Investigate â€” RCA

**When:** "what broke?", "which entity caused this?", cross-job correlation, blast radius, attack/cascade chains.

### Tool chain

| Phase                 | Tools                                                                                                          |
| --------------------- | -------------------------------------------------------------------------------------------------------------- |
| Discovery             | `ad_get_available_metadata`, `ad_get_jobs`, `ad_discover_related_jobs`, `ad_discover_jobs_by_datafeed_index`   |
| Timeline / scope      | `ad_query_anomaly_timeline`                                                                                    |
| Cross-job / entities  | `ad_rca_cross_job_entity_match`, `ad_rca_multi_job_entities`, `ad_rca_entity_profile`                          |
| Records / influencers | `ad_query_anomaly_records`, `ad_query_influencers`                                                             |
| RCA depth             | `ad_rca_detector_fingerprint`, `ad_rca_correlation`, `ad_rca_blast_radius`, `ad_rca_score_reassessment`        |
| Evidence / categories | `ad_get_job_datafeed_config`, `ad_rca_source_evidence`, `ad_get_categories`, `ad_search_log_category_examples` |

### Protocol

Follow the 14-step sequence in [references/protocols/investigation.md](references/protocols/investigation.md). High
level: `ad_get_available_metadata` â†’ pair `ad_discover_jobs_by_datafeed_index` with `ad_discover_related_jobs` â†’
`ad_query_anomaly_timeline` â†’ rank with `ad_rca_multi_job_entities` (`min_job_count=2`) â†’ `ad_rca_detector_fingerprint`
â†’ drill with `ad_query_anomaly_records` + `ad_query_influencers` (low `min_score=25`) â†’ profile with
`ad_rca_entity_profile` â†’ order with `ad_rca_correlation` â†’ confirm with `ad_rca_source_evidence`. When
`by_field_name == "mlcategory"`, compare with `ad_get_categories` + paired `ad_search_log_category_examples` (baseline
vs. anomaly window).

Finish with a written RCA: **root cause entity Â· affected jobs Â· temporal progression Â· fault class
(resource/network/application) Â· severity Â· recommended actions**. Worked example:
[references/worked-example.md](references/worked-example.md). Full ES|QL templates and parameters:
[references/investigate-anomaly-esql-tools.md](references/investigate-anomaly-esql-tools.md).

### Rules

1. **Multi-job entities are prime suspects; single-job entities are usually victims.** Use `min_job_count=2`.
2. **Earliest anomaly timestamp wins** â€” sort `ad_rca_correlation` by timestamp; first-appearing entity = origin.
3. **`multi_bucket_impact â‰¥ 3` = sustained behavioral shift**, weight higher than transient spikes.
4. **Never close an RCA without `ad_rca_source_evidence`** â€” raw source documents are ground truth.
5. **Use low `min_score` (25 or lower) for influencer queries** â€” high thresholds miss correlated entities.

---

## Mode: Explain â€” Score / model behavior

**When:** "why is my score 30/90?", "score dropped overnight", "what is renormalization?", "why wasn't this detected?".

### Score types

| Field                  | Scope           | Meaning                                                                 |
| ---------------------- | --------------- | ----------------------------------------------------------------------- |
| `record_score`         | Single record   | Normalized severity after renormalization.                              |
| `initial_record_score` | Single record   | Score at detection time. Gap vs `record_score` = renormalization drift. |
| `anomaly_score`        | Bucket          | Aggregate severity across all detectors in a bucket.                    |
| `influencer_score`     | Entity Ã— bucket | How anomalous a specific entity is in that bucket.                      |

### `anomaly_score_explanation` components

| Component                        | Effect  | What it means                                                |
| -------------------------------- | ------- | ------------------------------------------------------------ |
| `anomaly_length`                 | â†‘ score | More consecutive anomalous buckets                           |
| `single_bucket_impact`           | â†‘ score | Lower probability â†’ higher impact                            |
| `multi_bucket_impact`            | â†‘ score | Sustained pattern contribution                               |
| `anomaly_characteristics_impact` | â†‘ score | Mean shift vs. variance change                               |
| `high_variance_penalty`          | â†“ score | Noisy data â†’ wide bounds â†’ anomaly less surprising           |
| `incomplete_bucket_penalty`      | â†“ score | Bucket has less data than expected (ingest lag, sparse data) |

### Why a score looks wrong

- **Unexpectedly low:** `high_variance_penalty`, renormalization, <3 weeks training for weekly seasonality,
  `bucket_span` too large, wrong detector function (`mean` vs `high_mean`), `incomplete_bucket_penalty`, suppression by
  `custom_rules`.
- **Unexpectedly high:** insufficient history (early training over-flags), high-cardinality split (too few points per
  entity), `use_null: true` on a sparse field.

### Tool chain

| Purpose                | Tools                                                                              |
| ---------------------- | ---------------------------------------------------------------------------------- |
| Records + explanation  | `ad_query_anomaly_records` (exact `job_id_pattern`)                                |
| Renormalization drift  | `ad_rca_score_reassessment` (`score_drift = initial_record_score - record_score`)  |
| Model bounds (visual)  | `ad_get_model_plot` â€” actual outside `model_lower`/`model_upper` = anomaly         |
| Forecast overlap       | `ad_get_forecast_results`                                                          |
| Influencer attribution | `ad_query_influencers`                                                             |
| Config & detector      | `ad_get_job_datafeed_config` â€” `bucket_span`, function, `custom_rules`, `use_null` |
| Categorization         | `ad_get_categories`                                                                |
| Model snapshots        | `ad_get_model_snapshots`                                                           |
| Structured diagnostic  | **`ad_wf_troubleshoot_anomaly_score`** (full decision tree)                        |

### Decision tree (`ad_wf_troubleshoot_anomaly_score`)

1. `ad_get_jobs` â€” â‰¥3 weeks data for weekly seasonality?
2. `ad_ts_model_memory_health` â€” `memory_status` healthy?
3. `ad_ts_delayed_data_annotations` â€” no incomplete buckets?
4. `ad_query_anomaly_records` â€” compare `record_score` vs `initial_record_score`.
5. `ad_get_job_datafeed_config` â€” `bucket_span`, detector function, `custom_rules`, `use_null`.
6. `ad_get_model_plot` â€” wide bounds â†’ `high_variance_penalty`.
7. `ad_rca_score_reassessment` â€” renormalization drift across history.
8. Explain `anomaly_score_explanation` factors.

### Rules

1. **Always show both `initial_record_score` and `record_score`** â€” the gap is the renormalization story.
2. **Explain renormalization before diagnosing config** â€” score drift is the most common "score dropped" cause and needs
   no config change.
3. **`actual << typical` with `count`/`low_count` is an absence anomaly** â€” distinguish outages from value spikes.
4. **`high_variance_penalty` and `incomplete_bucket_penalty` explain most "low score" surprises** without remediation.
5. **Weekly seasonality needs â‰¥3 weeks of training data** â€” flag young jobs as the cause.

For detector function selection details, see
[references/anomaly-detection-functions.md](references/anomaly-detection-functions.md).

---

## Mode: Troubleshoot â€” Job ops

**When:** "missing documents", "datafeed stopped", "hard_limit", "results look wrong", lifecycle changes, calendars,
CCS.

### Common issues â†’ fast paths

| Issue                                | Fast path                                                                                                                         | Full decision tree                 |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Missing docs / `query_delay` warning | `ad_ts_delayed_data_annotations` â†’ `ad_ts_bucket_event_gaps` â†’ `ad_ts_ingest_latency_estimate` â†’ `ad_update_datafeed_query_delay` | `ad_wf_troubleshoot_query_delay`   |
| Memory `soft_limit` / `hard_limit`   | `ad_ts_model_memory_health` â†’ `ad_wf_ts_field_cardinality` â†’ `ad_estimate_memory_requirement` â†’ `ad_update_model_memory_limit`    | `ad_wf_troubleshoot_memory_limit`  |
| Datafeed not running / job state     | `ad_get_jobs` (state) â†’ `ad_get_job_messages` â†’ `ad_manage_datafeed`                                                              | â€”                                  |
| CCS / `remote_cluster:` indices      | `ad_ts_ccs_diagnostics`                                                                                                           | â€”                                  |
| Score sanity check                   | â€”                                                                                                                                 | `ad_wf_troubleshoot_anomaly_score` |

> `hard_limit` corrupts model state and causes downstream missing-doc false alarms (categorizer silently skips events
> for unknown categories). **Fix memory before fixing `query_delay`.**

### Memory concepts

| Field                               | Meaning                                                 |
| ----------------------------------- | ------------------------------------------------------- |
| `model_bytes`                       | Current memory used                                     |
| `peak_model_bytes`                  | High-water mark since job opened                        |
| `model_bytes_memory_limit`          | Configured `model_memory_limit`                         |
| `memory_status`                     | `ok` / `soft_limit` (pruning) / `hard_limit` (critical) |
| `total_by_field_count > 100k`       | `by_field` cardinality too high â€” dominant driver       |
| `total_partition_field_count > 10k` | Partition explosion                                     |
| `total_category_count > 10k`        | Too many distinct log patterns                          |

Prefer **`ad_estimate_memory_requirement`** (samples cardinality from source, calls Estimate Model Memory API) over
heuristics like `peak_model_bytes * 1.3` â€” the heuristic ignores pure influencer and categorization memory.

### Datafeed & timing concepts

- **`query_delay`** â€” how far behind real time the datafeed queries. Too small â†’ missing docs; too large â†’ slower
  alerts. Set to **P95 ingest latency + buffer** (default `60s`â€“`120s`).
- **`delayed_data_check_config`** â€” how aggressively the datafeed checks for late data.
- **`bucket_span`** â€” analysis interval. Align with data granularity and detection window.
- **`frequency`** â€” defaults to `min(query_delay, bucket_span / 2)`.

### Lifecycle for config changes (memory limit, query_delay)

1. Stop datafeed: `ad_manage_datafeed` (`action=_stop`)
2. Close job
3. Update config: `ad_update_model_memory_limit`, `ad_update_datafeed_query_delay`,
   `ad_update_delayed_data_check_config`
4. Open job: `ad_open_job`
5. Start datafeed: `ad_manage_datafeed` (`action=_start`)

Recover a corrupted period without resetting the whole model: `ad_revert_model_snapshot`.

### Tool surface

| Category               | Tools                                                                                                                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Permissions / metadata | `ad_validate_ml_tool_permissions`, `ad_get_available_metadata`, `ad_get_jobs`                                                                                                                           |
| Job + datafeed state   | `ad_get_job_datafeed_config`, `ad_get_job_messages`, `ad_manage_datafeed`, `ad_preview_datafeed_with_latency`                                                                                           |
| Timing / missing docs  | `ad_ts_delayed_data_annotations`, `ad_ts_bucket_event_gaps`, `ad_ts_ingest_latency_estimate`, `ad_update_datafeed_query_delay`, `ad_update_delayed_data_check_config`, `ad_wf_troubleshoot_query_delay` |
| Memory                 | `ad_ts_model_memory_health`, `ad_wf_ts_field_cardinality`, `ad_estimate_memory_requirement`, `ad_update_model_memory_limit`, `ad_wf_troubleshoot_memory_limit`                                          |
| Model / lifecycle      | `ad_get_model_snapshots`, `ad_revert_model_snapshot`, `ad_open_job`, `ad_create_job`                                                                                                                    |
| CCS                    | `ad_ts_ccs_diagnostics`                                                                                                                                                                                 |
| Calendars              | `ad_get_calendar_events`, `ad_create_calendar_event`                                                                                                                                                    |

Full parameter tables, ES|QL templates, and REST step lists:
[references/troubleshoot-anomaly-tool-reference.md](references/troubleshoot-anomaly-tool-reference.md).

### Rules

1. **`ad_validate_ml_tool_permissions` first** â€” missing privileges produce misleading empty results.
2. **Fix memory before `query_delay`** â€” `hard_limit` corrupts state; `query_delay` fixes on a memory-limited job are
   wasted.
3. **Stop the datafeed before updating it.** Updating a running datafeed is rejected.
4. **Close the job before updating memory limit.** Sequence above.
5. **Prefer workflow tools (`ad_wf_*`) over manually chaining diagnostics** for complex decisions.
6. **`ad_preview_datafeed_with_latency` before starting** â€” confirm the datafeed returns data after config changes.

---

## Mode: Manage â€” Create / configure jobs

**When:** "set up a job", "create an ML detector", "monitor X over time", "detect rare/unusual/anomalous values".

### 4-step workflow

```text
PUT  _ml/anomaly_detectors/<job_id>          # 1. Define job        (ad_create_job)
PUT  _ml/datafeeds/datafeed-<job_id>         # 2. Define datafeed   (ad_create_datafeed)
POST _ml/anomaly_detectors/<job_id>/_open    # 3a. Open job         (ad_open_job)
POST _ml/datafeeds/datafeed-<job_id>/_start  # 3b. Start datafeed   (ad_manage_datafeed action=_start)
GET  _ml/anomaly_detectors/<job_id>/results/records  # 4. Read results
```

### Process

1. **Build configs.** Parse the user request into job + datafeed JSON with no null fields.
2. **Apply smart defaults:**

   | Field            | Default                                 | Override when                                     |
   | ---------------- | --------------------------------------- | ------------------------------------------------- |
   | `bucket_span`    | `"15m"`                                 | User specifies a different span                   |
   | `time_field`     | `"@timestamp"`                          | User names a different timestamp field            |
   | `index`          | `"logs-*"`                              | User specifies an index or pattern                |
   | `datafeed_query` | `{"match_all": {}}`                     | User mentions filters, processes, or time windows |
   | `influencers`    | by/over/partition fields from detectors | User adds extra influencer fields                 |
   | `job_id`         | Generated from user description         | User provides an explicit ID                      |
   | `query_delay`    | `"60s"`                                 | P95 ingest latency is higher                      |

3. **Choose detector function** from user intent â€” full table in
   [references/anomaly-detection-functions.md](references/anomaly-detection-functions.md):
   - "high CPU" / "unusually large" â†’ `high_mean` or `high_sum`
   - "rare logins" / "unusual values" â†’ `rare` (variants below)
   - "too many requests" / "spike in count" â†’ `high_count`

   `rare` variants:
   - Infrequent globally â†’ `rare by_field_name: X`
   - Infrequent vs peers â†’ `rare by_field_name: X over_field_name: Y`
   - Infrequent per segment â†’ `rare by_field_name: X partition_field_name: Y`
   - Infrequent per segment vs peers â†’ `rare by_field_name: X over_field_name: Y partition_field_name: Z`

4. **Validate.** `platform.core.get_index_mapping` on the target index to verify field existence/types â†’
   `ad_validate_job_spec`. If errors, fix and re-validate (max 3 attempts).

   **VERIFICATION_MUST_GATE_ACTION:** If any required verification is negative or empty (aggregation, `exists`,
   search, mapping lookup, validation, or equivalent), immediately record and preserve the task-local gate:
   `verification_status: failed/empty`, `blocking_verification_result: <exact result>`, and
   `blocked_action: ml_job_build_or_create`. Treat `buckets: []` as a hard negative result even if later mapping,
   permission, connection, or metadata checks succeed. This state persists for the entire user task until an explicit
   revalidation of the same requested data scope returns positive data: same source index/pattern, same time window,
   same required metric, same entity split/grouping, and non-empty buckets/documents. Before every later critical step
   (query/script construction, job/datafeed payload preparation, validation, preview, presenting API calls,
   `ad_create_job`, `ad_create_datafeed`, `ad_open_job`, or `ad_manage_datafeed`), re-check the preserved
   `verification_status`. If it is still `failed/empty`, restate the exact prior negative result and stop; do not build,
   present, create, open, start, or modify any ML job/datafeed automatically. Do not use optimistic language such as
   "Excellent" while this gate is set. If revalidation is impossible or remains negative, the job must not be created.
   Offer an alternative only when that alternative has also been verified under its own explicit positive verification
   state. Never drop the negative verification state just because intermediate reasoning steps or unrelated successful
   checks occurred.

5. **Present and confirm.** Show the **complete** job + datafeed bodies formatted as the exact API calls. Ask for
   approval **once**. If feedback, incorporate and re-present (up to 3 rounds).

6. **Deploy.** After confirmation: `ad_create_job` â†’ `ad_create_datafeed` â†’ `ad_open_job` â†’ `ad_manage_datafeed`
   (`action=_start`). Report final `job_id` and `datafeed_id`.

For **batch analysis on historical data**, pass `start` and `end` to the datafeed start call.

> Worked examples (rare-username, DNS exfil, large-downloads) with full JSON bodies and datafeed filters:
> [references/job-creation-recipes.md](references/job-creation-recipes.md).

### Rules

1. **Create job before datafeed.** Datafeed references job by ID.
2. **Open job before starting datafeed.** Start on a closed job is rejected.
3. **`query_delay` = P95 ingest latency + buffer** (60sâ€“120s safe default).
4. **Forecasts require non-population jobs** â€” `over_field_name` jobs cannot be forecasted; warn before attempting.
5. **`by_field_name` vs `over_field_name`:** `by` compares entity to its own history; `over` compares to peer group in
   the same bucket. `partition_field_name` = fully independent sub-model with its own normalization.
6. **`bucket_span` matches detection granularity** â€” 15m for high-frequency, 1h for operational metrics, 1d for daily
   patterns. Larger smooths short spikes; smaller increases noise.

7. **VERIFICATION_MUST_GATE_ACTION:** Negative or empty verification blocks job creation for the rest of the task until
   an explicit positive revalidation of the same requested data scope replaces `verification_status: failed/empty`. Do
   not infer availability from intent, defaults, planned query construction, successful permissions/mapping checks, or
   unrelated later checks when the preserved negative verification disproves data availability. Immediately before
   building, presenting, validating for create, or executing a job/datafeed, restate the negative result (for example
   `buckets: []`, `0 buckets`, or no available data) and refuse to proceed unless same-scope revalidation has succeeded.

---

## Registration (Kibana Agent Builder)

Requires Node.js 18+. Defaults to `elastic`/`changeme` when no credentials are supplied.

```bash
cd skills/kibana/kibana-anomaly-detection

# tools â†’ workflows â†’ skills
node scripts/kibana-agent-builder.mjs all register --kibana-url http://localhost:5601

# HTTPS with self-signed cert
node scripts/kibana-agent-builder.mjs all register --kibana-url https://localhost:5601 --insecure
```

`all register` runs `tools register`, then `workflows register`, then `skills register`. Kibana allows **at most five**
`tool_ids` per skill; the script fills them by scanning `SKILL.md` for tool mentions (in document order), then appends
ids from `references/kibana/tools/esql/*.json` until the cap (workflow-only tools omitted by default). If you run
`skills register` alone, run `tools register` first so those ids exist.

Workflow tool exclusions and prefixes live in `scripts/agent_builder_constants.json`.

**MCP API key permissions:**

- Kibana: `read_onechat`, `space_read`
- Index: `read`, `view_index_metadata` on `.ml-anomalies-*`, `.ml-annotations-*`, `.ml-notifications-*`, `.ml-config`
- For source evidence: `read` on source data indices

---

## Tool inventory

ES|QL tool specs live under `references/kibana/tools/esql/*.json`; workflow definitions under
`references/kibana/workflows/*.yaml`. Each Mode section above lists the tools it uses. Full surface:
[references/tools.md](references/tools.md) (ES|QL) and [references/workflow-tools.md](references/workflow-tools.md)
(workflows).

### Key system indices

| Index                 | Relevant content                                                                                                              |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `.ml-anomalies-*`     | `record`, `bucket`, `influencer`, `model_plot`, `model_forecast`, `model_snapshot`, `category_definition`, `model_size_stats` |
| `.ml-config`          | job/datafeed documents (visible even for never-run jobs)                                                                      |
| `.ml-annotations-*`   | delayed data (`event == "delayed_data"`)                                                                                      |
| `.ml-notifications-*` | job messages (`level`: info/warning/error)                                                                                    |

---

## Examples

**RCA:** "Something caused a spike in our error rate at 2pm â€” what broke?" â†’ Investigate â†’ `ad_get_available_metadata` â†’
`ad_query_anomaly_timeline` â†’ `ad_rca_cross_job_entity_match` â†’ `ad_rca_multi_job_entities` â†’ RCA report.

**Score drop:** "My anomaly score went from 90 to 55 â€” did the model change?" â†’ Explain â†’ `ad_rca_score_reassessment`
for drift â†’ explain renormalization if `score_drift` is large.

**Memory limit:** "Job status shows `hard_limit` and results look wrong." â†’ Troubleshoot â†’ `ad_ts_model_memory_health` â†’
`ad_wf_ts_field_cardinality` â†’ `ad_estimate_memory_requirement` â†’ `ad_update_model_memory_limit` (lifecycle: stop
datafeed â†’ close â†’ update â†’ open â†’ start).

**New job:** "Detect unusual error rates per host on nginx access logs." â†’ Manage â†’ `high_count` detector with
`by_field_name: "host.keyword"` â†’ validate â†’ present â†’ deploy.

**Multi-mode:** "We had an incident last night, scores were high but now low â€” is the job healthy?" â†’ Investigate the
incident â†’ Explain the score drift â†’ Troubleshoot if `hard_limit` or delayed data is suspected.

---

## Guidelines

1. **Pick a mode first.** Don't blend RCA logic with score-explanation logic in one response.
2. **`ad_validate_ml_tool_permissions` first** on empty results â€” privileges are the most common false-negative cause.
3. **Score bands are absolute thresholds**: `>75` critical, `50â€“75` warning, `25â€“50` minor, `<25` informational.
4. **Multi-job entities are prime suspects.** Use `min_job_count=2` in `ad_rca_multi_job_entities`.
5. **Show `initial_record_score` alongside `record_score`** â€” the gap tells the renormalization story.
6. **Fix memory before `query_delay`.** `hard_limit` invalidates downstream diagnostics.
7. **Stop datafeed â†’ close job â†’ update config â†’ open job â†’ start datafeed** for any config change to memory or query
   delay.
8. **Confirm RCAs with `ad_rca_source_evidence`.** Raw source documents are ground truth.
