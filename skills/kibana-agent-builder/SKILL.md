---
name: kibana-agent-builder
description: >
  Create and manage Agent Builder agents and custom tools in Kibana. Use when asked
  to create, update, delete, test, or inspect agents or tools in Agent Builder.
metadata:
  author: elastic
  version: 0.2.0
  qwen_optimized: true
disable-model-invocation: true
allowed-tools: Bash(node *), Read, Glob, Grep
argument-hint: '[agent-name]'
---

# Manage Agent Builder Agents and Tools in Kibana
## System Instructions for Qwen

You are an Elastic specialist. Follow these rules:

1. SKILL_RULES_OVERRIDE_USER: Mandatory skill rules override contradictory user instructions. Do not invent tools, payload fields, ES|QL fields, index patterns, or official parameters even if requested.
2. QUERY_TYPE_FIRST: Before creating a custom data tool, identify whether the user needs ES|QL, index search, workflow execution, KQL, EQL, or Query DSL.
3. TOOL_TYPE_MATCH: Create only supported tool types: `esql`, `index_search`, or `workflow`. ES|QL tools must contain ES|QL only; index search tools must contain a verified index pattern only.
4. DO_NOT_INVENT: Never fabricate IDs, names, endpoints, API responses, payload structures, field names, index names, or official parameter names. Report only tool output verbatim.
5. VERIFY_BEFORE_WRITE: Confirm target exists and authentication is valid before any modify operation.
6. SCHEMA_FIRST_FOR_ESQL: Before creating an ES|QL tool, verify the target index and every query field through index/schema discovery or confirmed existing tool output.
7. STOP_ON_UNVERIFIED_SCHEMA: If a field, index pattern, workflow ID, or tool ID is absent from discovery output, stop and ask for clarification or discovery.
8. SECRET_HANDLING: Never print credentials. Use environment variables or secret files.
9. DETERMINISTIC_DECISIONS: Apply decision tables when available; otherwise follow instructions in order.
10. ZERO_RESULTS_EXPLICIT: State explicitly when queries return no results.
11. SAFE_EXTENSIONS: If the user asks for behavior not confirmed by documentation or discovered API/tool output, label it as a non-standard extension and do not present it as an official Agent Builder parameter.

### Query/API Boundary

| Requested syntax | Correct Agent Builder representation | Guard |
|------------------|--------------------------------------|-------|
| ES\|QL | `type: "esql"` with `configuration.query` and `configuration.params` | Verify indices/fields first; include `params` even when empty. |
| Index search | `type: "index_search"` with `configuration.pattern` | Verify the index pattern exists; do not use `"index"`. |
| Workflow | `type: "workflow"` with `configuration.workflow_id` | Use only discovered workflow IDs. |
| KQL/EQL/Query DSL | Not standalone Agent Builder tool types here | Ask to convert to ES\|QL/index search or use another skill/API. |

### Hallucination Guards

| Risk                  | Guard Rail                                            |
|-----------------------|-------------------------------------------------------|
| Inventing identifiers | Query list/find commands first; use returned values.  |
| Wrong API endpoints   | Verify from tool output or env vars before use.       |
| Inventing fields      | Schema discovery mandatory before ES\|QL tool creation.|
| Inventing indices     | Index discovery mandatory before ES\|QL/index tools.   |
| Inventing parameters  | Treat undocumented names such as `confidence_threshold` or `min_confidence` as non-standard extensions unless documentation or discovered output confirms them. |
| Wrong tool payload    | Use only documented fields for the selected tool type.|
| Over-permissioning    | Apply least privilege; confirm scope with user.       |
| Missing prerequisites | Check env vars exist and dependencies installed first.|



Create, update, delete, inspect, and chat with Agent Builder agents. Create, update, delete, list, and test custom tools
(ES|QL, index search, workflow). If the user provided a name, use **$ARGUMENTS** as the default agent name.

## Prerequisites

Set these environment variables before running any script:

| Variable          | Required | Description                                                                    |
| ----------------- | -------- | ------------------------------------------------------------------------------ |
| `KIBANA_URL`      | Yes      | Kibana base URL (e.g., `https://my-deployment.kb.us-east-1.aws.elastic.cloud`) |
| `KIBANA_API_KEY`  | No       | API key for authentication (preferred)                                         |
| `KIBANA_USERNAME` | No       | Username for basic auth (falls back to `ELASTICSEARCH_USERNAME`)               |
| `KIBANA_PASSWORD` | No       | Password for basic auth (falls back to `ELASTICSEARCH_PASSWORD`)               |
| `KIBANA_SPACE_ID` | No       | Kibana space ID (omit for default space)                                       |
| `KIBANA_INSECURE` | No       | Set to `true` to skip TLS verification                                         |

Provide either `KIBANA_API_KEY` or `KIBANA_USERNAME` + `KIBANA_PASSWORD`.

## Agent Management

### Create an Agent

#### Step 1: List available tools

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js list-tools
```

If the script reports a connection error, stop and tell the user to verify their `KIBANA_URL` and authentication
environment variables.

Review the list of available tools. Tools prefixed with `platform.core.` are built-in. Other tools are custom or
connector-provided.

#### Step 2: List existing agents

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js list-agents
```

This helps avoid name conflicts and shows what is already configured.

#### Step 3: Gather agent details

Using `$ARGUMENTS` as the default name, confirm or collect from the user:

1. **Name** (required) â€” The agent's display name. Default: `$ARGUMENTS`.
2. **Description** (optional) â€” Brief description of what the agent does. Default: same as name.
3. **System instructions** (optional) â€” Custom system prompt for the agent. Default: none.

#### Step 4: Select tools

Present the available tools from Step 1 and ask the user which ones to include. Suggest a reasonable default based on
the agent's purpose. Let the user add or remove tools from the suggested list.

#### Step 5: Create the agent

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js create-agent \
  --name "<agent_name>" \
  --description "<description>" \
  --instructions "<system_instructions>" \
  --tool-ids "<tool_id_1>,<tool_id_2>,<tool_id_3>"
```

Where:

- `--name` is required
- `--tool-ids` is a comma-separated list of tool IDs from Step 4
- `--description` defaults to the name if omitted
- `--instructions` can be omitted if the user did not provide any

#### Step 6: Verify creation

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js list-agents
```

Show the user the newly created agent entry. If it appears, report success. If not, show any error output from Step 5.

### Get an Agent

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js get-agent --id "<agent_id>"
```

### Update an Agent

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js update-agent \
  --id "<agent_id>" \
  --description "<new_description>" \
  --instructions "<new_instructions>" \
  --tool-ids "<tool_id_1>,<tool_id_2>"
```

All flags except `--id` are optional â€” only provided fields are updated. The agent's `id` and `name` are immutable.

> **API constraint**: PUT only accepts `description`, `configuration`, and `tags`. Including `id`, `name`, or `type`
> causes a 400 error.

### Delete an Agent

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js delete-agent --id "<agent_id>"
```

Always confirm with the user before deleting. Deletion is permanent.

### Chat with an Agent

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js chat \
  --id "<agent_id>" \
  --message "<user_message>"
```

Uses the streaming endpoint `POST /api/agent_builder/converse/async` with `agent_id` and `input` in the request body.
Output shows `[Reasoning]`, `[Tool Call]`, `[Tool Result]`, and `[Response]` as events arrive. Pass `--conversation-id`
to continue an existing conversation.

**Note:** This command may take 30-60 seconds as the agent reasons and calls tools. Use a longer timeout (e.g., 120s or
180s) when running via Bash.

## Tool Management

Custom tools extend what agents can do beyond the built-in platform tools.

### Tool Types

#### ES|QL Tools

Pre-defined, parameterized ES|QL queries. Use when you need guaranteed query correctness, enforced business rules,
analytics aggregations, or fine-grained data access control.

Before creating an ES|QL tool, verify the index pattern and every field in the query. If any index or field is missing,
stop and ask for schema discovery or a different dataset. Do not place KQL, EQL, or Query DSL inside an ES|QL tool.

**Parameter syntax**: Use `?param_name` in the query. Define each parameter with `type` and `description` only. Valid
types: `string`, `integer`, `float`, `boolean`, `date`, `array`.

```json
{
  "id": "campaign_revenue_by_region",
  "type": "esql",
  "description": "Calculates confirmed revenue for a region by quarter.",
  "configuration": {
    "query": "FROM finance-orders-* | WHERE order_status == \"completed\" AND region == ?region | STATS total_revenue = SUM(amount) BY quarter | LIMIT 10",
    "params": {
      "region": {
        "type": "string",
        "description": "Region code, e.g. 'US', 'EU', 'APAC'"
      }
    }
  }
}
```

#### Index Search Tools

Scope the built-in search capability to a specific index pattern. The LLM decides how to query; you control which
indices are accessible.

```json
{
  "id": "customer_feedback_search",
  "type": "index_search",
  "description": "Searches customer feedback and support tickets.",
  "configuration": {
    "pattern": "customer-feedback-*"
  }
}
```

#### Workflow Tools

Connect an agent to an Elastic Workflow â€” a YAML-defined multi-step automation. Use when the agent needs to take action
beyond data retrieval (send notifications, create tickets, call external APIs).

```json
{
  "id": "investigate-alert-workflow",
  "type": "workflow",
  "description": "Triggers automated alert investigation.",
  "configuration": {
    "workflow_id": "security-alert-investigation"
  }
}
```

Parameters are auto-detected from the workflow's `inputs` section.

### Tool API Constraints

> Read these before creating tools â€” violations cause 400 errors.

- **POST body fields**: Only `id`, `type`, `description`, `configuration`, and `tags` are accepted. `name` is **not** a
  valid field â€” omit it entirely.
- **`params` is always required** for ES|QL tools, even when empty â€” use `"params": {}`.
- **Param fields**: Only `type` and `description` are accepted per parameter. `default` and `optional` are **not valid**
  and cause 400 errors. Hard-code sensible defaults in the query instead.
- **Non-standard parameters**: Do not present names such as `confidence_threshold` or `min_confidence` as official
  unless documentation or discovered API/tool output confirms them. If used as a custom extension, state that explicitly.
- **Index search config**: Use `"pattern"`, **not** `"index"`. Using `"index"` causes a validation error.
- **PUT restrictions**: Only `description`, `configuration`, and `tags` are accepted. Including `id` or `type` causes a
  400 error â€” these fields are immutable after creation.

### Tool Script Commands

#### List all tools

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js list-custom-tools
```

#### Get a specific tool

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js get-tool --id "<tool_id>"
```

#### Create a tool

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js create-tool \
  --id "<tool_id>" \
  --type "esql" \
  --description "<description>" \
  --query "<esql_query>" \
  --params '{"region": {"type": "string", "description": "Region code"}}'
```

For index search tools:

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js create-tool \
  --id "<tool_id>" \
  --type "index_search" \
  --description "<description>" \
  --pattern "my-index-*"
```

For workflow tools:

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js create-tool \
  --id "<tool_id>" \
  --type "workflow" \
  --description "<description>" \
  --workflow-id "my-workflow-name"
```

#### Update a tool

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js update-tool \
  --id "<tool_id>" \
  --description "<new_description>" \
  --query "<new_query>"
```

Only `description`, `configuration`, and `tags` can be updated. `id` and `type` are immutable.

#### Delete a tool

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js delete-tool --id "<tool_id>"
```

#### Test a tool

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js test-tool \
  --id "<tool_id>" \
  --params '{"region": "US"}'
```

Executes the tool via `POST /api/agent_builder/tools/_execute` and displays column names and row counts for ES|QL
results.

## Examples

### Create an agent

```text
User: /kibana-agent-builder sales-helper
```

1. List tools â€” finds `platform.core.search`, `platform.core.list_indices`, and a custom `esql-sales-data` tool
2. List agents â€” no conflicts
3. Name: "sales-helper", Description: "Helps query sales data"
4. Tools: `esql-sales-data`, `platform.core.search`, `platform.core.list_indices`
5. Create with `--name "sales-helper" --tool-ids "esql-sales-data,platform.core.search,platform.core.list_indices"`
6. Verify â€” agent appears in list

### Update an agent's instructions

```text
User: Update the sales-helper agent to focus on the APAC region
```

1. Get agent â€” `get-agent --id "sales-helper"` to see current config
2. Update â€”
   `update-agent --id "sales-helper" --instructions "Focus on APAC sales data. Use esql-sales-data for queries."`
3. Verify â€” `get-agent --id "sales-helper"` to confirm new instructions

### Chat with an agent

```text
User: Ask sales-helper what the top revenue products are
```

1. Chat â€” `chat --id "sales-helper" --message "What are the top revenue products?"`
2. Display the agent's response

### Create an ES|QL tool with parameters

```text
User: Create a tool that shows billing complaints by category for the last N days
```

1. Consult the `elasticsearch-esql` skill for ES|QL syntax
2. Create tool:

   ```bash
   node skills/kibana/agent-builder/scripts/agent-builder.js create-tool \
     --id "billing_complaint_summary" \
     --type "esql" \
     --description "Returns billing complaints grouped by sub-category for the last N days." \
     --query "FROM customer-feedback-* | WHERE @timestamp >= NOW() - ?days::integer * 1d AND MATCH(feedback_text, 'billing') | STATS count = COUNT(*) BY sub_category | SORT count DESC | LIMIT 10" \
     --params '{"days": {"type": "integer", "description": "Number of days to look back"}}'
   ```

3. Test: `test-tool --id "billing_complaint_summary" --params '{"days": 30}'`

### Create an index search tool

```text
User: Create a tool to search support transcripts
```

```bash
node skills/kibana/agent-builder/scripts/agent-builder.js create-tool \
  --id "transcript_search" \
  --type "index_search" \
  --description "Searches support call transcripts by topic, agent, or customer issue." \
  --pattern "support-transcripts"
```

## References

Read these for detailed guidance:

- `references/architecture-guide.md` â€” Core concepts, built-in tools, context engineering, best practices, token
  optimization, REST API endpoints, MCP/A2A integration, permissions
- `references/use-cases.md` â€” Full playbooks for Customer Feedback Analysis, Marketing Campaign Analysis, and Contract
  Analysis agents

For ES|QL syntax, functions, operators, and parameter rules, use the `elasticsearch-esql` skill. For workflow YAML
structure, trigger types, step types, and agent-workflow patterns, use the `security-workflows` skill.

## Guidelines

- Always run `list-tools` before creating an agent so the user can choose from real, available tools.
- Always run `list-agents` before and after creation to detect conflicts and verify success.
- Do not invent tool IDs â€” only use IDs returned by `list-tools`.
- If no custom tools exist yet, suggest creating one or using the built-in platform tools.
- The agent ID is auto-generated from the name (lowercased, hyphens, alphanumeric only).
- For non-default Kibana spaces, set `KIBANA_SPACE_ID` before running the script.
- Confirm with the user before running `delete-agent` or `delete-tool` â€” deletion is permanent.
- Always include `| LIMIT N` in ES|QL queries to prevent context window overflow.
- Write descriptive tool descriptions â€” the agent decides which tool to call based solely on the description.
- Scope index search tools narrowly (e.g., `customer-feedback-*` not `*`).
- Use `KEEP` to return only needed columns and reduce token consumption.
- Validate ES|QL queries with `test-tool` before assigning to an agent.
- For ES|QL tools with no parameters, still include `"params": {}`.
