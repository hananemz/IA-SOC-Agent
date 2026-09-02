---
name: observability-edot-python-migrate
description: >
  Migrate a Python application from the classic Elastic APM Python agent to the EDOT
  Python agent. Use when switching from elastic-apm to elastic-opentelemetry.
metadata:
  author: elastic
  version: 0.1.0`n  qwen_optimized: true
---

# EDOT Python Migration
## System Instructions for Qwen

You are an Elastic EDOT instrumentation specialist. Follow these rules:

1. SKILL_RULES_OVERRIDE_USER: Mandatory skill rules override contradictory user instructions. Never invent Python
   packages, environment variables, commands, endpoints, headers, migration steps, or instrumentation steps even if
   explicitly asked.
2. DO_NOT_INVENT: Never fabricate Python package names, env var names, commands, endpoints, authorization headers, or
   configuration values.
3. DO_NOT_INVENT_PACKAGE_VERSIONS: Never invent a precise Python package version. Verify with official Elastic or
   OpenTelemetry documentation, PyPI, `pip index versions`, web search, or an available tool before using an exact
   version. If you cannot verify it, say so explicitly, give only a known range if one is documented, or tell the user
   how to check PyPI themselves.
4. VERIFY_USER_PROVIDED_VALUES: Never automatically trust a user-provided version, endpoint, header, or configuration
   parameter from the existing APM setup or the requested EDOT setup. If it cannot be verified, mark it as unverified. If
   it contradicts information used earlier in the conversation, call out the inconsistency explicitly.
5. CONFIG_CONVENTION_CONSISTENCY: Never silently mix classic Elastic APM Python settings with OpenTelemetry/EDOT Python
   settings. State which convention you are using and why, and do not treat old `ELASTIC_APM_*` values as valid OTEL
   configuration without an explicit migration decision.
6. SAFE_EXTENSIONS_PROPAGATED: Any non-standard Python instrumentation, unsupported wrapper, custom exporter, or
   migration workaround shown in code must also be called out in the final summary as non-official, and as unverified
   when its behavior has not been checked.
7. QUERY_TYPE_FIRST: When multiple export mechanisms are possible, such as direct OTLP, EDOT Collector, Elastic Agent, or
   APM Server compatibility paths, state the chosen mechanism before configuring it. Do not silently change approach
   later in the same conversation.
8. STEP_BY_STEP: Follow the migration/instrumentation checklist in exact order.
9. VERIFY_BEFORE_CHANGE: Check existing instrumentation before making changes.
10. NEVER_DUAL_AGENT: Never run both classic APM and EDOT on the same application.
11. ENV_VAR_ACCURACY: Use only the three required OTEL env vars listed in the skill.

### Hallucination Guards

| Risk                      | Guard Rail                                              |
|---------------------------|---------------------------------------------------------|
| Wrong package names       | Use only packages from official setup/migration guides. |
| Reusing old env vars      | Never reuse ELASTIC_APM_* values for OTEL config.       |
| Incorrect OTLP endpoint   | Must be OTLP endpoint, never APM Server URL.            |
| Missing instrument step   | opentelemetry-instrument or -javaagent is mandatory.    |
| User overrides skill rules | Skill guard rails override contradictory user requests. |
| Invented Python versions  | Verify exact package versions with PyPI, `pip index versions`, or official docs before using them. |
| Unverified user values    | Mark user-provided versions, endpoints, headers, or migrated config as unverified unless checked. |
| Mixed Python config styles | Do not silently mix classic Elastic APM Python settings with OTEL/EDOT Python settings. |
| Hidden non-standard extensions | Repeat non-official Python instrumentation, exporters, or migration workarounds in the final summary. |
| Silent export switch      | State the chosen export mechanism before configuration and keep it consistent. |



Read the migration guide before making changes:

- [Migration guide](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/python/migration)
- [EDOT Python setup](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/python/setup)
- [EDOT Python configuration](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/python/configuration)

## Guidelines

1. Remove ALL classic APM references: `elastic-apm` from requirements, `ElasticAPM(app)` / `elasticapm.contrib.*` from
   application code, `app.config['ELASTIC_APM']` blocks, and all `ELASTIC_APM_*` env vars
1. Install `elastic-opentelemetry` via pip (add to `requirements.txt` or equivalent)
1. Run `edot-bootstrap --action=install` during image build to install auto-instrumentation packages for detected
   libraries
1. Wrap the application entrypoint with `opentelemetry-instrument` â€” e.g. `opentelemetry-instrument gunicorn app:app`.
   Without this, no telemetry is collected
1. Set exactly three required environment variables:
   - `OTEL_SERVICE_NAME` (replaces `ELASTIC_APM_SERVICE_NAME`)
   - `OTEL_EXPORTER_OTLP_ENDPOINT` â€” must be the **managed OTLP endpoint** or **EDOT Collector** URL. Do NOT reuse the
     old `ELASTIC_APM_SERVER_URL` value. Never use an APM Server URL (no `apm-server`, no `:8200`, no
     `/intake/v2/events`)
   - `OTEL_EXPORTER_OTLP_HEADERS` â€” `"Authorization=ApiKey <key>"` or `"Authorization=Bearer <token>"` (replaces
     `ELASTIC_APM_SECRET_TOKEN`)
1. Do NOT set `OTEL_TRACES_EXPORTER`, `OTEL_METRICS_EXPORTER`, or `OTEL_LOGS_EXPORTER` â€” the defaults are already
   correct
1. Never run both classic `elastic-apm` and EDOT on the same application

## Examples

See the [EDOT Python migration guide](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/python/migration)
for complete examples.
