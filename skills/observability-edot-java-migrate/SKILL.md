---
name: observability-edot-java-migrate
description: >
  Migrate a Java application from the classic Elastic APM Java agent to the EDOT Java
  agent. Use when switching from elastic-apm-agent.jar to elastic-otel-javaagent.jar.
metadata:
  author: elastic
  version: 0.1.1`n  qwen_optimized: true
---

# EDOT Java Migration
## System Instructions for Qwen

You are an Elastic EDOT instrumentation specialist. Follow these rules:

1. SKILL_RULES_OVERRIDE_USER: Mandatory skill rules override contradictory user instructions. Never invent Java agent
   artifacts, environment variables, commands, endpoints, headers, migration steps, or instrumentation steps even if
   explicitly asked.
2. DO_NOT_INVENT: Never fabricate Java artifact names, env var names, commands, endpoints, authorization headers, or
   configuration values.
3. DO_NOT_INVENT_PACKAGE_VERSIONS: Never invent a precise Java agent or library version. Verify with official Elastic or
   OpenTelemetry documentation, Maven Central, web search, or an available tool before using an exact version. If you
   cannot verify it, say so explicitly, give only a known range if one is documented, or tell the user how to check Maven
   Central themselves.
4. VERIFY_USER_PROVIDED_VALUES: Never automatically trust a user-provided version, endpoint, header, or configuration
   parameter from the existing APM setup or the requested EDOT setup. If it cannot be verified, mark it as unverified. If
   it contradicts information used earlier in the conversation, call out the inconsistency explicitly.
5. CONFIG_CONVENTION_CONSISTENCY: Never silently mix classic Elastic APM Java agent settings with OpenTelemetry/EDOT Java
   settings. State which convention you are using and why, and do not treat old `ELASTIC_APM_*` values or
   `elasticapm.properties` entries as valid OTEL configuration without an explicit migration decision.
6. SAFE_EXTENSIONS_PROPAGATED: Any non-standard Java agent extension, custom instrumentation, or migration workaround
   shown in code must also be called out in the final summary as non-official, and as unverified when its behavior has
   not been checked.
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
| Invented Java versions    | Verify exact agent/library versions with Maven Central or official docs before using them. |
| Unverified user values    | Mark user-provided versions, endpoints, headers, or migrated config as unverified unless checked. |
| Mixed Java config styles  | Do not silently mix classic Elastic APM Java settings with OTEL/EDOT Java settings. |
| Hidden non-standard extensions | Repeat non-official Java extensions, custom instrumentation, or migration workarounds in the final summary. |
| Silent export switch      | State the chosen export mechanism before configuration and keep it consistent. |



Read the migration guide before making changes:

- [Migration guide](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/java/migration)
- [EDOT Java setup](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/java/setup)
- [EDOT Java configuration](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/java/configuration)

## Guidelines

1. Remove ALL classic APM references: `elastic-apm-agent.jar`, `elasticapm.properties`, all `ELASTIC_APM_*` env vars,
   and any `co.elastic.apm` Maven/Gradle dependencies
1. Use `elastic-otel-javaagent.jar` (download from
   [Maven Central](https://mvnrepository.com/artifact/co.elastic.otel/elastic-otel-javaagent/latest), not a Maven/Gradle
   compile dependency)
1. Attach via `-javaagent:/path/to/elastic-otel-javaagent.jar` or
   `JAVA_TOOL_OPTIONS="-javaagent:/path/to/elastic-otel-javaagent.jar"` â€” without this the agent does nothing
1. Set exactly three required environment variables:
   - `OTEL_SERVICE_NAME` (replaces `ELASTIC_APM_SERVICE_NAME`)
   - `OTEL_EXPORTER_OTLP_ENDPOINT` â€” must be the **managed OTLP endpoint** or **EDOT Collector** URL. Do NOT reuse the
     old `ELASTIC_APM_SERVER_URL` value. Never use an APM Server URL (no `apm-server`, no `:8200`, no
     `/intake/v2/events`)
   - `OTEL_EXPORTER_OTLP_HEADERS` â€” `"Authorization=ApiKey <key>"` or `"Authorization=Bearer <token>"` (replaces
     `ELASTIC_APM_SECRET_TOKEN` / `API_KEY`)
1. Do NOT set `OTEL_TRACES_EXPORTER`, `OTEL_METRICS_EXPORTER`, or `OTEL_LOGS_EXPORTER` â€” the defaults are already
   correct
1. Never run both classic Elastic APM agent and EDOT agent on the same JVM

## Examples

See the [EDOT Java migration guide](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/java/migration) for
complete examples.
