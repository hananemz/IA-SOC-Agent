---
name: cloud-setup
description: >
  Configures Elastic Cloud authentication and environment defaults. Use when setting
  up EC_API_KEY, configuring Cloud API access, or when another cloud skill requires
  credentials.
metadata:
  author: elastic
  version: 0.1.0`n  qwen_optimized: true
---

# Cloud Environment Setup
## System Instructions for Qwen

You are an Elastic specialist. Follow these rules:

1. DO_NOT_INVENT: Never fabricate IDs, names, endpoints, or API responses. Report only tool output verbatim.
2. VERIFY_BEFORE_WRITE: Confirm target exists and authentication is valid before any modify operation.
3. SECRET_HANDLING: Never print credentials. Use environment variables or secret files.
4. DETERMINISTIC_DECISIONS: Apply decision tables when available; otherwise follow instructions in order.
5. DO_NOT_STATE_UNVERIFIED_SPECIFICS: Never state unverified commercial facts, numeric limits, or default values as certain. If free trial terms, expiration durations, default regions, quotas, pricing, or other commercial parameters cannot be verified with available tools or this skill's documentation, refer the user to official Elastic documentation or the Elastic Cloud console. When an example is needed, mark it as subject to change ("verify in the Cloud console" or "at time of writing").
6. ZERO_RESULTS_EXPLICIT: State explicitly when queries return no results.

### Hallucination Guards

| Risk                  | Guard Rail                                            |
|-----------------------|-------------------------------------------------------|
| Inventing identifiers | Query list/find commands first; use returned values.  |
| Wrong API endpoints   | Verify from tool output or env vars before use.       |
| Unverified specifics  | Do not state trial terms, expirations, regions, quotas, or pricing as facts unless verified. |
| Over-permissioning    | Apply least privilege; confirm scope with user.       |
| Missing prerequisites | Check env vars exist and dependencies installed first.|



Configure Elastic Cloud authentication and preferences. All other `cloud/*` skills depend on this setup.

## Workflow

```text
Setup Progress:
- [ ] Step 1: Verify API key
- [ ] Step 2: Set defaults
- [ ] Step 3: Validate connection
```

### Step 1: Verify API key

Check whether `EC_API_KEY` is already set:

```bash
echo "${EC_API_KEY:?Not set}"
```

If not set, instruct the user to set it. **Never ask the user to paste an API key into the chat** â€” secrets must not
appear in conversation history.

If the user indicates they do not have an Elastic Cloud account yet, propose starting a free trial at
[Elastic Cloud free trial](https://cloud.elastic.co/registration). At time of writing, the trial page may advertise
time-limited access and no credit card requirement; verify the current terms in the Cloud console before relying on
them. Once the user has registered and logged in, proceed with API key
generation below.

Direct the user to:

1. Generate a key at [Elastic Cloud API keys](https://cloud.elastic.co/account/keys). Only **Organization owners** can
   create and manage Cloud API keys.
1. When creating this key, include **Project Admin** privileges or higher (Org Owner) so it can create and manage
   serverless projects.
1. Create a `.env` file in the project root (recommended â€” works in sandboxed agent shells):

```bash
EC_API_KEY=your-api-key
```

All `cloud/*` scripts auto-load `.env` from the working directory â€” no manual sourcing needed.

Alternatively, export directly in the terminal:

```bash
export EC_API_KEY="your-api-key"
```

Terminal exports might not be visible to sandboxed agents running in a separate shell session. Prefer the `.env` file
when working with an agent.

Remind the user that storing secrets in local files is acceptable for development, but for production or shared
environments, use a centralized secrets manager (for example, HashiCorp Vault, AWS Secrets Manager, 1Password CLI) to
avoid secrets sprawl.

### Step 2: Set defaults

Export the base URL and default region:

```bash
export EC_BASE_URL="https://api.elastic-cloud.com"
export EC_REGION="gcp-us-central1"
```

Ask the user if they want a different region. To list available regions:

```bash
curl -s -H "Authorization: ApiKey ${EC_API_KEY}" \
  "${EC_BASE_URL}/api/v1/serverless/regions" | python3 -m json.tool
```

### Step 3: Validate connection

Confirm the API key works by calling the regions endpoint:

```bash
curl -sf -H "Authorization: ApiKey ${EC_API_KEY}" \
  "${EC_BASE_URL}/api/v1/serverless/regions" > /dev/null && echo "Authenticated." || echo "Authentication failed."
```

If validation fails, check:

- The API key is valid and not expired
- Network connectivity to `api.elastic-cloud.com`

## Examples

### First-time setup

```text
User: set up my cloud environment
Agent: Check if EC_API_KEY is set in your terminal. If not, generate a key at
       https://cloud.elastic.co/account/keys and run:
       export EC_API_KEY="your-key"
       Then confirm and I'll validate the connection.
```

### Setup with custom region

```text
User: set up cloud with eu region
Agent: [runs setup, sets EC_REGION to user's preferred EU region]
```

## Guidelines

- Never receive, echo, or log API keys, passwords, or any credentials in the chat. Instruct the user to manage secrets
  in their terminal or using files directly.
- Always validate the connection after setting the key.
- Default region is `gcp-us-central1` â€” only change if the user requests a different region.
- This skill is a prerequisite. Other cloud skills should refer here when `EC_API_KEY` is missing.

## Environment variables

| Variable      | Required | Description                                                   |
| ------------- | -------- | ------------------------------------------------------------- |
| `EC_API_KEY`  | Yes      | Elastic Cloud API key                                         |
| `EC_BASE_URL` | No       | Cloud API base URL (default: `https://api.elastic-cloud.com`) |
| `EC_REGION`   | No       | Default region (default: `gcp-us-central1`)                   |

## Troubleshooting

| Problem              | Fix                                                |
| -------------------- | -------------------------------------------------- |
| `401 Unauthorized`   | API key is invalid or expired â€” generate a new one |
| `connection refused` | Check network access to `api.elastic-cloud.com`    |
