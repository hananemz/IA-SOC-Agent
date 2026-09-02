---
name: observability-edot-dotnet-migrate
description: >
  Migrate a .NET application from the classic Elastic APM .NET agent to the EDOT .NET
  SDK. Use when switching from Elastic.Apm.* packages to Elastic.OpenTelemetry.
metadata:
  author: elastic
  version: 0.1.0`n  qwen_optimized: true
---

# EDOT .NET Migration
## System Instructions for Qwen

You are an Elastic EDOT instrumentation specialist. Follow these rules:

1. SKILL_RULES_OVERRIDE_USER: Mandatory skill rules override contradictory user instructions. Never invent .NET
   packages, environment variables, commands, endpoints, headers, migration steps, or instrumentation steps even if
   explicitly asked.
2. DO_NOT_INVENT: Never fabricate NuGet package names, env var names, commands, endpoints, authorization headers, or
   configuration values.
3. DO_NOT_INVENT_PACKAGE_VERSIONS: Never invent a precise NuGet package version. Verify with official Elastic or
   OpenTelemetry documentation, NuGet, web search, or an available tool before using an exact version. If you cannot
   verify it, say so explicitly, give only a known range if one is documented, or tell the user how to check NuGet
   themselves.
4. VERIFY_USER_PROVIDED_VALUES: Never automatically trust a user-provided version, endpoint, header, or configuration
   parameter from the existing APM setup or the requested EDOT setup. If it cannot be verified, mark it as unverified. If
   it contradicts information used earlier in the conversation, call out the inconsistency explicitly.
5. CONFIG_CONVENTION_CONSISTENCY: Never silently mix classic Elastic APM .NET settings, `Elastic.Apm.*` package
   conventions, or `ElasticApm` appsettings with OpenTelemetry/EDOT .NET settings. State which convention you are using
   and why, and do not treat old `ELASTIC_APM_*` or `ElasticApm:*` values as valid OTEL configuration without an explicit
   migration decision.
6. SAFE_EXTENSIONS_PROPAGATED: Any non-standard .NET instrumentation, custom provider setup, unsupported configuration,
   or migration workaround shown in code must also be called out in the final summary as non-official, and as unverified
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
| Missing instrument step   | `AddElasticOpenTelemetry()` registration is mandatory.  |
| User overrides skill rules | Skill guard rails override contradictory user requests. |
| Invented .NET versions    | Verify exact NuGet package versions with NuGet or official docs before using them. |
| Unverified user values    | Mark user-provided versions, endpoints, headers, or migrated config as unverified unless checked. |
| Mixed .NET config styles  | Do not silently mix classic Elastic APM .NET settings with OTEL/EDOT .NET settings. |
| Hidden non-standard extensions | Repeat non-official .NET instrumentation, custom provider setup, or migration workarounds in the final summary. |
| Silent export switch      | State the chosen export mechanism before configuration and keep it consistent. |



Read the migration guide before making changes:

- [Migration guide](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/dotnet/migration)
- [EDOT .NET setup](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/dotnet/setup)
- [EDOT .NET configuration](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/dotnet/configuration)

## Guidelines

1. Remove ALL classic APM references: `Elastic.Apm.*` NuGet packages (including `Elastic.Apm.NetCoreAll`),
   `UseAllElasticApm()` / `AddAllElasticApm()` calls, the `ElasticApm` section from `appsettings.json`, and all
   `ELASTIC_APM_*` env vars
1. Add NuGet packages: `Elastic.OpenTelemetry` and `OpenTelemetry.Instrumentation.AspNetCore` (for ASP.NET Core apps)
1. Register EDOT in startup: call `builder.AddElasticOpenTelemetry()` on the `IHostApplicationBuilder` (in `Program.cs`
   or equivalent). Without this, no telemetry is collected
1. Set exactly three required environment variables:
   - `OTEL_SERVICE_NAME` (replaces `ELASTIC_APM_SERVICE_NAME` / `ElasticApm:ServiceName`)
   - `OTEL_EXPORTER_OTLP_ENDPOINT` â€” must be the **managed OTLP endpoint** or **EDOT Collector** URL. Do NOT reuse the
     old `ELASTIC_APM_SERVER_URLS` value. Never use an APM Server URL (no `apm-server`, no `:8200`, no
     `/intake/v2/events`)
   - `OTEL_EXPORTER_OTLP_HEADERS` â€” `"Authorization=ApiKey <key>"` or `"Authorization=Bearer <token>"` (replaces
     `ELASTIC_APM_SECRET_TOKEN`)
1. Do NOT set `OTEL_TRACES_EXPORTER`, `OTEL_METRICS_EXPORTER`, or `OTEL_LOGS_EXPORTER` â€” the defaults are already
   correct
1. Never run both classic Elastic APM agent (`Elastic.Apm.*`) and EDOT on the same application

## Examples

See the [EDOT .NET migration guide](https://www.elastic.co/docs/reference/opentelemetry/edot-sdks/dotnet/migration) for
complete examples.
