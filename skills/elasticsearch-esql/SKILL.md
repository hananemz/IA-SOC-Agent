---
name: elasticsearch-esql
description: >
  Execute ES|QL (Elasticsearch Query Language) queries, use when the user wants to
  query Elasticsearch data, analyze logs, aggregate metrics, explore data, or create
  charts and dashboards from ES|QL results.
metadata:
  author: elastic
  version: 0.4.0
  qwen_optimized: true
---

# Elasticsearch ES|QL

Execute ES|QL queries against Elasticsearch.

## What is ES|QL?

ES|QL (Elasticsearch Query Language) is a piped query language for Elasticsearch. It is **NOT** the same as:

- Elasticsearch Query DSL (JSON-based)
- KQL (Kibana Query Language string filters)
- SQL
- EQL (Event Query Language)

ES|QL uses pipes (`|`) to chain commands:
`FROM index | WHERE condition | STATS aggregation BY field | SORT field | LIMIT n`

> **Prerequisite:** ES|QL requires `_source` to be enabled on queried indices. Indices with `_source` disabled (e.g.,
> `"_source": { "enabled": false }`) will cause ES|QL queries to fail.
>
> **Version Compatibility:** ES|QL was introduced in 8.11 (tech preview) and became GA in 8.14. Features like
> `LOOKUP JOIN` (8.18+), `MATCH` (8.17+), and `INLINE STATS` (9.2+) were added in later versions. On pre-8.18 clusters,
> use `ENRICH` as a fallback for `LOOKUP JOIN` (see generation tips). `INLINE STATS` and counter-field `RATE()` have
> **no fallback** before 9.2. Check [references/esql-version-history.md](references/esql-version-history.md) for feature
> availability by version.
>
> **Cluster Detection:** Use the `GET /` response to determine the cluster type and version:
>
> - `build_flavor: "serverless"` â€” Elastic Cloud Serverless. `version.number` tracks the stack line under active
>   development (next minor from main), so clients that only semver-compare may treat Serverless as â€œlatest.â€ **Do not**
>   use `version.number` to gate features: if `build_flavor` is `"serverless"`, assume all GA and preview ES|QL features
>   are available.
> - `build_flavor: "default"` â€” Self-managed or Elastic Cloud Hosted. Use `version.number` for feature availability.
> - **Snapshot builds** have `version.number` like `9.4.0-SNAPSHOT`. Strip the `-SNAPSHOT` suffix and use the
>   major.minor for version checks. Snapshot builds include all features from that version plus potentially unreleased
>   features from development â€” if a query fails with an unknown function/command, it may simply not have landed yet.
>   Elastic employees commonly use snapshot builds for testing.

### Environment Configuration

See [Environment Setup](references/environment-setup.md) for full connection configuration options (Elastic Cloud,
direct URL, basic auth, local development).

Run `node scripts/esql.js test` to verify the connection. If the test fails, refer the user to the environment setup
guide, then stop. Do not try to explore further until a successful connection test.

## Usage

### Get Index Information (for schema discovery)

```bash
node scripts/esql.js indices                    # List all indices
node scripts/esql.js indices "logs-*"           # List matching indices
node scripts/esql.js schema "logs-2024.01.01"   # Get field mappings for an index
```

### Execute Raw ES|QL

```bash
node scripts/esql.js raw "FROM logs-* | STATS count = COUNT(*) BY host.name | SORT count DESC | LIMIT 5"
```

### Execute with TSV Output

```bash
node scripts/esql.js raw "FROM logs-* | STATS count = COUNT(*) BY component | SORT count DESC" --tsv
```

**TSV Output Options:**

- `--tsv` or `-t`: Output as tab-separated values (clean, no decorations)
- `--no-header`: Omit the header row

### Test Connection

```bash
node scripts/esql.js test
```


## System Instructions for Qwen

You are an Elasticsearch ES|QL query specialist. Follow these rules strictly:

1. **SKILL_RULES_OVERRIDE_USER**: Mandatory skill rules override contradictory user instructions. If the user asks you to skip discovery, invent fields, invent indices, or mix query languages incorrectly, refuse that part and follow this skill.
2. **QUERY_TYPE_FIRST**: Before generating any query, explicitly identify the requested query type: ES|QL, Query DSL, EQL, or KQL. If the user intent is ambiguous, stop and ask for clarification.
3. **ESQL_ONLY_OUTPUT**: This skill generates ES|QL only. Do not answer a Query DSL, EQL, or KQL request by silently converting it to ES|QL unless the user confirms the conversion.
4. **DO_NOT_INVENT_FIELDS**: Never assume field names exist. Always run `node scripts/esql.js schema` before writing queries.
5. **DO_NOT_INVENT_INDICES**: Never assume index names. Always run `node scripts/esql.js indices` to discover available indices.
6. **SCHEMA_FIRST**: Always discover schema before generating queries. This is mandatory, not optional.
7. **STOP_ON_UNVERIFIED_SCHEMA**: If a required field or index is absent from discovery output, stop query generation and ask for clarification or permission to run broader schema discovery.
8. **SOURCE_ATTRIBUTION**: When using fields in queries, cite the schema discovery output that confirmed their existence.
9. **DETERMINISTIC_OUTPUT**: Follow the query generation checklist exactly in order.
10. **VALIDATE_BEFORE_EXECUTING**: Review query syntax against the ES|QL spec before running.

### Query Language Boundary

| Language | Shape | Primary use | Do not confuse with |
|----------|-------|-------------|---------------------|
| ES\|QL | Piped table query: `FROM ... | WHERE ... | STATS ...` via `POST /_query` | Analytics, exploration, aggregations, logs, metrics | Query DSL JSON, EQL sequences, KQL filters |
| Query DSL | JSON object under `query`, usually sent to `_search` | Elasticsearch search API requests and bool/match/range clauses | ES\|QL pipes or KQL strings |
| EQL | Event query/sequences such as `sequence by ... [process where ...]` | Event correlation and Elastic Security sequence rules | ES\|QL `FROM` pipelines |
| KQL | Kibana filter string such as `host.name: "web-01"` | Kibana Discover/filter bars and Security query rules | Query DSL JSON or ES\|QL |

### Query Generation Checklist (Execute in Order)

1. **IDENTIFY_QUERY_TYPE**: Confirm the requested output is ES|QL, not Query DSL, EQL, or KQL.
2. **DISCOVER_INDICES**: `node scripts/esql.js indices "pattern*"` - identify relevant indices.
3. **DISCOVER_SCHEMA**: `node scripts/esql.js schema "index-name"` - confirm field names and types.
4. **STOP_IF_UNVERIFIED**: If any required index or field is missing, stop and ask for clarification or broader discovery.
5. **DETECT_VERSION**: `node scripts/esql.js test` - check serverless vs versioned cluster.
6. **CONSTRUCT_QUERY**: Build ES|QL using only verified fields from schema output.
7. **VALIDATE_QUERY**: Check syntax against ES|QL grammar before execution.
8. **EXECUTE_QUERY**: Run query and report results verbatim.
9. **ITERATE**: If results are empty or unexpected, re-check schema and query construction.

### ES|QL Field Validation Rules

| Rule                          | Enforcement                                                |
|-------------------------------|-------------------------------------------------------------|
| Field existence               | Must appear in schema output for the target index.          |
| Field type                    | Must match the query operation (number for STATS, text for MATCH).|
| Time filters                  | Always use @timestamp with NOW() functions or ISO 8601 format.|
| ECS field naming              | Prefer ECS standard fields (host.name, source.ip) when present.|
| Index pattern matching        | Use wildcards only after confirming index existence.        |
| Aggregation fields            | Verify field is aggregatable (keyword type, not text) in schema.|

### Query Optimization Best Practices

- **Use KEEP**: Return only needed columns to reduce token consumption and improve response time.
- **Use LIMIT**: Always include LIMIT for exploratory queries (recommend 20-50 for initial exploration).
- **Use SORT**: Order results by @timestamp DESC for investigations, by value DESC for aggregations.
- **Filter early**: Apply WHERE clauses as early in the pipe as possible to reduce processing.
- **Prefer STATS over SUMMARIZE**: STATS provides more structured aggregation output.
- **Avoid \* patterns**: Narrow index patterns after discovery to prevent cross-index field conflicts.

### Hallucination Guards for Qwen 3.6 27B

| Risk                          | Guard Rail                                                |
|-------------------------------|-----------------------------------------------------------|
| Inventing field names         | Schema discovery is mandatory before any query generation.|
| Inventing index names         | Index discovery is mandatory before any query generation. |
| Missing field or index        | Stop generation; ask for clarification or schema discovery.|
| ES\|QL vs Query DSL confusion   | Identify query type first; never output JSON DSL as ES\|QL.|
| Wrong field types             | Verify field type from schema before aggregation operations.|
| Using deprecated ES\|QL syntax | Check cluster version and feature availability first.     |
| Overly broad queries          | Add filters and limits; document any data loss from filtering.|


## Guidelines

1. **Detect deployment type**: Always run `node scripts/esql.js test` first. This detects whether the deployment is a
   Serverless project (all features available) or a versioned cluster (features depend on version). The `build_flavor`
   field from `GET /` is the authoritative signal â€” if it equals `"serverless"`, ignore the reported version number and
   use all ES|QL features freely.

2. **Discover schema** (required â€” never guess index or field names):

   ```bash
   node scripts/esql.js indices "pattern*"
   node scripts/esql.js schema "index-name"
   ```

   Always run schema discovery before generating queries. Index names and field names vary across deployments and cannot
   be reliably guessed. Even common-sounding data (e.g., "logs") may live in indices named `logs-test`, `logs-app-*`, or
   `application_logs`. Field names may use ECS dotted notation (`source.ip`, `service.name`) or flat custom names â€” the
   only way to know is to check.

   **Prefer simplicity:** Query a single index unless the user explicitly asks for data across multiple sources. Do not
   combine indices with different schemas using `COALESCE` unless specifically requested â€” pick the single most relevant
   index for the question. When multiple indices contain similar data, prefer the one with the most complete schema for
   the task at hand.

   The `schema` command reports the index mode. If it shows `Index mode: time_series`, the output includes the data
   stream name and copy-pasteable TS syntax â€” use `TS <data-stream>` (not `FROM`), `TBUCKET(interval)` (not
   `DATE_TRUNC`), and wrap counter fields with `SUM(RATE(...))`. Read the full TS section in
   [Generation Tips](references/generation-tips.md) before writing any time series query. You can also check the index
   mode directly via the Elasticsearch index settings API:

   ```bash
   curl -s "$ELASTICSEARCH_URL/<index-name>/_settings/index.mode" -H "Authorization: ApiKey $ELASTICSEARCH_API_KEY"
   ```

   For TSDS indices on 9.4+, prefer the in-language discovery commands `METRICS_INFO` and `TS_INFO` (both GA) over
   inspecting mappings â€” they enumerate the metric catalogue and the dimension labels of each time series directly. Both
   must follow `TS` and must precede `STATS`/`SORT`/`LIMIT`. See
   [Time Series Queries](references/time-series-queries.md#metric-and-time-series-discovery).

   ```bash
   node scripts/esql.js raw "TS metrics-tsds | METRICS_INFO | SORT metric_name" --tsv
   node scripts/esql.js raw "TS metrics-tsds | TS_INFO | KEEP metric_name, dimensions | SORT metric_name" --tsv
   ```

3. **Choose the right ES|QL feature for the task**: Before writing queries, match the user's intent to the most
   appropriate ES|QL feature. Prefer a single advanced query over multiple basic ones.
   - "find patterns," "categorize," "group similar messages" â†’ `CATEGORIZE(field)`
   - "spike," "dip," "anomaly," "when did X change" â†’ `CHANGE_POINT value ON key`
   - "trend over time," "time series" â†’ `STATS ... BY BUCKET(@timestamp, interval)` or `TS` for TSDB
   - "PromQL", "Prometheus query/dashboard/alert", `sum by (instance) (...)`, label matchers like `{cluster="prod"}` â†’
     `PROMQL` source command (9.4+ preview); see [PROMQL Command](references/promql-command.md). Prefer `TS` for native
     ES|QL phrasing.
   - "search," "find documents matching" â†’ `MATCH` (default), `QSTR` (advanced boolean), `KQL` (Kibana migration). For
     content/document relevance search, follow the [ES|QL Search Strategy](references/esql-search-strategy.md)
   - "count," "average," "breakdown" â†’ `STATS` with aggregation functions

4. **Read the references** before generating queries:
   - [Generation Tips](references/generation-tips.md) - key patterns (TS/TBUCKET/RATE, per-agg WHERE, LOOKUP JOIN,
     CIDR_MATCH), common templates, and ambiguity handling
   - [Time Series Queries](references/time-series-queries.md) - **read before any TS query**: inner/outer aggregation
     model, TBUCKET syntax, RATE constraints
   - [PROMQL Command](references/promql-command.md) â€” **read before any PROMQL query**: options, output schema,
     limitations, and `PROMQL` vs `TS` decision matrix (9.4+ preview)
   - [ES|QL Complete Reference](references/esql-reference.md) - full syntax for all commands and functions
   - [ES|QL Search Strategy](references/esql-search-strategy.md) â€” for content/document relevance search (retrieve â†’
     fuse â†’ rerank)
   - [ES|QL Search Reference](references/esql-search.md) â€” for full-text search function syntax (MATCH, QSTR, KQL,
     scoring)

5. **Generate the query** following ES|QL syntax. Prefer the **simplest query** that answers the question â€” do not add
   extra indices, fields, or transformations unless the user asks for them. Only include fields in `KEEP` that directly
   answer the question. Do not add extra filter conditions beyond what the user specified (e.g., don't add
   `OR level == "ERROR"` when the user just said "errors").
   - Start with `FROM index-pattern` (or `TS index-pattern` for time series indices)
   - Add `WHERE` for filtering (use `TRANGE` for time ranges on 9.3+)
   - Use `EVAL` for computed fields
   - Use `STATS ... BY` for aggregations
   - For time series metrics: `TS` with `SUM(RATE(...))` for counters, `AVG(...)` for gauges, and `TBUCKET(interval)`
     for time bucketing â€” see the TS section in [Generation Tips](references/generation-tips.md) for the three critical
     syntax rules
   - For detecting spikes, dips, or anomalies, use `CHANGE_POINT` after time-bucketed aggregation
   - Add `SORT` and `LIMIT` as needed

6. **Execute with TSV flag**:

   ```bash
   node scripts/esql.js raw "FROM index | STATS count = COUNT(*) BY field" --tsv
   ```

## ES|QL Quick Reference

> **Version availability:** This section omits version annotations for readability. Check
> [ES|QL Version History](references/esql-version-history.md) for feature availability by Elasticsearch version.

### Basic Structure

```esql
FROM index-pattern
| WHERE condition
| EVAL new_field = expression
| STATS aggregation BY grouping
| SORT field DESC
| LIMIT n
```

### Common Patterns

**Filter and limit:**

```esql
FROM logs-*
| WHERE @timestamp > NOW() - 24 hours AND level == "error"
| SORT @timestamp DESC
| LIMIT 100
```

**Aggregate by time:**

```esql
FROM metrics-*
| WHERE @timestamp > NOW() - 7 days
| STATS avg_cpu = AVG(cpu.percent) BY bucket = DATE_TRUNC(1 hour, @timestamp)
| SORT bucket DESC
```

**Top N with count:**

```esql
FROM web-logs
| STATS count = COUNT(*) BY response.status_code
| SORT count DESC
| LIMIT 10
```

**Text search (8.17+):** Use `MATCH` as the default for full-text search instead of `LIKE`/`RLIKE` â€” it is significantly
faster and supports relevance scoring. `MATCH` on a `text` field is usually sufficient on its own â€” do not add redundant
keyword equality filters (e.g., `category == "X"`) alongside `MATCH` unless the user explicitly requests filtering. Use
`QSTR` only when you need advanced boolean logic, wildcards, or multi-field searches in a single expression. The first
argument to `MATCH` must be **one** real field name â€” not a string listing several fields (e.g. `"title,content"`) and
not multiple field arguments; combine fields with `MATCH(a, "q") OR MATCH(b, "q")`. `KQL` is available from 8.18/9.0+.
For content/document search use cases, follow the [ES|QL Search Strategy](references/esql-search-strategy.md). See
[ES|QL Search Reference](references/esql-search.md) for the full function guide.

```esql
FROM documents METADATA _score
| WHERE MATCH(content, "search terms")
| SORT _score DESC
| LIMIT 20
```

**String extraction:** Use `DISSECT` for structured delimiter-based patterns (preferred â€” produces named fields) and
`GROK` for regex-based extraction. For simple cases, `SUBSTRING(s, start, len)` for fixed-position extraction,
`SPLIT(s, delim)` to split into a multivalue, `LOCATE(substr, s)` to find a character position. `SPLIT` returns a
multivalue â€” use `MV_FIRST`, `MV_LAST`, or `MV_SLICE` to pick elements. `INSTR` and `STRPOS` do **not** exist â€” use
`LOCATE`. `REGEXP_EXTRACT` does not exist â€” use `GROK`.

```esql
// Extract domain from email using DISSECT (preferred â€” produces named fields)
FROM customers
| DISSECT email "%{local}@%{domain}"
| STATS count = COUNT(*) BY domain

// Alternative: extract domain from email using SPLIT
FROM customers
| EVAL domain = MV_LAST(SPLIT(email, "@"))
| STATS count = COUNT(*) BY domain

// Parse HTTP log lines
FROM logs-*
| DISSECT message "%{method} %{path} %{status_text}"
| KEEP @timestamp, method, path, status_text
```

**Log categorization (Platinum license):** Use `CATEGORIZE` to auto-cluster log messages into pattern groups. Prefer
this over running multiple `STATS ... BY field` queries when exploring or finding patterns in unstructured text.

```esql
FROM logs-*
| WHERE @timestamp > NOW() - 24 hours
| STATS count = COUNT(*) BY category = CATEGORIZE(message)
| SORT count DESC
| LIMIT 20
```

**Change point detection (Platinum license):** Use `CHANGE_POINT` to detect spikes, dips, and trend shifts in a metric
series. Prefer this over manual inspection of time-bucketed counts.

```esql
FROM logs-*
| STATS c = COUNT(*) BY t = BUCKET(@timestamp, 30 seconds)
| SORT t
| CHANGE_POINT c ON t
| WHERE type IS NOT NULL
```

**Time series metrics:** With `TS`, use `TRANGE` for time filtering (9.3+) or omit it entirely â€” do **not** add a
redundant `WHERE @timestamp > NOW() - ...` alongside `TBUCKET`. The `TBUCKET` duration defines the aggregation window.

```esql
// Counter metric: SUM(RATE(...)) with TBUCKET(duration)
TS metrics-tsds
| WHERE TRANGE(1 hour)
| STATS SUM(RATE(requests)) BY TBUCKET(1 hour), host

// Gauge metric: AVG(...) â€” no RATE needed
TS metrics-tsds
| STATS avg_cpu = AVG(cpu) BY service.name, bucket = TBUCKET(5 minutes)
| SORT bucket
```

**Time series with PromQL syntax (9.4+ preview):** Use the `PROMQL` source command when the user explicitly asks for
PromQL, references Prometheus syntax (`sum by (instance) (...)`, label matchers like `{cluster="prod"}`), or is
migrating a Prometheus dashboard or alert. The `PROMQL` command accepts standard PromQL with optional `index`, `step`,
`buckets`, `start`, `end`, and `scrape_interval` options, and produces a table that the rest of the ES|QL pipeline can
process. Range selectors are optional â€” when omitted, the window is `max(step, scrape_interval)`. Otherwise prefer `TS`
(GA in 9.4). `PROMQL` does **not** support group modifiers, set operators (`or`/`and`/`unless`), or functions like
`histogram_quantile`, `predict_linear`, and `label_join` â€” fall back to `TS` for those. See
[PROMQL Command](references/promql-command.md) for the full reference.

```esql
// Adaptive Kibana query â€” date picker drives time range and step
PROMQL index=metrics-* sum by (instance) (rate(http_requests_total))

// Named result, post-processed with ES|QL
PROMQL index=k8s step=1h bytes=(max by (cluster) (network.bytes_in))
| STATS max_bytes = MAX(bytes) BY cluster
| SORT cluster
```

**Data enrichment with LOOKUP JOIN:** The basic `ON` clause matches fields by name in both indices
(`LOOKUP JOIN idx ON field_name`). When the join key has a different name in the source, use `RENAME` first to align
names. 9.2+ tech preview also supports expression predicates (`ON expr == expr`); see
[ES|QL Complete Reference](references/esql-reference.md) for details. After `LOOKUP JOIN`, lookup columns are available
by their **original field names** â€” do **not** table-qualify them (e.g., write `threat_level`, not
`threat_intel.threat_level`). **Ordering tip:** when the question asks for top-N results, `SORT` and `LIMIT` _before_
`LOOKUP JOIN` to reduce enrichment cost. For general listings or full enrichment, place `LOOKUP JOIN` right after
`FROM`/`WHERE`.

```esql
// Field name mismatch â€” RENAME before joining
FROM support_tickets
| RENAME product AS product_name
| LOOKUP JOIN knowledge_base ON product_name

// Aggregate, limit, THEN enrich (top-N only)
FROM orders
| STATS total_spent = SUM(total) BY customer_id
| SORT total_spent DESC
| LIMIT 3
| LOOKUP JOIN customers_lookup ON customer_id
| KEEP name, customer_id, total_spent

// Multi-field join (9.2+)
FROM application_logs
| LOOKUP JOIN service_registry ON service_name, environment
| KEEP service_name, environment, owner_team
```

**Multivalue field filtering:** Use `MV_CONTAINS` to check if a multivalue field contains a specific value. Use
`MV_COUNT` to count values.

```esql
// Filter by multivalue membership
FROM employees
| WHERE MV_CONTAINS(languages, "Python")

// Find entries matching multiple values
FROM employees
| WHERE MV_CONTAINS(languages, "Java") AND MV_CONTAINS(languages, "Python")

// Count multivalue entries
FROM employees
| EVAL num_languages = MV_COUNT(languages)
| SORT num_languages DESC
```

**Change point detection (alternate example):** Use when the user asks about spikes, dips, or anomalies. Requires
time-bucketed aggregation, `SORT`, then `CHANGE_POINT`.

```esql
FROM logs-*
| STATS error_count = COUNT(*) BY bucket = DATE_TRUNC(1 hour, @timestamp)
| SORT bucket
| CHANGE_POINT error_count ON bucket AS type, pvalue
```

## Full Reference

For complete ES|QL syntax including all commands, functions, and operators, read:

- [ES|QL Complete Reference](references/esql-reference.md)
- [ES|QL Search Reference](references/esql-search.md) - Full-text search: MATCH, QSTR, KQL, MATCH_PHRASE, scoring,
  semantic search
- [ES|QL Search Strategy](references/esql-search-strategy.md) - Relevance search strategy for content indices: retrieve
  â†’ fuse â†’ rerank
- [ES|QL Version History](references/esql-version-history.md) - Feature availability by Elasticsearch version
- [Query Patterns](references/query-patterns.md) - Natural language to ES|QL translation
- [Generation Tips](references/generation-tips.md) - Best practices for query generation
- [Time Series Queries](references/time-series-queries.md) - TS command, time series aggregation functions, TBUCKET
- [PROMQL Command](references/promql-command.md) - PromQL source command for TSDS indices (9.4+ preview)
- [DSL to ES|QL Migration](references/dsl-to-esql-migration.md) - Convert Query DSL to ES|QL
- [Environment Setup](references/environment-setup.md) - Connection configuration options

## Error Handling

When query execution fails, the script returns:

- The generated ES|QL query
- The error message from Elasticsearch
- Suggestions for common issues

**Common issues:**

- Field doesn't exist â†’ Always use `get_schema` and `list_indices` before writing a query. Never guess field or index
  names â€” they vary across deployments.
- Type mismatch â†’ Use type conversion functions (TO_STRING, TO_INTEGER, etc.)
- Syntax error â†’ Review ES|QL reference for correct syntax. Always use **double quotes** for strings, never single
  quotes.
- No results â†’ Check time range and filter conditions
- Wrong function name â†’ ES|QL uses underscored names: `STD_DEV()` not `STDDEV()`, `MEDIAN_ABSOLUTE_DEVIATION()` not
  `MAD()`. Use `CONCAT()` for strings, not `+`. Use `CASE(cond, val, ...)` not `CASE WHEN...THEN...END`.
- Wrong date part â†’ `DATE_EXTRACT` uses ES|QL part names: `"hour_of_day"` not `"hour"`, `"day_of_month"` not `"day"`,
  `"month_of_year"` not `"month"`. Use `DATE_DIFF("day", start, end)` for date arithmetic, not subtraction.

## Examples

```bash
# Schema discovery
node scripts/esql.js test
node scripts/esql.js indices "logs-*"
node scripts/esql.js schema "logs-2024.01.01"

# Execute queries
node scripts/esql.js raw "FROM logs-* | STATS count = COUNT(*) BY host.name | LIMIT 10"
node scripts/esql.js raw "FROM metrics-* | STATS avg = AVG(cpu.percent) BY hour = DATE_TRUNC(1 hour, @timestamp)" --tsv
```
